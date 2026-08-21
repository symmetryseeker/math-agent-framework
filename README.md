# Math Agent Framework (MAF)

[![license](https://img.shields.io/github/license/symmetryseeker/math-agent-framework)](https://github.com/symmetryseeker/math-agent-framework/blob/main/LICENSE)
[![python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

**Reusable mathematical derivation & verification framework** — SymPy/NumPy/SciPy symbolic & numerical engine, Lean 4 formal proofs (compiler-verified), and QED-style multi-agent adversarial verification, exposed as a CLI, an MCP server, and a DeepSeek Harness (DSH) plugin.

**可复用数学推导与验证框架** — SymPy/NumPy/SciPy 符号与数值引擎、Lean 4 形式化证明（真编译验证）、QED 风格多 Agent 对抗验证；提供 CLI、MCP Server 与 DeepSeek Harness (DSH) 插件三套接口。

> Maintainer: [symmetryseeker](https://github.com/symmetryseeker) (single maintainer). This project has **no external collaborators** — all maintenance is done by the author.
> 维护者：symmetryseeker（单维护者）。本项目**没有外部协作者**，全部维护由作者完成。

---

## 30 秒理解 / 30-second overview

把数学推导从"硬编码脚本"变成"模型定义驱动"。你只需继承 `BaseModel`、用 `@derivation_step` 装饰器声明推导步骤，框架自动完成符号推导、数值验证、文档生成、形式化证明与多 Agent 对抗验证，并自动注册工具（MCP / CLI / DSH）。

```text
BaseModel (@derivation_step)
   → SymbolicEngine (SymPy)     符号推导：求导/积分/求解/线性化/Hessian
   → NumericalEngine (SciPy)    数值验证：蒙特卡洛/拐点/标准误
   → VerificationEngine         五层验证：符号/FOC-SOC/边界/反例/链一致
   → FormalProofEngine (Lean 4) 形式化证明（真编译验证）
   → MultiAgentVerificationEngine  QED 对抗验证（Proposer/Critic/Judge，可接真实 LLM）
   → DocumentEngine             文档生成 (MD/Quarto/DOCX/LaTeX/JSON)
   → MCP Server / CLI / DSH 插件  三套工具面
```

Every result is bound with **provenance** (engine versions, seed, tolerances) so it is reproducible and auditable.
所有输出都绑定 **provenance**（引擎版本/seed/容差），保证可复现、可审计。

---

## 依赖声明 / Dependencies

| 依赖 | 必需 | 说明 |
|---|---|---|
| Python ≥ 3.11 | ✅ | `python --version` |
| sympy / numpy / scipy / pyyaml / mcp / python-docx | ✅ | `pip install -r requirements.txt` 或 `pip install math-agent-framework` |
| **Lean 4 + Mathlib**（elan） | ⚠️ 可选但推荐 | 形式化证明**真编译验证**需要。`bash scripts/install-lean.sh` 或 `math-agent lean-doctor` 检测 |
| 真实 LLM（Proposer/Critic/Judge） | ⚠️ 可选 | OpenAI 兼容端点，经环境变量配置，见下方 |

> **No secrets in code**: the LLM client reads `MATH_AGENT_API_KEY` / `MATH_AGENT_BASE_URL` / `MATH_AGENT_MODEL` from environment variables only. Never commit keys.
> **代码不含任何密钥**：LLM 客户端只从环境变量读取，绝不硬编码。

---

## 快速开始 / Quick start

```bash
pip install -r requirements.txt          # 安装依赖
python cli/cli.py list                    # 列出可用模型
python cli/cli.py derive network_embedded_growth   # 运行完整推导流水线
python cli/cli.py verify quadratic_form   # 运行验证
python cli/cli.py proof quadratic_minimum # 生成 + 真编译验证 Lean 证明
python cli/cli.py lean-doctor             # 检测 Lean 工具链
```

或通过 MCP 接入 Claude Code：

```bash
claude mcp add-json math-agent-framework '{
  "command": "python",
  "args": ["-m", "mcp.mcp_server"],
  "env": {}
}' -s local
```

或作为 DeepSeek Harness 插件（详见 [dsh-plugin/](dsh-plugin/)）：

```bash
dsh plugin --profile web add <dsh-math-agent-tarball>
dsh web
```

---

## 内置模型 / Built-in models

| 模型 | 内容 |
|---|---|
| `network_embedded_growth` | 网络嵌入内生增长模型（CES/IPF/二次型/动态优化/比较静态/小网络陷阱，6 步） |
| `quadratic_form` | 二次型 U / 倒 U 关系（FOC + Hessian 分类） |
| `ode_solver` | 常微分方程（分类/解析/数值/验证） |
| `pde_solver` | 偏微分方程（transport/heat/wave/laplace/poisson） |
| `analysis_problems` | 经典分析学问题集（极限/级数/积分/连续性/特殊函数/渐近） |

## 定义你自己的模型 / Define your own model

```python
# models/user/my_model.py
from models.base_model import BaseModel, derivation_step

class MyModel(BaseModel):
    name = "my_model"
    description = "我的数学模型"

    def define_symbols(self, engine):
        engine.declare_symbols({"x": None, "a1": None, "a2": None})

    def define_equations(self, engine):
        engine.set_expression(engine.get_symbol("a1") * engine.get_symbol("x")
                              + engine.get_symbol("a2") * engine.get_symbol("x") ** 2)

    @derivation_step(1, "FOC", tools=["SymPy"])
    def step1_foc(self, engine, params):
        return engine.differentiate(engine.get_expression(), engine.get_symbol("x")).solve().build().to_dict()
```

新增文件即自动注册工具（模型热插拔：重启 server 生效）。

---

## Lean 4 真编译验证 / Lean 4 compiler-verified proofs

`math-agent proof quadratic_minimum` 会：

1. 生成可编译的 Lean 4 源码（`import Mathlib`）
2. 调用真实 `lean` 编译器编译
3. 返回 `verified: true | false | null`（null = 工具链缺失，诚实报告，绝不谎称通过）

```bash
bash scripts/install-lean.sh     # 安装 elan + Mathlib（一次性，较大下载）
python cli/cli.py proof quadratic_minimum
# → Verified: [PASS] Lean 编译器验证通过
```

验证结果按源码 digest 缓存到 `output/lean_cache/`。

---

## 多 Agent 对抗验证 / Multi-agent adversarial verification

QED 风格 Proposer + Critic + Judge：

```bash
# 引擎模式（确定性 FOC/边界检验）
python -c "
from core.multi_agent_verify_engine import MultiAgentVerificationEngine
import numpy as np
def lpg(p): return p['a1']*p['_x'] + p['a2']*p['_x']**2
def grad(p): return {'_x': p['a1'] + 2*p['a2']*p['_x']}
def gen(): return {'a1': float(np.random.uniform(-3,3)), 'a2': float(np.random.uniform(-3,3))}
def tp(p): return -p['a1']/(2*p['a2'])
critic = MultiAgentVerificationEngine.make_foc_critic(lpg, grad, gen, tp)
v = MultiAgentVerificationEngine().verify(
    claim='x* = -a1/(2a2)',
    proposer_fn=lambda c: {'proof':'FOC','confidence':0.9},
    critic_fns=[critic])
print(v.verdict, v.vote_counts)
"
```

```bash
# 模型模式（需 API key；未配置自动降级为引擎模式）
export MATH_AGENT_API_KEY="sk-..."
python cli/cli.py verify network_embedded_growth
```

---

## AEN 接入 / AEN integration (roadmap)

MAF 将按 [Agent Experience Network (AEN)](https://github.com/symmetryseeker/dsh-akn-plugin) 协议接入：

- 每次推导 run → `TaskEpisode` + `TraceEvidenceBundle`（provenance 即 Configuration Cell / Environment Fingerprint）
- 数学技巧（FOC 求导顺序、PDE 发散恢复、退化参数、数值容差）→ 通用经验种子（`generality: universal`）
- 通过 `dsh-plugin/` 的 TS 壳写本地证据库，可晋升到公共 Hub

Math techniques are **universally transferable** experiences — the first seed layer of a co-evolving agent experience network.

---

## 项目结构 / Project layout

```
core/           符号/数值/验证/流水线/文档/形式化证明/多Agent引擎 + provenance
models/         内置模型与 BaseModel 接口
mcp/            MCP stdio server + 动态工具注册表
cli/            命令行入口
dsh-plugin/     DeepSeek Harness 插件壳（TS）→ 见 dsh-plugin/README
leanenv/        Lean 4 + Mathlib 项目（形式化证明）
tests/          pytest 测试
scripts/        工具脚本（lean 安装、凭据扫描）
docs/           文档
```

## License

Apache-2.0. See [LICENSE](LICENSE).
