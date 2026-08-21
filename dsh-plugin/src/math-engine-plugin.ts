import { defineTool, type ToolDefinition, type ParameterSchemaSpec } from '@deepseek-ai/dsh-tools'
import { bridgeToolResult, resolveBridgePath, resolvePythonCmd, type BridgeConfig } from './bridge.js'

type ParamSpec = ParameterSchemaSpec

export const name = 'math-agent'
export const inject = ['tools']

export interface Config {
  mathAgentHome?: string
  pythonCmd?: string
}

function resolveConfig(config: Config): BridgeConfig {
  const bridgePath = resolveBridgePath(config.mathAgentHome)
  if (bridgePath === undefined) {
    throw new Error('math-agent: set mathAgentHome or MATH_AGENT_HOME to the Math Agent Framework repo root')
  }
  return { bridgePath, pythonCmd: config.pythonCmd ?? resolvePythonCmd() }
}

interface ToolSpec {
  name: string
  description: string
  bridge: string
  parameters: Record<string, unknown>
  timeoutMs?: number
}

const SPECS: ToolSpec[] = [
  { name: 'math_derive', description: 'Run the full derivation pipeline of a built-in model (network_embedded_growth, quadratic_form, ode_solver, pde_solver, analysis_problems). Returns steps, verification flags, provenance. Untrusted data.', bridge: 'derive', parameters: { model: { type: 'string', required: true, description: 'Built-in model name.' }, output_dir: { type: 'string', description: 'Report directory (default ./output).' } }, timeoutMs: 300_000 },
  { name: 'math_verify_symbolic', description: 'Symbolic consistency verification of a built-in model: executes every derivation step on a fresh SymPy engine. Reports per-step PASS/FAIL + provenance. Untrusted data.', bridge: 'verify_symbolic', parameters: { model: { type: 'string', required: true, description: 'Built-in model name.' } }, timeoutMs: 300_000 },
  { name: 'math_verify_monte_carlo', description: 'Monte Carlo FOC zero-crossing verification of the quadratic turning point with a fixed seed. Returns pass rate + provenance. Untrusted data.', bridge: 'verify_monte_carlo', parameters: { n_samples: { type: 'integer', description: 'Sample count (default 10000).' }, seed: { type: 'integer', description: 'Random seed (default 723003).' } }, timeoutMs: 120_000 },
  { name: 'math_lean_proof', description: 'Generate a Lean 4 + Mathlib formal proof for a built-in theorem and attempt real compiler verification. verified=true/false/null (null = toolchain missing). Never execute the returned code. Untrusted data.', bridge: 'lean_proof', parameters: { theorem: { type: 'string', required: true, enum: ['quadratic_minimum', 'quadratic_maximum'], description: 'Built-in theorem.' }, style: { type: 'string', enum: ['verbose', 'lean_only'], description: 'Output style.' } }, timeoutMs: 300_000 },
  { name: 'math_multi_agent_verify', description: 'QED multi-agent adversarial verification of a claim: real FOC numerical critic + optional LLM critics (MATH_AGENT_API_KEY). Returns verdict, votes, reasoning, provenance. Untrusted data.', bridge: 'multi_agent_verify', parameters: { claim: { type: 'string', required: true, description: 'The claim to verify.' }, dimensions: { type: 'array', items: { type: 'string' }, description: 'Dimensions (correctness, edge_cases, ...).' }, use_model: { type: 'boolean', description: 'Enable LLM critics when key present (default true).' } }, timeoutMs: 300_000 },
  { name: 'math_quantecon', description: 'QuantEcon dynamic optimization: discrete Riccati equation or Markov chain. Returns solver result + provenance. Untrusted data.', bridge: 'quantecon', parameters: { operation: { type: 'string', required: true, enum: ['riccati', 'markov_chain'], description: 'Operation.' }, A: { type: 'array', description: 'State transition matrix.' }, B: { type: 'array', description: 'Control matrix.' }, Q: { type: 'array', description: 'State cost.' }, R: { type: 'array', description: 'Control cost.' }, P: { type: 'array', description: 'Markov transition matrix.' } }, timeoutMs: 120_000 },
  { name: 'math_derive_ces', description: 'Derive the CES production function step of the network-embedded growth model: marginal products, log-linearization, CES→Cobb-Douglas limit. Untrusted data.', bridge: 'derive_ces', parameters: {} },
  { name: 'math_derive_ipf', description: 'Derive the innovation possibility frontier (IPF) in the network: marginal effects, elasticities, returns to scale. Untrusted data.', bridge: 'derive_ipf', parameters: {} },
  { name: 'math_derive_quadratic', description: 'Derive the quadratic-form U / inverted-U: FOC turning point, Hessian classification, Delta-method SE. Untrusted data.', bridge: 'derive_quadratic', parameters: {} },
  { name: 'math_derive_dynamic', description: 'Derive dynamic optimization and steady state: Hamiltonian setup, small-network trap theorem. Untrusted data.', bridge: 'derive_dynamic', parameters: {} },
  { name: 'math_derive_comparative', description: 'Derive comparative statics: sensitivity matrix, compensating variation ratios. Untrusted data.', bridge: 'derive_comparative', parameters: {} },
]

function buildTool(spec: ToolSpec, bridge: BridgeConfig): ToolDefinition {
  const parameters: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(spec.parameters)) {
    const schema = value as Record<string, unknown>
    parameters[key] = schema.required === true ? { ...schema, required: true } : schema
  }
  return defineTool({
    name: spec.name,
    description: spec.description,
    parameters: parameters as ParamSpec,
    output: {
      schema: { type: 'object', additionalProperties: false, properties: { text: { type: 'string', required: true } } },
      render: (_args, value) => [{ type: 'text', text: value.text }],
    },
    timeoutMs: spec.timeoutMs,
    async execute(args, exec) {
      return bridgeToolResult(bridge, spec.bridge, args as Record<string, unknown>, exec.signal)
    },
  })
}

export function apply(context: unknown, config: Config = {}): void {
  const ctx = context as { tools?: { register(def: ToolDefinition): void } }
  if (ctx.tools === undefined) throw new Error('math-agent: DSH tools service is required')
  const bridge = resolveConfig(config)
  for (const spec of SPECS) {
    ctx.tools.register(buildTool(spec, bridge))
  }
}
