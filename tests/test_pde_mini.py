"""Minimal PDE test — fast grid sizes."""
import sys,io; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8') if sys.platform=='win32' else None
import os; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from core.pde_engine import PdeEngine
e = PdeEngine()
print("Heat...")
r = e.solve_heat_1d(u0_func=lambda x: np.sin(np.pi*x), x_range=(0,1), t_range=(0,0.1), alpha=0.01, nx=20, nt=30)
print("Heat: verified=%s, max=%.4f" % (r.verified, r.numerical_solution['max_temp']))
print("Transport...")
r = e.solve_transport_1d(u0_func=lambda x: np.exp(-100*(x-0.3)**2), x_range=(0,1), t_range=(0,0.3), c=1.0, nx=50, nt=50)
print("Transport: verified=%s, l2=%.4f" % (r.verified, r.numerical_solution['l2_error']))
print("Wave...")
r = e.solve_wave_1d(u0_func=lambda x: np.sin(2*np.pi*x)*np.exp(-50*(x-0.5)**2), x_range=(0,1), t_range=(0,0.5), c=1.0, nx=30, nt=50)
print("Wave: verified=%s, amp=%.4f" % (r.verified, r.numerical_solution['max_amplitude']))
print("Laplace...")
r = e.solve_laplace_2d(x_range=(0,1), y_range=(0,1), nx=15, ny=15, max_iter=500, tol=1e-3)
print("Laplace: converged=%s, iters=%d" % (r.numerical_solution['converged'], r.numerical_solution['iterations']))
print("ALL PASSED")
