"""
SkillRegistry — Skill discovery and execution engine.
======================================================
A Skill is a named capability that bundles:
    - trigger: when to activate this skill
    - prompt: what the LLM should do
    - tool_sequence: which MCP tools to call, in what order
    - output_schema: expected format of the result
    - verification: how to check the result is correct

Skills are defined as YAML files in harness/skills/.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class SkillCategory(Enum):
    DERIVATION = "derivation"       # symbolic math derivation
    VERIFICATION = "verification"   # checking correctness
    SOLVING = "solving"             # solving equations (ODE/PDE/etc.)
    ANALYSIS = "analysis"           # limits, series, integrals
    DOCUMENTATION = "documentation" # report generation
    FULL_PIPELINE = "full_pipeline" # end-to-end workflow


@dataclass
class ToolCallStep:
    """A single step in a skill's tool sequence."""
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    on_failure: str = "skip"  # skip | retry | abort
    required: bool = True


@dataclass
class Skill:
    """A named, reusable mathematical capability."""
    name: str
    category: SkillCategory
    description: str
    trigger_keywords: List[str] = field(default_factory=list)
    system_prompt_extension: str = ""  # appended to base prompt
    tool_sequence: List[ToolCallStep] = field(default_factory=list)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    verification_rules: List[Dict[str, Any]] = field(default_factory=list)
    fallback_skill: Optional[str] = None  # if this fails, try this

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "trigger_keywords": self.trigger_keywords,
            "tool_sequence": [
                {"tool": s.tool_name, "args": s.arguments, "desc": s.description,
                 "on_failure": s.on_failure, "required": s.required}
                for s in self.tool_sequence
            ],
            "output_schema": self.output_schema,
            "verification_rules": self.verification_rules,
        }


class SkillRegistry:
    """
    Registry of all available mathematical skills.

    Skills are defined in YAML and auto-discovered.
    """

    def __init__(self, skills_dir: Optional[str] = None):
        self._skills: Dict[str, Skill] = {}
        self._by_category: Dict[SkillCategory, List[str]] = {c: [] for c in SkillCategory}
        self._by_keyword: Dict[str, str] = {}  # keyword -> skill name

        if skills_dir is None:
            skills_dir = os.path.join(os.path.dirname(__file__), "skills")
        self._skills_dir = skills_dir

        self._register_builtin_skills()
        if os.path.isdir(skills_dir):
            self._load_yaml_skills(skills_dir)

    # ── Builtin Skills ──

    def _register_builtin_skills(self):
        """Register all builtin skills programmatically."""

        # Skill 1: ODE Derivation
        self.register(Skill(
            name="derive_ode",
            category=SkillCategory.DERIVATION,
            description="Classify and solve ordinary differential equations",
            trigger_keywords=["ode", "differential equation", "solve ode", "ordinary",
                            "y'", "y''", "dy/dx", "d2y/dx2", "微分方程"],
            system_prompt_extension=(
                "You are solving an ODE. Follow these steps:\n"
                "1. Classify the ODE type first (math_*_step1_classify)\n"
                "2. Choose the appropriate solution method based on classification\n"
                "3. Solve using the matched method\n"
                "4. Verify the solution with checkodesol\n"
                "5. Report the general solution and verification status"
            ),
            tool_sequence=[
                ToolCallStep("math_ode_solver_step1_classify", {}, "Classify ODE type"),
                ToolCallStep("math_ode_solver_step2_solve_separable", {}, "Solve separable ODEs", required=False),
                ToolCallStep("math_ode_solver_step3_solve_linear", {}, "Solve linear 1st order ODEs", required=False),
                ToolCallStep("math_ode_solver_step4_solve_2nd_order", {}, "Solve 2nd order ODEs", required=False),
                ToolCallStep("math_ode_solver_step5_solve_system", {}, "Solve ODE systems", required=False),
                ToolCallStep("math_ode_solver_verify", {}, "Verify all solutions"),
            ],
            output_schema={"solution": "string", "classification": "dict", "verified": "boolean"},
            fallback_skill="derive_analysis",
        ))

        # Skill 2: PDE Solving
        self.register(Skill(
            name="solve_pde",
            category=SkillCategory.SOLVING,
            description="Classify and solve partial differential equations (analytical + numerical)",
            trigger_keywords=["pde", "partial differential", "heat equation", "wave equation",
                            "laplace", "poisson", "transport", "偏微分"],
            system_prompt_extension=(
                "You are solving a PDE. Follow this decision tree:\n"
                "1. Classify: is it elliptic, parabolic, or hyperbolic?\n"
                "   - Use math_pde_solver_step1_classify\n"
                "2. If 1st order: use analytical pdsolve\n"
                "3. If 2nd order:\n"
                "   - Parabolic (Heat): numerical finite difference\n"
                "   - Hyperbolic (Wave): 3-point explicit scheme\n"
                "   - Elliptic (Laplace/Poisson): Jacobi iteration\n"
                "4. Always check CFL/stability conditions\n"
                "5. Compare with analytical solution when available"
            ),
            tool_sequence=[
                ToolCallStep("math_pde_solver_step1_classify", {}, "Classify PDE type"),
                ToolCallStep("math_pde_solver_step2_first_order", {}, "1st order analytical solve", required=False),
                ToolCallStep("math_pde_solver_step3_heat", {}, "Heat equation", required=False),
                ToolCallStep("math_pde_solver_step4_wave", {}, "Wave equation", required=False),
                ToolCallStep("math_pde_solver_step5_laplace", {}, "Laplace equation", required=False),
                ToolCallStep("math_pde_solver_step6_poisson", {}, "Poisson equation", required=False),
            ],
            output_schema={"classification": "dict", "solution": "dict", "method": "string", "verified": "boolean"},
            fallback_skill="derive_analysis",
        ))

        # Skill 3: Analysis Problems
        self.register(Skill(
            name="solve_analysis",
            category=SkillCategory.ANALYSIS,
            description="Solve analysis problems: limits, series convergence, integrals, continuity",
            trigger_keywords=["limit", "series", "integral", "convergence", "continuity",
                            "asymptotic", "gamma", "beta", "zeta", "极限", "级数",
                            "积分", "收敛", "连续"],
            system_prompt_extension=(
                "You are solving an analysis problem.\n"
                "For LIMITS: evaluate directly, try L'Hopital if 0/0 or inf/inf, verify numerically.\n"
                "For SERIES: test divergence (lim a_n != 0), then ratio/root test, compare with p-series.\n"
                "For INTEGRALS: try direct integration, then by-parts/substitution if needed, verify by differentiation.\n"
                "For CONTINUITY: check singularities, compute left/right limits at suspicious points.\n"
                "Always verify results with a second method when possible."
            ),
            tool_sequence=[
                ToolCallStep("math_analysis_problems_step1_limits", {}, "Evaluate limits"),
                ToolCallStep("math_analysis_problems_step2_series", {}, "Test series convergence"),
                ToolCallStep("math_analysis_problems_step3_integration", {}, "Compute integrals"),
                ToolCallStep("math_analysis_problems_step4_continuity", {}, "Check continuity"),
                ToolCallStep("math_analysis_problems_step5_special_functions", {}, "Special functions", required=False),
                ToolCallStep("math_analysis_problems_step6_asymptotic", {}, "Asymptotic analysis", required=False),
            ],
            output_schema={"limits": "dict", "series": "dict", "integrals": "dict", "verified": "boolean"},
            fallback_skill=None,
        ))

        # Skill 4: Full Verification Pipeline
        self.register(Skill(
            name="verify_mathematical",
            category=SkillCategory.VERIFICATION,
            description="Run the full 5-level verification pipeline on any mathematical claim",
            trigger_keywords=["verify", "check", "validate", "prove", "验证", "检验", "证明"],
            system_prompt_extension=(
                "You are verifying a mathematical claim. Run the 5-level pipeline:\n"
                "Level 1: SymPy symbolic verification (identity checks, FOC/SOC)\n"
                "Level 2: Monte Carlo numerical verification (random parameter testing)\n"
                "Level 3: SageMath CAS cross-verification (independent engine)\n"
                "Level 4: Lean 4 formal proof template generation\n"
                "Level 5: QED multi-agent adversarial verification\n"
                "If any level fails, report the failure with diagnostic information.\n"
                "A claim is ACCEPTED only if ALL available levels pass."
            ),
            tool_sequence=[
                ToolCallStep("math_verify_symbolic", {}, "SymPy symbolic check"),
                ToolCallStep("math_verify_monte_carlo", {"n_samples": 10000}, "Monte Carlo numerical check"),
                ToolCallStep("math_sage_verify", {}, "SageMath cross-verification", required=False),
                ToolCallStep("math_formal_proof", {"theorem": "quadratic_minimum"}, "Lean 4 proof template", required=False),
                ToolCallStep("math_multi_agent_verify", {}, "QED multi-agent adversarial check"),
            ],
            output_schema={"verdict": "string", "levels": "dict", "pass_rate": "number"},
            fallback_skill=None,
        ))

        # Skill 5: End-to-End Full Pipeline
        self.register(Skill(
            name="full_mathematical_pipeline",
            category=SkillCategory.FULL_PIPELINE,
            description="Run the complete end-to-end pipeline: derive -> verify -> document",
            trigger_keywords=["full pipeline", "complete derivation", "end to end",
                            "完整推导", "全流程"],
            system_prompt_extension=(
                "You are running the complete mathematical pipeline.\n"
                "Phase 1: DERIVATION — run all derivation steps for the selected model.\n"
                "Phase 2: VERIFICATION — run the 5-level verification pipeline.\n"
                "Phase 3: DOCUMENTATION — generate a comprehensive report with all results.\n"
                "At each phase, check results before proceeding. If a phase fails, report and stop."
            ),
            tool_sequence=[
                ToolCallStep("math_unified_verify_pipeline", {"levels": ["symbolic", "monte_carlo", "sagemath", "formal_proof", "multi_agent"]}, "Run unified verification"),
                ToolCallStep("math_generate_appendix", {"format": "md"}, "Generate documentation"),
            ],
            output_schema={"derivation": "dict", "verification": "dict", "documentation": "string"},
            fallback_skill="verify_mathematical",
        ))

        # Skill 6: Harmonic Oscillator (Physics)
        self.register(Skill(
            name="analyze_oscillator",
            category=SkillCategory.DERIVATION,
            description="Analyze damped/driven harmonic oscillator: energy, resonance, phase portrait",
            trigger_keywords=["oscillator", "harmonic", "resonance", "damping",
                            "谐振", "阻尼", "共振"],
            system_prompt_extension=(
                "You are analyzing a harmonic oscillator system.\n"
                "1. Classify: undamped, damped (under/critical/over), or driven?\n"
                "2. Solve the ODE analytically.\n"
                "3. Analyze energy conservation (undamped) or dissipation (damped).\n"
                "4. Find resonance condition for driven oscillator.\n"
                "5. Characterize the phase portrait."
            ),
            tool_sequence=[
                ToolCallStep("math_harmonic_oscillator_step1_classify", {}, "Classify oscillator type"),
                ToolCallStep("math_harmonic_oscillator_step2_undamped", {}, "Solve undamped"),
                ToolCallStep("math_harmonic_oscillator_step3_damped", {}, "Solve damped"),
                ToolCallStep("math_harmonic_oscillator_step4_resonance", {}, "Resonance analysis"),
                ToolCallStep("math_harmonic_oscillator_step5_energy", {}, "Energy analysis"),
            ],
            output_schema={"classification": "dict", "solution": "dict", "resonance": "dict", "verified": "boolean"},
            fallback_skill="derive_ode",
        ))

    # ── YAML Skill Loading ──

    def _load_yaml_skills(self, skills_dir: str):
        """Load additional skills from YAML files."""
        for yaml_file in Path(skills_dir).glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                skill = self._parse_yaml_skill(data)
                self.register(skill)
            except Exception as e:
                print(f"  [WARN] Failed to load skill {yaml_file}: {e}")

    def _parse_yaml_skill(self, data: dict) -> Skill:
        """Parse a YAML skill definition into a Skill object."""
        steps = []
        for s in data.get("tool_sequence", []):
            steps.append(ToolCallStep(
                tool_name=s["tool"],
                arguments=s.get("args", {}),
                description=s.get("desc", ""),
                on_failure=s.get("on_failure", "skip"),
                required=s.get("required", True),
            ))
        return Skill(
            name=data["name"],
            category=SkillCategory(data.get("category", "derivation")),
            description=data.get("description", ""),
            trigger_keywords=data.get("trigger_keywords", []),
            system_prompt_extension=data.get("system_prompt_extension", ""),
            tool_sequence=steps,
            output_schema=data.get("output_schema", {}),
            verification_rules=data.get("verification_rules", []),
            fallback_skill=data.get("fallback_skill"),
        )

    # ── Registration & Lookup ──

    def register(self, skill: Skill):
        self._skills[skill.name] = skill
        self._by_category[skill.category].append(skill.name)
        for kw in skill.trigger_keywords:
            self._by_keyword[kw.lower()] = skill.name

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def find_by_keyword(self, user_input: str) -> Optional[Skill]:
        """Find the best-matching skill for a user's input."""
        user_lower = user_input.lower()
        # Exact match first
        for kw, skill_name in self._by_keyword.items():
            if kw in user_lower:
                return self._skills[skill_name]
        # Partial match
        best_match, best_len = None, 0
        for kw, skill_name in self._by_keyword.items():
            if len(kw) > best_len and any(word in user_lower for word in kw.split()):
                best_match = self._skills[skill_name]
                best_len = len(kw)
        return best_match

    def list_all(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._skills.values()]

    def list_by_category(self, category: SkillCategory) -> List[str]:
        return self._by_category.get(category, [])
