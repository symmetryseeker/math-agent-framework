"""Provenance 可复现性测试 — 版本/seed/容差绑定"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.provenance import (
    DEFAULT_SEED,
    MAF_VERSION,
    attach_provenance,
    engine_versions,
    snapshot_provenance,
)


def test_snapshot_contains_version_and_seed():
    p = snapshot_provenance()
    assert p["maf_version"] == MAF_VERSION
    assert p["seed"] == DEFAULT_SEED
    assert "sympy" in p["engine_versions"]
    assert "numpy" in p["engine_versions"]
    assert "python" in p["host"]


def test_snapshot_custom_seed_and_tolerances():
    p = snapshot_provenance(seed=7, tolerances={"foc": 1e-8})
    assert p["seed"] == 7
    assert p["tolerances"]["foc"] == 1e-8


def test_attach_provenance_no_overwrite():
    base = {"a": 1, "provenance": {"custom": True}}
    result = attach_provenance(base)
    assert result["provenance"]["custom"] is True


def test_derivation_result_has_provenance():
    from core.symbolic_engine import SymbolicEngine
    engine = SymbolicEngine()
    engine.declare_symbols({"x": None, "a": None})
    x = engine.get_symbol("x")
    a = engine.get_symbol("a")
    result = engine.differentiate(a * x, x, name="d(ax)/dx").simplify().build()
    payload = result.to_dict()
    assert "provenance" in payload
    assert payload["provenance"]["maf_version"] == MAF_VERSION


def test_verification_report_has_provenance():
    from core.verification_engine import VerificationEngine
    verifier = VerificationEngine("t")
    verifier.add_symbolic_check("identity", lambda: True)
    payload = verifier.get_report().to_dict()
    assert "provenance" in payload


def test_pipeline_metadata_has_provenance():
    from core.pipeline_engine import PipelineEngine
    pipeline = PipelineEngine("p", output_dir="output/_test_pipeline")
    pipeline.add_step("s", "identity", lambda params: {"value": 1})
    results = pipeline.run({})
    assert "provenance" in results["metadata"]
    assert results["metadata"]["provenance"]["maf_version"] == MAF_VERSION
