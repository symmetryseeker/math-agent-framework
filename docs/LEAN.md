# Lean 4 真编译验证

MAF 的 `FormalProofEngine` 用 **Lean 4 + Mathlib** 对内置定理做**真编译验证**——
不是模板生成，而是调用真实 `lake env lean` 编译，`verified: true/false/null` 诚实返回。

## 工具链安装

```sh
bash scripts/install-lean.sh      # 幂等：elan → lean stable → Mathlib（leanenv/）
python cli/cli.py lean-doctor     # 检测 lean/lake/mathlib 状态
```

- leanenv/ 是 Mathlib 项目（`lean-toolchain` 固定 `v4.34.0-rc1`，`lakefile.lean` require mathlib）。
- Mathlib 首次拉取走 blobless 克隆 + CDN 预编译 olean（约 1GB），之后增量。
- 未安装 Lean 时引擎**不谎称**：`math_lean_proof` 返回 `verified: null` 并给出安装指引。

## 使用

```sh
python cli/cli.py proof quadratic_minimum          # 生成 + 真编译验证
python scripts/verify-lean-proofs.py --strict       # 验证所有内置证明（CI 用）
```

## 内置已验证定理（`leanenv/Proofs/Quadratic.lean`）

- `quadratic_first_deriv` — f'(x) = a + 2b·x（deriv_add/const_mul/pow + fun_prop）
- `quadratic_minimum_unique` — b>0 时 IsLocalMin at x* = -a/(2b)
  （配方恒等式 field_simp+ring → IsMinFilter + Filter.Eventually.of_forall）
- `quadratic_maximum_unique` — b<0 时 IsLocalMax

这些证明已用真实 Lean 编译器编译通过（exit 0），结果按源码 digest 缓存到 `output/lean_cache/`。

## 验证缓存

- 缓存优先：命中时跳过工具链探测（`lean --version` 子进程较慢）。
- `FormalProofEngine().clear_cache()` 或 `python scripts/verify-lean-proofs.py --clear` 清缓存。

## 新增定理

1. 在 `core/formal_proof_engine.py` 的 `PATTERNS` 加 `lean_code`（import Mathlib 的完整证明）。
2. 跑 `python scripts/verify-lean-proofs.py quadratic_xxx` 对着编译器迭代直到 exit 0。
3. 通过后把验证通过的源码固化进 PATTERNS，提交。
