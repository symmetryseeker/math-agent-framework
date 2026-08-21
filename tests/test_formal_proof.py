"""FormalProofEngine 测试 — 键名统一 + 工具链检测 + 可选真编译验证"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.formal_proof_engine import FormalProofEngine, check_toolchain


def test_generate_proof_uses_lean_code_key():
    """修复历史 bug: 已知定理必须返回 lean_code 键（而非 lean_template）。"""
    engine = FormalProofEngine()
    result = engine.generate_proof("quadratic_minimum", verify=False)
    assert "lean_code" in result
    assert "lean_template" not in result
    assert "proof_steps" in result
    assert result["statement"]


def test_generate_proof_unknown_returns_available_patterns():
    engine = FormalProofEngine()
    result = engine.generate_proof("unknown_theorem_xyz", verify=False)
    assert "lean_code" in result
    assert "available_patterns" in result
    assert "quadratic_minimum" in result["available_patterns"]


def test_check_toolchain_shape():
    status = check_toolchain()
    assert "lean" in status
    assert "lake" in status
    assert "mathlib" in status
    assert "message" in status


def test_verify_proof_without_toolchain_is_null_not_false():
    """工具链缺失时必须返回 verified=None（诚实），而非谎称失败。"""
    engine = FormalProofEngine()
    status = check_toolchain()
    if status["lean"] is None:
        result = engine.verify_proof("import Mathlib\ntheorem t : True := by trivial")
        assert result["verified"] is None
        assert "toolchain" in result
