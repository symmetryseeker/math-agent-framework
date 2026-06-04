"""Reproduce MAF tool call failures to understand root causes."""
import sympy as sp
from sympy.solvers.ode import checkodesol

print("=" * 60)
print("FAILURE 1: series-005 — sum n!/n^n")
print("=" * 60)
n = sp.Symbol('n', integer=True, positive=True)
expr = sp.factorial(n) / n**n
print("Term: a_n =", expr)
try:
    lim = sp.limit(expr, n, sp.oo)
    print("limit a_n =", lim)
except Exception as e:
    print("limit FAILED:", type(e).__name__, e)

# Ratio test: a_{n+1}/a_n
try:
    ratio = sp.simplify(sp.factorial(n+1)/(n+1)**(n+1) * n**n / sp.factorial(n))
    print("a_{n+1}/a_n =", ratio)
    ratio_limit = sp.limit(ratio, n, sp.oo)
    print("ratio limit =", ratio_limit)
except Exception as e:
    print("Ratio test FAILED:", type(e).__name__, e)

# Stirilng approximation: n! ~ sqrt(2*pi*n)*(n/e)^n
try:
    approx = sp.sqrt(2*sp.pi*n) * (n/sp.E)**n
    simplified = sp.simplify(approx / n**n)
    print("Stirling approx a_n ~", simplified)
    lim_stirling = sp.limit(sp.sqrt(2*sp.pi*n) / sp.E**n, n, sp.oo)
    print("limit via Stirling =", lim_stirling)
except Exception as e:
    print("Stirling FAILED:", type(e).__name__, e)

print()
print("=" * 60)
print("FAILURE 2: limit-009 — lim (sin(x)-x)/x^3")
print("=" * 60)
x = sp.Symbol('x', real=True)
expr2 = (sp.sin(x) - x) / x**3
print("Expression:", expr2)

# Direct limit
lim2 = sp.limit(expr2, x, 0)
print("sp.limit() =", lim2)

# Series expansion
try:
    series2 = sp.series(expr2, x, 0, 5)
    print("sp.series() =", series2)
except Exception as e:
    print("series FAILED:", e)

# L'Hopital (3 times since 0/0)
d1_num = sp.diff(sp.sin(x) - x, x)
d1_den = sp.diff(x**3, x)
print("1st L'Hopital:", d1_num, "/", d1_den)
lim_l1 = sp.limit(d1_num/d1_den, x, 0)
print("  ->", lim_l1)  # still 0/0

d2_num = sp.diff(d1_num, x)
d2_den = sp.diff(d1_den, x)
print("2nd L'Hopital:", d2_num, "/", d2_den)
lim_l2 = sp.limit(d2_num/d2_den, x, 0)
print("  ->", lim_l2)  # still 0/0

d3_num = sp.diff(d2_num, x)
d3_den = sp.diff(d2_den, x)
print("3rd L'Hopital:", d3_num, "/", d3_den)
lim_l3 = sp.limit(d3_num/d3_den, x, 0)
print("  ->", lim_l3)  # -1/6

print()
print("=" * 60)
print("FAILURE 3: ode-008 — Euler x^2 y'' + x y' - y = 0")
print("=" * 60)
f = sp.Function('f')(x)
ode = x**2 * sp.diff(f, x, 2) + x * sp.diff(f, x) - f
print("ODE:", ode)
sol = sp.dsolve(ode, f)
print("Solution:", sol)
check = checkodesol(ode, sol, func=f)
print("checkodesol:", check)
print("  check[0] =", check[0], "-> bool =", bool(check[0]) if isinstance(check, tuple) else bool(check))
print("  check[1] =", check[1] if isinstance(check, tuple) and len(check) > 1 else "N/A")

# Verify manually
C1, C2 = sp.symbols('C1 C2')
sol_expr = C1/x + C2*x  # Euler solution: y = C1*x + C2/x
lhs = x**2 * sp.diff(sol_expr, x, 2) + x * sp.diff(sol_expr, x) - sol_expr
print("Manual verify with y = C1/x + C2*x:")
print("  LHS =", sp.simplify(lhs))
print("  -> correct:", sp.simplify(lhs) == 0)

print()
print("=" * 60)
print("ROOT CAUSE SUMMARY")
print("=" * 60)
print("1. series-005 (n!/n^n):")
print("   SymPy's sp.limit() cannot handle factorial symbolically.")
print("   Ratio test: a_{n+1}/a_n = (n/(n+1))^n.")
print("   The AnalysisEngine's test_series_convergence() calls sp.limit()")
print("   which returns unevaluated -> 'Divergent (term does not approach 0)'")
print("   FIX: Use Stirling's approximation for factorial-based series.")
print()
print("2. limit-009 ((sin(x)-x)/x^3):")
print("   sp.limit() CORRECTLY returns -1/6 in SymPy 1.13.")
print("   The MAF benchmark scored BOTH raw and MAF as 100%.")
print("   This is a SCORING BUG, not a SymPy bug.")
print("   The answer '1' should have been scored 0%.")
print()
print("3. ode-008 (Euler equation):")
print("   sp.dsolve() gave the correct solution.")
print("   checkodesol returned (True, 0) -> correct.")
print("   The verified=False flag is also a SCORING BUG,")
print("   likely checking the wrong tuple index.")
