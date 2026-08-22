# Math Agent Framework — 架构

> Math Agent Framework（MAF）是一个**模型定义驱动**的可复用数学推导与验证框架。

## 定位

把数学推导从"硬编码脚本"变成"声明式模型"。你继承 `BaseModel`、用 `@derivation_step` 装饰器声明步骤，
框架自动完成符号推导、数值验证、文档生成、形式化证明与多 Agent 对抗验证，并暴露三套工具面。

```text
BaseModel (@derivation_step)
   → SymbolicEngine (SymPy)    符号推导：求导/积分/求解/线性化/Hessian
   → NumericalEngine (SciPy)   数值验证：蒙特卡洛/拐点/标准误
   → VerificationEngine        五层验证：符号/FOC-SOC/边界/反例/链一致
   → FormalProofEngine (Lean4) 形式化证明（真编译验证）
   → MultiAgentVerificationEngine  QED 对抗验证（Proposer/Critic/Judge，可接真实 LLM）
   → DocumentEngine            文档生成 (MD/Quarto/DOCX/LaTeX/JSON)
   → CLI / MCP Server / DSH 插件   三套工具面
```

## 引擎分层

| 层 | 包 | 职责 |
|---|---|---|
| 推导层 | `core/symbolic_engine.py` `core/numerical_engine.py` | SymPy 符号 / SciPy 数值 |
| 验证层 | `core/verification_engine.py` `core/multi_agent_verify_engine.py` `core/formal_proof_engine.py` | 五层验证 / QED / Lean 真编译 |
| 高级引擎 | `core/analysis_engine.py` `core/pde_engine.py` `core/quantecon_engine.py` `core/sagemath_engine.py` | 分析学 / PDE / 动态优化 / CAS 交叉验证 |
| 编排层 | `core/pipeline_engine.py` | 步骤调度、依赖、报告聚合 |
| 可复现性 | `core/provenance.py` | 引擎版本/seed/容差指纹，绑定所有输出 |
| 接口层 | `cli/` `mcp/` `dsh-plugin/` `bridge.py` | CLI / MCP / DSH 插件 / 桥 |

## 模型定义

```python
class MyModel(BaseModel):
    name = "my_model"
    description = "我的数学模型"
    def define_symbols(self, engine): ...
    @derivation_step(1, "FOC", tools=["SymPy"])
    def step1_foc(self, engine, params): ...
```

每个 `@derivation_step` 自动生成一个工具（CLI 子命令 / MCP 工具 / DSH 工具），
新增模型文件即热插拔（重启 server 生效）。

## 关键设计

1. **Provenance 可复现**：所有 `DerivationResult`/`VerificationReport`/`NumericalResult`/Pipeline 输出
   绑定引擎版本、seed、容差 → 结果可审计、可复现。
2. **诚实验证**：`FormalProofEngine` 用真实 `lake env lean` 编译验证，工具链缺失返回 `verified: null`
   而非谎称通过；多 Agent 的 FOC/边界 critic 做真实数值检验（非恒 accept）。
3. **无密钥**：LLM 客户端只从环境变量读取 `MATH_AGENT_API_KEY` / `MATH_AGENT_BASE_URL` / `MATH_AGENT_MODEL`。
4. **可移植插件**：`dsh-plugin/` TS 壳用 `defineTool` 注册工具，经 `bridge.py` 桥接 Python 引擎；
   `MATH_AGENT_HOME` / `MATH_AGENT_PYTHON` 环境变量配置，无硬编码路径。

## DSH 插件桥接

```
DSH Agent → dsh-math-agent (TS) → bridge.py (stdin JSON) → MAF 引擎 → stdout JSON → DSH 工具结果
```

bridge 协议：`{"tool": "<name>", "args": {...}}` → `{"status": "ok", "result": ..., "provenance": ...}`。
每个工具输出携带 provenance，标注 untrusted data。

## 与 AEN 的关系

MAF 是 Agent Experience Network (AEN) 的**首个引擎型种子源**：推导 run 导出为 AEN 证据
（`TaskEpisode`/`TraceEvidenceBundle`），数学技巧蒸馏为 `generality: universal` 的通用经验。
详见 `benchmarks/swebench/` 的跨任务族 2×2×2 评测接入。
