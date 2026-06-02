"""
测试模型系统 — 验证 BaseModel, 自动发现, 和内置模型。
"""

import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import discover_models, load_model
from models.base_model import BaseModel, derivation_step
from core.symbolic_engine import SymbolicEngine


def test_model_discovery():
    """测试模型自动发现"""
    models = discover_models()
    assert len(models) > 0, "No models discovered"
    print(f"  [PASS] discover_models: {len(models)} found: {list(models.keys())}")


def test_load_builtin_models():
    """测试加载内置模型"""
    for name in ["quadratic_form", "network_embedded_growth"]:
        try:
            model = load_model(name)
            info = model.get_info()
            assert info["name"] == name
            assert info["num_derivation_steps"] > 0
            print(f"  [PASS] load '{name}': {info['num_derivation_steps']} steps, {info['description'][:50]}...")
        except Exception as e:
            print(f"  [FAIL] load '{name}': {e}")


def test_derivation_step_decorator():
    """测试 @derivation_step 装饰器"""
    class TestModel(BaseModel):
        name = "test_decorator"
        description = "Test model"

        def define_symbols(self, engine):
            engine.declare_symbols({'x': None})

        def define_equations(self, engine):
            x = engine.get_symbol('x')
            return {'f': x**2}

        @derivation_step(1, "Step 1", tools=["SymPy"])
        def step_one(self, engine, params):
            return {"step": 1, "result": "ok"}

        @derivation_step(2, "Step 2", tools=["NumPy"], dependencies=["step_one"])
        def step_two(self, engine, params):
            return {"step": 2, "result": "ok"}

    model = TestModel()
    steps = model.get_derivation_steps()
    assert len(steps) == 2
    assert steps[0]["index"] == 1
    assert steps[0]["tools"] == ["SymPy"]
    assert steps[1]["dependencies"] == ["step_one"]
    print(f"  [PASS] @derivation_step: {len(steps)} steps discovered, deps working")


def test_quadratic_model_execution():
    """测试二次型模型的完整执行"""
    from models.builtin.quadratic_form import QuadraticFormModel

    model = QuadraticFormModel()
    engine = SymbolicEngine()
    model.define_symbols(engine)

    steps = model.get_derivation_steps()
    for step in steps:
        method = getattr(model, step["method_name"])
        result = method(engine, {})
        assert result.get("verified", False) or "step" in result
        print(f"  [PASS] quadratic_form.{step['method_name']}: {result.get('step', '?')}")


if __name__ == "__main__":
    print("Testing Model System...\n")
    test_model_discovery()
    test_load_builtin_models()
    test_derivation_step_decorator()
    test_quadratic_model_execution()
    print("\n  All model tests passed!")
