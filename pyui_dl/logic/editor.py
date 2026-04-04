"""
logic/editor.py  ―  ロジックエディタ（日本語対応版）
"""

import os

import pygame

from pyui_dl.logic.models import (
    ACTION_PARAM_DEFAULTS,
    ACTION_TYPES,
    COND_OPS,
    EVENT_PARAMS,
    EVENT_TYPES,
    VAR_OPS,
    make_action,
    make_condition,
    make_rule,
)

COL_WHITE = (255, 255, 255)
COL_GRAY = (160, 160, 160)
COL_DIM = (90, 90, 90)
COL_YELLOW = (255, 230, 60)
COL_CYAN = (80, 220, 255)
COL_GREEN = (80, 255, 160)
COL_ORANGE = (255, 140, 40)
COL_RED = (255, 80, 80)
COL_PURPLE = (180, 100, 255)

HUD_X = 10
HUD_Y = 10
HUD_W = 640
LINE_H = 20

SUB_RULE = "RULE"
SUB_EDIT = "EDIT"
SUB_INPUT = "INPUT"


def _get_jp_font(size: int) -> pygame.font.Font:
    """日本語対応フォントを返す（優先順位付き）。"""
    base = os.path.dirname(os.path.dirname(__file__))
    candidates = [
        os.path.join(base, "fonts", "NotoSansCJK-Regular.ttc"),
        os.path.join(base, "fonts", "MPLUSRounded1c-Black.ttf"),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    return pygame.font.SysFont("notosanscjkjp", size) or pygame.font.SysFont(None, size)


class LogicEditor:
    def __init__(self, logic_data):
        self.logic = logic_data
        self.enabled = False
        self.widget = None
        self.font = _get_jp_font(16)
        self.small = _get_jp_font(13)

        self._rule_idx = 0
        self._sub = SUB_RULE
        self._edit_section = 0
        self._edit_row = 0
        self._input_buf = ""
        self._input_apply = None
        self._input_hints: list = []

    # ── 外部 API ──────────────────────────────────────

    def set_widget(self, widget):
        if self.widget is not widget:
            self.widget = widget
            self._rule_idx = 0
            self._sub = SUB_RULE

    def toggle(self):
        self.enabled = not self.enabled
        self._sub = SUB_RULE

    def is_inputting(self) -> bool:
        """SUB_INPUT中（文字入力待ち）かどうか。"""
        return self.enabled and self._sub == SUB_INPUT

    # ── 内部ヘルパー ──────────────────────────────────

    def _widget_name(self):
        return self.widget.name if self.widget else "__global__"

    def _rules(self):
        if not self.widget:
            return []
        return self.logic.get_rules(self._widget_name())

    def _current_rule(self):
        rules = self._rules()
        if not rules:
            return None
        return rules[max(0, min(self._rule_idx, len(rules) - 1))]

    # ── 入力処理 ─────────────────────────────────────

    def handle_keydown(self, event) -> bool:
        if not self.enabled:
            return False
        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        if self._sub == SUB_INPUT:
            return self._handle_input_key(event)
        if self._sub == SUB_RULE:
            return self._handle_rule_list_key(event, ctrl)
        if self._sub == SUB_EDIT:
            return self._handle_edit_key(event, ctrl, shift)
        return True

    def handle_text_input(self, text: str) -> bool:
        if not self.enabled:
            return False
        if self._sub == SUB_INPUT:
            self._input_buf += text
            return True
        return False

    def _handle_rule_list_key(self, event, ctrl) -> bool:
        rules = self._rules()
        k = event.key

        if k == pygame.K_UP:
            self._rule_idx = max(0, self._rule_idx - 1)
        elif k == pygame.K_DOWN:
            self._rule_idx = min(max(0, len(rules) - 1), self._rule_idx + 1)
        elif k == pygame.K_a:
            self.logic.add_rule(self._widget_name())
            self._rule_idx = len(self._rules()) - 1
        elif k == pygame.K_d:
            r = self._current_rule()
            if r:
                self.logic.remove_rule(self._widget_name(), r["id"])
                self._rule_idx = max(0, self._rule_idx - 1)
        elif k == pygame.K_c:
            r = self._current_rule()
            if r:
                self.logic.duplicate_rule(self._widget_name(), r["id"])
                self._rule_idx = len(self._rules()) - 1
        elif k in (pygame.K_e, pygame.K_RETURN):
            if self._current_rule():
                self._sub = SUB_EDIT
                self._edit_section = 0
                self._edit_row = 0
        elif k == pygame.K_ESCAPE:
            self.enabled = False
        return True

    def _handle_edit_key(self, event, ctrl, shift) -> bool:
        rule = self._current_rule()
        if not rule:
            self._sub = SUB_RULE
            return True
        k = event.key

        if k == pygame.K_ESCAPE:
            self._sub = SUB_RULE
            return True
        if k == pygame.K_TAB:
            self._edit_section = (self._edit_section + (-1 if shift else 1)) % 3
            self._edit_row = 0
            return True

        if self._edit_section == 0:
            self._edit_event(event, rule)
        elif self._edit_section == 1:
            self._edit_conditions(event, rule, ctrl, shift)
        elif self._edit_section == 2:
            self._edit_actions(event, rule, ctrl, shift)
        return True

    def _edit_event(self, event, rule):
        ev = rule["event"]
        params = EVENT_PARAMS.get(ev["type"], [])
        rows = ["type"] + params
        k = event.key

        if k == pygame.K_UP:
            self._edit_row = max(0, self._edit_row - 1)
        elif k == pygame.K_DOWN:
            self._edit_row = min(len(rows) - 1, self._edit_row + 1)
        elif k in (pygame.K_RETURN, pygame.K_RIGHT):
            row = rows[self._edit_row] if self._edit_row < len(rows) else None
            if row == "type":
                idx = EVENT_TYPES.index(ev["type"]) if ev["type"] in EVENT_TYPES else 0
                ev["type"] = EVENT_TYPES[(idx + 1) % len(EVENT_TYPES)]
                for p in EVENT_PARAMS.get(ev["type"], []):
                    ev.setdefault(p, "")
            elif row:
                self._start_input(
                    str(ev.get(row, "")), lambda v, ev=ev, row=row: ev.update({row: v})
                )

    def _edit_conditions(self, event, rule, ctrl, shift):
        conds = rule["conditions"]
        k = event.key

        if k == pygame.K_a:
            conds.append(make_condition())
            self._edit_row = len(conds) - 1
        elif k == pygame.K_d and conds:
            idx = max(0, min(self._edit_row, len(conds) - 1))
            conds.pop(idx)
            self._edit_row = max(0, self._edit_row - 1)
        elif k == pygame.K_UP:
            self._edit_row = max(0, self._edit_row - 1)
        elif k == pygame.K_DOWN:
            self._edit_row = min(max(0, len(conds) - 1), self._edit_row + 1)
        elif k == pygame.K_RETURN and conds:
            idx = max(0, min(self._edit_row, len(conds) - 1))
            c = conds[idx]
            if ctrl:
                self._start_input(
                    str(c["value"]),
                    lambda v, c=c: c.update({"value": self._parse_val(v)}),
                )
            elif shift:
                # Shift+Enter: op をサイクル（従来通り）
                op_i = COND_OPS.index(c["op"]) if c["op"] in COND_OPS else 0
                c["op"] = COND_OPS[(op_i + 1) % len(COND_OPS)]
            elif event.key == pygame.K_RETURN:
                self._start_input(c["var"], lambda v, c=c: c.update({"var": v}))
        elif k == pygame.K_o and conds:
            # o: op を直接入力
            idx = max(0, min(self._edit_row, len(conds) - 1))
            c = conds[idx]
            self._start_input_with_hints(
                c["op"],
                lambda v, c=c: c.update({"op": v if v in COND_OPS else c["op"]}),
                COND_OPS,
            )

    def _edit_actions(self, event, rule, ctrl, shift):
        actions = rule["actions"]
        k = event.key

        if k == pygame.K_a:
            actions.append(make_action("set_var"))
            self._edit_row = len(actions) - 1
        elif k == pygame.K_d and actions:
            idx = max(0, min(self._edit_row, len(actions) - 1))
            actions.pop(idx)
            self._edit_row = max(0, self._edit_row - 1)
        elif k == pygame.K_UP:
            self._edit_row = max(0, self._edit_row - 1)
        elif k == pygame.K_DOWN:
            self._edit_row = min(max(0, len(actions) - 1), self._edit_row + 1)
        elif k == pygame.K_RETURN and actions:
            idx = max(0, min(self._edit_row, len(actions) - 1))
            act = actions[idx]
            if shift:
                # Shift+Enter: type をサイクル（従来通り）
                t_i = (
                    ACTION_TYPES.index(act["type"])
                    if act["type"] in ACTION_TYPES
                    else 0
                )
                new_type = ACTION_TYPES[(t_i + 1) % len(ACTION_TYPES)]
                actions[idx] = make_action(new_type)
            else:
                self._action_edit_param(actions, 0)
        elif k == pygame.K_t and actions:
            # t: アクション type を直接入力
            idx = max(0, min(self._edit_row, len(actions) - 1))
            act = actions[idx]

            def _apply_type(v, actions=actions, idx=idx):
                if v in ACTION_TYPES:
                    actions[idx] = make_action(v)

            self._start_input_with_hints(act["type"], _apply_type, ACTION_TYPES)
        elif k == pygame.K_1 and actions:
            self._action_edit_param(actions, 0)
        elif k == pygame.K_2 and actions:
            self._action_edit_param(actions, 1)
        elif k == pygame.K_3 and actions:
            self._action_edit_param(actions, 2)

    def _action_edit_param(self, actions, slot):
        idx = max(0, min(self._edit_row, len(actions) - 1))
        act = actions[idx]
        params = ACTION_PARAM_DEFAULTS.get(act["type"], {})
        keys = [k for k in params if k != "type"]
        if slot >= len(keys):
            return
        pkey = keys[slot]
        self._start_input(
            str(act.get(pkey, "")),
            lambda v, act=act, pkey=pkey: act.update(
                {pkey: self._try_cast(v, act.get(pkey))}
            ),
        )

    def _start_input(self, current, on_confirm):
        self._sub = SUB_INPUT
        self._input_buf = current
        self._input_apply = on_confirm
        self._input_hints: list[str] = []  # 候補リスト（呼び出し元がセット）

    def _start_input_with_hints(self, current, on_confirm, hints: list):
        self._start_input(current, on_confirm)
        self._input_hints = hints

    def _handle_input_key(self, event) -> bool:
        k = event.key
        if k == pygame.K_RETURN:
            if self._input_apply:
                self._input_apply(self._input_buf)
            self._sub = SUB_EDIT
        elif k == pygame.K_ESCAPE:
            self._sub = SUB_EDIT
        elif k == pygame.K_BACKSPACE:
            self._input_buf = self._input_buf[:-1]
        return True

    @staticmethod
    def _parse_val(s):
        try:
            return int(s)
        except Exception:
            pass
        try:
            return float(s)
        except Exception:
            pass
        if s.lower() in ("true", "yes"):
            return True
        if s.lower() in ("false", "no"):
            return False
        return s

    @staticmethod
    def _try_cast(new_str, old_val):
        if isinstance(old_val, bool):
            return new_str.lower() not in ("false", "no", "0", "")
        if isinstance(old_val, int):
            try:
                return int(new_str)
            except Exception:
                return old_val
        if isinstance(old_val, float):
            try:
                return float(new_str)
            except Exception:
                return old_val
        return new_str

    # ── 描画 ─────────────────────────────────────────

    def draw(self, screen):
        if not self.enabled:
            return
        lines = []  # (text, color)

        wname = self._widget_name()
        lines.append((f"■ LOGIC MODE ■  対象: {wname}", COL_ORANGE))
        lines.append(("─" * 60, COL_DIM))

        rules = self._rules()
        if self._sub == SUB_RULE:
            self._build_rule_list(lines, rules)
        else:
            self._build_rule_edit(lines, rules)

        hud_h = len(lines) * LINE_H + 20
        bg = pygame.Surface((HUD_W, hud_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        screen.blit(bg, (HUD_X, HUD_Y))

        for i, (text, color) in enumerate(lines):
            surf = self.font.render(text, True, color)
            screen.blit(surf, (HUD_X + 10, HUD_Y + 10 + i * LINE_H))

    def _build_rule_list(self, lines, rules):
        if not rules:
            lines.append(("  （ルールなし）", COL_GRAY))
        else:
            for i, r in enumerate(rules):
                sel = i == self._rule_idx
                col = COL_YELLOW if sel else COL_WHITE
                marker = "▶" if sel else "  "
                ev_str = self._fmt_event(r["event"])
                acts = r["actions"]
                act_str = "  |  ".join(self._fmt_action(a) for a in acts[:2])
                if len(acts) > 2:
                    act_str += f"  +{len(acts) - 2}件"
                label = r.get("label", "")
                prefix = f"[{label}] " if label else ""
                lines.append(
                    (f"  {marker} {r['id']}  {prefix}{ev_str}  →  {act_str}", col)
                )

        lines.append(("─" * 60, COL_DIM))
        lines.append(("a:追加  d:削除  c:コピー  e/Enter:編集  Esc:終了", COL_GRAY))

    def _build_rule_edit(self, lines, rules):
        rule = self._current_rule()
        if not rule:
            return

        lines.append(
            (f"  ルールID: {rule['id']}  ラベル: {rule.get('label', '')}", COL_WHITE)
        )
        lines.append(("─" * 60, COL_DIM))

        # ─ EVENT ─
        sec_col = COL_CYAN if self._edit_section == 0 else COL_GRAY
        editing = "◉ 編集中" if self._edit_section == 0 else "Tab で移動"
        lines.append((f"  [EVENT]  ({editing})", sec_col))
        ev = rule["event"]
        params = EVENT_PARAMS.get(ev["type"], [])
        for row_i, item in enumerate(["type"] + params):
            sel = self._edit_section == 0 and self._edit_row == row_i
            col = (
                COL_YELLOW
                if sel
                else (COL_CYAN if self._edit_section == 0 else COL_GRAY)
            )
            val = ev["type"] if item == "type" else ev.get(item, "")
            if self._sub == SUB_INPUT and sel:
                val = self._input_buf + "█"
            lines.append((f"    {'▶' if sel else ' '} {item}: {val}", col))

        lines.append(("  ─", COL_DIM))

        # ─ CONDITIONS ─
        sec_col = COL_GREEN if self._edit_section == 1 else COL_GRAY
        editing = "◉ 編集中" if self._edit_section == 1 else "Tab"
        conds = rule["conditions"]
        lines.append((f"  [条件]  {len(conds)}件  ({editing})", sec_col))
        if not conds:
            lines.append(
                (
                    "    （なし） — a で追加",
                    COL_DIM if self._edit_section != 1 else sec_col,
                )
            )
        for ci, c in enumerate(conds):
            sel = self._edit_section == 1 and self._edit_row == ci
            col = (
                COL_YELLOW
                if sel
                else (COL_GREEN if self._edit_section == 1 else COL_GRAY)
            )
            var_d = (
                (self._input_buf + "█")
                if (self._sub == SUB_INPUT and sel)
                else c["var"]
            )
            lines.append(
                (f"    {'▶' if sel else ' '} {var_d} {c['op']} {c['value']}", col)
            )
        if self._edit_section == 1:
            lines.append(
                (
                    "    a:追加  d:削除  ↑↓:選択  Enter:変数名  o:演算子直接入力  Shift+Enter:演算子サイクル  Ctrl+Enter:値",
                    COL_DIM,
                )
            )

        lines.append(("  ─", COL_DIM))

        # ─ ACTIONS ─
        sec_col = COL_PURPLE if self._edit_section == 2 else COL_GRAY
        editing = "◉ 編集中" if self._edit_section == 2 else "Tab"
        actions = rule["actions"]
        lines.append((f"  [アクション]  {len(actions)}件  ({editing})", sec_col))
        if not actions:
            lines.append(
                (
                    "    （なし） — a で追加",
                    COL_DIM if self._edit_section != 2 else sec_col,
                )
            )
        for ai, act in enumerate(actions):
            sel = self._edit_section == 2 and self._edit_row == ai
            col = (
                COL_YELLOW
                if sel
                else (COL_PURPLE if self._edit_section == 2 else COL_GRAY)
            )
            params = ACTION_PARAM_DEFAULTS.get(act["type"], {})
            keys = [k for k in params if k != "type"]
            if self._sub == SUB_INPUT and sel:
                param_str = self._input_buf + "█"
            else:
                param_str = "  ".join(f"{k}:{act.get(k, '')}" for k in keys[:3])
            lines.append((f"    {'▶' if sel else ' '} {act['type']}  {param_str}", col))
        if self._edit_section == 2:
            lines.append(
                (
                    "    a:追加  d:削除  Enter:パラメータ編集  1/2/3:各パラメータ  t:種類直接入力  Shift+Enter:種類サイクル",
                    COL_DIM,
                )
            )

        lines.append(("─" * 60, COL_DIM))
        lines.append(("Tab:セクション移動  Esc:一覧へ戻る", COL_GRAY))

        # INPUT モード中は候補ヒントを追記
        if self._sub == SUB_INPUT and self._input_hints:
            buf = self._input_buf.lower()
            matched = [h for h in self._input_hints if buf in h.lower()]
            if matched:
                hint_str = "  ".join(matched[:8])
                lines.append((f"候補: {hint_str}", (120, 200, 255)))

    @staticmethod
    def _fmt_event(ev):
        t = ev.get("type", "?")
        extras = {k: v for k, v in ev.items() if k != "type"}
        if extras:
            ex_str = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{t}({ex_str})"
        return t

    @staticmethod
    def _fmt_action(act):
        t = act.get("type", "?")
        params = ACTION_PARAM_DEFAULTS.get(t, {})
        keys = [k for k in params if k != "type"]
        vals = " ".join(f"{k}={act.get(k, '')}" for k in keys[:2])
        return f"{t} {vals}".strip()
