"""Test the harness: orchestrator, skills, routing, prompts."""
import sys, io, os
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.orchestrator import MathAgentOrchestrator
from harness.skill_registry import SkillRegistry
from harness.tool_routing import ToolRouter

print("=== Test 1: Plan ODE request ===")
o = MathAgentOrchestrator()
plan = o.plan("solve y'' + 3y' + 2y = 0")
print("Domain:", plan.domain.value)
print("Skill:", plan.matched_skill)
print("Tasks:", len(plan.tasks))
for t in plan.tasks:
    print("  -", t.role.value, ":", len(t.tool_sequence), "tools")

print()
print("=== Test 2: Plan Limit request ===")
plan2 = o.plan("find lim sin(x)/x as x approaches 0")
print("Domain:", plan2.domain.value)
print("Skill:", plan2.matched_skill)

print()
print("=== Test 3: Plan Verification request ===")
plan3 = o.plan("verify XE* = -alpha1/(2*alpha2)")
print("Domain:", plan3.domain.value)
print("Skill:", plan3.matched_skill)

print()
print("=== Test 4: List all skills ===")
skills = SkillRegistry()
all_skills = skills.list_all()
print("Total skills:", len(all_skills))
for s in all_skills:
    print("  - %s [%s]: %s" % (s['name'], s['category'], s['description'][:50]))

print()
print("=== Test 5: Tool routing ===")
router = ToolRouter()
for query in ["solve y''+y=0", "heat equation u_t = u_xx", "lim sin(x)/x", "integrate x*exp(x)"]:
    domain = router.detect_domain(query)
    tools = router.route(domain, query)
    print("  '%s' -> %s -> %s" % (query, domain.value, [t['tool'] for t in tools]))

print()
print("=== Test 6: Prompts ===")
orchestrator_prompt = o.get_system_prompt()
print("Orchestrator prompt: %d chars" % len(orchestrator_prompt))
exec_prompt = o.get_execution_prompt(plan)
print("Execution prompt: %d chars" % len(exec_prompt))
deriv_prompt = o.get_system_prompt(
    __import__('harness.orchestrator', fromlist=['AgentRole']).AgentRole.DERIVATION
)
print("Derivation prompt: %d chars" % len(deriv_prompt))

print()
print("ALL HARNESS TESTS PASSED")
