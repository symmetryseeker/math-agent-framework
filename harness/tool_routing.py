"""
ToolRouter — Decision-tree tool selection logic.
=================================================
Instead of relying on the LLM to guess which tool to call, the ToolRouter
provides explicit decision rules for common mathematical scenarios.

This makes the agent's behavior predictable and controllable.
"""

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class MathDomain(Enum):
    """Recognized mathematical domains."""
    ODE = "ode"
    PDE = "pde"
    LIMIT = "limit"
    SERIES = "series"
    INTEGRAL = "integral"
    CONTINUITY = "continuity"
    OPTIMIZATION = "optimization"
    DYNAMIC_SYSTEM = "dynamic_system"
    ALGEBRA = "algebra"
    UNKNOWN = "unknown"


# ── Domain Detection Rules ──

DOMAIN_PATTERNS = {
    MathDomain.ODE: [
        "y'", "y''", "dy/dx", "d2y/dx2", "ode", "differential equation",
        "ordinary", "微分方程", "常微分",
    ],
    MathDomain.PDE: [
        "pde", "partial", "heat equation", "wave equation", "laplace",
        "poisson", "transport", "u_t", "u_xx", "u_tt", "偏微分",
    ],
    MathDomain.LIMIT: [
        "limit", "lim", "approaches", "tends to", "asymptote", "极限", "趋于",
    ],
    MathDomain.SERIES: [
        "series", "convergence", "divergence", "sum", "ratio test",
        "taylor", "maclaurin", "power series", "级数", "收敛", "发散",
    ],
    MathDomain.INTEGRAL: [
        "integral", "integrate", "antiderivative", "area under",
        "definite integral", "积分", "不定积分", "定积分",
    ],
    MathDomain.CONTINUITY: [
        "continuous", "continuity", "differentiable", "singularity",
        "discontinuity", "连续", "可微", "间断",
    ],
    MathDomain.OPTIMIZATION: [
        "optimize", "maximize", "minimize", "extremum", "turning point",
        "stationary", "FOC", "SOC", "Kuhn", "优化", "极值", "拐点",
    ],
    MathDomain.DYNAMIC_SYSTEM: [
        "dynamic", "riccati", "hamiltonian", "steady state",
        "equilibrium", "phase portrait", "动态", "稳态", "均衡",
    ],
}


class ToolRouter:
    """
    Decision-tree tool selector for mathematical problems.

    Usage:
        router = ToolRouter()
        domain = router.detect_domain("solve y'' + y = 0")
        tools = router.route(domain, detail="2nd_order_linear")
        # -> [{"tool": "math_ode_solver_step1_classify", ...}, ...]
    """

    def detect_domain(self, user_input: str) -> MathDomain:
        """Detect which mathematical domain a user query belongs to."""
        user_lower = user_input.lower()
        scores = {}
        for domain, patterns in DOMAIN_PATTERNS.items():
            score = sum(1 for p in patterns if p.lower() in user_lower)
            if score > 0:
                scores[domain] = score
        if not scores:
            return MathDomain.UNKNOWN
        return max(scores, key=scores.get)

    def detect_ode_subtype(self, user_input: str) -> str:
        """Detect ODE subtype for method selection."""
        lower = user_input.lower()
        if "system" in lower or "方程组" in lower:
            return "system"
        if "2nd" in lower or "second" in lower or "y''" in lower or "二阶" in lower:
            return "2nd_order"
        if "bernoulli" in lower:
            return "bernoulli"
        if "exact" in lower:
            return "exact"
        if "homogeneous" in lower or "齐次" in lower:
            return "homogeneous"
        if "linear" in lower or "线性" in lower:
            return "linear_1st"
        if "separable" in lower or "可分离" in lower:
            return "separable"
        return "general_1st"

    def detect_pde_subtype(self, user_input: str) -> str:
        """Detect PDE subtype."""
        lower = user_input.lower()
        if "heat" in lower or "热" in lower or "diffusion" in lower:
            return "heat"
        if "wave" in lower or "波" in lower:
            return "wave"
        if "laplace" in lower or "拉普拉斯" in lower:
            return "laplace"
        if "poisson" in lower or "泊松" in lower:
            return "poisson"
        if "transport" in lower or "advection" in lower or "对流" in lower:
            return "transport"
        return "general_pde"

    def route(self, domain: MathDomain, user_input: str = "", detail: str = "") -> List[Dict[str, Any]]:
        """
        Return the optimal tool call sequence for a given mathematical domain.

        Returns a list of tool call descriptors:
            [{"tool": "tool_name", "args": {...}, "required": bool}, ...]
        """
        if domain == MathDomain.ODE:
            return self._route_ode(user_input)
        elif domain == MathDomain.PDE:
            return self._route_pde(user_input)
        elif domain == MathDomain.LIMIT:
            return self._route_single("math_analyze_limit", user_input)
        elif domain == MathDomain.SERIES:
            return self._route_single("math_analyze_series", user_input)
        elif domain == MathDomain.INTEGRAL:
            return self._route_single("math_analyze_integral", user_input)
        elif domain == MathDomain.CONTINUITY:
            return self._route_single("math_analyze_continuity", user_input)
        elif domain == MathDomain.OPTIMIZATION:
            return self._route_optimization()
        elif domain == MathDomain.DYNAMIC_SYSTEM:
            return [
                {"tool": "math_quantecon_optimize", "args": {"operation": "riccati"}, "required": True},
                {"tool": "math_verify_monte_carlo", "args": {"n_samples": 5000}, "required": True},
            ]
        else:
            return self._route_full_pipeline()

    def _route_ode(self, user_input: str) -> List[Dict[str, Any]]:
        subtype = self.detect_ode_subtype(user_input)
        base = [{"tool": "math_ode_solver_step1_classify", "args": {}, "required": True}]

        method_map = {
            "separable": "math_ode_solver_step2_solve_separable",
            "linear_1st": "math_ode_solver_step3_solve_linear",
            "bernoulli": "math_ode_solver_step3_solve_linear",
            "exact": "math_ode_solver_step2_solve_separable",
            "homogeneous": "math_ode_solver_step2_solve_separable",
            "2nd_order": "math_ode_solver_step4_solve_2nd_order",
            "system": "math_ode_solver_step5_solve_system",
            "general_1st": "math_ode_solver_step2_solve_separable",
        }

        tool_name = method_map.get(subtype, "math_ode_solver_step2_solve_separable")
        base.append({"tool": tool_name, "args": {}, "required": True})
        base.append({"tool": "math_ode_solver_verify", "args": {}, "required": True})
        return base

    def _route_pde(self, user_input: str) -> List[Dict[str, Any]]:
        subtype = self.detect_pde_subtype(user_input)
        base = [{"tool": "math_pde_solver_step1_classify", "args": {}, "required": True}]

        method_map = {
            "heat": "math_pde_solver_step3_heat",
            "wave": "math_pde_solver_step4_wave",
            "laplace": "math_pde_solver_step5_laplace",
            "poisson": "math_pde_solver_step6_poisson",
            "transport": "math_pde_solver_step2_first_order",
            "general_pde": "math_pde_solver_step2_first_order",
        }

        tool_name = method_map.get(subtype, "math_pde_solver_step2_first_order")
        base.append({"tool": tool_name, "args": {}, "required": True})

        # Always verify numerical solutions
        if subtype in ("heat", "wave", "laplace", "poisson"):
            base.append({"tool": "math_verify_monte_carlo", "args": {"n_samples": 1000}, "required": False})
        return base

    def _route_single(self, tool: str, user_input: str) -> List[Dict[str, Any]]:
        return [{"tool": tool, "args": {"expression": user_input}, "required": True}]

    def _route_optimization(self) -> List[Dict[str, Any]]:
        return [
            {"tool": "math_quadratic_form_step1_foc", "args": {}, "required": True},
            {"tool": "math_quadratic_form_step2_hessian", "args": {}, "required": True},
            {"tool": "math_verify_symbolic", "args": {}, "required": True},
            {"tool": "math_verify_monte_carlo", "args": {"n_samples": 10000}, "required": True},
        ]

    def _route_full_pipeline(self) -> List[Dict[str, Any]]:
        return [
            {"tool": "math_unified_verify_pipeline", "args": {"levels": ["symbolic", "monte_carlo", "sagemath", "formal_proof", "multi_agent"]}, "required": True},
            {"tool": "math_generate_appendix", "args": {"format": "md"}, "required": False},
        ]
