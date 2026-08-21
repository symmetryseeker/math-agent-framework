import { spawn } from 'node:child_process'
import { once } from 'node:events'

export interface BridgeConfig {
  pythonCmd: string
  bridgePath: string
}

export interface BridgeResult {
  status: 'ok' | 'error'
  result?: unknown
  error?: string
  provenance?: Record<string, unknown>
}

export function resolveBridgePath(configured?: string): string | undefined {
  if (configured !== undefined && configured.length > 0) return configured
  const fromEnv = process.env.MATH_AGENT_HOME
  if (fromEnv !== undefined && fromEnv.length > 0) return fromEnv
  return undefined
}

export function resolvePythonCmd(): string {
  return process.env.MATH_AGENT_PYTHON ?? 'python'
}

export async function runBridge(
  config: BridgeConfig,
  tool: string,
  args: Record<string, unknown>,
  signal?: AbortSignal,
  timeoutMs = 180_000,
): Promise<BridgeResult> {
  if (signal !== undefined) signal.throwIfAborted()
  const child = spawn(config.pythonCmd, [config.bridgePath], {
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: true,
  })
  const timer = setTimeout(() => child.kill('SIGKILL'), timeoutMs)
  const stdout: Buffer[] = []
  const stderr: Buffer[] = []
  child.stdout?.on('data', (chunk: Buffer) => stdout.push(chunk))
  child.stderr?.on('data', (chunk: Buffer) => stderr.push(chunk))
  const abortHandler = () => child.kill('SIGKILL')
  signal?.addEventListener('abort', abortHandler, { once: true })
  try {
    child.stdin?.write(`${JSON.stringify({ tool, args })}\n`)
    child.stdin?.end()
    const [code] = (await once(child, 'close')) as [number | null]
    clearTimeout(timer)
    if (code !== 0) {
      return {
        status: 'error',
        error: `bridge exited ${code}: ${Buffer.concat(stderr).toString('utf8').slice(0, 2000)}`,
      }
    }
    const text = Buffer.concat(stdout).toString('utf8').trim()
    const lines = text.split('\n').filter((line) => line.trim().length > 0)
    const last = lines[lines.length - 1]
    if (last === undefined) return { status: 'error', error: 'bridge produced no output' }
    try {
      return JSON.parse(last) as BridgeResult
    } catch {
      return { status: 'error', error: `bridge produced invalid JSON: ${text.slice(0, 2000)}` }
    }
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abortHandler)
    child.stdin?.destroy()
  }
}

export async function bridgeToolResult(
  config: BridgeConfig,
  tool: string,
  args: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<{ text: string }> {
  const result = await runBridge(config, tool, args, signal)
  if (result.status === 'error') {
    throw new Error(result.error ?? 'math-engine bridge error')
  }
  const payload: Record<string, unknown> = { untrusted: true, tool }
  if (typeof result.result === 'object' && result.result !== null) {
    Object.assign(payload, result.result)
  }
  return { text: JSON.stringify(payload, null, 2) }
}
