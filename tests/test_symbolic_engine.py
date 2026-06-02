"""
测试 SymbolicEngine — 验证符号推导引擎的通用性。
"""

import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.symbolic_engine import SymbolicEngine, DerivationResult


def test_declare_symbols():
    """测试符号声明"""
    engine = SymbolicEngine()
    engine.declare_symbols({
        'x': None,
        'alpha': {'positive': True, 'real': True},
    })
    assert 'x' in engine._symbols
    assert 'alpha' in engine._symbols
    print("  [PASS] declare_symbols")


def test_differentiate():
    """测试符号求导"""
    engine = SymbolicEngine()
    engine.declare_symbols({'x': None, 'a': None})
    x = engine.get_symbol('x')
    a = engine.get_symbol('a')

    result = engine.differentiate(a * x**2, x).simplify().build()
    assert '2*a*x' in result.expression_simplified.replace(' ', '')
    print(f"  [PASS] differentiate: f(x)=ax², f'(x)={result.expression_simplified}")


def test_solve_equation():
    """测试方程求解"""
    engine = SymbolicEngine()
    engine.declare_symbols({'x': None, 'a': None, 'b': None})
    x = engine.get_symbol('x')
    a = engine.get_symbol('a')
    b = engine.get_symbol('b')

    # Solve a*x + b = 0 → x = -b/a
    result = engine.solve_equation(a * x + b, x).build()
    assert '-b/a' in str(result.expression_simplified).replace(' ', '')
    print(f"  [PASS] solve: ax+b=0 → x={result.expression_simplified}")


def test_elasticity():
    """测试弹性计算"""
    engine = SymbolicEngine()
    engine.declare_symbols({'x': {'positive': True}, 'gamma': {'positive': True}})
    x = engine.get_symbol('x')
    gamma = engine.get_symbol('gamma')

    # f(x) = x^gamma → elasticity = gamma
    result = engine.compute_elasticity(x**gamma, x).build()
    assert 'gamma' in str(result.expression_simplified)
    print(f"  [PASS] elasticity: f(x)=x^γ → ε={result.expression_simplified}")


def test_hessian():
    """测试 Hessian 矩阵与驻点分类"""
    engine = SymbolicEngine()
    engine.declare_symbols({
        'x': {'real': True}, 'y': {'real': True},
        'a': {'real': True}, 'b': {'real': True},
    })
    x = engine.get_symbol('x')
    y = engine.get_symbol('y')
    a = engine.get_symbol('a')
    b = engine.get_symbol('b')

    f = a * x**2 + b * y**2
    H = engine.compute_hessian(f, [x, y])
    classification = engine.classify_stationary_point(H.raw, [x, y])

    assert 'determinant' in classification
    print(f"  [PASS] hessian: det={classification['determinant']}, classification={classification}")


def test_builder_chain():
    """测试链式调用"""
    engine = SymbolicEngine()
    engine.declare_symbols({'x': None, 'N': {'positive': True}})
    x = engine.get_symbol('x')

    result = (engine.differentiate(x**3, x)
              .simplify()
              .to_latex()
              .with_condition("x > 0", "domain")
              .evaluate({x: 2.0})
              .build())

    assert result.numerical_value is not None
    assert result.numerical_value == 12.0  # 3*2^2 = 12
    print(f"  [PASS] chain: f'(2) = {result.numerical_value}")


def test_history():
    """测试推导历史"""
    engine = SymbolicEngine()
    engine.declare_symbols({'x': None})
    x = engine.get_symbol('x')

    engine.differentiate(x**2, x).simplify().to_latex().build()
    engine.differentiate(x**3, x).simplify().to_latex().build()

    assert len(engine.get_history()) == 2
    print(f"  [PASS] history: {len(engine.get_history())} entries")


if __name__ == "__main__":
    print("Testing SymbolicEngine...\n")
    test_declare_symbols()
    test_differentiate()
    test_solve_equation()
    test_elasticity()
    test_hessian()
    test_builder_chain()
    test_history()
    print("\n  All tests passed!")
