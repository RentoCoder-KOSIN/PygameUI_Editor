"""
logic/runtime.py  ―  ロジック JSON を実際に動かすランタイムエンジン

ゲーム側からこう使う:
    from pyui_dl.logic.runtime import LogicRuntime
    runtime = LogicRuntime(logic_data, ui_root)

    # 毎フレーム
    runtime.tick(dt)                       # タイマーイベントを進める
    runtime.fire("on_click",   "btn_exit") # クリックを通知
    runtime.fire("on_collide", "player", with_tag="enemy")  # 衝突を通知
"""

import random


class LogicRuntime:
    def __init__(self, logic_data, ui_root):
        self.logic = logic_data
        self.ui_root = ui_root
        self.vars = dict(logic_data.global_vars)  # 実行時変数
        self._timers: dict[str, float] = {}  # rule_id → 残り秒
        self._handlers: dict[str, list] = {}  # カスタムイベント登録

    # ── 公開 API ─────────────────────────────────────

    def fire(self, event_type: str, widget_name: str, **params) -> list[str]:
        """イベントを発火し、マッチしたルールのアクションを実行。
        実行したアクション名リストを返す。"""
        executed = []
        for rule in self.logic.get_rules(widget_name):
            ev = rule["event"]
            if ev["type"] != event_type:
                continue
            # パラメータ照合
            if not self._match_params(ev, params):
                continue
            # 条件チェック
            if not self._check_conditions(rule["conditions"]):
                continue
            # アクション実行
            for act in rule["actions"]:
                self._exec_action(act, widget_name)
                executed.append(act["type"])
        return executed

    def tick(self, dt: float):
        """タイマーイベントを進める（毎フレーム dt 秒を渡す）。"""
        for wname, rules in self.logic.widget_rules.items():
            for rule in rules:
                ev = rule["event"]
                if ev["type"] != "on_timer":
                    continue
                rid = rule["id"]
                delay = float(ev.get("delay", 1.0))
                self._timers[rid] = self._timers.get(rid, delay) - dt
                if self._timers[rid] <= 0:
                    self._timers[rid] = delay
                    if self._check_conditions(rule["conditions"]):
                        for act in rule["actions"]:
                            self._exec_action(act, wname)

    def get(self, var_name, default=None):
        return self.vars.get(var_name, default)

    def set(self, var_name, value):
        self.vars[var_name] = value

    # ── 内部処理 ─────────────────────────────────────

    def _match_params(self, ev: dict, params: dict) -> bool:
        for k, v in params.items():
            if str(ev.get(k, "")) != str(v):
                return False
        return True

    def _check_conditions(self, conds: list) -> bool:
        for c in conds:
            var_val = self.vars.get(c["var"])
            if var_val is None:
                return False
            try:
                val = type(var_val)(c["value"])
            except (TypeError, ValueError):
                val = c["value"]
            op = c["op"]
            if op == "==" and not (var_val == val):
                return False
            if op == "!=" and not (var_val != val):
                return False
            if op == ">" and not (var_val > val):
                return False
            if op == ">=" and not (var_val >= val):
                return False
            if op == "<" and not (var_val < val):
                return False
            if op == "<=" and not (var_val <= val):
                return False
        return True

    def _exec_action(self, act: dict, source_widget: str):
        t = act["type"]

        if t == "set_var":
            var = act.get("var", "")
            op = act.get("op", "=")
            val = act.get("value", 0)
            cur = self.vars.get(var, 0)
            try:
                val = type(cur)(val)
            except Exception:
                pass
            if op == "=":
                self.vars[var] = val
            elif op == "+=":
                self.vars[var] = cur + val
            elif op == "-=":
                self.vars[var] = cur - val
            elif op == "*=":
                self.vars[var] = cur * val
            elif op == "/=":
                self.vars[var] = cur / val if val != 0 else cur

        elif t == "set_visible":
            w = self.ui_root.find_by_name(act.get("target", ""))
            if w:
                w.alpha = 255 if act.get("visible", True) else 0

        elif t == "move_to":
            w = self.ui_root.find_by_name(act.get("target", ""))
            if w:
                w.rel_x = int(act.get("x", 0))
                w.rel_y = int(act.get("y", 0))
                self.ui_root.update_layout(
                    0, 0, self.ui_root.rect.w, self.ui_root.rect.h
                )

        elif t == "move_by":
            w = self.ui_root.find_by_name(act.get("target", ""))
            if w:
                w.rel_x += int(act.get("dx", 0))
                w.rel_y += int(act.get("dy", 0))
                self.ui_root.update_layout(
                    0, 0, self.ui_root.rect.w, self.ui_root.rect.h
                )

        elif t == "destroy":
            w = self.ui_root.find_by_name(act.get("target", ""))
            if w and w.parent:
                w.parent.children.remove(w)

        elif t == "emit_event":
            ev_name = act.get("event", "")
            target = act.get("target", source_widget)
            self.fire(ev_name, target)

        # change_scene / play_sound / spawn / set_state / play_anim は
        # ゲーム側で on_action コールバックを使って実装する
        elif t in ("change_scene", "play_sound", "spawn", "set_state", "play_anim"):
            for cb in self._handlers.get(t, []):
                cb(act, source_widget, self)

    def on_action(self, action_type: str, callback):
        """change_scene 等のカスタムアクションにコールバックを登録。"""
        self._handlers.setdefault(action_type, []).append(callback)
