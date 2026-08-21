"""
provenance.py — 推导结果的可复现性信息
========================================
将引擎版本、Python 版本、seed、容差等环境指纹绑定到每次推导/验证输出。

设计目的:
    1. 可复现性: 同一模型同一参数在相同环境下应产生一致结果
    2. AEN 接入: 该指纹对应 AEN 的 Configuration Cell / Environment Fingerprint，
       使推导结果可作为 TaskEpisode / Experience 的证据被审计
    3. 诚实声明: 结果的成立边界（版本、seed、容差）随结果一同发布

不包含任何凭据或用户数据，可安全随结果发布。
"""

from __future__ import annotations

import os
import platform
import sys
from typing import Any, Dict, Optional

# 框架版本号（与 pyproject.toml 保持一致）
MAF_VERSION = "2.0.0"

# 默认容差与 seed（与 config.yaml 的 engines.numerical 一致）
DEFAULT_SEED = 42
DEFAULT_TOLERANCE_FOC = 1e-6
DEFAULT_TOLERANCE_SOC = 1e-4


def engine_versions() -> Dict[str, str]:
    """探测核心依赖版本（缺失时记录为 null）。"""
    versions: Dict[str, str] = {}
    for module_name in ("sympy", "numpy", "scipy", "quantecon", "mcp", "pydantic"):
        try:
            module = __import__(module_name)
            versions[module_name] = getattr(module, "__version__", "unknown")
        except Exception:
            versions[module_name] = "unavailable"
    return versions


def host_fingerprint() -> Dict[str, str]:
    """主机环境指纹（不含敏感信息）。"""
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "arch": platform.machine(),
    }


def snapshot_provenance(
    seed: Optional[int] = None,
    tolerances: Optional[Dict[str, float]] = None,
    model_name: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    生成当前环境的可复现性指纹。

    Args:
        seed: 数值采样的随机种子（默认 DEFAULT_SEED）
        tolerances: {容差名: 值}，如 {'foc': 1e-6, 'soc': 1e-4}
        model_name: 被推导的模型名（若有）
        params: 模型参数快照（应仅为可 JSON 化的标量）
        extra: 额外附加信息

    Returns:
        {
          "maf_version": "2.0.0",
          "engine_versions": {...},
          "host": {...},
          "seed": 42,
          "tolerances": {...},
          "model": "...",  (可选)
          "params": {...}, (可选)
          ...extra
        }
    """
    provenance: Dict[str, Any] = {
        "maf_version": MAF_VERSION,
        "engine_versions": engine_versions(),
        "host": host_fingerprint(),
        "seed": DEFAULT_SEED if seed is None else seed,
        "tolerances": {
            "foc": DEFAULT_TOLERANCE_FOC,
            "soc": DEFAULT_TOLERANCE_SOC,
        } if tolerances is None else tolerances,
    }
    if model_name is not None:
        provenance["model"] = model_name
    if params is not None:
        provenance["params"] = params
    if extra is not None:
        provenance.update(extra)
    return provenance


def attach_provenance(
    target: Dict[str, Any],
    *,
    key: str = "provenance",
    **provenance_kwargs: Any,
) -> Dict[str, Any]:
    """
    把 provenance 合并进一个结果字典（不覆盖已有 provenance）。

    Args:
        target: 要附加的目标字典（会被复制，不原地修改）
        key: 写入的键名（默认 "provenance"）
        **provenance_kwargs: 透传给 snapshot_provenance 的参数

    Returns:
        附加 provenance 后的新字典
    """
    result = dict(target)
    if key not in result:
        result[key] = snapshot_provenance(**provenance_kwargs)
    return result


def jsonable(value: Any) -> Any:
    """把非 JSON 可序列化对象转换为可序列化形式（用于 params 快照）。"""
    import numbers

    if isinstance(value, (str, int, bool, type(None))):
        return value
    if isinstance(value, numbers.Real):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return str(value)
