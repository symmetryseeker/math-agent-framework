#!/usr/bin/env python
"""
export-evidence.py — 把 MAF 推导 run 导出为 AEN 证据（DerivationRun JSON）
============================================================================
MAF 是 AEN（Agent Experience Network）的引擎型种子源。本脚本运行选定的推导/验证，
把结果导出为 DerivationRun JSON——这是 AEN 侧 `scripts/seed-math-experiences.mjs`
（dsh-akn-plugin）转换 TaskEpisode/TraceEvidence/ExperienceRevision 的证据基础。

用法:
    python scripts/export-evidence.py --out <dir> [--tools derive_ces,derive_quadratic,...]

输出: <out>/<tool>.json  →  {"status": "ok", "result": ..., "provenance": {...}}

每个输出携带 provenance（引擎版本/seed/容差），保证可复现、可审计。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIDGE = REPO_ROOT / "bridge.py"

DEFAULT_TOOLS = ["derive_ces", "derive_quadratic", "verify_monte_carlo"]


def run_bridge(tool: str, args: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(BRIDGE)],
        input=json.dumps({"tool": tool, "args": args}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"bridge {tool} exited {proc.returncode}: {proc.stderr[-500:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Export MAF derivation runs as AEN evidence")
    parser.add_argument("--out", default=str(REPO_ROOT / "seeds" / "runs"), help="输出目录")
    parser.add_argument("--tools", default=",".join(DEFAULT_TOOLS), help="逗号分隔的工具名")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for tool in [name.strip() for name in args.tools.split(",") if name.strip()]:
        payload = run_bridge(tool, {})
        if payload.get("status") != "ok":
            print(f"[warn] {tool}: {payload.get('error', 'failed')}")
            continue
        target = out_dir / f"{tool}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        exported.append(tool)
        print(f"[ok] {tool} -> {target}")

    print(json.dumps({"exported": exported, "dir": str(out_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
