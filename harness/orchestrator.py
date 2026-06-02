"""
MathAgentOrchestrator — Central multi-agent orchestration engine.
==================================================================
Coordinates Derivation, Verification, and Documentation agents
to solve mathematical problems end-to-end.

Architecture:
    User Request
        │
        ▼
    Orchestrator.detect_domain()  ──▶  ToolRouter
        │
        ▼
    Orchestrator.match_skill()    ──▶  SkillRegistry
        │
        ▼
    Orchestrator.dispatch()
        │
        ├──▶ DerivationAgent.solve()
        ├──▶ VerificationAgent.verify()
        └──▶ DocumentationAgent.report()
        │
        ▼
    Orchestrator.synthesize()  ──▶  Final Response
"""

import json
import os
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .tool_routing import ToolRouter, MathDomain
from .skill_registry import SkillRegistry, Skill, SkillCategory


class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    DERIVATION = "derivation"
    VERIFICATION = "verification"
    DOCUMENTATION = "documentation"


@dataclass
class AgentTask:
    """A task dispatched to a specialist agent."""
    role: AgentRole
    skill: Optional[Skill]
    tool_sequence: List[Dict[str, Any]]
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class OrchestratorResult:
    """Complete result from the orchestrator."""
    user_request: str
    domain: MathDomain
    matched_skill: Optional[str]
    tasks: List[AgentTask] = field(default_factory=list)
    final_verdict: str = "PENDING"
    synthesis: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "user_request": self.user_request,
            "domain": self.domain.value,
            "matched_skill": self.matched_skill,
            "tasks": [
                {"role": t.role.value, "status": t.status,
                 "result": t.result, "error": t.error}
                for t in self.tasks
            ],
            "final_verdict": self.final_verdict,
            "synthesis": self.synthesis,
            "timestamp": self.timestamp,
        }


class MathAgentOrchestrator:
    """
    Central orchestrator for mathematical problem-solving.

    Usage:
        orchestrator = MathAgentOrchestrator()

        # Analyze what the user wants
        plan = orchestrator.plan("solve y'' + 3y' + 2y = 0")

        # Execute the plan (requires MCP tool call capability)
        result = orchestrator.execute(plan, tool_caller=my_mcp_call_function)

        # Or get the prompt for an LLM to follow
        prompt = orchestrator.get_system_prompt()
    """

    def __init__(self):
        self.router = ToolRouter()
        self.skills = SkillRegistry()
        self._prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")

    # ── Planning ──

    def plan(self, user_request: str) -> OrchestratorResult:
        """
        Analyze a user request and produce an execution plan.

        This is a pure analysis step — no tools are called yet.
        It returns an OrchestratorResult with the planned task sequence.
        """
        # Step 1: Detect domain
        domain = self.router.detect_domain(user_request)

        # Step 2: Match skill
        skill = self.skills.find_by_keyword(user_request)

        # Step 3: Get tool sequence from router
        if skill:
            tool_sequence = [
                {"tool": s.tool_name, "args": s.arguments, "required": s.required}
                for s in skill.tool_sequence
            ]
            system_prompt_ext = skill.system_prompt_extension
        else:
            tool_sequence = self.router.route(domain, user_request)
            system_prompt_ext = ""

        # Step 4: Create tasks
        tasks = [
            AgentTask(
                role=AgentRole.DERIVATION,
                skill=skill,
                tool_sequence=[t for t in tool_sequence if t.get("required", True)],
                context={"domain": domain.value},
            ),
            AgentTask(
                role=AgentRole.VERIFICATION,
                skill=self.skills.get("verify_mathematical"),
                tool_sequence=self.router.route(MathDomain.UNKNOWN, ""),
                context={"domain": domain.value},
            ),
        ]

        # Add documentation task if skill is a full pipeline
        if skill and skill.category == SkillCategory.FULL_PIPELINE:
            tasks.append(AgentTask(
                role=AgentRole.DOCUMENTATION,
                skill=None,
                tool_sequence=[
                    {"tool": "math_generate_appendix", "args": {"format": "md"}, "required": False},
                ],
            ))

        return OrchestratorResult(
            user_request=user_request,
            domain=domain,
            matched_skill=skill.name if skill else None,
            tasks=tasks,
        )

    # ── System Prompts ──

    def get_system_prompt(self, role: AgentRole = AgentRole.ORCHESTRATOR, skill: Optional[Skill] = None) -> str:
        """Get the system prompt for a given agent role."""
        prompt_file = {
            AgentRole.ORCHESTRATOR: "orchestrator.txt",
            AgentRole.DERIVATION: "derivation.txt",
            AgentRole.VERIFICATION: "verification.txt",
            AgentRole.DOCUMENTATION: "documentation.txt",
        }.get(role, "orchestrator.txt")

        prompt_path = os.path.join(self._prompts_dir, prompt_file)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()
        except FileNotFoundError:
            base_prompt = f"You are the {role.value} agent."

        # Append skill-specific instructions
        if skill and skill.system_prompt_extension:
            base_prompt += "\n\n## Skill-Specific Instructions\n" + skill.system_prompt_extension

        # Append available tools
        base_prompt += "\n\n## Available Skills\n"
        for s in self.skills.list_all():
            base_prompt += f"- {s['name']}: {s['description']}\n"

        return base_prompt

    def get_execution_prompt(self, plan: OrchestratorResult) -> str:
        """
        Generate a prompt that tells the LLM exactly what to do.

        This is the key output — it gives the LLM a concrete, step-by-step
        execution plan rather than leaving tool selection to chance.
        """
        lines = [
            "## Execution Plan",
            f"",
            f"**User Request**: {plan.user_request}",
            f"**Domain**: {plan.domain.value}",
            f"**Matched Skill**: {plan.matched_skill or 'none (using general routing)'}",
            f"",
            "### Tool Call Sequence",
            "",
        ]

        for i, task in enumerate(plan.tasks):
            lines.append(f"#### Phase {i+1}: {task.role.value.upper()}")
            for j, tool in enumerate(task.tool_sequence):
                req = "REQUIRED" if tool.get("required", True) else "OPTIONAL"
                lines.append(f"  {j+1}. [{req}] `{tool['tool']}`")
                if tool.get("args"):
                    lines.append(f"     args: {json.dumps(tool['args'])}")
            lines.append("")

        lines.extend([
            "### Instructions",
            "1. Call each tool in sequence. Check results before proceeding.",
            "2. If a REQUIRED tool fails, report the error and stop.",
            "3. If an OPTIONAL tool fails, skip it and continue.",
            "4. After all phases, synthesize a final answer.",
            "5. Structure your response: Classification → Solution → Verification → Summary.",
        ])

        return "\n".join(lines)

    def get_verification_only_prompt(self, claim: str) -> str:
        """Generate a verification-only execution prompt."""
        return f"""## Verification Task

**Claim to verify**: {claim}

Execute the 5-level verification pipeline:

1. [REQUIRED] `math_verify_symbolic` — symbolic identity check
2. [REQUIRED] `math_verify_monte_carlo` — 10,000 random parameter test
3. [OPTIONAL] `math_sage_verify` — SageMath cross-verification
4. [OPTIONAL] `math_formal_proof` — Lean 4 proof template
5. [REQUIRED] `math_multi_agent_verify` — QED adversarial check

Report the verdict: ACCEPTED / REJECTED / NEEDS_REVIEW.
For each level, report pass rate and any counterexamples found."""

    # ── Execution ──

    async def execute(self, plan: OrchestratorResult, tool_caller: Callable) -> OrchestratorResult:
        """
        Execute a plan by calling MCP tools through the provided tool_caller.

        Args:
            plan: The OrchestratorResult from plan()
            tool_caller: async function(tool_name: str, arguments: dict) -> dict

        Returns:
            Updated OrchestratorResult with task results filled in.
        """
        for task in plan.tasks:
            task.status = "running"
            task_result = {}

            for tool in task.tool_sequence:
                tool_name = tool["tool"]
                is_required = tool.get("required", True)

                try:
                    result = await tool_caller(tool_name, tool.get("args", {}))
                    task_result[tool_name] = result
                except Exception as e:
                    if is_required:
                        task.status = "failed"
                        task.error = f"Required tool {tool_name} failed: {e}"
                        plan.final_verdict = "FAILED"
                        return plan
                    else:
                        task_result[tool_name] = {"error": str(e), "skipped": True}

            task.result = task_result
            task.status = "success"

        plan.final_verdict = "COMPLETED"
        return plan

    # ── Synthesis ──

    def synthesize(self, plan: OrchestratorResult) -> str:
        """Synthesize a human-readable summary from the execution results."""
        lines = [
            f"## Result: {plan.user_request}",
            f"",
            f"**Domain**: {plan.domain.value}",
            f"**Skill**: {plan.matched_skill or 'auto-detected'}",
            f"**Verdict**: {plan.final_verdict}",
            f"",
        ]

        for task in plan.tasks:
            emoji = "✅" if task.status == "success" else "❌" if task.status == "failed" else "⏳"
            lines.append(f"### {emoji} {task.role.value.title()} Agent")
            if task.error:
                lines.append(f"Error: {task.error}")
            if task.result:
                for tool_name, result in task.result.items():
                    if isinstance(result, dict):
                        status = result.get("status", result.get("verified", "?"))
                        lines.append(f"- {tool_name}: {status}")
            lines.append("")

        return "\n".join(lines)
