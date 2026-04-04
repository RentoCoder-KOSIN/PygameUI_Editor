import json

from pyui_dl.ui.button import Button
from pyui_dl.ui.image import Image
from pyui_dl.ui.layout import AbsoluteLayout, HBox, VBox
from pyui_dl.ui.shapes import Circle


class Serializer:
    TYPE_MAP = {
        "VBox": VBox,
        "HBox": HBox,
        "AbsoluteLayout": AbsoluteLayout,
        "Button": Button,
        "Image": Image,
        "Circle": Circle,
    }

    @staticmethod
    def from_json(data):
        cls = Serializer.TYPE_MAP.get(data.get("type"), VBox)
        kw = data.copy()
        kw.pop("type", None)
        children = kw.pop("children", [])
        inst = cls(**kw)
        for c in children:
            inst.add_child(Serializer.from_json(c))
        return inst

    @staticmethod
    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return Serializer.from_json(json.load(f))

    @staticmethod
    def save_file(root, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(root.to_dict(), f, indent=2, ensure_ascii=False)
