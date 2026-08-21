#!/usr/bin/env bash
# install-lean.sh — 幂等安装 Lean 4 + Mathlib（形式化证明真编译验证）
# ================================================================
# 分步执行，每步可重入：
#   1) elan        — 安装 elan（如果 ~/.elan/bin/lean 不存在）
#   2) lean stable — 默认工具链
#   3) leanenv     — 本项目 leanenv/ 拉取 Mathlib（lake update + cache get + build）
#
# 用法: bash scripts/install-lean.sh
# 检测: python cli/cli.py lean-doctor

set -euo pipefail

LEANENV_DIR="$(cd "$(dirname "$0")/../leanenv" && pwd)"
ELAN_BIN="$HOME/.elan/bin"

echo "==> [1/4] elan"
if [ ! -x "$ELAN_BIN/lean" ]; then
  echo "    installing elan to ~/.elan ..."
  curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- --default-toolchain stable
else
  echo "    elan already installed ($($ELAN_BIN/lean --version | head -1))"
fi
export PATH="$ELAN_BIN:$PATH"

echo "==> [2/4] lean toolchain"
elan default stable >/dev/null 2>&1 || true
lean --version

echo "==> [3/4] Mathlib (lake update)"
cd "$LEANENV_DIR"
lake update

echo "==> [4/4] Mathlib cache + build"
lake exe cache get || echo "    (cache get 不可用，将走源码编译，耗时较长)"
lake build

echo ""
echo "Lean toolchain ready:"
lean --version
lake --version
echo "Mathlib: $(test -d "$LEANENV_DIR/.lake/packages/mathlib" && echo available || echo missing)"
