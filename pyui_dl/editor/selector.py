import tkinter as tk
from tkinter import colorchooser, filedialog

import pygame

from pyui_dl.ui.button import Button
from pyui_dl.ui.image import Image
from pyui_dl.ui.layout import AbsoluteLayout, HBox, VBox
from pyui_dl.ui.shapes import Circle
from pyui_dl.utils.serializer import Serializer

# モード定数
MODE_NORMAL = "NORMAL"
MODE_INSERT = "INSERT"


class Selector:
    # collision_tag サイクル順
    COLLISION_TAGS = ["none", "wall", "floor", "obstacle", "player", "trigger"]
    # collision_shape_type サイクル順
    COLLISION_SHAPES = ["rect", "circle"]

    # tag ごとのオーバーレイ色 (R,G,B,A)  None=描画しない
    TAG_COLORS = {
        "none": None,
        "wall": (255, 80, 80, 120),
        "floor": (255, 180, 60, 120),
        "obstacle": (200, 80, 255, 120),
        "player": (80, 200, 255, 120),
        "trigger": (80, 255, 160, 120),
    }
    TAG_OUTLINE = {
        "wall": (255, 80, 80),
        "floor": (255, 180, 60),
        "obstacle": (200, 80, 255),
        "player": (80, 200, 255),
        "trigger": (80, 255, 160),
    }

    @staticmethod
    def _load_font(size: int):
        import os

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
        return pygame.font.SysFont(None, size)

    def __init__(self):
        self.selected_widget = None
        self.is_dragging = False
        self.is_resizing = False
        self.drag_off = [0, 0]
        self.handle_size = 12
        self.font = self._load_font(17)
        self.small_font = self._load_font(14)
        self.edit_target = "TEXT"
        self.show_hud = True
        self.show_collision_preview = True  # F1 でトグル
        self.mode = MODE_NORMAL
        self._ui_root = None  # プレビュー描画用キャッシュ
        self._clipboard = None  # コピー用クリップボード
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()

    # ------------------------------------------------------------------ #
    #  internal helpers
    # ------------------------------------------------------------------ #
    def _enter_insert(self, target="TEXT"):
        self.mode = MODE_INSERT
        self.edit_target = target

    def _enter_normal(self):
        self.mode = MODE_NORMAL

    def _add_to_parent(self, new_widget):
        target = (
            self.selected_widget
            if isinstance(self.selected_widget, (VBox, HBox, AbsoluteLayout))
            else self.selected_widget.parent
        )
        target.add_child(new_widget)
        self.selected_widget = new_widget

    def _cycle(self, lst, current):
        """リスト内で current の次要素を返す（末尾なら先頭）。"""
        try:
            idx = lst.index(current)
        except ValueError:
            idx = -1
        return lst[(idx + 1) % len(lst)]

    # ------------------------------------------------------------------ #
    #  collision preview
    # ------------------------------------------------------------------ #
    def _draw_collision_preview(self, screen):
        """collision_tag が設定された全ウィジェットをカラーオーバーレイで表示する。"""
        if self._ui_root is None:
            return

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        for w in self._ui_root.collect_all_widgets():
            tag = getattr(w, "collision_tag", "none")
            shape = getattr(w, "collision_shape_type", "rect")
            fill = self.TAG_COLORS.get(tag)
            if fill is None:
                continue
            outline = self.TAG_OUTLINE.get(tag, (255, 255, 255))

            if shape == "circle":
                cx = w.rect.centerx
                cy = w.rect.centery
                r = max(1, min(w.rect.w, w.rect.h) // 2)
                pygame.draw.circle(overlay, fill, (cx, cy), r)
                pygame.draw.circle(overlay, (*outline, 220), (cx, cy), r, 2)
            else:
                pygame.draw.rect(overlay, fill, w.rect)
                pygame.draw.rect(overlay, (*outline, 220), w.rect, 2)

            lbl = self.small_font.render(tag, True, (255, 255, 255))
            overlay.blit(lbl, (w.rect.x + 2, w.rect.y + 2))

        screen.blit(overlay, (0, 0))

    # ------------------------------------------------------------------ #
    #  public API
    # ------------------------------------------------------------------ #
    def ask_file(self):
        self.tk_root.attributes("-topmost", True)
        return filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )

    def start_select(self, root, pos):
        self._ui_root = root  # プレビュー用に常に更新
        if self.selected_widget:
            h = pygame.Rect(
                self.selected_widget.rect.right - self.handle_size,
                self.selected_widget.rect.bottom - self.handle_size,
                self.handle_size,
                self.handle_size,
            )
            if h.collidepoint(pos):
                self.is_resizing = True
                return
        self.selected_widget = root.get_widget_at(pos)
        if self.selected_widget:
            self.is_dragging = True
            self._enter_normal()
            self.drag_off = [
                pos[0] - self.selected_widget.rect.x,
                pos[1] - self.selected_widget.rect.y,
            ]

    def stop_drag(self):
        self.is_dragging = self.is_resizing = False

    def handle_text_input(self, text):
        if not self.selected_widget:
            return False
        if self.mode != MODE_INSERT:
            return False
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            return False
        if self.edit_target == "NAME":
            self.selected_widget.name += text
        elif hasattr(self.selected_widget, "text"):
            self.selected_widget.text += text
        return True

    def update(self, pos):
        if not self.selected_widget:
            return False
        p = self.selected_widget.parent
        if self.is_resizing:
            self.selected_widget.width = max(10, pos[0] - self.selected_widget.rect.x)
            self.selected_widget.height = max(10, pos[1] - self.selected_widget.rect.y)
            if isinstance(p, (VBox, HBox)):
                self.selected_widget.weight = max(
                    0.1,
                    (pos[1] - self.selected_widget.rect.y) / self.selected_widget.rect.h
                    if isinstance(p, VBox)
                    else (pos[0] - self.selected_widget.rect.x)
                    / self.selected_widget.rect.w,
                )
            return True
        if self.is_dragging and isinstance(p, AbsoluteLayout):
            self.selected_widget.rel_x = pos[0] - p.rect.x - self.drag_off[0]
            self.selected_widget.rel_y = pos[1] - p.rect.y - self.drag_off[1]
            return True
        return False

    # ------------------------------------------------------------------ #
    #  draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        # 当たり判定プレビュー（常に描画、選択不要）
        if self.show_collision_preview:
            self._draw_collision_preview(screen)

        if not self.selected_widget:
            return

        # 選択枠
        color = (255, 120, 40) if self.mode == MODE_INSERT else (255, 0, 0)
        pygame.draw.rect(screen, color, self.selected_widget.rect, 2)

        # リサイズハンドル
        h = pygame.Rect(
            self.selected_widget.rect.right - self.handle_size,
            self.selected_widget.rect.bottom - self.handle_size,
            self.handle_size,
            self.handle_size,
        )
        pygame.draw.rect(screen, (0, 150, 255), h)

        if not self.show_hud:
            return

        # ---- HUD: オブジェクトのプロパティのみ表示 ----
        self._draw_hud(screen)

    def _draw_hud(self, screen):
        """選択中ウィジェットのプロパティのみをHUDに表示する。"""
        w = self.selected_widget
        wtype = type(w).__name__

        COL_VAL = (255, 255, 255)
        COL_EDIT = (255, 255, 0)
        COL_DIM = (120, 120, 120)
        COL_TAG = self.TAG_OUTLINE.get(
            getattr(w, "collision_tag", "none"), (160, 160, 160)
        )
        COL_HEADER = (255, 140, 40) if self.mode == MODE_INSERT else (100, 255, 100)

        line_h = 19
        pad_x, pad_y = 12, 10

        # --- プロパティ行を組み立て ---
        rows = []  # (label, value_str, color)

        # 共通
        name_col = (
            COL_EDIT
            if (self.mode == MODE_INSERT and self.edit_target == "NAME")
            else COL_VAL
        )
        rows.append(("type", wtype, COL_DIM))
        rows.append(("name", w.name, name_col))
        rows.append(("pos", f"x:{w.rel_x}  y:{w.rel_y}", COL_VAL))
        rows.append(("size", f"w:{w.width}  h:{w.height}", COL_VAL))
        rows.append(
            ("color", f"rgb({w.color[0]}, {w.color[1]}, {w.color[2]})", COL_VAL)
        )
        rows.append(("alpha", str(w.alpha), COL_VAL))
        rows.append(("angle", f"{w.angle}°", COL_VAL))
        rows.append(("radius", str(w.radius), COL_VAL))

        # text を持つ型（Button, Image）
        if hasattr(w, "text"):
            text_col = (
                COL_EDIT
                if (self.mode == MODE_INSERT and self.edit_target == "TEXT")
                else COL_VAL
            )
            rows.append(("text", w.text if w.text else "（空）", text_col))

        # Image 固有
        if hasattr(w, "path"):
            import os

            rows.append(
                ("path", os.path.basename(w.path) if w.path else "（なし）", COL_VAL)
            )
            rows.append(("show_bg", "ON" if w.show_bg else "OFF", COL_VAL))

        # レイアウト固有
        rows.append(("weight", f"{w.weight:.2f}", COL_VAL))
        rows.append(("padding", str(w.padding), COL_VAL))

        # 当たり判定
        tag = getattr(w, "collision_tag", "none")
        shape = getattr(w, "collision_shape_type", "rect")
        rows.append(("collision_tag", tag, COL_TAG))
        rows.append(("collision_shape", shape, COL_TAG))

        # --- サイズ計算して背景描画 ---
        label_w = max(self.font.size(lbl)[0] for lbl, _, _ in rows) + 8
        val_surfs = [self.font.render(val, True, col) for _, val, col in rows]
        content_w = label_w + max(s.get_width() for s in val_surfs) + pad_x * 2
        header_h = line_h + 4
        total_h = header_h + len(rows) * line_h + pad_y

        bg = pygame.Surface((content_w, total_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 185))
        screen.blit(bg, (10, 10))

        # ヘッダー（モード＋ウィジェット名）
        mode_label = f"-- {self.mode} --"
        if self.mode == MODE_INSERT:
            mode_label += f"  [{self.edit_target}を編集中]"
        screen.blit(
            self.font.render(mode_label, True, COL_HEADER), (10 + pad_x, 10 + 4)
        )

        # プロパティ行
        for i, ((lbl, _, col), val_surf) in enumerate(zip(rows, val_surfs)):
            y = 10 + header_h + i * line_h
            lbl_surf = self.font.render(lbl, True, COL_DIM)
            screen.blit(lbl_surf, (10 + pad_x, y))
            screen.blit(val_surf, (10 + pad_x + label_w, y))

    # ------------------------------------------------------------------ #
    #  input
    # ------------------------------------------------------------------ #
    def handle_input(self, event, ui_root):
        """KEYDOWN イベントを処理。True を返すとレイアウト再計算が走る。"""
        self._ui_root = ui_root  # 常に最新を保持

        # TAB: HUD ON/OFF
        if event.key == pygame.K_TAB:
            self.show_hud = not self.show_hud
            return True

        # Esc
        if event.key == pygame.K_ESCAPE:
            if self.mode == MODE_INSERT:
                self._enter_normal()
            else:
                self.selected_widget = None
            return True

        if not self.selected_widget:
            return False

        ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        # ============================================================
        # INSERT モード
        # ============================================================
        if self.mode == MODE_INSERT:
            if ctrl and event.key == pygame.K_n:
                self.edit_target = "NAME" if self.edit_target == "TEXT" else "TEXT"
                return True
            if event.key == pygame.K_BACKSPACE:
                if self.edit_target == "NAME":
                    self.selected_widget.name = self.selected_widget.name[:-1]
                elif hasattr(self.selected_widget, "text"):
                    self.selected_widget.text = self.selected_widget.text[:-1]
                return True
            if event.key == pygame.K_RETURN:
                self._enter_normal()
                return True
            return False

        # ============================================================
        # NORMAL モード
        # ============================================================
        p = self.selected_widget.parent

        # --- Ctrl+〇 ---
        if ctrl:
            # Ctrl+F: 当たり判定プレビュー ON/OFF（選択不要）
            if ctrl and event.key == pygame.K_f:
                self.show_collision_preview = not self.show_collision_preview
                return True

            if event.key == pygame.K_k:
                self.tk_root.attributes("-topmost", True)
                c = colorchooser.askcolor()[0]
                if c:
                    self.selected_widget.color = [int(x) for x in c]
                return True
            if event.key == pygame.K_r:
                self.selected_widget.angle = (self.selected_widget.angle + 15) % 360
                return True
            if event.key == pygame.K_n:
                self._enter_insert(target="NAME")
                return True
            if shift and event.key == pygame.K_c:
                # Ctrl+Shift+C: コピー
                self._clipboard = self.selected_widget.to_dict()
                return True
            if shift and event.key == pygame.K_v:
                # Ctrl+Shift+V: 貼り付け
                if self._clipboard:
                    n = Serializer.from_json(self._clipboard)
                    n.name += f"_copy{pygame.time.get_ticks()}"
                    p = self.selected_widget.parent if self.selected_widget else None
                    if p is None:
                        return True
                    if isinstance(p, AbsoluteLayout):
                        src = self.selected_widget
                        n.rel_x = getattr(src, "rel_x", 0) + 10
                        n.rel_y = getattr(src, "rel_y", 0) + 10
                        p.add_child(n)
                    else:
                        idx = p.children.index(self.selected_widget)
                        p.children.insert(idx + 1, n)
                        n.parent = p
                    self.selected_widget = n
                return True
            if event.key == pygame.K_m:
                d = self.selected_widget.to_dict()
                n = Serializer.from_json(d)
                n.name += "_mir"
                if isinstance(p, AbsoluteLayout):
                    n.rel_x = (
                        p.width
                        - self.selected_widget.width
                        - self.selected_widget.rel_x
                    )
                    p.add_child(n)
                elif p:
                    idx = p.children.index(self.selected_widget)
                    p.children.insert(idx + 1, n)
                    n.parent = p
                self.selected_widget = n
                return True
            if event.key == pygame.K_b:
                self._add_to_parent(
                    Button(text="New", name=f"btn_{pygame.time.get_ticks()}")
                )
                return True
            if event.key == pygame.K_h:
                self._add_to_parent(HBox(name=f"hbox_{pygame.time.get_ticks()}"))
                return True
            if event.key == pygame.K_v:
                self._add_to_parent(VBox(name=f"vbox_{pygame.time.get_ticks()}"))
                return True
            if event.key == pygame.K_l:
                self._add_to_parent(
                    AbsoluteLayout(name=f"abs_{pygame.time.get_ticks()}")
                )
                return True
            if event.key == pygame.K_c:
                self._add_to_parent(
                    Circle(name=f"circle_{pygame.time.get_ticks()}", w=100, h=100)
                )
                return True
            if event.key == pygame.K_i:
                path = self.ask_file()
                self._add_to_parent(
                    Image(
                        path=path, name=f"img_{pygame.time.get_ticks()}", w=100, h=100
                    )
                )
                return True
            # Ctrl+G: Image の背景 ON/OFF
            if event.key == pygame.K_g:
                if isinstance(self.selected_widget, Image):
                    self.selected_widget.show_bg = not self.selected_widget.show_bg
                return True
            # Ctrl+J: collision_tag をサイクル
            if event.key == pygame.K_j:
                cur = getattr(self.selected_widget, "collision_tag", "none")
                self.selected_widget.collision_tag = self._cycle(
                    self.COLLISION_TAGS, cur
                )
                return True
            # Ctrl+T: collision_shape_type をサイクル
            if event.key == pygame.K_t:
                cur = getattr(self.selected_widget, "collision_shape_type", "rect")
                self.selected_widget.collision_shape_type = self._cycle(
                    self.COLLISION_SHAPES, cur
                )
                return True
            # Ctrl+矢印: HBox/VBox 内で順序入れ替え
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                if isinstance(p, (HBox, VBox)):
                    ch = p.children
                    idx = ch.index(self.selected_widget)
                    if isinstance(p, HBox) and event.key == pygame.K_LEFT and idx > 0:
                        ch[idx], ch[idx - 1] = ch[idx - 1], ch[idx]
                    elif (
                        isinstance(p, HBox)
                        and event.key == pygame.K_RIGHT
                        and idx < len(ch) - 1
                    ):
                        ch[idx], ch[idx + 1] = ch[idx + 1], ch[idx]
                    elif isinstance(p, VBox) and event.key == pygame.K_UP and idx > 0:
                        ch[idx], ch[idx - 1] = ch[idx - 1], ch[idx]
                    elif (
                        isinstance(p, VBox)
                        and event.key == pygame.K_DOWN
                        and idx < len(ch) - 1
                    ):
                        ch[idx], ch[idx + 1] = ch[idx + 1], ch[idx]
                return True
            if event.key in (pygame.K_d, pygame.K_BACKSPACE):
                if p:
                    p.children.remove(self.selected_widget)
                    self.selected_widget = None
                return True
            return True

        # --- Shift+〇 ---
        if shift:
            if event.key == pygame.K_l:
                self.selected_widget.alpha = min(255, self.selected_widget.alpha + 15)
                return True
            if event.key == pygame.K_k:
                self.selected_widget.alpha = max(0, self.selected_widget.alpha - 15)
                return True
            if event.key == pygame.K_r:
                self.selected_widget.radius = (self.selected_widget.radius + 5) % 55
                return True
            if event.key == pygame.K_LEFTBRACKET:
                self.selected_widget.width += 5
                return True
            if event.key == pygame.K_RIGHTBRACKET:
                self.selected_widget.width = max(5, self.selected_widget.width - 5)
                return True
            if event.key == pygame.K_p:
                self.selected_widget.height += 5
                return True
            if event.key == pygame.K_o:
                self.selected_widget.height = max(5, self.selected_widget.height - 5)
                return True
            if event.key == pygame.K_UP:
                self.selected_widget.rel_y -= 1
                return True
            if event.key == pygame.K_DOWN:
                self.selected_widget.rel_y += 1
                return True
            if event.key == pygame.K_LEFT:
                self.selected_widget.rel_x -= 1
                return True
            if event.key == pygame.K_RIGHT:
                self.selected_widget.rel_x += 1
                return True
            return True

        # --- 修飾なし ---
        if event.key == pygame.K_i:
            self._enter_insert(target="TEXT")
            return True
        if event.key == pygame.K_d:
            if p:
                p.children.remove(self.selected_widget)
                self.selected_widget = None
            return True
        if event.key == pygame.K_BACKSPACE:
            return True
        if event.key == pygame.K_RETURN:
            self.selected_widget = None
            return True

        return False
