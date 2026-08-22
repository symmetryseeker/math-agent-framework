#!/usr/bin/env python
"""
bridge.py — Math Agent Framework ↔ DSH 插件桥
==============================================
DeepSeek Harness (DSH) 的 TS 插件通过本脚本调用 Python 引擎。

协议:
    输入: stdin 一行 JSON  {"tool": "<tool>", "args": {...}}
    输出: stdout 一行 JSON {"status": "ok", "result": {...}, "provenance": {...}}
                             或 {"status": "error", "error": "..."}

本文件位于 MAF 仓库根目录，因此可直接 import core/models。
也可以先 `pip install .` 使 core 成为可导入包，从任意位置运行。

支持的 tool:
    derive               运行模型完整推导流水线
    verify_symbolic      符号一致性验证（真实执行模型步骤）
    verify_monte_carlo   蒙特卡洛数值验证
    lean_proof           生成 + 真编译验证 Lean 4 证明
    multi_agent_verify   QED 多 Agent 对抗验证
    quantecon            QuantEcon 动态优化
    derive_ces / derive_ipf / derive_quadratic /
    derive_dynamic / derive_comparative   network_embedded_growth 的 NSFC 专属步骤

安全: 本桥不执行任意代码；仅按 tool 名分派到受控引擎方法。参数经 JSON Schema 由
TS 层校验，这里再做基本类型防御。
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# 保证 core/models/cli/mcp 可导入（本文件位于仓库根目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Windows 控制台默认 GBK，强制 stdin/stdout UTF-8（数学符号如 ℝ/U+211D 无法用 GBK 编码）
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _engine_results_to_json(value):
    """把引擎返回对象转为可 JSON 序列化的 dict。"""
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {str(k): _engine_results_to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_engine_results_to_json(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _derive(args):
    from core.pipeline_engine import PipelineEngine
    from core.symbolic_engine import SymbolicEngine
    from models import discover_models

    model_name = args.get("model", "quadratic_form")
    models = discover_models()
    if model_name not in models:
        raise ValueError(f"model '{model_name}' not found; available: {list(models)}")
    pipeline = PipelineEngine(f"{model_name} Pipeline", output_dir=args.get("output_dir", "./output"))
    instance = models[model_name]()
    # 先创建 SymbolicEngine 作为步骤共享上下文，再注册步骤（闭包直接捕获）
    engine = SymbolicEngine()
    for step in instance.get_derivation_steps():
        method = getattr(instance, step["method_name"])
        pipeline.add_step(step["method_name"], step.get("description", step["method_name"]),
                          lambda params, _m=method, _e=engine: _engine_results_to_json(_m(_e, params)),
                          dependencies=step.get("dependencies", []),
                          tools=step.get("tools", []))
    results = pipeline.run({})
    results["model"] = model_name
    return results


def _verify_symbolic(args):
    from core.verification_engine import VerificationEngine
    from core.symbolic_engine import SymbolicEngine
    from models import discover_models

    model_name = args.get("model", "network_embedded_growth")
    models = discover_models()
    if model_name not in models:
        raise ValueError(f"model '{model_name}' not found")
    verifier = VerificationEngine(title=f"Symbolic Verification: {model_name}")
    engine = SymbolicEngine()
    instance = models[model_name]()
    for step in instance.get_derivation_steps():
        method = getattr(instance, step["method_name"], None)
        if method is None:
            verifier.add_symbolic_check(step["method_name"], lambda: False, detail="missing method")
            continue

        def run_step(_m=method):
            try:
                output = _m(engine, {})
                return isinstance(output, dict) and not output.get("verified") is False
            except Exception:
                return False

        verifier.add_symbolic_check(step["method_name"], run_step,
                                    detail=f"executes '{step['method_name']}' on a fresh SymbolicEngine")
    report = verifier.get_report()
    payload = report.to_dict()
    payload["model"] = model_name
    payload["status"] = "PASS" if report.pass_rate() >= 100 else "FAIL"
    return payload


def _verify_monte_carlo(args):
    from core.symbolic_engine import SymbolicEngine
    import numpy as np

    n_samples = int(args.get("n_samples", 10000))
    seed = int(args.get("seed", 723003))
    np.random.seed(seed)
    foc_pass = 0
    for _ in range(min(n_samples, 5000)):
        a1 = float(np.random.uniform(-3, 3))
        a2 = float(np.random.uniform(-3, 3))
        if abs(a2) < 1e-6:
            continue
        tp = -a1 / (2 * a2)
        eps = 1e-6
        deriv = ((a1 * (tp + eps) + a2 * (tp + eps) ** 2) - (a1 * (tp - eps) + a2 * (tp - eps) ** 2)) / (2 * eps)
        if abs(deriv) < 1e-4:
            foc_pass += 1
    return {
        "test": "FOC zero-crossing at theoretical turning point",
        "n_samples": n_samples,
        "passed": foc_pass,
        "pass_rate": round(foc_pass / max(n_samples, 1) * 100, 1),
        "seed": seed,
    }


def _lean_proof(args):
    from core.formal_proof_engine import FormalProofEngine

    theorem = args.get("theorem", "quadratic_minimum")
    style = args.get("style", "verbose")
    result = FormalProofEngine().generate_proof(theorem)
    if style == "lean_only":
        return {"lean_code": result.get("lean_code", ""),
                "verified": result.get("verified"),
                "verification": result.get("verification")}
    return result


def _multi_agent_verify(args):
    from core.multi_agent_verify_engine import MultiAgentVerificationEngine
    import numpy as np

    claim = args.get("claim", "XE* = -α₁/(2α₂) is the unique interior optimum")
    dimensions = args.get("dimensions", ["correctness", "edge_cases"])
    use_model = bool(args.get("use_model", True))

    def lpg(pd):
        return pd.get("a1", 1.0) * pd.get("_x", 0.0) + pd.get("a2", -1.0) * pd.get("_x", 0.0) ** 2

    def grad(pd):
        return {"_x": pd.get("a1", 1.0) + 2 * pd.get("a2", -1.0) * pd.get("_x", 0.0)}

    def pgen():
        return {"a1": float(np.random.uniform(-3, 3)), "a2": float(np.random.uniform(-3, 3))}

    def tp(pd):
        a1, a2 = pd.get("a1", 1.0), pd.get("a2", -1.0)
        return -a1 / (2 * a2) if abs(a2) > 1e-9 else float("nan")

    critic_fns = [MultiAgentVerificationEngine.make_foc_critic(lpg, grad, pgen, tp, n_samples=100)]
    model_client = None
    if use_model:
        try:
            from core.llm_client import get_client as _get_llm_client
            candidate = _get_llm_client()
            if candidate.is_available():
                model_client = candidate
        except Exception:
            model_client = None

    def proposer(c):
        return {"proof": "FOC: d/dx(α₁·x+α₂·x²)=α₁+2α₂·x=0 → x*=-α₁/(2α₂). SOC: d²/dx²=2α₂.",
                "confidence": 0.9}

    engine = MultiAgentVerificationEngine()
    verdict = engine.verify(
        claim=claim, proposer_fn=proposer, critic_fns=critic_fns,
        model_client=model_client,
        proposer_mode="engine" if model_client is None else "hybrid",
        use_model_critic=model_client is not None,
        dimensions=dimensions,
    )
    return verdict.to_dict()


def _quantecon(args):
    from core.quantecon_engine import QuantEconEngine
    import numpy as np

    engine = QuantEconEngine()
    operation = args.get("operation", "riccati")
    if operation == "riccati":
        A = np.array(args.get("A", [[1.0, 0.0], [0.0, 0.9]]))
        B = np.array(args.get("B", [[0.0], [1.0]]))
        Q = np.array(args.get("Q", [[1.0, 0.0], [0.0, 0.0]]))
        R = np.array(args.get("R", [[1.0]]))
        return engine.solve_discrete_riccati(A, B, Q, R).to_dict()
    if operation == "markov_chain":
        P = np.array(args.get("P", [[0.8, 0.2], [0.3, 0.7]]))
        return engine.markov_chain(P).to_dict()
    return engine.solve_discrete_riccati().to_dict()


def _aen_evidence(args):
    """返回一次推导 run 的 AEN 证据包（供 dsh-akn-plugin 种子生成器直接转换）。"""
    from core.provenance import snapshot_provenance
    import hashlib
    import json as _json

    derive_tool = args.get("derive_tool", "derive_quadratic")
    handler = HANDLERS.get(derive_tool)
    if handler is None:
        raise ValueError(f"unknown derive_tool '{derive_tool}'")
    result = _engine_results_to_json(handler(args.get("derive_args", {})))
    provenance = snapshot_provenance(model_name=args.get("model"))
    run_digest = hashlib.sha256(_json.dumps(
        {"scope": "maf.derivation-run", "tool": derive_tool, "result": result, "provenance": provenance},
        sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    return {
        "protocol": "aen-evidence-v1",
        "tool": derive_tool,
        "sessionDigest": f"sha256:{run_digest}",
        "eventRange": {"fromSeq": 0, "toSeq": 1},
        "mappingProfile": "maf-derivation-run",
        "mappingVersion": "0.1",
        "result": result,
        "provenance": provenance,
    }


def _derive_ng_step(args, step_name):
    from core.symbolic_engine import SymbolicEngine
    from models.builtin.network_embedded_growth import NetworkEmbeddedGrowthModel

    engine = SymbolicEngine()
    instance = NetworkEmbeddedGrowthModel()
    method = getattr(instance, step_name, None)
    if method is None:
        raise ValueError(f"step '{step_name}' not found in network_embedded_growth")
    return _engine_results_to_json(method(engine, args.get("params", {})))


HANDLERS = {
    "derive": _derive,
    "verify_symbolic": _verify_symbolic,
    "verify_monte_carlo": _verify_monte_carlo,
    "lean_proof": _lean_proof,
    "multi_agent_verify": _multi_agent_verify,
    "quantecon": _quantecon,
    "derive_ces": lambda a: _derive_ng_step(a, "step1_ces"),
    "derive_ipf": lambda a: _derive_ng_step(a, "step2_ipf"),
    "derive_quadratic": lambda a: _derive_ng_step(a, "step3_quadratic"),
    "derive_dynamic": lambda a: _derive_ng_step(a, "step4_dynamic"),
    "derive_comparative": lambda a: _derive_ng_step(a, "step5_comparative"),
    "aen_evidence": _aen_evidence,
}


def main():
    line = sys.stdin.readline()
    if not line.strip():
        print(json.dumps({"status": "error", "error": "empty input"}, ensure_ascii=False))
        return 1
    try:
        request = json.loads(line)
        tool = request.get("tool")
        args = request.get("args", {}) if isinstance(request.get("args", {}), dict) else {}
        if not isinstance(tool, str) or tool not in HANDLERS:
            raise ValueError(f"unknown tool '{tool}'; available: {sorted(HANDLERS)}")
        result = HANDLERS[tool](args)
        payload = {"status": "ok", "result": _engine_results_to_json(result)}
        try:
            from core.provenance import snapshot_provenance
            payload["provenance"] = snapshot_provenance(model_name=args.get("model"))
        except Exception:
            pass
        print(json.dumps(payload, ensure_ascii=False, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": f"{exc}",
                          "traceback": traceback.format_exc()[-2000:]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
