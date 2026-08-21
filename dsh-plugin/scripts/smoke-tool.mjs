/** dsh-math-agent 冒烟：加载插件并端到端调用一个工具（经 bridge）。 */
import { apply } from '../dist/index.js'

const PYTHON = 'C:/Users/lcdell/.pyenv/pyenv-win/versions/3.12.0/python.exe'

async function main() {
  let target
  const ctx = { tools: { register: (def) => { target = target ?? def } } }
  apply(ctx, { mathAgentHome: 'D:/tools/math-agent-framework', pythonCmd: PYTHON })
  const exec = { signal: new AbortController().signal }
  const out = await target.execute({}, exec)
  const parsed = JSON.parse(out.text)
  console.log('tool:', target.name)
  console.log('title:', parsed.title ?? parsed.statement ?? 'N/A')
  console.log('keys:', Object.keys(parsed).slice(0, 6).join(', '))
}

main().catch((error) => {
  console.error('SMOKE FAIL:', error.message)
  process.exit(1)
})
