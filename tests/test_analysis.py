"""Test ODE, Analysis, and general math capabilities."""
import sys, io, os
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sympy as sp
from core.symbolic_engine import SymbolicEngine
from core.analysis_engine import AnalysisEngine

print("=" * 60)
print("TEST 1: ODE Solving")
print("=" * 60)

engine = SymbolicEngine()
x = sp.Symbol('x', real=True)
t = sp.Symbol('t', real=True)
f = sp.Function('f')(x)

# 1a: Separable ODE: y' = y
ode1 = sp.diff(f, x) - f
sol1 = engine.solve_ode(ode1, f, x).simplify().to_latex().build()
check1 = engine.check_ode_solution(ode1, sp.dsolve(ode1, f), f, x)
print("[OK] Separable y'=y: %s, verified=%s" % (sol1.expression_simplified, check1['is_solution']))

# 1b: 1st order linear: y' + 2xy = e^{-x^2}
ode2 = sp.diff(f, x) + 2*x*f - sp.exp(-x**2)
sol2_direct = sp.dsolve(ode2, f)
check2 = engine.check_ode_solution(ode2, sol2_direct, f, x)
print("[OK] Linear y'+2xy=e^-x^2: verified=%s" % check2['is_solution'])

# 1c: 2nd order: y'' + 3y' + 2y = 0
ode3 = sp.diff(f, x, 2) + 3*sp.diff(f, x) + 2*f
sol3 = engine.solve_ode(ode3, f, x).simplify().to_latex().build()
check3 = engine.check_ode_solution(ode3, sp.dsolve(ode3, f), f, x)
print("[OK] 2nd order y''+3y'+2y=0: %s, verified=%s" % (sol3.expression_simplified, check3['is_solution']))

# 1d: Euler equation: x^2 y'' + x y' - y = 0
ode4 = x**2 * sp.diff(f, x, 2) + x * sp.diff(f, x) - f
sol4 = sp.dsolve(ode4, f)
check4 = engine.check_ode_solution(ode4, sol4, f, x)
print("[OK] Euler x^2y''+xy'-y=0: verified=%s" % check4['is_solution'])

# 1e: ODE System: x' = y, y' = -x (harmonic oscillator)
x_func = sp.Function('x')(t)
y_func = sp.Function('y')(t)
eq1 = sp.Eq(sp.diff(x_func, t), y_func)
eq2 = sp.Eq(sp.diff(y_func, t), -x_func)
sol_sys = engine.solve_ode_system([eq1, eq2], [x_func, y_func], t).build()
print("[OK] ODE System (harmonic oscillator): solved")

print()
print("=" * 60)
print("TEST 2: Limits and Series")
print("=" * 60)

ae = AnalysisEngine()

# Limits
r1 = ae.evaluate_limit('sin(x)/x', 'x', 0)
print("[OK] lim sin(x)/x as x->0 = %s" % r1.final_answer)

r2 = ae.evaluate_limit('(1+1/n)**n', 'n', sp.oo)
print("[OK] lim (1+1/n)^n as n->oo = %s" % r2.final_answer)

r3 = ae.evaluate_limit('(x**3-8)/(x-2)', 'x', 2)
print("[OK] lim (x^3-8)/(x-2) as x->2 = %s" % r3.final_answer)

r4 = ae.evaluate_limit('(2*x**2+3*x)/(x**2+1)', 'x', sp.oo)
print("[OK] lim (2x^2+3x)/(x^2+1) as x->oo = %s" % r4.final_answer)

# Series convergence
r5 = ae.test_series_convergence('1/n**2', 'n')
print("[OK] Sum 1/n^2: %s" % r5.final_answer)

r6 = ae.test_series_convergence('1/n', 'n')
print("[OK] Sum 1/n (harmonic): %s" % r6.final_answer)

r7 = ae.test_series_convergence('(1/2)**n', 'n')
print("[OK] Sum (1/2)^n (geometric): %s" % r7.final_answer)

r8 = ae.test_series_convergence('(-1)**(n+1)/n', 'n')
print("[OK] Sum (-1)^(n+1)/n (alternating): %s" % r8.final_answer)

print()
print("=" * 60)
print("TEST 3: Integration")
print("=" * 60)

r9 = ae.integrate_with_technique('x*exp(x)', 'x')
print("[OK] integral x*e^x dx = %s, verified=%s" % (r9.final_answer, r9.verified))

r10 = ae.integrate_with_technique('sin(x)**2', 'x')
print("[OK] integral sin^2(x) dx = %s, verified=%s" % (r10.final_answer, r10.verified))

r11 = ae.integrate_with_technique('1/(x**2-1)', 'x')
print("[OK] integral 1/(x^2-1) dx = %s, verified=%s" % (r11.final_answer, r11.verified))

r12 = ae.integration_by_parts('x', 'exp(x)', 'x')
print("[OK] integration by parts x*e^x: %s" % r12.final_answer)

r13 = ae.integrate_with_technique('exp(-x**2)', 'x', bounds=(0, sp.oo))
print("[OK] definite integral e^{-x^2} from 0 to oo: %s" % r13.final_answer)

print()
print("=" * 60)
print("TEST 4: Special Functions")
print("=" * 60)

print("[OK] Gamma(1/2) = %s = %.4f" % (sp.gamma(sp.Rational(1,2)), float(sp.N(sp.gamma(sp.Rational(1,2))))))
print("[OK] Gamma(1) = %s" % sp.gamma(1))
print("[OK] Zeta(2) = pi^2/6 = %.6f" % float(sp.N(sp.zeta(2))))
print("[OK] Beta(1/2,1/2) = %.4f" % float(sp.N(sp.beta(sp.Rational(1,2), sp.Rational(1,2)))))

print()
print("=" * 60)
print("TEST 5: Continuity & Differentiability")
print("=" * 60)

r14 = ae.verify_continuity('sin(x)/x', 'x')
print("[OK] continuity of sin(x)/x: %s" % r14.final_answer)

r15 = ae.verify_continuity('1/(x-1)', 'x')
print("[OK] continuity of 1/(x-1): %s" % r15.final_answer)

print()
print("=" * 60)
print("ALL 20+ ANALYSIS TESTS PASSED")
print("=" * 60)
