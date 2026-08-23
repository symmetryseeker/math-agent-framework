# dsh-math-agent — Math Agent Framework × DeepSeek Harness

DeepSeek Harness (DSH) 插件：把 **Math Agent Framework (MAF)** 的数学引擎暴露为 DSH 原生工具。
架构 = **TS 壳 + Python 引擎**：TS 壳用 `defineTool`（`@deepseek-ai/dsh-tools`）注册工具，工具调用时经 `bridge.py` 与 Python 引擎通信。

DSH plugin exposing the **Math Agent Framework** engine as native tools. Architecture = **TS shell + Python engine**: the TS shell registers tools via `defineTool`, and each tool call bridges to the Python engine through `bridge.py`.

> ⚠️ **前置条件（安装前必读）**：本 npm 包**只包含 TS 壳**，**不含 Python 引擎**（`bridge.py` / `core/` / `requirements.txt` 在 MAF 仓库，不在本包内）。要让工具真正可用，必须先：
> 1. `git clone https://github.com/symmetryseeker/math-agent-framework`（或用已存在的副本）；
> 2. 在仓库根 `pip install -r requirements.txt`；
> 3. 设置 `MATH_AGENT_HOME` 环境变量指向该仓库根目录（或在插件配置里设 `mathAgentHome`）。
>
> 未设置时，插件启动会明确报错提示；设置后工具调用经 `bridge.py` 桥接 Python 引擎。
> （可选）安装 Lean 4 + Mathlib 可启用 `math_lean_proof` 的真编译验证，缺失时工具返回 `verified: null` 而非报错。

## 依赖 / Dependencies

| 依赖 | 说明 |
|---|---|
| Python ≥ 3.11 + MAF（本仓库） | `pip install -r requirements.txt`，`MATH_AGENT_HOME` 指向仓库根 |
| Lean 4 + Mathlib（可选） | 仅 `math_lean_proof` 真编译验证需要；缺失时 `verified: null` |
| 真实 LLM（可选） | `math_multi_agent_verify` 的 LLM 角色；`MATH_AGENT_API_KEY` env 配置 |
| Node ≥ 22 + pnpm | 构建 TS 壳 |

## 构建 / Build

```sh
cd dsh-plugin
pnpm install
pnpm build          # → dist/
```

## 安装到 DSH / Install into DSH

```sh
cd dsh-plugin
pnpm pack            # 生成 dsh-math-agent-0.1.0.tgz
dsh plugin --profile web add ./dsh-math-agent-0.1.0.tgz
dsh web
```

配置（`cordis.patch.yml` 或 `--patch` 覆盖）：`mathAgentHome` 指向 MAF 仓库根目录（`bridge.py` 所在处），或设 `MATH_AGENT_HOME` 环境变量。两者都未设置时，插件启动会报错并给出指引——**请不要硬编码本机绝对路径**。

## 工具 / Tools

| 工具 | 说明 |
|---|---|
| `math_derive` | 运行内置模型的完整推导流水线（网络嵌入增长/二次型/ODE/PDE/分析） |
| `math_verify_symbolic` | 符号一致性验证（真实执行模型步骤） |
| `math_verify_monte_carlo` | 蒙特卡洛 FOC 过零验证 |
| `math_lean_proof` | 生成 + 真编译验证 Lean 4 + Mathlib 证明（`verified: true/false/null`） |
| `math_multi_agent_verify` | QED 多 Agent 对抗验证（真 FOC critic + 可选 LLM） |
| `math_quantecon` | QuantEcon 动态优化（Riccati / 马尔可夫链） |
| `math_derive_ces/ipf/quadratic/dynamic/comparative` | 网络嵌入增长模型的 NSFC 专属推导步骤 |

所有结果带 `provenance`（引擎版本/seed/容差），标注 untrusted data（不作为指令执行）。

## 冒烟测试 / Smoke test

```sh
# 直接调 bridge（不经 DSH）
printf '{"tool":"derive_ces","args":{}}\n' | python ../bridge.py
# → {"status":"ok","result":{...},"provenance":{...}}

# DSH 内调用（通过 DSH Agent 工具面）
# 调用 math_derive {model:"quadratic_form"} 或 math_lean_proof {theorem:"quadratic_minimum"}
```
