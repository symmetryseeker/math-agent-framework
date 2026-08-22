"""
FormalProofEngine — Lean 4 形式化证明引擎（真编译验证）
========================================================
从"模板生成"升级为"可编译验证"：

    - 生成 Lean 4 源码（import Mathlib）
    - 调用真实 Lean 编译器（lean/lake env lean）编译验证
    - 验证结果按源码 digest 缓存，避免重复编译
    - 工具链缺失时诚实报告 `verified: null`，而不是谎称通过

修复的历史问题:
    1. 旧版已知定理返回键 `lean_template`，但 MCP 层读 `lean_code` → 现在统一为 `lean_code`
    2. 旧版从不调用 lean 编译器，"形式化证明"实为模板 → 现在新增 verify_proof / check_toolchain

工具链要求（可选但推荐）:
    - Lean 4 + Mathlib: 安装 elan 后 `elan default stable`，项目内 leanenv/ 提供 Mathlib
    - 未安装时引擎照常生成代码，verify 返回 verified=None，并给出安装指引
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# 框架根目录 / leanenv 项目目录
FRAMEWORK_DIR = Path(__file__).resolve().parent.parent
LEANENV_DIR = FRAMEWORK_DIR / "leanenv"
CACHE_DIR = FRAMEWORK_DIR / "output" / "lean_cache"

# 加入 ~/.elan/bin（elan 默认安装位置）
def _lean_paths() -> List[str]:
    extra = [str(Path.home() / ".elan" / "bin")]
    return extra + os.environ.get("PATH", "").split(os.pathsep)


def _which(name: str) -> Optional[str]:
    candidates = [name, f"{name}.exe", f"{name}.cmd", f"{name}.bat"]
    for directory in _lean_paths():
        for candidate_name in candidates:
            candidate = Path(directory) / candidate_name
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)
    # PATH 兜底（shutil.which 依赖 PATHEXT，Windows 下能找到 .exe）
    return shutil.which(name)


def _mathlib_available() -> bool:
    """leanenv 项目是否已拉取 Mathlib。"""
    return (LEANENV_DIR / ".lake" / "packages" / "mathlib").is_dir()


def check_toolchain() -> Dict[str, Any]:
    """
    检测 Lean 工具链状态。

    Returns:
        {
          "lean": "<version>" | None,
          "lake": "<version>" | None,
          "mathlib": bool,
          "leanenv": "<abs path>" | None,
          "message": "人可读的状态说明"
        }
    """
    lean_bin = _which("lean")
    lake_bin = _which("lake")
    lean_version: Optional[str] = None
    lake_version: Optional[str] = None

    if lean_bin is not None:
        try:
            out = subprocess.run(
                [lean_bin, "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
            lean_version = out.splitlines()[0] if out else lean_bin
        except Exception:
            lean_version = lean_bin

    if lake_bin is not None:
        try:
            out = subprocess.run(
                [lake_bin, "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
            lake_version = out.splitlines()[0] if out else lake_bin
        except Exception:
            lake_version = lake_bin

    mathlib = _mathlib_available()

    # 项目要求的工具链（leanenv/lean-toolchain），与 PATH 上的默认 lean 可能不同
    project_toolchain: Optional[str] = None
    try:
        content = (LEANENV_DIR / "lean-toolchain").read_text(encoding="utf-8").strip()
        if content:
            project_toolchain = content
    except Exception:
        pass

    # 精简版本字符串："Lean (version X, ...)" → "X"
    def short_version(full: Optional[str]) -> Optional[str]:
        if full is None:
            return None
        for prefix in ("Lean (version ", "Lake version ", "Lean "):
            if full.startswith(prefix):
                return full[len(prefix):].split(",")[0].strip()
        return full.split(",")[0].strip()

    lean_short = short_version(lean_version)
    lake_short = short_version(lake_version)

    if lean_bin is None:
        message = (
            "Lean 4 未安装。安装指引：curl -fsSL https://raw.githubusercontent.com/"
            "leanprover/elan/master/elan-init.sh | sh && elan default stable"
        )
    elif not mathlib:
        message = (
            f"Lean 已装（{lean_short}）但 Mathlib 未拉取。在 {LEANENV_DIR} 下运行 "
            "'lake update && lake exe cache get && lake build' 以获取 Mathlib。"
        )
    else:
        message = f"Lean {lean_short} + Mathlib 就绪，可进行真编译验证。"
        if project_toolchain is not None and project_toolchain not in str(lean_version):
            message += f"（项目 leanenv 要求 {project_toolchain}，验证经 lake env 使用项目工具链）"

    return {
        "lean": lean_short,
        "lake": lake_short,
        "mathlib": mathlib,
        "leanenv": str(LEANENV_DIR) if LEANENV_DIR.is_dir() else None,
        "projectToolchain": project_toolchain,
        "message": message,
    }


class FormalProofEngine:
    """
    形式化证明引擎：生成 Lean 4 源码并（若工具链可用）真编译验证。
    """

    # 预定义定理模式（`lean_code` 为经 Lean 4 + Mathlib 真编译验证的源码）
    # 注：以下证明已在 leanenv/.lake 下用 `lake env lean` 编译验证（exit 0）。
    # 若 Mathlib API 随版本演化导致编译失败，引擎会如实返回 verified=false。
    PATTERNS: Dict[str, Dict[str, Any]] = {
        "quadratic_minimum": {
            "statement": "f(x) = a·x + b·x² has a local minimum at x* = -a/(2b) when b > 0",
            "lean_code": """import Mathlib

theorem quadratic_first_deriv {a b : ℝ} :
    deriv (fun x : ℝ => a * x + b * x ^ 2) = fun x => a + 2 * b * x := by
  funext x
  have hid : DifferentiableAt ℝ (fun x : ℝ => x) x := by fun_prop
  have hsq : DifferentiableAt ℝ (fun x : ℝ => x ^ 2) x := by fun_prop
  have hx : DifferentiableAt ℝ (fun x : ℝ => a * x) x := by fun_prop
  have hb2 : DifferentiableAt ℝ (fun x : ℝ => b * x ^ 2) x := by fun_prop
  change deriv ((fun x : ℝ => a * x) + fun x : ℝ => b * x ^ 2) x = a + 2 * b * x
  rw [deriv_add hx hb2]
  rw [deriv_const_mul a hid]
  rw [deriv_const_mul b hsq]
  change a * deriv (fun x : ℝ => x) x + b * deriv ((fun x : ℝ => x) ^ 2) x = a + 2 * b * x
  rw [deriv_pow hid 2]
  simp [deriv_id'']
  ring_nf

theorem quadratic_minimum_unique {a b : ℝ} (hbpos : 0 < b) :
    IsLocalMin (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  rw [IsLocalMin, IsMinFilter]
  apply Filter.Eventually.of_forall
  intro x
  have hb : b ≠ 0 := ne_of_gt hbpos
  have hsq : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2)
      = b * (x + a / (2 * b)) ^ 2 := by
    field_simp [hb]
    ring
  have hdiff : 0 ≤ a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) := by
    rw [hsq]
    exact mul_nonneg (le_of_lt hbpos) (sq_nonneg (x + a / (2 * b)))
  linarith
""",
            "proof_steps": [
                "1. Compute first derivative: f'(x) = a + 2b·x (deriv_add/const_mul/pow, fun_prop)",
                "2. Complete the square: f(x) − f(x*) = b·(x − x*)² (field_simp + ring)",
                "3. Since b > 0, b·(x−x*)² ≥ 0, so f(x*) ≤ f(x) for all x (IsMinFilter + of_forall)",
                "4. Global (hence local) minimum at x* — compiler-verified",
            ],
        },
        "quadratic_maximum": {
            "statement": "f(x) = a·x + b·x² has a local maximum at x* = -a/(2b) when b < 0",
            "lean_code": """import Mathlib

theorem quadratic_maximum_unique {a b : ℝ} (hbneg : b < 0) :
    IsLocalMax (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  rw [IsLocalMax, IsMaxFilter]
  apply Filter.Eventually.of_forall
  intro x
  have hb : b ≠ 0 := ne_of_lt hbneg
  have hsq : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2)
      = b * (x + a / (2 * b)) ^ 2 := by
    field_simp [hb]
    ring
  have hdiff : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) ≤ 0 := by
    rw [hsq]
    exact mul_nonpos_of_nonpos_of_nonneg (le_of_lt hbneg) (sq_nonneg (x + a / (2 * b)))
  linarith
""",
            "proof_steps": [
                "1. Complete the square: f(x) − f(x*) = b·(x − x*)² (field_simp + ring)",
                "2. Since b < 0, b·(x−x*)² ≤ 0, so f(x) ≤ f(x*) for all x (IsMaxFilter + of_forall)",
                "3. Global (hence local) maximum at x* — compiler-verified",
            ],
        },
    }

    def __init__(self, leanenv_dir: Optional[Path] = None, cache_dir: Optional[Path] = None):
        self.leanenv_dir = Path(leanenv_dir) if leanenv_dir is not None else LEANENV_DIR
        self.cache_dir = Path(cache_dir) if cache_dir is not None else CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── 工具链 ──

    def toolchain(self) -> Dict[str, Any]:
        return check_toolchain()

    # ── 代码 digest ──

    @staticmethod
    def _digest(lean_code: str) -> str:
        return hashlib.sha256(lean_code.encode("utf-8")).hexdigest()

    def _cache_path(self, digest: str) -> Path:
        return self.cache_dir / f"{digest}.json"

    # ── 真编译验证 ──

    def verify_proof(
        self,
        lean_code: str,
        theorem_name: Optional[str] = None,
        work_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        用真实 Lean 编译器验证一段 Lean 4 源码。

        Args:
            lean_code: Lean 4 源码（可含 import Mathlib）
            theorem_name: 定理名（仅用于缓存键与日志）
            work_dir: 工作目录（默认框架根下的 leanenv 项目）

        Returns:
            {
              "verified": True|False|None,
              "exit_code": int|null,
              "output": "...",
              "cache_hit": bool,
              "toolchain": {...},
              "theorem": theorem_name,
            }
        """
        # 先查缓存：命中时跳过工具链探测（lean --version 子进程可能较慢）
        digest = self._digest(lean_code)
        cache_file = self._cache_path(digest)
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                cached["cache_hit"] = True
                return cached
            except Exception:
                pass

        toolchain = check_toolchain()
        if toolchain["lean"] is None:
            return {
                "verified": None,
                "exit_code": None,
                "output": toolchain["message"],
                "cache_hit": False,
                "toolchain": toolchain,
                "theorem": theorem_name,
            }
        if not toolchain["mathlib"]:
            return {
                "verified": None,
                "exit_code": None,
                "output": toolchain["message"],
                "cache_hit": False,
                "toolchain": toolchain,
                "theorem": theorem_name,
            }

        project_dir = Path(work_dir) if work_dir is not None else self.leanenv_dir
        project_dir.mkdir(parents=True, exist_ok=True)

        # 写入临时 .lean 文件到 leanenv 项目内（lake env lean 需要项目上下文）
        scratch = project_dir / "_scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        source_file = scratch / f"{digest[:12]}.lean"
        source_file.write_text(lean_code, encoding="utf-8")

        lake_bin = _which("lake")
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join(_lean_paths())

        try:
            result = subprocess.run(
                [lake_bin, "env", "lean", str(source_file)],
                cwd=str(project_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )
            verified = result.returncode == 0
            output = (result.stdout or "") + (result.stderr or "")
            # 编译产物不影响后续运行；删除源码文件（lean 已消费）
            try:
                source_file.unlink()
            except Exception:
                pass
            payload = {
                "verified": verified,
                "exit_code": result.returncode,
                "output": output.strip()[:4000],
                "cache_hit": False,
                "toolchain": toolchain,
                "theorem": theorem_name,
            }
            cache_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return payload
        except subprocess.TimeoutExpired:
            return {
                "verified": False,
                "exit_code": None,
                "output": "Lean 编译超时（300s）",
                "cache_hit": False,
                "toolchain": toolchain,
                "theorem": theorem_name,
            }
        except FileNotFoundError as exc:
            return {
                "verified": None,
                "exit_code": None,
                "output": f"无法启动 Lean 编译器: {exc}",
                "cache_hit": False,
                "toolchain": toolchain,
                "theorem": theorem_name,
            }

    # ── 生成 ──

    def generate_proof(
        self,
        theorem_name: str,
        *,
        verify: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        生成（并可选验证）形式化证明。

        Args:
            theorem_name: 'quadratic_minimum' | 'quadratic_maximum' | 其他
            verify: 是否尝试用真实 Lean 编译器验证（默认 True）
            **kwargs: 预留（如自定义参数）

        Returns:
            {
              "statement": ...,
              "lean_code": ...,           # 统一键名（修复旧版 lean_template/lean_code 不一致）
              "proof_steps": [...],
              "verified": True|False|None,  # None = 工具链缺失，未编译
              "verification": {...} | None,
              "toolchain": {...},
              "available_patterns": [...]  # 仅未知定理时
            }
        """
        toolchain = check_toolchain()

        if theorem_name in self.PATTERNS:
            pattern = self.PATTERNS[theorem_name]
            entry: Dict[str, Any] = {
                "statement": pattern["statement"],
                "lean_code": pattern["lean_code"],
                "proof_steps": pattern["proof_steps"],
                "verified": None,
                "verification": None,
                "toolchain": toolchain,
            }
            if verify:
                entry["verification"] = self.verify_proof(pattern["lean_code"], theorem_name)
                entry["verified"] = entry["verification"]["verified"]
            return entry

        # 未知定理 → 仅生成自定义模板，明确标记未验证
        custom = self.generate_custom_template(
            kwargs.get("theorem_statement", f"Custom theorem: {theorem_name}"),
            kwargs.get("variables", []),
            kwargs.get("conclusion", "True"),
        )
        return {
            "statement": f"Custom theorem: {theorem_name}",
            "lean_code": custom,
            "proof_steps": ["Define theorem statement", "Construct proof (TODO)"],
            "verified": None,
            "verification": None,
            "toolchain": toolchain,
            "available_patterns": list(self.PATTERNS.keys()),
        }

    def generate_custom_template(
        self,
        theorem_statement: str,
        variables: List[Dict[str, str]],
        conclusion: str,
    ) -> str:
        """
        为自定义定理生成 Lean 4 代码模板（未验证，含 `sorry` 占位）。
        """
        lines = ["import Mathlib", ""]
        lines.append("/-!")
        lines.append(f"  Theorem: {theorem_statement}")
        lines.append("-/")
        lines.append("")

        params = []
        for v in variables:
            params.append(f"{v['name']} : {v.get('type', 'ℝ')}")
        for v in variables:
            if "condition" in v:
                params.append(f"{v['name']}cond : {v['condition']}")

        lines.append(f"theorem custom_theorem ({' '.join(params)}) :")
        lines.append(f"    {conclusion} := by")
        lines.append("  -- TODO: Fill in proof")
        lines.append("  sorry")

        return "\n".join(lines)

    # ── 缓存管理 ──

    def clear_cache(self) -> int:
        """清空验证缓存，返回清除的文件数。"""
        removed = 0
        for entry in self.cache_dir.glob("*.json"):
            try:
                entry.unlink()
                removed += 1
            except Exception:
                pass
        return removed
