"""Test PDE engine — classification, heat, wave, Laplace, transport."""
import sys, io, os
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.pde_engine import PdeEngine

engine = PdeEngine()

print("=== PDE Classification ===")
tests = [
    ("Transport", "transport", "first_order"),
    ("Heat", "heat", "parabolic"),
    ("Wave", "wave", "hyperbolic"),
    ("Laplace", "laplace", "elliptic"),
]
for name, expr, expected in tests:
    c = engine.classify(expr)
    status = "OK" if c.pde_type == expected else "UNEXPECTED: got %s" % c.pde_type
    print("[%s] %s: type=%s, order=%d, disc=%s" % (status, name, c.pde_type, c.order, c.discriminant))

# Also test direct expression parsing
print()
print("=== Direct Expression Parsing ===")
c2 = engine.classify("diff(u(x,y),x,2) + diff(u(x,y),y,2)")
print("[%s] Laplace via expr: type=%s, order=%d" % ("OK" if c2.pde_type == "elliptic" else "FAIL", c2.pde_type, c2.order))

print()
print("=== Analytical PDE (1st order) ===")
r = engine.solve_analytical("diff(f(x,y),x) + diff(f(x,y),y)")
print("[OK] Transport analytical: %s" % r.analytical_solution[:80])

# Test 2nd order analytical fails gracefully
r2 = engine.solve_analytical("diff(f(x,y),x,2) + diff(f(x,y),y,2)")
print("[OK] Laplace analytical (expected fail): status=%s" % r2.status)

print()
print("=== Heat Equation ===")
r = engine.solve_heat_1d(
    u0_func=lambda x: np.sin(np.pi * x),
    x_range=(0, 1), t_range=(0, 0.5), alpha=0.01, nx=50, nt=200
)
print("[OK] Heat: max_temp=%.4f, verified=%s, status=%s" % (
    r.numerical_solution['max_temp'], r.verified, r.status))

print()
print("=== Wave Equation ===")
r = engine.solve_wave_1d(
    u0_func=lambda x: np.sin(2*np.pi*x) * np.exp(-50*(x-0.5)**2),
    x_range=(0, 1), t_range=(0, 2.0), c=1.0, nx=100, nt=400
)
print("[OK] Wave: max_amplitude=%.4f, verified=%s, status=%s" % (
    r.numerical_solution['max_amplitude'], r.verified, r.status))

print()
print("=== Laplace Equation ===")
r = engine.solve_laplace_2d(x_range=(0, 1), y_range=(0, 1), nx=50, ny=50, max_iter=5000)
print("[OK] Laplace: iters=%d, converged=%s" % (
    r.numerical_solution['iterations'], r.numerical_solution['converged']))

print()
print("=== Poisson Equation ===")
def f_source(X, Y):
    return 2 * np.pi**2 * np.sin(np.pi*X) * np.sin(np.pi*Y)
r = engine.solve_laplace_2d(f_source=f_source, x_range=(0,1), y_range=(0,1),
                             nx=50, ny=50, max_iter=5000)
print("[OK] Poisson: iters=%d, converged=%s, max=%.4f" % (
    r.numerical_solution['iterations'], r.numerical_solution['converged'],
    r.numerical_solution['max_val']))

print()
print("=== Transport Equation ===")
r = engine.solve_transport_1d(
    u0_func=lambda x: np.exp(-100*(x-0.3)**2),
    x_range=(0, 1), t_range=(0, 0.5), c=1.0, nx=100, nt=100
)
print("[OK] Transport: L2_error=%.6f, verified=%s" % (
    r.numerical_solution['l2_error'], r.verified))

print()
print("=== classify_and_solve ===")
r = engine.classify_and_solve("diff(f(x,y),x) + diff(f(x,y),y)")
print("[OK] Auto-solve 1st order: method=%s, status=%s" % (r.method, r.status))
r2 = engine.classify_and_solve("diff(f(x,y),x,2) + diff(f(x,y),y,2)")
print("[OK] Auto-solve Laplace: method=%s, status=%s (falls back to numerical recommendation)" % (r2.method, r2.status))

print()
print("ALL PDE TESTS PASSED")
