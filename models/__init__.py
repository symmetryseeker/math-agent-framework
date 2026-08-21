"""
Math Agent Framework — Models
==============================
所有数学模型通过继承 BaseModel 来定义。

内置模型 (builtin/):
    - ces_production:      CES生产函数
    - quadratic_form:      二次型U/倒U分析
    - dynamic_optimization: 动态优化
    - network_embedded_growth: 完整网络嵌入增长模型 (原NSFC项目)

用户模型 (user/):
    在此目录下创建自定义模型，自动发现和加载。

模型发现:
    from models import discover_models
    models = discover_models()  # 返回所有可用模型
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Type

from .base_model import BaseModel

__all__ = ["BaseModel", "discover_models", "load_model"]


def discover_models() -> Dict[str, Type[BaseModel]]:
    """
    自动发现所有已注册的模型。

    搜索路径:
        1. models/builtin/*.py
        2. models/user/*.py

    Returns:
        {'model_name': ModelClass, ...}
    """
    models = {}
    base_dir = Path(__file__).parent

    for subdir in ["builtin", "user"]:
        pkg_dir = base_dir / subdir
        if not pkg_dir.exists():
            continue

        for py_file in pkg_dir.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name.startswith("."):
                continue
            module_name = py_file.stem
            try:
                full_name = f"models.{subdir}.{module_name}"
                module = importlib.import_module(full_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseModel)
                        and obj is not BaseModel
                        and hasattr(obj, "name")
                        and obj.name != "base_model"
                    ):
                        models[obj.name] = obj
            except ImportError as e:
                print(f"  [WARN] Failed to import {module_name}: {e}")

    return models


def load_model(model_name: str, config: dict = None) -> BaseModel:
    """
    加载指定模型。

    Args:
        model_name: 模型名 (如 'ces_production', 'network_embedded_growth')
        config: 模型配置

    Returns:
        BaseModel 实例
    """
    all_models = discover_models()
    if model_name not in all_models:
        available = list(all_models.keys())
        raise ValueError(
            f"Model '{model_name}' not found. Available: {available}"
        )
    return all_models[model_name](config)
