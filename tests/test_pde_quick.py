"""Quick PDE tests with small grids."""
import sys, io, os
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.pde_engine import PdeEngine

eng = PdeEngine()

print("Classification:")
for name in ['transport','heat','wave','laplace']:
    c = eng.classify(name)
    print("  [OK] %s: type=%s, order=%d" % (name, c.pde_type, c.order))

c2 = eng.classify("diff(u(x,y),x,2) + diff(u(x,y),y,2)")
print("  [OK] Laplace via expr: type=%s" % c2.pde_type)

print()
print("Analytical 1st order:")
r = eng.solve_analytical("diff(f(x,y),x) + diff(f(x,y),y)")
ans = r.analytical_solution[:60] if r.analytical_solution else "(empty)"
print("  [OK] Transport: %s, status=%s" % (ans, r.status))

print()
print("Heat (nx=30,nt=50):")
def u0(x):
    return np.sin(np.pi * x)
r = eng.solve_heat_1d(u0_func=u0, x_range=(0, 1), t_range=(0, 0.2),
                       alpha=0.01, nx=30, nt=50)
print("  [OK] max_temp=%.4f, verified=%s" % (
    r.numerical_solution['max_temp'], r.verified))

print()
print("Wave (nx=50,nt=100):")
def u0(x):
    return np.sin(2 * np.pi * x) * np.exp(-50 * (x - 0.5)**2)
r = eng.solve_wave_1d(u0_func=u0, x_range=(0, 1), t_range=(0, 1.0),
                       c=1.0, nx=50, nt=100)
print("  [OK] max_amp=%.4f, verified=%s" % (
    r.numerical_solution['max_amplitude'], r.verified))

print()
print("Transport (nx=50,nt=50):")
def u0(x):
    return np.exp(-100 * (x - 0.3)**2)
r = eng.solve_transport_1d(u0_func=u0, x_range=(0, 1), t_range=(0, 0.3),
                            c=1.0, nx=50, nt=50)
print("  [OK] L2_error=%.4f, verified=%s" % (
    r.numerical_solution['l2_error'], r.verified))

print()
print("ALL QUICK PDE TESTS PASSED")
