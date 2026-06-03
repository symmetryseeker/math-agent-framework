# Math Agent Framework [![PyPI](https://img.shields.io/pypi/v/math-agent-framework)](https://pypi.org/project/math-agent-framework/) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![MCP-ready](https://img.shields.io/badge/MCP-ready-green.svg)](https://modelcontextprotocol.io/)

**Give LLMs mathematical rigor. Give computation conceptual understanding.**
**让 LLM 的数学推理接受严格检验，让符号计算获得概念理解。**

---

### Install / 安装

```bash
pip install math-agent-framework        # PyPI (recommended)
# or: pip install git+https://github.com/symmetryseeker/math-agent-framework.git
```

### Three Ways to Use / 三种使用方式

| Mode | Command | Needs API Key? |
|------|---------|---------------|
| **CLI** | `math-agent derive harmonic_oscillator` | No |
| **Python SDK** | `from core import SymbolicEngine` | No |
| **MCP Agent** | Register in Claude Code → LLM plans, engines compute | **You provide your own** |

#### Mode 1: CLI / 命令行

```bash
math-agent quickstart          # Interactive guided tour
math-agent list                # List all available models
math-agent derive ode_solver   # Solve ODE with verification
math-agent doc ode_solver --format md  # Generate report
```

#### Mode 2: Python SDK / Python调用

```python
from core.symbolic_engine import SymbolicEngine
engine = SymbolicEngine()
engine.declare_symbols({"x": None})
# ... build your derivation
```

#### Mode 3: MCP Agent / Agent模式

This mode lets an LLM plan derivations while the framework computes and verifies:
LLM 负责规划推导路径，框架负责计算和验证。

**Step 1:** Register the MCP server in Claude Code (or any MCP client):

```bash
claude mcp add-json math-agent-framework '{
  "command": "python",
  "args": ["-m", "mcp.mcp_server"],
  "env": {}
}' -s local
```

**Configure your LLM API key / 配置你的 LLM API Key:**

```bash
# Claude Code (recommended) — your key stays in Claude's config
export ANTHROPIC_API_KEY="sk-your-key-here"
# or for DeepSeek:
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-key-here"
```


---

### The Problem / 问题

LLMs understand mathematical concepts — they can plan derivations, explain theorems, and reason about structure.
But they **hallucinate calculations**. An LLM may confidently claim ∫x·eˣdx = eˣ + C, and you won't know it's wrong until you check.

LLM 理解数学概念——能规划推导路径、解释定理、推理结构。
但它**会幻觉计算**。它可能自信地说 ∫x·eˣdx = eˣ + C，不亲手验证就不会发现错误。

Symbolic engines (SymPy, NumPy) compute faithfully — every derivative, integral, and solution is deterministic and correct.
But they have **zero conceptual understanding**. They can't explain why a result matters or choose the right approach for a problem.

符号引擎（SymPy, NumPy）忠实计算——每次求导、积分、求解都是确定且正确的。
但它**零概念理解**，不能解释结果的意义，也无法为问题选择正确的方法。

### The Solution / 解决方案

**Math Agent Framework bridges this gap.** It creates a controlled partnership:

**Math Agent Framework 填补了这个鸿沟。** 它建立了一个受控的协作关系：

```
LLM understands the problem   →   plans the derivation path
    (概念理解 / conceptual)         (规划推导路径 / plans)

Framework executes faithfully  →   computes every step deterministically
    (忠实执行 / execution)          (确定性计算 / computes)

Verification pipeline           →   catches every hallucination
    (验证流水线 / verification)     (扼杀幻觉 / kills hallucinations)
```

The LLM provides **conceptual oversight** — choosing which ODE method to apply, interpreting results, explaining significance.
The framework provides **computational fidelity** — SymPy derives, NumPy verifies with 10,000 Monte Carlo samples, SageMath cross-checks, and a 5-level pipeline issues the final verdict.

LLM 提供**概念监督**——选择ODE解法、解释结果、说明意义。
框架提供**计算保真**——SymPy 推导、NumPy 万组蒙特卡洛验证、SageMath 交叉检验、五层流水线给出最终裁决。

**The result: an LLM whose mathematical output is no longer trust-based. It is verified.**
**结果：LLM 的数学输出不再基于信任，而是经过验证。**

```bash
pip install math-agent-framework
math-agent list
math-agent derive ode_solver
```

![Demo: damped harmonic oscillator](demo/demo.gif)

> **Above**: deriving a damped harmonic oscillator — classify → solve → verify → report. One command.
> **上图**: 阻尼谐振子推导——分类→求解→验证→报告。一条命令。

---

## 30秒快速开始 / 30-Second Quick Start

## 为什么不用 SymPy？ / Why not just SymPy?

| Capability / 能力 | SymPy | Math Agent Framework |
|---|---|---|
| Symbolic derivation / 符号推导 | ✅ | ✅ |
| Numerical verification / 数值验证 | Partial | ✅ (10K-sample Monte Carlo) |
| Reusable pipelines / 可复用流水线 | ❌ | ✅ (model-driven, ~50 lines) |
| Document generation / 文档生成 (MD/LaTeX/DOCX) | ❌ | ✅ |
| MCP tool auto-registration / MCP工具自动注册 | ❌ | ✅ (60+ tools) |
| LLM agent orchestration / LLM编排 (Harness) | ❌ | ✅ (skills + prompts + routing) |
| ODE classify + solve + verify / ODE分类求解验证 | ❌ | ✅ (5 types) |
| PDE analytical + numerical / PDE解析+数值 | ❌ | ✅ (Heat/Wave/Laplace/Poisson/Transport) |
| 5-level verification pipeline / 五层验证流水线 | ❌ | ✅ |
| Cross-engine validation / 跨引擎交叉验证 | ❌ | ✅ (SymPy vs SageMath) |

**SymPy computes. This framework verifies, documents, and orchestrates.**
**SymPy 负责计算，本框架负责验证、文档和编排。**

---

## 30秒快速开始 / 30-Second Quick Start

```bash
pip install math-agent-framework      # 安装 / Install
math-agent list                       # 列出所有可用模型 / List models
math-agent derive ode_solver          # 求解ODE并验证 / Solve ODE + verify
math-agent derive pde_solver          # 求解PDE并验证 / Solve PDE + verify
math-agent doc ode_solver --format md # 生成Markdown报告 / Generate report
```

---

## 应用场景 / Use Cases

| Domain / 领域 | Capability / 能力 |
|---|---|
| Optics / Photonics / 光学 | Waveguide derivation, coupled-mode theory, dispersion |
| Physics / 物理 | Harmonic oscillator, resonance, energy conservation |
| Engineering / 工程 | ODE/PDE solving, stability, parameter sensitivity |
| Mathematics / 数学 | Limits, series convergence, integrals, continuity |
| Research / 科研 | Reproducible pipelines, verified appendices |
| LLM Agents / 智能体 | MCP-native math tooling for Claude Code / GPT |

---

## Harness: 多智能体编排 / Multi-Agent Orchestration

```
User: "solve y'' + 3y' + 2y = 0"   / 用户输入
  -> Orchestrator detects: ODE (2nd order)   / 编排器检测领域
  -> matched skill: derive_ode                / 匹配技能
  -> tool sequence: [classify -> solve_2nd_order -> verify]
  -> LLM follows plan, engines execute locally / LLM按计划调用本地引擎
```

| Skill / 技能 | Trigger / 触发词 | Tool Sequence / 工具序列 | Verification / 验证 |
|---|---|---|---|
| `derive_ode` | ode, y', dy/dx | classify → solve → verify | checkodesol |
| `solve_pde` | pde, heat, wave | classify → analytical/numerical | CFL / L2 error |
| `solve_analysis` | limit, series, integral | limits → series → integrals | dual verification |
| `verify_mathematical` | verify, prove | 5-level pipeline | multi-engine |
| `full_pipeline` | complete derivation | derive → verify → document | full stack |
| `analyze_oscillator` | oscillator, resonance | classify → solve → energy | conservation |

---

## 验证流水线 / Verification Pipeline

Every derivation passes through 5 levels of verification.
每次推导都经过五层验证：

```
Level 1: SymPy symbolic   — identity checks, FOC/SOC, Hessian / 符号恒等式检验
Level 2: Monte Carlo      — 10,000 random parameter sets / 万组随机参数
Level 3: SageMath CAS      — independent engine cross-check / 独立引擎交叉验证
Level 4: Lean 4            — formal proof template generation / 形式化证明模板
Level 5: QED Multi-Agent   — Proposer + Critic + Judge / 多Agent对抗验证
```

## 架构 / Architecture

```
┌─────────────────────────────────────────┐
│  LLM Agent (Claude / GPT)               │
│  负责规划推导、选择工具、解释结果           │
│  Requires: API Key                       │
└──────────────┬──────────────────────────┘
               │ MCP Protocol
               ▼
┌─────────────────────────────────────────┐
│  Math Agent Framework (this repo)        │
│  All computation runs locally             │
│  全部本地计算                               │
│                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Derivation│ │Verification│ │Output    │ │
│  │SymPy     │ │5-level    │ │MD/LaTeX  │ │
│  │NumPy     │ │MonteCarlo │ │DOCX/JSON │ │
│  │QuantEcon │ │SageMath   │ │Lean4     │ │
│  │Analysis  │ │MultiAgent │ │Visual    │ │
│  │PDE       │ │           │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ │
│                                          │
│  Harness: Skills + Prompts + ToolRouter  │
│  CLI · MCP Server · Python SDK           │
└──────────────────────────────────────────┘
```

> **12 engines · 60+ MCP tools · 6 skills · 5 builtin models**
> **12个引擎 · 60+个MCP工具 · 6个技能 · 5个内置模型**

---

## 自定义模型 (~50行) / Custom Model

```python
from models.base_model import BaseModel, derivation_step

class WaveguideModel(BaseModel):
    name = "waveguide"
    description = "Optical waveguide mode derivation / 光波导模式推导"

    def define_symbols(self, engine):
        engine.declare_symbols({"x": None, "n1": {"positive": True},
                                 "k0": {"positive": True}, "beta": {"real": True}})

    def define_equations(self, engine):
        return {"helmholtz": "diff(E(x),x,2) + (n1**2*k0**2 - beta**2)*E(x)"}

    @derivation_step(1, "Solve waveguide mode / 求解波导模式", tools=["SymPy"])
    def step1_solve(self, engine, params):
        pass  # ~3 lines of derivation code / ~3行推导代码
```

---

## 可靠性 / Reliability

| Test Suite / 测试套件 | Count / 数量 | Status / 状态 |
|---|---|---|
| Engine unit tests / 引擎单元测试 | 7 | ✅ All pass / 全部通过 |
| Model system tests / 模型系统测试 | 6 | ✅ All pass / 全部通过 |
| Analysis tests / 分析学测试 | 20+ | ✅ All pass / 全部通过 |
| PDE tests / 偏微分方程测试 | 8 | ✅ All pass / 全部通过 |
| Harness tests / 编排系统测试 | 6 | ✅ All pass / 全部通过 |

---

## Roadmap / 路线图

- [x] SymPy symbolic engine + Builder API / 符号引擎
- [x] Numerical verification (Monte Carlo, grid search) / 数值验证
- [x] 5-level verification pipeline / 五层验证流水线
- [x] ODE/PDE solving (analytical + numerical) / 常微分/偏微分求解
- [x] Analysis engine (limits, series, integrals) / 分析学引擎
- [x] SageMath cross-validation / SageMath交叉验证
- [x] QuantEcon dynamic optimization / 动态优化
- [x] Multi-agent adversarial verification (QED) / 多Agent验证
- [x] Lean 4 formal proof templates / 形式化证明
- [x] MCP server (60+ auto-registered tools) / MCP服务器
- [x] Harness system (skills, prompts, routing) / 编排系统
- [ ] Wolfram Engine backend
- [ ] Jupyter notebook widgets
- [ ] Graph-based mathematical reasoning / 图数学推理
- [ ] Multi-step proof planning / 多步证明规划
- [ ] PyPI publication / PyPI发布

---

## MCP 集成 / MCP Integration

```bash
claude mcp add-json math-agent-framework '{
  "command": "python",
  "args": ["-m", "mcp.mcp_server"],
  "env": {}
}' -s local
```

Automatically registered tools include: model derivation, verification, analysis, unified pipeline, and harness orchestration.
自动注册工具包括：模型推导、验证、分析、统一流水线、编排调度。

## API Key 配置 / API Key Setup

Agent 模式需要 LLM API Key。CLI 和 Python SDK 模式不需要。

| 模式 Mode | 需要 API Key? | 配置位置 |
|-----------|---------------|---------|
| CLI (`math-agent derive`) | 不需要 | — |
| Python SDK (`from core import ...`) | 不需要 | — |
| MCP Agent (Claude Code) | 需要 | 在 Claude Code 中设置环境变量 |

**Claude Code 配置:**

```bash
export ANTHROPIC_API_KEY="sk-your-key-here"
```

**DeepSeek 配置:**

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-key-here"
```

你的 API Key 只在 Claude Code 中使用，本框架不接触。

## License / 许可证

MIT — see [LICENSE](LICENSE).

## Citation / 引用

```
@software{math_agent_framework,
  title = {Math Agent Framework: Agent-native Mathematical Derivation and Verification},
  year = {2026},
  url = {https://github.com/symmetryseeker/math-agent-framework}
}
```
