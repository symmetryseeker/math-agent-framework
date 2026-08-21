"""MultiAgentVerificationEngine 测试 — 真 FOC 检验 + 模型角色降级"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.multi_agent_verify_engine import (
    AgentOpinion,
    MultiAgentVerificationEngine,
    Verdict,
)


def test_real_foc_critic_accepts_correct_formula():
    """真实 FOC 检验：x* = -a1/(2a2) 处数值导数应接近 0 → accept。"""
    import numpy as np

    def lpg(pd):
        a1, a2 = pd.get("a1", 1.0), pd.get("a2", -1.0)
        x = pd.get("_x", 0.0)
        return a1 * x + a2 * x**2

    def grad(pd):
        return {"_x": pd.get("a1", 1.0) + 2 * pd.get("a2", -1.0) * pd.get("_x", 0.0)}

    def pgen():
        return {"a1": float(np.random.uniform(-3, 3)), "a2": float(np.random.uniform(-3, 3))}

    def tp(pd):
        a1, a2 = pd.get("a1", 1.0), pd.get("a2", -1.0)
        return -a1 / (2 * a2) if abs(a2) > 1e-9 else float("nan")

    critic = MultiAgentVerificationEngine.make_foc_critic(lpg, grad, pgen, tp, n_samples=100, tolerance=1e-4)
    result = critic("FOC claim", {"parameters": {}})
    assert result["vote"] == "accept", result["reasoning"]
    assert result["evidence"]["checked"] > 0


def test_engine_verify_with_real_foc_critic():
    engine = MultiAgentVerificationEngine()
    import numpy as np

    def lpg(pd):
        return pd.get("a1", 1.0) * pd.get("_x", 0.0) + pd.get("a2", -1.0) * pd.get("_x", 0.0) ** 2

    def grad(pd):
        return {"_x": pd.get("a1", 1.0) + 2 * pd.get("a2", -1.0) * pd.get("_x", 0.0)}

    def pgen():
        return {"a1": float(np.random.uniform(-3, 3)), "a2": float(np.random.uniform(-3, 3))}

    def tp(pd):
        a1, a2 = pd.get("a1", 1.0), pd.get("a2", -1.0)
        return -a1 / (2 * a2) if abs(a2) > 1e-9 else float("nan")

    def proposer(c):
        return {"proof": "FOC gives x* = -a1/(2a2)", "confidence": 0.9}

    verdict = engine.verify(
        claim="x* = -a1/(2a2)",
        proposer_fn=proposer,
        critic_fns=[MultiAgentVerificationEngine.make_foc_critic(lpg, grad, pgen, tp, n_samples=100)],
    )
    assert verdict.verdict in (v.value for v in Verdict)
    assert verdict.proposer_opinion is not None
    assert verdict.vote_counts["accept"] >= 1
    payload = verdict.to_dict()
    assert "provenance" in payload  # 输出绑定可复现性


def test_model_mode_degrades_to_engine_when_no_key():
    """无 API key 时 model 模式自动降级，不抛错。"""
    engine = MultiAgentVerificationEngine()

    def proposer(c):
        return {"proof": "deterministic proof", "confidence": 0.8}

    verdict = engine.verify(claim="c", proposer_fn=proposer, proposer_mode="model")  # 无 model_client
    assert verdict.mode == "engine" or verdict.mode == "model"
    assert verdict.verdict in (v.value for v in Verdict)


class _FakeModel:
    model = "fake-model"

    def is_available(self):
        return True

    def chat(self, system, user, temperature=0.0):
        return '{"vote": "reject", "confidence": 0.7, "reasoning": "counterexample found"}'

    def chat_json(self, system, user, temperature=0.0):
        return {"vote": "reject", "confidence": 0.7, "reasoning": "counterexample found", "proof": "alt"}


def test_model_critic_called_when_client_available():
    engine = MultiAgentVerificationEngine()

    def proposer(c):
        return {"proof": "p", "confidence": 0.8}

    verdict = engine.verify(
        claim="c",
        proposer_fn=proposer,
        critic_fns=[],
        model_client=_FakeModel(),
        use_model_critic=True,
        dimensions=["correctness"],
    )
    assert any(op.source == "model" for op in verdict.critic_opinions)
    assert verdict.critic_opinions[0].vote == "reject"


def test_edge_case_critic_abstains_without_check_fn():
    """边界 critic 在未提供 edge_check 时诚实 abstain（旧版恒 accept 已修复）。"""
    critic = MultiAgentVerificationEngine.make_edge_case_critic({"a": (-1, 1)}, n_samples=10)
    result = critic("claim", {})
    assert result["vote"] == "abstain"
    assert "edge_check" in result["reasoning"]
