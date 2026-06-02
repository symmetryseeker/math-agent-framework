"""
Math Agent Framework — Harness
===============================
Multi-agent orchestration system for mathematical derivation and verification.

Architecture:
    User Request
        │
        ▼
    Orchestrator Agent (plans approach, dispatches to specialists)
        │
        ├──▶ Derivation Agent   (symbolic computation)
        ├──▶ Verification Agent (multi-level verification)
        └──▶ Documentation Agent (report generation)

Each agent has:
    - A system prompt defining its role and behavior
    - A set of skills it can execute
    - Tool routing rules for selecting the right engine

Skills bundle: prompt + tool sequence + expected output schema + verification rules.
"""

from .orchestrator import MathAgentOrchestrator
from .skill_registry import SkillRegistry
from .tool_routing import ToolRouter

__all__ = ["MathAgentOrchestrator", "SkillRegistry", "ToolRouter"]
