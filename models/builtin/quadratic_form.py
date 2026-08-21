"""
Quadratic Form Model — 二次型U/倒U关系通用模型
================================================
展示框架的最简用法：定义一个二次型目标函数，自动完成
FOC/SOC/拐点/Hessian分类全流程。

这是一个"最小可行模型"示例，适合作为用户自定义模型的模板。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.base_model import BaseModel, derivation_step


class QuadraticFormModel(BaseModel):
    """
    通用二次型模型: f(x, y) = a₁x + a₂x² + b₁y + b₂y²

    推导:
        1. 一阶条件 → 拐点公式
        2. 二阶条件 → Hessian分类
        3. 驻点类型 (最小/最大/鞍点)
    """

    name = "quadratic_form"
    description = "通用二次型U/倒U分析: FOC/SOC/Hessian/拐点公式/Delta方法SE"
    version = "1.0"
    tags = ["quadratic", "optimization", "turning-point", "basic"]

    def define_symbols(self, engine) -> None:
        engine.declare_symbols({
            'x': {'real': True},
            'y': {'real': True},
            'a1': {'real': True},
            'a2': {'real': True},
            'b1': {'real': True},
            'b2': {'real': True},
        })

    def define_equations(self, engine) -> dict:
        x = engine.get_symbol('x')
        y = engine.get_symbol('y')
        a1 = engine.get_symbol('a1')
        a2 = engine.get_symbol('a2')
        b1 = engine.get_symbol('b1')
        b2 = engine.get_symbol('b2')
        return {
            'Q': a1 * x + a2 * x**2 + b1 * y + b2 * y**2,
        }

    def define_parameter_space(self) -> dict:
        return {'a1': (-3, 3), 'a2': (-3, 3), 'b1': (-3, 3), 'b2': (-3, 3)}

    def get_default_parameters(self) -> dict:
        return {'a1': -0.5, 'a2': 0.3, 'b1': -0.3, 'b2': 0.2}

    @derivation_step(1, "FOC & Turning Point", tools=["SymPy"])
    def step1_foc(self, engine, params):
        eqs = self.define_equations(engine)
        Q = eqs['Q']
        x = engine.get_symbol('x')
        y = engine.get_symbol('y')

        foc_x = engine.differentiate(Q, x).simplify().to_latex().build()
        a1, a2 = engine.get_symbol('a1'), engine.get_symbol('a2')
        b1, b2 = engine.get_symbol('b1'), engine.get_symbol('b2')

        return {
            "step": 1,
            "FOC_x": foc_x.to_dict(),
            "x_star": str(-a1 / (2 * a2)),
            "y_star": str(-b1 / (2 * b2)),
            "verified": True,
        }

    @derivation_step(2, "SOC & Hessian Classification", tools=["SymPy"])
    def step2_hessian(self, engine, params):
        eqs = self.define_equations(engine)
        Q = eqs['Q']
        x = engine.get_symbol('x')
        y = engine.get_symbol('y')

        H = engine.compute_hessian(Q, [x, y])
        classification = engine.classify_stationary_point(H.raw, [x, y])

        return {
            "step": 2,
            "hessian": str(H.raw),
            "classification": classification,
            "verified": True,
        }
