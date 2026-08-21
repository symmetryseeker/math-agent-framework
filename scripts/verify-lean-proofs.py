#!/usr/bin/env python
"""
verify-lean-proofs.py — 编译验证所有内置 Lean 证明
====================================================
遍历 FormalProofEngine.PATTERNS，用真实 Lean 编译器逐个验证。

用法:
    python scripts/verify-lean-proofs.py           # 全部
    python scripts/verify-lean-proofs.py quadratic_minimum   # 单个
    python scripts/verify-lean-proofs.py --clear   # 清缓存后重验
    python scripts/verify-lean-proofs.py --strict  # 任一失败退出码 1（CI 用）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.formal_proof_engine import FormalProofEngine, check_toolchain


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    clear = "--clear" in args
    names = [a for a in args if not a.startswith("--")]

    engine = FormalProofEngine()
    if clear:
        cleared = engine.clear_cache()
        print(f"cleared {cleared} cached verification results")

    toolchain = check_toolchain()
    print(f"toolchain: lean={toolchain['lean']} mathlib={toolchain['mathlib']}")

    if names:
        targets = [(n, engine.PATTERNS.get(n)) for n in names]
    else:
        targets = list(engine.PATTERNS.items())

    failed = False
    for name, pattern in targets:
        if pattern is None:
            print(f"[{name}] SKIP (unknown pattern)")
            continue
        result = engine.generate_proof(name)
        verified = result.get("verified")
        mark = {True: "PASS", False: "FAIL", None: "SKIP"}.get(verified, "SKIP")
        print(f"[{name}] {mark} verified={verified}")
        if verified is False:
            verification = result.get("verification") or {}
            print(f"    {verification.get('output', '')[:400]}")
            failed = True

    if strict and failed:
        print("\nSTRICT: 存在编译失败的证明")
        return 1
    print("\ndone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
