"""
logic/serializer.py  ―  LogicData の JSON 保存・読み込み
"""

import json
import os

from pyui_dl.logic.models import LogicData


class LogicSerializer:
    @staticmethod
    def load_file(path: str) -> LogicData:
        with open(path, "r", encoding="utf-8") as f:
            return LogicData.from_dict(json.load(f))

    @staticmethod
    def save_file(logic: LogicData, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(logic.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def logic_path_from_ui_path(ui_path: str) -> str:
        """ui.json → logic_ui.json のパスを返す。"""
        base, name = os.path.split(ui_path)
        stem = name.replace(".json", "")
        return os.path.join(base, f"logic_{stem}.json")
