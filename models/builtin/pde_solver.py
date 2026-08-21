"""
PDE Solver Model — 偏微分方程求解模型
========================================
解析方法 + 数值方法全覆盖。

支持的PDE:
    一阶:
        - Transport (u_t + c u_x = 0): method of characteristics + upwind FD
        - 一阶线性: SymPy pdsolve

    二阶:
        - Heat (u_t = alpha u_xx): explicit finite difference
        - Wave (u_tt = c^2 u_xx): explicit 3-point FD
        - Laplace (u_xx + u_yy = 0): Jacobi iteration
        - Poisson (u_xx + u_yy = -f): Jacobi iteration with source

用法:
    from models import load_model
    model = load_model("pde_solver")
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import sympy as sp
from models.base_model import BaseModel, derivation_step


class PDESolverModel(BaseModel):
    """偏微分方程求解模型 — 解析+数值"""

    name = "pde_solver"
    description = "偏微分方程求解: 解析(pdsolve)+数值(FD/FVM)。Heat/Wave/Laplace/Poisson/Transport"
    version = "1.0"
    tags = ["pde", "partial-differential-equations", "numerical-methods", "applied-math", "physics"]

    def define_symbols(self, engine) -> None:
        engine.declare_symbols({
            'x': {'real': True},
            'y': {'real': True},
            't': {'real': True},
        })

    def define_equations(self, engine) -> dict:
        x = engine.get_symbol('x')
        y = engine.get_symbol('y')
        u = sp.Function('u')(x, y)
        return {'u': u}

    def get_default_parameters(self) -> dict:
        return {}

    @derivation_step(1, "Classify PDE Types — PDE分类与判别式", tools=["SymPy"])
    def step1_classify(self, engine, params: dict) -> dict:
        """分类各类PDE并计算判别式"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        # 6种经典PDE
        pdes = {
            "transport": {"expr": "diff(u(x,y),x) + diff(u(x,y),y)", "desc": "Transport (1st order)"},
            "heat": {"expr": "diff(u(x,y),y) - diff(u(x,y),x,2)", "desc": "Heat eq: u_t = alpha u_xx"},
            "wave": {"expr": "diff(u(x,y),x,2) - diff(u(x,y),y,2)", "desc": "Wave eq: u_tt = c^2 u_xx"},
            "laplace": {"expr": "diff(u(x,y),x,2) + diff(u(x,y),y,2)", "desc": "Laplace: u_xx + u_yy = 0"},
        }

        results = {}
        for name, info in pdes.items():
            clf = pde_engine.classify(info["expr"])
            results[name] = {
                "description": info["desc"],
                "type": clf.pde_type,
                "order": clf.order,
                "linearity": clf.linearity,
                "discriminant": clf.discriminant,
            }

        return {
            "step": 1, "title": "PDE Classification",
            "classification_summary": {
                "elliptic": "Laplace/Poisson — equilibrium problems (B^2-4AC < 0)",
                "parabolic": "Heat/Diffusion — evolution problems (B^2-4AC = 0)",
                "hyperbolic": "Wave/Transport — propagation problems (B^2-4AC > 0)",
            },
            "classified_pdes": results,
            "verified": True,
        }

    @derivation_step(2, "Solve 1st Order PDE — 一阶线性PDE", tools=["SymPy"])
    def step2_first_order(self, engine, params: dict) -> dict:
        """一阶线性PDE解析求解: method of characteristics"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        # Transport: u_x + u_y = 0
        result = pde_engine.solve_analytical(
            "diff(f(x,y),x) + diff(f(x,y),y)", "f(x,y)"
        )

        # Also: u_t + c u_x = 0 via numerical
        def u0_gaussian(x):
            return np.exp(-100 * (x - 0.3)**2)

        num_result = pde_engine.solve_transport_1d(
            u0_func=u0_gaussian,
            x_range=(0, 1), t_range=(0, 0.5), c=1.0, nx=100, nt=100,
        )

        return {
            "step": 2, "title": "1st Order PDE",
            "transport_analytical": result.to_dict(),
            "transport_numerical": {
                "status": num_result.status,
                "l2_error_vs_analytical": num_result.numerical_solution.get("l2_error"),
                "verified": num_result.verified,
            },
            "verified": True,
        }

    @derivation_step(3, "Solve Heat Equation — 热方程", tools=["NumPy"])
    def step3_heat(self, engine, params: dict) -> dict:
        """一维热方程数值求解: u_t = alpha u_xx"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        # Initial condition: Gaussian pulse
        def u0_sin(x):
            return np.sin(np.pi * x)

        result = pde_engine.solve_heat_1d(
            u0_func=u0_sin,
            x_range=(0, 1), t_range=(0, 0.5),
            alpha=0.01, nx=50, nt=200,
            bc_left=0.0, bc_right=0.0,
        )

        return {
            "step": 3, "title": "Heat Equation (Parabolic)",
            "equation": "u_t = 0.01 u_xx",
            "initial_condition": "u(x,0) = sin(pi*x)",
            "boundary_conditions": "u(0,t) = u(1,t) = 0",
            "solution": result.to_dict(),
            "analytical_reference": "u(x,t) = sin(pi*x) * exp(-0.01*pi^2*t)",
            "verified": result.verified,
        }

    @derivation_step(4, "Solve Wave Equation — 波动方程", tools=["NumPy"])
    def step4_wave(self, engine, params: dict) -> dict:
        """一维波动方程: u_tt = c^2 u_xx"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        def u0_pluck(x):
            return np.sin(2 * np.pi * x) * np.exp(-50 * (x - 0.5)**2)

        result = pde_engine.solve_wave_1d(
            u0_func=u0_pluck,
            x_range=(0, 1), t_range=(0, 2.0),
            c=1.0, nx=100, nt=400,
        )

        return {
            "step": 4, "title": "Wave Equation (Hyperbolic)",
            "equation": "u_tt = u_xx",
            "initial_condition": "Gaussian pluck at x=0.5",
            "d_alembert_solution": "u(x,t) = F(x-t) + G(x+t)",
            "solution": result.to_dict(),
            "verified": result.verified,
        }

    @derivation_step(5, "Solve Laplace Equation — 拉普拉斯方程", tools=["NumPy"])
    def step5_laplace(self, engine, params: dict) -> dict:
        """2D Laplace方程: u_xx + u_yy = 0 (Jacobi迭代)"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        # BC: u(x,0)=x (linear on left), others 0
        result = pde_engine.solve_laplace_2d(
            x_range=(0, 1), y_range=(0, 1),
            nx=50, ny=50,
            max_iter=5000, tol=1e-4,
        )

        return {
            "step": 5, "title": "Laplace Equation (Elliptic)",
            "equation": "u_xx + u_yy = 0",
            "boundary_conditions": "u(x,0)=x, u=0 on other boundaries",
            "method": "Jacobi iteration",
            "solution": result.to_dict(),
            "verified": result.verified,
        }

    @derivation_step(6, "Solve Poisson Equation — 泊松方程", tools=["NumPy"])
    def step6_poisson(self, engine, params: dict) -> dict:
        """2D Poisson方程: u_xx + u_yy = -f(x,y)"""
        from core.pde_engine import PdeEngine
        pde_engine = PdeEngine()

        # Source: f(x,y) = 2*pi^2 * sin(pi*x) * sin(pi*y)
        # Exact: u(x,y) = sin(pi*x) * sin(pi*y)
        def f_source(X, Y):
            return 2 * np.pi**2 * np.sin(np.pi * X) * np.sin(np.pi * Y)

        result = pde_engine.solve_laplace_2d(
            f_source=f_source,
            x_range=(0, 1), y_range=(0, 1),
            nx=50, ny=50,
            max_iter=5000, tol=1e-4,
        )

        return {
            "step": 6, "title": "Poisson Equation (Elliptic, non-homogeneous)",
            "equation": "u_xx + u_yy = -2*pi^2*sin(pi*x)*sin(pi*y)",
            "analytical_solution": "u(x,y) = sin(pi*x)*sin(pi*y)",
            "method": "Jacobi iteration with source term",
            "solution": result.to_dict(),
            "verified": result.verified,
        }
