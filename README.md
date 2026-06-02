# Math Agent Framework / 数学推导智能体框架

**A reusable mathematical derivation and verification framework**
**可复用的数学推导与验证框架**

Model-driven architecture: define your equations once, and the framework automatically handles symbolic derivation, numerical verification, document generation, and MCP tool registration.

模型驱动架构：定义方程后，框架自动完成符号推导、数值验证、文档生成和 MCP 工具注册。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 本地安装 / Local Installation

```bash
# 方式一：从 PyPI 安装（推荐）
pip install math-agent-framework

# 方式二：从 GitHub 安装
pip install git+https://github.com/symmetryseeker/math-agent-framework.git

# 方式三：克隆后本地安装
git clone git@github.com:symmetryseeker/math-agent-framework.git
cd math-agent-framework
pip install -e .
```

### 环境要求 / Requirements

| 依赖 | 版本 | 必需 |
|------|------|------|
| Python | >= 3.10 | ✅ |
| sympy | >= 1.12 | ✅ |
| numpy | >= 1.24 | ✅ |
| scipy | >= 1.10 | ✅ |
| pyyaml | >= 6.0 | ✅ |
| mcp | >= 1.0 | ✅ (MCP模式) |
| python-docx | >= 0.8.11 | 可选 (Word输出) |
| quantecon | >= 0.7 | 可选 (动态优化) |

### 本地可用性分析 / Local Usability Analysis

**关键架构说明 / Key Architecture Note:**

```
┌──────────────────────────────────────────────────┐
│  LLM (Claude/GPT/etc.)                           │
│  负责: 理解问题、规划推导路径、选择工具、解释结果    │
│  需要: API Key (Claude API / OpenAI API / etc.)   │
└──────────────────┬───────────────────────────────┘
                   │ MCP Protocol (stdio)
                   ▼
┌──────────────────────────────────────────────────┐
│  Math Agent Framework (本框架)                    │
│  负责: 符号计算、数值验证、ODE/PDE求解、文档生成    │
│  需要: 零 API Key，全部本地计算                    │
└──────────────────────────────────────────────────┘
```

**分工 / Division of Labor:**

| 角色 | 谁来做 | 需要什么 |
|------|--------|---------|
| 推导规划（选什么方法、按什么顺序） | LLM | API Key |
| 符号计算（求导/积分/解方程） | 本框架 SymPy 引擎 | 仅 Python |
| 数值验证（蒙特卡洛/网格搜索） | 本框架 NumPy 引擎 | 仅 Python |
| 结果解释（公式→自然语言） | LLM | API Key |
| 文档生成（LaTeX/Word/Markdown） | 本框架 | 仅 Python |

**两种使用模式 / Two Usage Modes:**

| 模式 | API Key 需求 | 适用场景 |
|------|-------------|---------|
| **Agent 模式** (通过 Claude Code MCP) | ✅ 需要 LLM API Key | 完整推导+验证+解释 |
| **CLI 直接模式** (`math-agent derive ode_solver`) | ❌ 不需要 | 运行已定义的模型流水线 |
| **Python SDK 模式** (`from core import *`) | ❌ 不需要 | 手动调用引擎做计算 |

| 维度 | 状态 | 说明 |
|------|------|------|
| 离线计算 | ✅ | 所有引擎纯本地，无网络依赖 |
| 框架自身 API Key | ❌ 不需要 | 本框架不调用任何外部API |
| Agent 模式 API Key | ⚠️ 需要 | LLM 驱动的推导规划需要 Claude/GPT API |
| 跨平台 | ✅ | Windows/macOS/Linux |
| 可选依赖降级 | ✅ | SageMath/QuantEcon 不可用时自动跳过 |

---

## 架构 / Architecture

```
┌──────────────────────────────────────────────────────┐
│  LLM Agent (Claude / GPT)                            │
│  "Derive the CES function and verify the turning point"│
│  Requires: API Key                                    │
└────────────────────┬─────────────────────────────────┘
                     │ MCP Protocol
                     ▼
┌──────────────────────────────────────────────────────┐
│  Math Agent Framework (this repo)                    │
│  Zero API keys — all local computation               │
│                                                      │
│  ┌─────────────────┐ ┌──────────────────┐ ┌────────┐ │
│  │ Derivation Layer │ │ Verification Layer│ │ Output │ │
│  │ SymbolicEngine   │ │ VerificationEng   │ │ DocEng │ │
│  │ NumericalEngine  │ │ SageMathEngine    │ │ FormPrf│ │
│  │ QuantEconEngine  │ │ MultiAgentEngine  │ │ Visual │ │
│  │ AnalysisEngine   │ │                   │ │        │ │
│  │ PdeEngine        │ │                   │ │        │ │
│  └─────────────────┘ └──────────────────┘ └────────┘ │
│                                                      │
│  CLI (no API key) │ MCP Server │ Python SDK          │
└──────────────────────────────────────────────────────┘
```

> **LLM plans the derivation, Engines execute the computation.**
> **LLM 负责规划推导路径，引擎负责执行计算。**

---

## 快速开始 / Quick Start

```bash
# 列出所有可用模型 / List models
math-agent list

# 运行推导流水线 / Run derivation
math-agent derive ode_solver
math-agent derive analysis_problems
math-agent derive pde_solver
math-agent derive harmonic_oscillator

# 生成文档 / Generate docs
math-agent doc ode_solver --format md
math-agent doc ode_solver --format docx

# 交互式模式 / Interactive
math-agent interactive
```

## 能力矩阵 / Capabilities

| 领域 Domain | 能力 Capability | 验证方式 Verification |
|-------------|----------------|----------------------|
| 常微分方程 ODEs | 可分离/线性/Bernoulli/恰当/二阶/Euler/方程组 | dsolve + checkodesol |
| 偏微分方程 PDEs | Heat/Wave/Laplace/Poisson/Transport（解析+数值） | CFL / 残差 / L2误差 |
| 极限 Limits | 有限/无穷/单侧/L'Hopital | 符号+数值双重验证 |
| 级数 Series | Ratio/Root/Comparison/Integral/Alternating检验 | 收敛半径 |
| 积分 Integration | 直接/分部/换元/部分分式 | 微分反向验证 |
| 连续性 Continuity | 奇点检测/连续域 | continuous_domain |
| 特殊函数 Special Funcs | Gamma/Beta/Zeta/Erf/Bessel | 解析+数值 |
| 动态优化 Dynamic Opt | Riccati/LQ控制/马尔可夫链/纳什均衡 | QuantEcon |
| 形式化证明 Formal Proof | Lean 4 证明模板 | QED多Agent验证 |
| 可视化 Visualization | 2D曲线/3D曲面/动画 | Matplotlib |

## 自定义模型 / Custom Model

创建 `models/user/my_model.py` / Create:

```python
from models.base_model import BaseModel, derivation_step

class MyModel(BaseModel):
    name = "my_model"
    description = "My mathematical model / 我的数学模型"

    def define_symbols(self, engine):
        engine.declare_symbols({'x': None, 'a': {'positive': True}})

    def define_equations(self, engine):
        x, a = engine.get_symbol('x'), engine.get_symbol('a')
        return {'f': a * x**2 + x}

    @derivation_step(1, "Find FOC / 求一阶条件", tools=["SymPy"])
    def step1_foc(self, engine, params):
        eqs = self.define_equations(engine)
        x = engine.get_symbol('x')
        return engine.differentiate(eqs['f'], x) \
                     .simplify().to_latex().build().to_dict()
```

## MCP 集成 / MCP Integration

```bash
claude mcp add-json math-agent-framework '{
  "command": "python",
  "args": ["-m", "mcp.mcp_server"],
  "env": {}
}' -s local
```

自动注册的工具包括：模型推导工具、验证工具、分析工具、统一验证流水线。

## 内置模型 / Builtin Models

| 模型 Model | 描述 Description | 步骤 Steps |
|-----------|-----------------|------------|
| `quadratic_form` | 通用二次型 U/倒U 分析 | 2 |
| `harmonic_oscillator` | 阻尼/驱动谐振子（物理学） | 5 |
| `ode_solver` | ODE求解：分类→求解→验证 | 5 |
| `analysis_problems` | 极限/级数/积分/连续性/特殊函数 | 6 |
| `pde_solver` | PDE求解：Heat/Wave/Laplace/Poisson/Transport | 6 |

## 目录结构 / Directory Structure

```
math-agent-framework/
├── core/                    # 核心引擎（零外部依赖）
│   ├── symbolic_engine.py   # SymPy符号推导
│   ├── numerical_engine.py  # NumPy/SciPy数值计算
│   ├── verification_engine.py # 五层验证框架
│   ├── pipeline_engine.py   # 流水线编排
│   ├── document_engine.py   # 文档生成
│   ├── analysis_engine.py   # 分析学（极限/级数/积分）
│   ├── pde_engine.py        # PDE解析+数值求解
│   ├── sagemath_engine.py   # SageMath备用CAS
│   ├── quantecon_engine.py  # QuantEcon动态优化
│   ├── multi_agent_verify_engine.py # QED多Agent验证
│   ├── formal_proof_engine.py # Lean 4证明模板
│   └── visualization_engine.py # 数学可视化
├── models/                  # 模型定义
│   ├── base_model.py        # BaseModel抽象基类
│   ├── builtin/             # 内置示例
│   └── user/                # 用户自定义模型
├── mcp/                     # MCP服务器
├── cli/                     # 命令行工具
├── tests/                   # 测试
└── pyproject.toml           # 包配置
```

## 许可证 / License

MIT License — see [LICENSE](LICENSE) file.

## 引用 / Citation

```
@software{math_agent_framework,
  title = {Math Agent Framework: A Reusable Mathematical Derivation and Verification Framework},
  year = {2026},
  url = {https://github.com/symmetryseeker/math-agent-framework}
}
```
