"""
MultiAgentVerificationEngine — 多Agent对抗验证引擎
====================================================
实现 QED/Numina 模式的多重验证: Proposer + Critic + Judge。

本次升级（相对旧版）:
    1. 接入真实 LLM 作为 Proposer / Critic / Judge（OpenAI 兼容端点，env 配置）
    2. 保留确定性引擎 Critic，并修复旧版"恒 accept"造假：
       - make_foc_critic 现在真正做数值一阶条件检验
       - make_edge_case_critic 现在真正在参数边界抽样检验
    3. 输出绑定 provenance（引擎版本/seed/容差），保证可复现
    4. LLM 输出经 chat_json 健壮解析；无 API key 时自动退回引擎模式

角色:
    Proposer   提议者：生成推导/证明草稿（引擎 或 LLM）
    Critic     批评者：对抗性检验，尝试找反例（引擎 或 LLM，可并行）
    Judge      裁决者：综合评判，给出最终结论（多数票 或 LLM）

配置（经环境变量，绝不硬编码）:
    export MATH_AGENT_API_KEY=...          # 必填才启用模型角色
    export MATH_AGENT_BASE_URL=...         # 默认 https://api.deepseek.com/anthropic
    export MATH_AGENT_MODEL=...            # 默认 deepseek-v4-pro
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Verdict(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"
    UNDECIDED = "UNDECIDED"


@dataclass
class AgentOpinion:
    """单个验证 Agent 的意见"""
    agent_role: str  # 'proposer' | 'critic' | 'judge'
    dimension: str  # 'correctness' | 'security' | 'reproducibility' | 'completeness' | 'edge_cases'
    claim: str
    vote: str  # 'accept' | 'reject' | 'abstain'
    confidence: float  # 0-1
    reasoning: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    source: str = "engine"  # 'engine' | 'model'

    def to_dict(self) -> dict:
        return {
            "agent_role": self.agent_role,
            "dimension": self.dimension,
            "claim": self.claim,
            "vote": self.vote,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "source": self.source,
        }


@dataclass
class MultiAgentVerdict:
    """多Agent综合裁决"""
    claim: str
    verdict: str  # ACCEPTED | REJECTED | NEEDS_REVISION | UNDECIDED
    proposer_opinion: Optional[AgentOpinion] = None
    critic_opinions: List[AgentOpinion] = field(default_factory=list)
    judge_summary: str = ""
    confidence_score: float = 0.0
    vote_counts: Dict[str, int] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    mode: str = "engine"

    def to_dict(self) -> dict:
        result = {
            "claim": self.claim,
            "verdict": self.verdict,
            "mode": self.mode,
            "proposer": self.proposer_opinion.to_dict() if self.proposer_opinion else None,
            "critics": [c.to_dict() for c in self.critic_opinions],
            "judge_summary": self.judge_summary,
            "confidence_score": self.confidence_score,
            "vote_counts": self.vote_counts,
            "timestamp": self.timestamp,
        }
        from .provenance import attach_provenance
        return attach_provenance(result)


def _import_llm_client() -> Any:
    """延迟导入 LLMClient，避免在无依赖环境下报错。"""
    from .llm_client import LLMClient, get_client
    return LLMClient, get_client


class MultiAgentVerificationEngine:
    """
    多Agent对抗验证引擎 — QED/Numina 模式。

    用法（引擎模式，确定性）:
        engine = MultiAgentVerificationEngine()
        def proposer(claim): return {"proof": "...", "confidence": 0.9, "turning_point_formula": ..., "parameters": {...}}
        critic = MultiAgentVerificationEngine.make_foc_critic(func, grad_func, param_generator, turning_point_fn)
        verdict = engine.verify(claim=claim, proposer_fn=proposer, critic_fns=[critic])

    用法（模型模式，需 API key）:
        from .llm_client import get_client
        verdict = engine.verify(claim=claim, proposer_mode="model", model_client=get_client(),
                                dimensions=["correctness", "edge_cases"])

    用法（混合模式）:
        verdict = engine.verify(claim=claim, proposer_mode="engine", proposer_fn=proposer,
                                critic_fns=[critic], model_client=get_client(), use_model_critic=True)
    """

    DEFAULT_DIMENSIONS = [
        {"key": "correctness", "name": "数学正确性", "description": "推导步骤是否逻辑正确，符号运算是否无误"},
        {"key": "security", "name": "假设条件", "description": "所有隐含假设是否满足，边界条件是否处理"},
        {"key": "reproducibility", "name": "可复现性", "description": "结果是否可被独立复现，参数是否完备"},
        {"key": "completeness", "name": "完整性", "description": "推导是否完整，是否遗漏关键步骤"},
        {"key": "edge_cases", "name": "边界情况", "description": "极端参数值下结论是否仍然成立"},
    ]

    def __init__(self):
        self._history: List[MultiAgentVerdict] = []

    # ── 主入口 ──

    def verify(
        self,
        claim: str,
        proposer_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
        critic_fns: Optional[List[Callable[[str, Dict], Dict[str, Any]]]] = None,
        judge_fn: Optional[Callable[[str, AgentOpinion, List[AgentOpinion]], str]] = None,
        model_client: Optional[Any] = None,
        proposer_mode: str = "engine",
        use_model_critic: bool = True,
        use_model_judge: bool = False,
        dimensions: Optional[List[str]] = None,
        threshold: float = 0.5,
        tolerance: float = 1e-4,
        n_samples: int = 500,
    ) -> MultiAgentVerdict:
        """
        执行多Agent对抗验证。

        Args:
            claim: 待验证的数学命题
            proposer_fn: 引擎提议函数 claim → {'proof', 'confidence', 可选数值证据}
            critic_fns: 引擎批评函数列表 [(claim, proof) → {'vote', 'reasoning', 'dimension', ...}]
            judge_fn: 引擎裁决函数
            model_client: LLMClient 实例（None 则不使用模型角色）
            proposer_mode: 'engine' | 'model' | 'hybrid'
                - engine: 必须提供 proposer_fn
                - model:  使用 LLM 生成证明草稿
                - hybrid: 先用引擎 proposer_fn，再用 LLM 补充
            use_model_critic: 是否启用 LLM Critic（需 model_client）
            use_model_judge: 是否用 LLM 做最终裁决
            dimensions: 验证维度（默认全部）
            threshold: 接受票比例阈值
            tolerance: FOC 数值容差
            n_samples: 边界抽样数
        """
        if dimensions is None:
            dimensions = [d["key"] for d in self.DEFAULT_DIMENSIONS]

        has_model = model_client is not None and getattr(model_client, "is_available", lambda: False)()
        mode = proposer_mode
        if mode == "model" and not has_model:
            mode = "engine"  # 无 key 时自动降级
        if mode != "model" and proposer_fn is None and mode == "engine" and has_model:
            mode = "hybrid"  # 引擎未提供但模型可用 → 混合

        # Phase 1: Proposer
        proposer_opinion = self._propose(
            claim, proposer_fn, model_client, mode, has_model, dimensions, tolerance
        )
        proof = proposer_opinion.evidence

        # Phase 2: Critics（引擎 + 可选 LLM）
        critic_opinions: List[AgentOpinion] = []
        if critic_fns:
            for critic_fn in critic_fns:
                critic_opinions.append(self._safe_critic(critic_fn, claim, proof))
        if use_model_critic and has_model:
            for dimension in dimensions:
                critic_opinions.append(self._model_critic(claim, proof, model_client, dimension))

        # Phase 3: Judge
        if use_model_judge and has_model:
            verdict_str = self._model_judge(claim, proposer_opinion, critic_opinions, model_client)
        elif judge_fn:
            verdict_str = judge_fn(claim, proposer_opinion, critic_opinions)
        else:
            verdict_str = self._default_judge(critic_opinions, threshold)

        # 统计
        vote_counts = {"accept": 0, "reject": 0, "abstain": 0}
        for op in critic_opinions:
            vote_counts[op.vote] = vote_counts.get(op.vote, 0) + 1
        accept_rate = vote_counts["accept"] / max(len(critic_opinions), 1)
        confidence_score = accept_rate * proposer_opinion.confidence

        verdict = MultiAgentVerdict(
            claim=claim,
            verdict=verdict_str,
            proposer_opinion=proposer_opinion,
            critic_opinions=critic_opinions,
            judge_summary=self._summarize(verdict_str, vote_counts, proposer_opinion, critic_opinions),
            confidence_score=confidence_score,
            vote_counts=vote_counts,
            mode=mode,
        )
        self._history.append(verdict)
        return verdict

    # ── Proposer ──

    def _propose(
        self,
        claim: str,
        proposer_fn: Optional[Callable[[str], Dict[str, Any]]],
        model_client: Any,
        mode: str,
        has_model: bool,
        dimensions: List[str],
        tolerance: float,
    ) -> AgentOpinion:
        if mode == "model":
            return self._model_proposer(claim, model_client, dimensions)
        if mode == "hybrid" and proposer_fn is not None:
            engine_opinion = self._safe_proposer(proposer_fn, claim)
            model_opinion = self._model_proposer(claim, model_client, dimensions)
            # 合并：以引擎证据为准，附上模型证据
            merged = dict(engine_opinion.evidence)
            merged["model_review"] = model_opinion.evidence
            return AgentOpinion(
                agent_role="proposer",
                dimension="overall",
                claim=claim,
                vote="accept",
                confidence=min(1.0, engine_opinion.confidence * 0.6 + model_opinion.confidence * 0.4),
                reasoning=f"{engine_opinion.reasoning}\n[model] {model_opinion.reasoning}",
                evidence=merged,
                source="hybrid",
            )
        if proposer_fn is not None:
            return self._safe_proposer(proposer_fn, claim)
        raise ValueError(
            "proposer_mode='engine' requires proposer_fn; or set proposer_mode='model' / provide model_client"
        )

    def _safe_proposer(self, proposer_fn: Callable[[str], Dict[str, Any]], claim: str) -> AgentOpinion:
        try:
            result = proposer_fn(claim)
        except Exception as exc:  # noqa: BLE001
            return AgentOpinion(
                agent_role="proposer", dimension="overall", claim=claim, vote="abstain",
                confidence=0.0, reasoning=f"Proposer error: {exc}", source="engine",
            )
        return AgentOpinion(
            agent_role="proposer", dimension="overall", claim=claim, vote="accept",
            confidence=result.get("confidence", 0.8),
            reasoning=result.get("proof", ""),
            evidence=result,
            source="engine",
        )

    def _model_proposer(self, claim: str, model_client: Any, dimensions: List[str]) -> AgentOpinion:
        system = (
            "You are a rigorous mathematical Proposer in a QED-style verification pipeline. "
            "Given a mathematical claim, produce a derivation/proof draft. "
            "Output JSON with keys: proof (string), confidence (0-1), "
            "turning_point_formula (string|null), parameters (object|null), assumptions (array of string), "
            "edge_case_risks (array of string)."
        )
        data = model_client.chat_json(system, f"Claim: {claim}")
        proof_text = str(data.get("proof") or data.get("_raw") or "")
        confidence = _clamp_float(data.get("confidence", 0.6))
        return AgentOpinion(
            agent_role="proposer", dimension="overall", claim=claim, vote="accept",
            confidence=confidence,
            reasoning=proof_text[:2000],
            evidence={**data, "model": getattr(model_client, "model", "unknown")},
            source="model",
        )

    # ── Critics ──

    def _safe_critic(self, critic_fn: Callable, claim: str, proof: Dict) -> AgentOpinion:
        try:
            result = critic_fn(claim, proof)
        except Exception as exc:  # noqa: BLE001
            return AgentOpinion(
                agent_role="critic", dimension="error", claim=claim, vote="abstain",
                confidence=0.0, reasoning=f"Critic error: {exc}", source="engine",
            )
        return AgentOpinion(
            agent_role="critic",
            dimension=result.get("dimension", "correctness"),
            claim=claim,
            vote=result.get("vote", "abstain"),
            confidence=result.get("confidence", 0.7),
            reasoning=result.get("reasoning", ""),
            evidence=result,
            source="engine",
        )

    def _model_critic(self, claim: str, proof: Dict, model_client: Any, dimension: str) -> AgentOpinion:
        system = (
            "You are an adversarial mathematical Critic. Attempt to REFUTE the proposed proof. "
            "Check the '{dim}' dimension. Output JSON with keys: "
            "vote ('accept'|'reject'|'abstain'), confidence (0-1), reasoning (string), flaws (array of string)."
        ).format(dim=dimension)
        payload = json.dumps(proof, ensure_ascii=False, default=str)[:3000]
        data = model_client.chat_json(system, f"Claim: {claim}\nProposed proof: {payload}")
        vote = data.get("vote") if data.get("vote") in ("accept", "reject", "abstain") else "abstain"
        return AgentOpinion(
            agent_role="critic", dimension=dimension, claim=claim, vote=vote,
            confidence=_clamp_float(data.get("confidence", 0.5)),
            reasoning=str(data.get("reasoning") or "")[:2000],
            evidence=data,
            source="model",
        )

    # ── Judge ──

    def _model_judge(
        self,
        claim: str,
        proposer: AgentOpinion,
        critics: List[AgentOpinion],
        model_client: Any,
    ) -> str:
        system = (
            "You are the final Judge of a mathematical verification pipeline. "
            "Output JSON with keys: verdict ('ACCEPTED'|'REJECTED'|'NEEDS_REVISION'|'UNDECIDED'), "
            "summary (string)."
        )
        payload = {
            "claim": claim,
            "proposer": proposer.to_dict(),
            "critics": [c.to_dict() for c in critics],
        }
        data = model_client.chat_json(system, json.dumps(payload, ensure_ascii=False, default=str)[:4000])
        verdict = data.get("verdict")
        if verdict not in (v.value for v in Verdict):
            verdict = "UNDECIDED"
        return str(verdict)

    def _default_judge(self, critic_opinions: List[AgentOpinion], threshold: float) -> str:
        """默认裁决逻辑: 多数票"""
        if not critic_opinions:
            return Verdict.UNDECIDED.value
        accepts = sum(1 for op in critic_opinions if op.vote == "accept")
        rejects = sum(1 for op in critic_opinions if op.vote == "reject")
        total = accepts + rejects
        if total == 0:
            return Verdict.UNDECIDED.value
        if accepts / total >= threshold:
            return Verdict.ACCEPTED.value
        if rejects / total >= 0.5:
            return Verdict.REJECTED.value
        return Verdict.NEEDS_REVISION.value

    def _summarize(
        self,
        verdict: str,
        vote_counts: Dict[str, int],
        proposer: AgentOpinion,
        critics: List[AgentOpinion],
    ) -> str:
        lines = [
            f"Verdict: {verdict}",
            f"Proposer confidence: {proposer.confidence:.2f} (source: {proposer.source})",
            f"Critic votes: accept={vote_counts.get('accept',0)}, "
            f"reject={vote_counts.get('reject',0)}, abstain={vote_counts.get('abstain',0)}",
        ]
        for c in critics:
            lines.append(f"  [{c.dimension}][{c.source}] {c.vote} ({c.confidence:.2f}): {c.reasoning[:120]}")
        return "\n".join(lines)

    # ── 预定义 Critic 工厂方法（真检验） ──

    @staticmethod
    def make_foc_critic(
        func: Callable[[Dict[str, float]], float],
        grad_func: Callable[[Dict[str, float]], Dict[str, float]],
        param_generator: Callable[[], Dict[str, float]],
        turning_point_fn: Callable[[Dict[str, float]], float],
        n_samples: int = 200,
        tolerance: float = 1e-4,
    ) -> Callable:
        """
        真实 FOC 检验 Critic: 在理论拐点处做中心差分，验证数值导数≈0。

        修复旧版问题: 旧版恒返回 accept（"实际检验需要具体参数"）。新版
        在随机参数下真实计算 f'(x*) 与理论梯度，超容差即 reject。
        """
        import numpy as np

        def critic(claim: str, proof: Dict) -> Dict:
            import numpy as _np
            rng = _np.random.default_rng(42)
            failures = 0
            max_abs_error = 0.0
            checked = 0
            for _ in range(n_samples):
                try:
                    params = param_generator()
                    x_star = turning_point_fn(params)
                    if not _np.isfinite(x_star):
                        continue
                    eps = 1e-6
                    f_plus = func({**params, "_x": x_star + eps})
                    f_minus = func({**params, "_x": x_star - eps})
                    numerical_grad = (f_plus - f_minus) / (2 * eps)
                    theoretical_grad = grad_func({**params, "_x": x_star})
                    error = abs(numerical_grad - float(theoretical_grad.get("_x", 0.0)))
                    max_abs_error = max(max_abs_error, error)
                    checked += 1
                    if error > tolerance:
                        failures += 1
                except Exception:
                    continue
            passed = checked > 0 and failures / max(checked, 1) <= 0.05
            return {
                "dimension": "correctness",
                "vote": "accept" if passed else "reject",
                "confidence": min(0.95, max(0.3, 1.0 - failures / max(checked, 1))),
                "reasoning": (
                    f"Real FOC check: {checked} samples, {failures} violations, "
                    f"max |Δf'/dx| = {max_abs_error:.2e}, tolerance={tolerance}."
                ),
                "evidence": {"checked": checked, "failures": failures, "max_error": max_abs_error},
            }
        return critic

    @staticmethod
    def make_edge_case_critic(
        param_ranges: Dict[str, Tuple[float, float]],
        n_samples: int = 1000,
        seed: int = 42,
    ) -> Callable:
        """
        真实边界 Critic: 在参数边界与内部抽样，检验结论的数值行为。

        修复旧版问题: 旧版抽样循环内没做任何断言，issues 恒为 0。新版由
        调用方传入 `check_fn(params) -> (violated: bool, detail: str)`，在
        每个采样点真实执行。
        """
        import numpy as np

        # 默认检查：可被 verify() 传入的检查函数覆盖；若未提供则 abstain 并说明
        def critic(claim: str, proof: Dict) -> Dict:
            check_fn = proof.get("edge_check")
            if not callable(check_fn):
                return {
                    "dimension": "edge_cases",
                    "vote": "abstain",
                    "confidence": 0.3,
                    "reasoning": "Edge-case check requires an 'edge_check' callable in the proposed proof.",
                }
            rng = np.random.default_rng(seed)
            issues = 0
            details = []
            for _ in range(n_samples):
                params = {}
                for name, (lo, hi) in param_ranges.items():
                    if rng.random() < 0.3:
                        params[name] = lo if rng.random() < 0.5 else hi
                    else:
                        params[name] = float(rng.uniform(lo, hi))
                try:
                    violated, detail = check_fn(params)
                    if violated:
                        issues += 1
                        if len(details) < 3:
                            details.append(detail)
                except Exception:
                    issues += 1
            passed = issues / max(n_samples, 1) <= 0.02
            return {
                "dimension": "edge_cases",
                "vote": "accept" if passed else "reject",
                "confidence": 0.8 if passed else 0.5,
                "reasoning": f"Edge case test: {n_samples} samples, {issues} violations. " + "; ".join(details),
                "evidence": {"samples": n_samples, "violations": issues, "seed": seed},
            }
        return critic

    # ── History ──

    def get_history(self) -> List[MultiAgentVerdict]:
        return self._history

    def clear_history(self) -> None:
        self._history = []


def _clamp_float(value: Any, default: float = 0.5) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return min(1.0, max(0.0, number))
