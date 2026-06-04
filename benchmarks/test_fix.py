"""Test AnalysisEngine with the problematic cases before/after fix."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.analysis_engine import AnalysisEngine
import sympy as sp

ae = AnalysisEngine()

print("=" * 60)
print("BEFORE FIX: Test existing AnalysisEngine on buggy cases")
print("=" * 60)

# Case 1: n!/n^n
print("\n--- series-005: n!/n^n ---")
r = ae.test_series_convergence("factorial(n)/n**n", "n")
print("Result:", r.final_answer)
for s in r.steps:
    print("  Step %d [%s]: %s" % (s.step_number, s.operation, s.description[:80]))

# Case 2: limit-009
print("\n--- limit-009: (sin(x)-x)/x^3 ---")
r2 = ae.evaluate_limit("(sin(x)-x)/x**3", "x", 0)
print("Result:", r2.final_answer)
print("Verified:", r2.verified)
print("Numerical:", r2.verification.get("numerical", {}))

# Case 3: continuity
print("\n--- continuity sin(x)/x ---")
r3 = ae.verify_continuity("sin(x)/x", "x")
print("Result:", r3.final_answer)

# Case 4: integration by parts
print("\n--- integration x*exp(x) ---")
r4 = ae.integrate_with_technique("x*exp(x)", "x")
print("Result:", r4.final_answer)
print("Verified:", r4.verified)
print("Diff check:", r4.verification.get("differentiation_check", {}))
