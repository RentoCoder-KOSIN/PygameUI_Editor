"""
logic/models.py  ―  ロジックデータモデル
==========================================

構造:
    LogicData          ... ファイル全体（widget_rules + global_vars）
    WidgetRule         ... 1つの Widget に紐づくルール集
    Rule               ... 1つの「イベント → 条件 → アクション」
    Event              ... 何をトリガーにするか
    Condition          ... 実行する条件（省略可）
    Action             ... 何をするか

JSON例:
{
  "global_vars": {"hp": 100, "score": 0},
  "widget_rules": {
    "player": [
      {
        "id": "rule_001",
        "event":  {"type": "on_collide", "with_tag": "enemy"},
        "conditions": [{"var": "hp", "op": ">", "value": 0}],
        "actions": [
          {"type": "set_var",   "var": "hp", "op": "-=", "value": 10},
          {"type": "play_anim", "target": "player", "anim": "hurt"}
        ]
      }
    ]
  }
}
"""

import uuid


# ─────────────────────────────────────────
#  イベント種別
# ─────────────────────────────────────────
EVENT_TYPES = [
    "on_click",        # クリック
    "on_collide",      # 衝突（with_tag で相手を指定）
    "on_enter",        # 画面/エリア進入
    "on_exit",         # 画面/エリア退出
    "on_var_change",   # 変数変化（var で対象を指定）
    "on_timer",        # 一定時間後
    "on_game_start",   # ゲーム開始時
    "on_state_enter",  # ステート突入時
]

# イベントが持てるパラメータ（type → [param_key, ...] ）
EVENT_PARAMS = {
    "on_click":       [],
    "on_collide":     ["with_tag"],        # 例: "enemy", "wall", "player"
    "on_enter":       ["area"],            # Widget名
    "on_exit":        ["area"],
    "on_var_change":  ["var"],             # 変数名
    "on_timer":       ["delay"],           # 秒数 (float)
    "on_game_start":  [],
    "on_state_enter": ["state"],           # ステート名
}

# ─────────────────────────────────────────
#  条件演算子
# ─────────────────────────────────────────
COND_OPS = ["==", "!=", ">", ">=", "<", "<="]

# ─────────────────────────────────────────
#  アクション種別
# ─────────────────────────────────────────
ACTION_TYPES = [
    "set_var",         # 変数を操作  {"var": "hp", "op": "-=", "value": 10}
    "set_visible",     # 表示切替   {"target": "widget_name", "visible": true}
    "move_to",         # 位置移動   {"target": "widget_name", "x": 100, "y": 200}
    "move_by",         # 相対移動   {"target": "widget_name", "dx": 0, "dy": -10}
    "play_anim",       # アニメ再生 {"target": "widget_name", "anim": "hurt"}
    "change_scene",    # シーン遷移 {"scene": "game_over"}
    "spawn",           # Widget生成 {"template": "bullet", "x": 0, "y": 0}
    "destroy",         # Widget削除 {"target": "widget_name"}
    "set_state",       # ステート変更 {"target": "widget_name", "state": "idle"}
    "play_sound",      # 音再生     {"sound": "hit.wav"}
    "emit_event",      # イベント発火 {"event": "on_game_start", "target": "widget_name"}
]

# アクションが持つパラメータ定義 type → { key: default }
ACTION_PARAM_DEFAULTS = {
    "set_var":      {"var": "hp",    "op": "-=",    "value": 10},
    "set_visible":  {"target": "",   "visible": True},
    "move_to":      {"target": "",   "x": 0,        "y": 0},
    "move_by":      {"target": "",   "dx": 0,        "dy": 0},
    "play_anim":    {"target": "",   "anim": "idle"},
    "change_scene": {"scene": ""},
    "spawn":        {"template": "", "x": 0,         "y": 0},
    "destroy":      {"target": ""},
    "set_state":    {"target": "",   "state": "idle"},
    "play_sound":   {"sound": ""},
    "emit_event":   {"event": "",    "target": ""},
}

VAR_OPS = ["=", "+=", "-=", "*=", "/="]


# ─────────────────────────────────────────
#  データクラス（dictベース、軽量）
# ─────────────────────────────────────────

def make_event(event_type="on_click", **params):
    d = {"type": event_type}
    d.update(params)
    return d


def make_condition(var="hp", op=">", value=0):
    return {"var": var, "op": op, "value": value}


def make_action(action_type="set_var", **overrides):
    d = {"type": action_type}
    defaults = ACTION_PARAM_DEFAULTS.get(action_type, {})
    d.update(defaults)
    d.update(overrides)
    return d


def make_rule(event=None, conditions=None, actions=None, label=""):
    return {
        "id": str(uuid.uuid4())[:8],
        "label": label,
        "event": event or make_event("on_click"),
        "conditions": conditions or [],
        "actions": actions or [make_action("set_var")],
    }


# ─────────────────────────────────────────
#  LogicData  ―  ファイル全体
# ─────────────────────────────────────────

class LogicData:
    def __init__(self):
        # widget_name → [rule, ...]
        self.widget_rules: dict[str, list[dict]] = {}
        # 変数名 → 初期値
        self.global_vars: dict[str, object] = {}

    # ---- Widget ルール操作 ----

    def get_rules(self, widget_name: str) -> list[dict]:
        return self.widget_rules.setdefault(widget_name, [])

    def add_rule(self, widget_name: str, rule: dict | None = None) -> dict:
        if rule is None:
            rule = make_rule()
        self.widget_rules.setdefault(widget_name, []).append(rule)
        return rule

    def remove_rule(self, widget_name: str, rule_id: str) -> bool:
        rules = self.widget_rules.get(widget_name, [])
        before = len(rules)
        self.widget_rules[widget_name] = [r for r in rules if r["id"] != rule_id]
        return len(self.widget_rules[widget_name]) < before

    def duplicate_rule(self, widget_name: str, rule_id: str) -> dict | None:
        for r in self.widget_rules.get(widget_name, []):
            if r["id"] == rule_id:
                import copy
                new = copy.deepcopy(r)
                new["id"] = str(uuid.uuid4())[:8]
                new["label"] = r.get("label", "") + "_copy"
                self.widget_rules[widget_name].append(new)
                return new
        return None

    # ---- 変数操作 ----

    def set_var(self, name: str, value):
        self.global_vars[name] = value

    def remove_var(self, name: str):
        self.global_vars.pop(name, None)

    # ---- シリアライズ ----

    def to_dict(self) -> dict:
        return {
            "global_vars": self.global_vars.copy(),
            "widget_rules": {
                k: list(v) for k, v in self.widget_rules.items() if v
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LogicData":
        obj = cls()
        obj.global_vars = data.get("global_vars", {})
        obj.widget_rules = {
            k: list(v)
            for k, v in data.get("widget_rules", {}).items()
        }
        return obj
