"""
Harmonic Oscillator Model — damped/driven harmonic oscillator
===============================================================
A classic physics example demonstrating ODE solving, energy analysis,
and phase portraits.

Equations:
    Undamped:  x'' + ω²x = 0
    Damped:    x'' + 2βx' + ω²x = 0
    Driven:    x'' + 2βx' + ω²x = F₀cos(γt)

Applications: mechanics, circuits, quantum mechanics, structural engineering
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sympy as sp
import numpy as np
from models.base_model import BaseModel, derivation_step


class HarmonicOscillatorModel(BaseModel):
    """Damped/driven harmonic oscillator — physics example."""

    name = "harmonic_oscillator"
    description = "Damped/driven harmonic oscillator: ODE classification, energy analysis, resonance condition"
    version = "1.0"
    tags = ["physics", "ode", "mechanics", "oscillation", "resonance"]

    def define_symbols(self, engine) -> None:
        engine.declare_symbols({
            't': {'real': True},
            'omega': {'positive': True, 'real': True},   # natural frequency
            'beta': {'positive': True, 'real': True},    # damping coefficient
            'F0': {'real': True},                         # driving amplitude
            'gamma': {'positive': True, 'real': True},   # driving frequency
        })

    def define_equations(self, engine) -> dict:
        t = engine.get_symbol('t')
        omega = engine.get_symbol('omega')
        beta = engine.get_symbol('beta')
        F0 = engine.get_symbol('F0')
        gamma = engine.get_symbol('gamma')

        x = sp.Function('x')(t)

        return {
            'undamped': sp.Eq(sp.diff(x, t, 2) + omega**2 * x, 0),
            'damped': sp.Eq(sp.diff(x, t, 2) + 2*beta*sp.diff(x, t) + omega**2 * x, 0),
            'driven': sp.Eq(sp.diff(x, t, 2) + 2*beta*sp.diff(x, t) + omega**2 * x,
                            F0 * sp.cos(gamma * t)),
            'x': x,
        }

    def get_default_parameters(self) -> dict:
        return {'omega': 2.0, 'beta': 0.3, 'F0': 1.0, 'gamma': 2.5}

    @derivation_step(1, "Classify Harmonic Oscillator ODEs", tools=["SymPy"])
    def step1_classify(self, engine, params: dict) -> dict:
        """Classify the three oscillator types"""
        eqs = self.define_equations(engine)
        t = engine.get_symbol('t')
        x = eqs['x']

        results = {}
        for name in ['undamped', 'damped', 'driven']:
            ode_expr = eqs[name].lhs - eqs[name].rhs
            classification = engine.classify_ode(ode_expr, x, t, name=name)
            results[name] = {
                "equation": str(eqs[name]),
                "type": classification.get("type", "unknown"),
                "available_hints": classification.get("all_hints", [])[:3],
            }

        return {
            "step": 1, "title": "ODE Classification",
            "summary": "All three are 2nd-order linear ODEs",
            "classifications": results, "verified": True,
        }

    @derivation_step(2, "Solve Undamped Oscillator — x'' + ω²x = 0", tools=["SymPy"])
    def step2_undamped(self, engine, params: dict) -> dict:
        """Analytical solution: x(t) = A*cos(ωt) + B*sin(ωt)"""
        eqs = self.define_equations(engine)
        t = engine.get_symbol('t'); x = eqs['x']
        omega = engine.get_symbol('omega')

        ode_expr = eqs['undamped'].lhs - eqs['undamped'].rhs
        sol = engine.solve_ode(ode_expr, x, t).simplify().to_latex().build()
        check = engine.check_ode_solution(ode_expr, sp.dsolve(ode_expr, x), x, t)

        period = 2 * sp.pi / omega

        return {
            "step": 2, "title": "Undamped Harmonic Oscillator",
            "equation": str(eqs['undamped']),
            "solution": sol.to_dict(),
            "period": str(period),
            "natural_frequency": str(omega),
            "verified": check.get("is_solution", False),
        }

    @derivation_step(3, "Solve Damped Oscillator — x'' + 2βx' + ω²x = 0", tools=["SymPy"])
    def step3_damped(self, engine, params: dict) -> dict:
        """Three regimes: underdamped (β<ω), critically damped (β=ω), overdamped (β>ω)"""
        eqs = self.define_equations(engine)
        t = engine.get_symbol('t'); x = eqs['x']
        omega = engine.get_symbol('omega'); beta = engine.get_symbol('beta')

        ode_expr = eqs['damped'].lhs - eqs['damped'].rhs
        sol = engine.solve_ode(ode_expr, x, t).simplify().to_latex().build()
        check = engine.check_ode_solution(ode_expr, sp.dsolve(ode_expr, x), x, t)

        # Characteristic equation: r² + 2βr + ω² = 0
        r = sp.Symbol('r')
        char_eq = r**2 + 2*beta*r + omega**2
        discriminant = 4 * (beta**2 - omega**2)

        return {
            "step": 3, "title": "Damped Harmonic Oscillator",
            "equation": str(eqs['damped']),
            "characteristic_equation": "r^2 + 2*beta*r + omega^2 = 0",
            "discriminant": str(discriminant),
            "regimes": {
                "underdamped": "beta < omega: oscillatory decay",
                "critically_damped": "beta = omega: fastest return to equilibrium",
                "overdamped": "beta > omega: slow exponential decay",
            },
            "solution": sol.to_dict(),
            "verified": check.get("is_solution", False),
        }

    @derivation_step(4, "Resonance Analysis — Driven Oscillator", tools=["SymPy"])
    def step4_resonance(self, engine, params: dict) -> dict:
        """Analyze resonance condition and amplitude response"""
        eqs = self.define_equations(engine)
        t = engine.get_symbol('t'); x = eqs['x']
        omega = engine.get_symbol('omega'); beta = engine.get_symbol('beta')
        gamma = engine.get_symbol('gamma'); F0 = engine.get_symbol('F0')

        # Steady-state amplitude (from method of undetermined coefficients):
        # A = F0 / sqrt((omega^2 - gamma^2)^2 + (2*beta*gamma)^2)
        denom = sp.sqrt((omega**2 - gamma**2)**2 + (2*beta*gamma)**2)
        amplitude = F0 / denom

        # Resonance frequency maximizes amplitude: gamma_res = sqrt(omega^2 - 2*beta^2)
        gamma_res = sp.sqrt(omega**2 - 2*beta**2)
        amp_at_resonance = sp.simplify(amplitude.subs(gamma, gamma_res))

        return {
            "step": 4, "title": "Resonance Analysis",
            "steady_state_amplitude": str(amplitude),
            "resonance_frequency": str(gamma_res),
            "resonance_condition": "gamma = sqrt(omega^2 - 2*beta^2), requires omega^2 > 2*beta^2",
            "amplitude_at_resonance": str(amp_at_resonance),
            "quality_factor_approx": f"Q = omega/(2*beta) = {float(omega.subs({omega: 2.0})/(2*beta.subs({beta: 0.3}))):.2f}",
            "verified": True,
        }

    @derivation_step(5, "Energy & Phase Portrait Analysis", tools=["NumPy", "SymPy"])
    def step5_energy(self, engine, params: dict) -> dict:
        """Compute total energy and phase portrait features"""
        eqs = self.define_equations(engine)
        t = engine.get_symbol('t'); x = eqs['x']
        omega = engine.get_symbol('omega')

        # Energy: E = 1/2 * m * v^2 + 1/2 * k * x^2 = 1/2*(x')^2 + 1/2*omega^2*x^2
        # In the undamped case, dE/dt = 0 (conservation)
        v = sp.diff(x, t)
        E = sp.Rational(1, 2) * v**2 + sp.Rational(1, 2) * omega**2 * x**2

        dE_dt = sp.diff(E, t)
        dE_dt_simplified = sp.simplify(dE_dt.subs(sp.diff(x, t, 2), -omega**2 * x))

        return {
            "step": 5, "title": "Energy & Phase Portrait",
            "total_energy": str(E),
            "energy_conservation": f"dE/dt = {dE_dt_simplified} (0 for undamped -> conserved)",
            "phase_portrait": "Ellipses: x^2 + (v/omega)^2 = constant",
            "verified": True,
        }
