"""
BaseModel — 数学模型基类
=========================
所有数学模型必须继承此类，实现抽象方法。

设计原则:
    - 用户只需定义"模型是什么"，框架负责"如何推导和验证"
    - 一个模型 = 符号声明 + 方程定义 + 推导步骤 + 验证规则
    - 支持模型参数化（可用于敏感性分析）

用法:
    class MyModel(BaseModel):
        name = "my_model"
        description = "我的数学模型"

        def define_symbols(self, engine):
            engine.declare_symbols({
                'x': None, 'y': None, 'a': {'positive': True, 'real': True}
            })

        def define_equations(self, engine):
            x, y, a = [engine.get_symbol(s) for s in ['x', 'y', 'a']]
            return {'main_eq': a * x**2 + y**2}

        @derivation_step(1, "Find FOC", tools=["SymPy"])
        def derive_foc(self, engine, params):
            eqs = self.define_equations(engine)
            result = engine.differentiate(eqs['main_eq'], engine.get_symbol('x'))
            return result.simplify().to_latex().build().to_dict()
"""

import json
import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field


def derivation_step(
    index: int,
    description: str,
    tools: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
):
    """
    装饰器：标记一个方法为推导步骤。

    用法:
        @derivation_step(1, "CES Production Function", tools=["SymPy"])
        def step1_ces(self, engine, params):
            ...
    """
    def decorator(func):
        func._derivation_step = {
            "index": index,
            "description": description,
            "tools": tools or [],
            "dependencies": dependencies or [],
        }
        return func
    return decorator


class BaseModel(ABC):
    """
    数学模型基类。

    子类必须实现:
        - define_symbols(engine)
        - define_equations(engine)

    子类可选重写:
        - define_pipeline() — 自定义流水线
        - define_verification() — 自定义验证
        - define_parameter_space() — 参数空间定义
    """

    # ── 类级别元数据 ──
    name: str = "base_model"
    description: str = "Base mathematical model"
    version: str = "1.0"
    author: str = ""
    tags: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._derivation_results: Dict[str, Any] = {}

    # ── Abstract Methods (必须实现) ──

    @abstractmethod
    def define_symbols(self, engine) -> None:
        """
        定义模型使用的所有数学符号。

        Args:
            engine: SymbolicEngine 实例
        """
        ...

    @abstractmethod
    def define_equations(self, engine) -> Dict[str, Any]:
        """
        定义模型的核心方程。

        Returns:
            {
                'main_equation': expr,
                'cost_function': expr,
                'constraints': [expr, ...],
                ...
            }
        """
        ...

    # ── Optional Methods (可选重写) ──

    def define_parameter_space(self) -> Dict[str, Tuple[float, float]]:
        """
        定义参数空间（用于数值模拟和蒙特卡洛）。

        Returns:
            {'param_name': (min, max), ...}
        """
        return {}

    def define_verification_rules(self) -> List[Dict[str, Any]]:
        """
        定义验证规则。

        Returns:
            [
                {'type': 'foc', 'name': '...', 'params': {...}},
                {'type': 'soc', 'name': '...', 'params': {...}},
                ...
            ]
        """
        return []

    def get_default_parameters(self) -> Dict[str, float]:
        """获取默认参数值（用于数值示例）"""
        return {}

    # ── Derivation Step Discovery ──

    def get_derivation_steps(self) -> List[Dict[str, Any]]:
        """
        自动发现所有被 @derivation_step 装饰的方法。

        Returns:
            按 index 排序的步骤列表
        """
        steps = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "_derivation_step"):
                meta = method._derivation_step.copy()
                meta["method_name"] = name
                meta["method"] = method
                steps.append(meta)

        # Also check unbound methods on the class
        for name, method in inspect.getmembers(type(self), predicate=inspect.isfunction):
            if hasattr(method, "_derivation_step"):
                # Check we haven't already added it
                if not any(s["method_name"] == name for s in steps):
                    meta = method._derivation_step.copy()
                    meta["method_name"] = name
                    meta["method"] = lambda eng, params, m=method: m(self, eng, params)
                    steps.append(meta)

        steps.sort(key=lambda s: s["index"])
        return steps

    # ── Model Info ──

    def get_info(self) -> Dict[str, Any]:
        """获取模型元信息"""
        steps = self.get_derivation_steps()
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "num_derivation_steps": len(steps),
            "steps": [
                {
                    "index": s["index"],
                    "description": s["description"],
                    "tools": s["tools"],
                    "dependencies": s["dependencies"],
                }
                for s in steps
            ],
            "parameters": self.get_default_parameters(),
            "parameter_space": {
                k: list(v) for k, v in self.define_parameter_space().items()
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.get_info(), ensure_ascii=False, indent=2)
