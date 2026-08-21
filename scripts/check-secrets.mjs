#!/usr/bin/env node
/**
 * check-secrets.mjs — 源码凭据扫描
 * =================================
 * 在提交/CI 前扫描整个仓库，阻止 API key、密码、token、私钥、路径等进入发布内容。
 * 规则与 dsh-akn-plugin 的扫描器保持一致。
 *
 * 用法:
 *   node scripts/check-secrets.mjs            # 扫描默认目录
 *   node scripts/check-secrets.mjs --fail     # 发现即退出码 1（CI 用）
 */

import { readFile, readdir, stat } from 'node:fs/promises'
import { resolve, sep } from 'node:path'

const ROOT = resolve(import.meta.dirname, '..')
const IGNORED_DIRS = new Set(['.git', 'node_modules', '__pycache__', '.lake', '.aen', 'output', 'leanenv/.lake'])
const IGNORED_EXT = new Set(['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.docx', '.pdf', '.pyc'])
const MAX_FILE_BYTES = 2 * 1024 * 1024

const RULES = [
  { id: 'private-key-pem', pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/ },
  { id: 'provider-api-key', pattern: /\b(?:sk|dsk)-[A-Za-z0-9_-]{16,}\b/ },
  { id: 'github-token', pattern: /\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b/ },
  { id: 'aws-access-key', pattern: /\bAKIA[0-9A-Z]{16}\b/ },
  { id: 'jwt-token', pattern: /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/ },
  { id: 'http-basic-password', pattern: /HTTPBasic(?:Auth)?\([^)]*['"][^'"]{8,}['"]\)/ },
  { id: 'bearer-token', pattern: /\bBearer\s+[A-Za-z0-9._~+/-]{16,}={0,2}\b/i },
  { id: 'generic-secret-assignment', pattern: /\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*['"][^'"]{8,}['"]/i },
  { id: 'email-pii', pattern: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i },
  { id: 'macos-user-path', pattern: /\/Users\/[^/\s]+\// },
  { id: 'linux-home-path', pattern: /\/home\/[^/\s]+\// },
  { id: 'windows-user-path', pattern: /[A-Za-z]:\\Users\\[^\\\s]+\\/ },
]

async function* walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.name.startsWith('.') || IGNORED_DIRS.has(entry.name)) continue
    const full = resolve(dir, entry.name)
    if (entry.isDirectory()) yield* walk(full)
    else if (entry.isFile()) yield full
  }
}

export async function scan() {
  const findings = []
  for await (const file of walk(ROOT)) {
    const ext = file.slice(file.lastIndexOf('.')).toLowerCase()
    if (IGNORED_EXT.has(ext)) continue
    const size = (await stat(file)).size
    if (size > MAX_FILE_BYTES) continue
    const content = await readFile(file, 'utf8').catch(() => '')
    if (!content) continue
    for (const rule of RULES) {
      if (rule.pattern.test(content)) {
        findings.push({ file: file.slice(ROOT.length + 1), rule: rule.id })
      }
    }
  }
  return findings
}

const failOnFindings = process.argv.includes('--fail')
const findings = await scan()
if (findings.length > 0) {
  console.error('SECRET SCAN FAILED — 以下文件包含疑似凭据/敏感信息:')
  for (const f of findings) console.error(`  [${f.rule}] ${f.file}`)
  console.error('请移除凭据后再提交。泄露的密钥必须在服务商控制台轮换。')
  process.exit(failOnFindings ? 1 : 0)
}
console.log(`check-secrets: OK — 未发现凭据 (${findings.length} findings)`)
