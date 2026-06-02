# Math Agent Framework

**A reusable mathematical derivation and verification framework** — model-driven architecture with 12 engines, 60+ MCP tools, and 4 builtin models.

## Overview

Define your mathematical model once (equations, symbols, derivation steps), and the framework automatically handles symbolic derivation, numerical verification, document generation, and MCP tool registration.

```bash
pip install math-agent-framework
math-agent list
math-agent derive ode_solver
```

## Architecture

```
User Model (BaseModel subclass)
       |
       v
+------------------+     +-------------------+     +------------------+
| Derivation Layer  |     | Verification Layer |     | Output Layer     |
| SymbolicEngine    |     | VerificationEngine |     | DocumentEngine   |
| NumericalEngine   |     | SageMathEngine     |     | FormalProofEngine|
| QuantEconEngine   |     | MultiAgentEngine   |     | VisualizationEng |
| AnalysisEngine    |     |                    |     |                   |
| PdeEngine         |     |                    |     |                   |
+------------------+     +-------------------+     +------------------+
       |                         |                         |
       +-------------------------+-------------------------+
                                 |
                    +------------+------------+
                    | CLI | MCP Server | Python SDK |
                    +------------------------------+
```

## Quick Start

```bash
# Install
pip install math-agent-framework

# List available models
math-agent list

# Run a derivation pipeline
math-agent derive ode_solver
math-agent derive analysis_problems
math-agent derive pde_solver

# Generate documentation
math-agent doc ode_solver --format md

# Interactive mode
math-agent interactive
```

## Capabilities

| Domain | Capability | Verification |
|--------|-----------|-------------|
| ODEs | Separable, linear, Bernoulli, exact, 2nd order, Euler, systems | dsolve + checkodesol |
| PDEs | Heat, Wave, Laplace, Poisson, Transport (analytical + numerical) | CFL / residual / L2 error |
| Limits | Finite, infinite, one-sided, L'Hopital | Symbolic + numerical |
| Series | Ratio, Root, Comparison, Integral, Alternating tests | Convergence radius |
| Integration | Direct, by-parts, substitution, partial fractions | Derivative back-check |
| Continuity | Singularity detection, continuous domain | continuous_domain |
| Special Functions | Gamma, Beta, Zeta, Erf, Bessel | Analytic + numeric |
| Dynamic Optimization | Riccati, LQ control, Markov chains, Nash equilibrium | QuantEcon |
| Formal Proofs | Lean 4 proof templates | QED multi-agent verification |
| Visualization | 2D curves, 3D surfaces, animations, CES surfaces | Matplotlib |

## Creating a Custom Model

Create `models/user/my_model.py`:

```python
from models.base_model import BaseModel, derivation_step

class MyModel(BaseModel):
    name = "my_model"
    description = "My mathematical model"

    def define_symbols(self, engine):
        engine.declare_symbols({'x': None, 'a': {'positive': True}})

    def define_equations(self, engine):
        x, a = engine.get_symbol('x'), engine.get_symbol('a')
        return {'f': a * x**2 + x}

    @derivation_step(1, "Find FOC", tools=["SymPy"])
    def step1_foc(self, engine, params):
        eqs = self.define_equations(engine)
        x = engine.get_symbol('x')
        return engine.differentiate(eqs['f'], x) \
                     .simplify().to_latex().build().to_dict()
```

## MCP Integration

Register with Claude Code:

```bash
claude mcp add-json math-agent-framework '{
  "command": "python",
  "args": ["-m", "mcp.mcp_server"],
  "env": {}
}' -s local
```

Automatically registered tools include model-specific tools, verification tools, analysis tools, and the unified verification pipeline.

## Builtin Models

| Model | Description | Steps |
|-------|-------------|-------|
| `quadratic_form` | General quadratic form U/inverted-U analysis | 2 |
| `ode_solver` | ODE solving: classify -> solve -> verify | 5 |
| `analysis_problems` | Limits, series, integrals, continuity, special functions | 6 |
| `pde_solver` | PDE solving: Heat/Wave/Laplace/Poisson/Transport | 6 |

## License

MIT License — see LICENSE file.

## Citation

If you use this framework in your research, please cite:

```
@software{math_agent_framework,
  title = {Math Agent Framework: A Reusable Mathematical Derivation and Verification Framework},
  year = {2026},
  url = {https://github.com/math-agent-framework/math-agent-framework}
}
```
