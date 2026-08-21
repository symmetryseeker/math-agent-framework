"""
ModelBridge — 模型桥接层
=========================
连接原始项目的数据文件与新框架，使新框架可以直接读取原始推导结果。
"""

import json, os
from pathlib import Path
from typing import Any, Dict, List, Optional

class ModelBridge:
    """原始项目 -> 新框架的桥接层。"""

    def __init__(self, legacy_dir: Optional[str] = None):
        self.LEGACY_DIR = Path(legacy_dir) if legacy_dir else None

    def load_legacy_report(self, report_name: str = "full_derivation_pipeline.json") -> Optional[Dict]:
        """加载原始项目的推导报告"""
        if self.LEGACY_DIR is None:
            return None
        path = self.LEGACY_DIR / "derivations" / report_name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def convert_legacy_to_framework_format(self, legacy_report: Dict) -> Dict:
        """将原始报告格式转换为框架格式"""
        steps = {}
        for key, value in legacy_report.items():
            if key.startswith("step"):
                steps[key] = {"status": "success", "output": value}
        return {"metadata": legacy_report.get("metadata", {}), "steps": steps}
