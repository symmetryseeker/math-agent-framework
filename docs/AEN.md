# MAF × AEN 集成

Math Agent Framework 是 [Agent Experience Network (AEN)](https://github.com/symmetryseeker/dsh-akn-plugin)
的**首个引擎型种子源**。数学技巧天然通用可迁移——它们是经验网络"预训练/社会化知识"层
（`generality: universal`）的第一块基石，是"共进化指导自进化"的起点。

## 数据流

```text
MAF 推导 run
  → bridge.py aen_evidence   （sessionDigest + provenance + eventRange）
  → dsh-akn-plugin scripts/seed-math-experiences.mjs
  → TaskEpisode / TraceEvidenceBundle / ExperienceRevision（内容寻址）
  → AEN 本地证据库 → review → Promotion → 公共 Hub
```

## 证据导出

```sh
python scripts/export-evidence.py --out seeds/runs        # 批量导出 DerivationRun JSON
python -c "..."  # 或经 bridge 单条导出:
printf '{"tool":"aen_evidence","args":{"derive_tool":"derive_ces"}}' | python bridge.py
```

导出的 JSON 携带 `provenance`（引擎版本/seed/容差），构成 AEN 的 Configuration Cell 指纹。

## 数学种子（dsh-akn-plugin）

`seed-math-experiences.mjs` 把上述证据转成 5 个 `generality: universal` 的数学技巧种子：

| 种子 | kind |
|---|---|
| CES 边际产出顺序 | execution_strategy |
| 二次型拐点 + SOC | execution_strategy |
| CES 边界参数奇异 | negative_result |
| 蒙特卡洛 FOC 验收线 | safety_constraint |
| FOC 空解集恢复 | failure_recovery |

诚实标注 H0（单 run 观测性），不冒充 H3 因果。

## 跨任务族评测（H3 / generality 证据）

`benchmarks/swebench/`（dsh-akn-plugin）把 SWE-bench 标准任务接为 `BenchmarkTask`（`suiteKind: 'transfer'`），
跑 baseline vs experience_applied 的 2×2×2——这是 `generality: universal` 的 transfer 评测证据来源，
也是"经验网络确实提升 Agent 表现"的价值证明路径。

## 快速验证

```sh
# MAF 侧：演示注入验证经验 → 通过率提升（0.6 → 0.8）
python benchmarks/maf-uplift/run.py
# AEN 侧（dsh-akn-plugin）：
node scripts/seed-math-experiences.mjs          # 生成种子 + 可检索
node benchmarks/swebench/run-smoke.mjs          # 2×2×2 uplift aggregate
```
