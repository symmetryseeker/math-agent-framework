"""
Math Agent Framework — Models
==============================
All mathematical models are defined by subclassing BaseModel.

Builtin models (builtin/):
    - quadratic_form:     Quadratic form U/inverted-U analysis
    - ode_solver:         ODE classification, solving, and verification
    - analysis_problems:  Limits, series convergence, integration, continuity
    - pde_solver:         PDE solving: Heat/Wave/Laplace/Poisson/Transport
    - harmonic_oscillator: Damped/driven harmonic oscillator (physics)

User models (user/):
    Create custom models in this directory; they are auto-discovered.

Model discovery:
    from models import discover_models
    models = discover_models()
"""

import os, importlib, inspect
from pathlib import Path
from typing import Dict, List, Type
from .base_model import BaseModel

__all__ = ["BaseModel", "discover_models", "load_model"]

def discover_models() -> Dict[str, Type[BaseModel]]:
    """Auto-discover all registered models."""
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
                    if (issubclass(obj, BaseModel) and obj is not BaseModel
                            and hasattr(obj, "name") and obj.name != "base_model"):
                        models[obj.name] = obj
            except ImportError as e:
                print(f"  [WARN] Failed to import {module_name}: {e}")
    return models

def load_model(model_name: str, config: dict = None) -> BaseModel:
    """Load a specific model by name."""
    all_models = discover_models()
    if model_name not in all_models:
        available = list(all_models.keys())
        raise ValueError(f"Model '{model_name}' not found. Available: {available}")
    return all_models[model_name](config)
