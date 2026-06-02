# Math Agent Framework · [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![MCP-ready](https://img.shields.io/badge/MCP-ready-green.svg)](https://modelcontextprotocol.io/)

**Agent-native symbolic derivation, numerical verification, and MCP-ready math infrastructure.**

Not another math library. A **verification-first, LLM-orchestrated mathematical reasoning framework** — define your equations once, and the framework handles derivation, verification, documentation, and MCP tool registration automatically.

```bash
pip install math-agent-framework
math-agent list
math-agent derive ode_solver
```

---

## 为什么不用 SymPy？ / Why not just SymPy?

| Capability | SymPy | Math Agent Framework |
|---|---|---|
| Symbolic derivation | Yes | Yes |
| Numerical verification | Partial | Yes (10K-sample Monte Carlo) |
| Reusable derivation pipelines | No | Yes (model-driven, ~50 lines) |
| Document generation (MD/LaTeX/DOCX) | No | Yes |
| MCP tool auto-registration | No | Yes (60+ tools) |
| LLM agent orchestration (Harness) | No | Yes (skills + prompts + routing) |
| ODE classification + solve + verify | No | Yes (5 types) |
| PDE analytical + numerical | No | Yes (Heat/Wave/Laplace/Poisson/Transport) |
| 5-level verification pipeline | No | Yes |
| Cross-engine validation | No | Yes (SymPy vs SageMath) |

**SymPy computes. This framework verifies, documents, and orchestrates.**

---

## 30秒快速开始 / 30-Second Quick Start

```bash
pip install math-agent-framework
math-agent list                    # List all available models
math-agent derive ode_solver       # Solve ODE with verification
math-agent derive pde_solver       # Solve PDE (Heat/Wave/Laplace)
math-agent doc ode_solver --format md  # Generate markdown report
```

---

## 应用场景 / Use Cases

| Domain | Capability |
|---|---|
| Optics / Photonics | Waveguide mode derivation, coupled-mode theory, dispersion |
| Physics | Harmonic oscillator, resonance, energy conservation |
| Engineering | ODE/PDE solving, stability analysis, parameter sensitivity |
| Mathematics | Limits, series convergence, integral techniques, continuity |
| Research | Reproducible derivation pipelines, verified appendices |
| LLM Agents | MCP-native math tooling for Claude Code / GPT |

---

## Harness: 多智能体编排 / Multi-Agent Orchestration

```
User: "solve y'' + 3y' + 2y = 0"
  -> Orchestrator detects: ODE (2nd order)
  -> matched skill: derive_ode
  -> tool sequence: [classify -> solve_2nd_order -> verify]
  -> execution prompt with step-by-step instructions
  -> LLM follows plan, engines execute locally, result verified
```

| Skill | Trigger | Tool Sequence | Verification |
|---|---|---|---|
| `derive_ode` | ode, y', dy/dx | classify -> solve -> verify | checkodesol |
| `solve_pde` | pde, heat, wave | classify -> analytical/numerical | CFL / L2 error |
| `solve_analysis` | limit, series, integral | limits -> series -> integrals | dual verification |
| `verify_mathematical` | verify, prove | 5-level pipeline | multi-engine |
| `full_pipeline` | complete derivation | derive -> verify -> document | full stack |
| `analyze_oscillator` | oscillator, resonance | classify -> solve -> energy | conservation |

---

## 验证流水线 / Verification Pipeline

```
Level 1: SymPy symbolic   — identity checks, FOC/SOC, Hessian
Level 2: Monte Carlo      — 10,000 random parameter sets
Level 3: SageMath CAS      — independent engine cross-check
Level 4: Lean 4            — formal proof template generation
Level 5: QED Multi-Agent   — Proposer + Critic + Judge verification
```

---

## 自定义模型 (~50行) / Custom Model

```python
from models.base_model import BaseModel, derivation_step

class WaveguideModel(BaseModel):
    name = "waveguide"
    description = "Optical waveguide mode derivation"

    def define_symbols(self, engine):
        engine.declare_symbols({"x": None, "n1": {"positive": True},
                                 "k0": {"positive": True}, "beta": {"real": True}})

    def define_equations(self, engine):
        return {"helmholtz": "diff(E(x),x,2) + (n1**2*k0**2 - beta**2)*E(x)"}

    @derivation_step(1, "Solve waveguide mode", tools=["SymPy"])
    def step1_solve(self, engine, params):
        pass  # ~3 lines of derivation code
```

---

## 可靠性 / Reliability

| Test Suite | Count | Status |
|---|---|---|
| Engine unit tests | 7 | All pass |
| Model system tests | 6 | All pass |
| Analysis tests | 20+ | All pass |
| PDE tests | 8 | All pass |
| Harness tests | 6 | All pass |

---

## Roadmap

- [x] SymPy symbolic engine + Builder API
- [x] Numerical verification (Monte Carlo, grid search)
- [x] 5-level verification pipeline
- [x] ODE/PDE solving (analytical + numerical)
- [x] Analysis engine (limits, series, integrals)
- [x] SageMath cross-validation
- [x] QuantEcon dynamic optimization
- [x] Multi-agent adversarial verification (QED)
- [x] Lean 4 formal proof templates
- [x] MCP server (60+ auto-registered tools)
- [x] Harness system (skills, prompts, routing)
- [ ] Wolfram Engine backend
- [ ] Jupyter notebook widgets
- [ ] Graph-based mathematical reasoning
- [ ] Multi-step proof planning
- [ ] PyPI publication

## License

MIT — see [LICENSE](LICENSE).
