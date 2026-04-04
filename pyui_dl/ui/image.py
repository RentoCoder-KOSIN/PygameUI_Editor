import os

import pygame

from .widget import Widget


class Image(Widget):
    def __init__(self, path="", name="Image", **kwargs):
        p = kwargs.get("path", path)
        super().__init__(name=name, **kwargs)
        self.path = p
        self.text = kwargs.get("text", "")
        self.text_color = kwargs.get("text_color", [255, 255, 255])
        self.show_bg = kwargs.get("show_bg", True)  # 背景ON/OFFフラグ
        self.raw = None
        self.load_image(p)
        base = os.path.dirname(os.path.dirname(__file__))
        self._font_path = os.path.join(base, "fonts", "MPLUSRounded1c-Black.ttf")
        self._font_cache = {}

    def load_image(self, p):
        if p and os.path.exists(p):
            try:
                self.raw = pygame.image.load(p).convert_alpha()
            except FileNotFoundError:
                self.raw = None

    def _get_font(self, size):
        if size not in self._font_cache:
            try:
                self._font_cache[size] = pygame.font.Font(self._font_path, size)
            except FileNotFoundError:
                self._font_cache[size] = pygame.font.SysFont(None, size)
        return self._font_cache[size]

    def _fit_font(self, text, max_w, max_h, start_size=20):
        pad = 4
        size = start_size
        while size > 6:
            font = self._get_font(size)
            if (
                font.size(text)[0] <= max_w - pad * 2
                and font.get_linesize() <= max_h - pad * 2
            ):
                return font
            size -= 1
        return self._get_font(6)

    def draw(self, screen):
        temp = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        # ---- 背景（show_bg が True の時だけ描画） ----
        if self.show_bg:
            pygame.draw.rect(
                temp,
                (*self.color, self.alpha),
                (0, 0, self.rect.w, self.rect.h),
                border_radius=self.radius,
            )

        has_text = bool(self.text)

        # ---- アイコン領域の計算 ----
        icon_size = self.rect.h
        if has_text:
            icon_rect = pygame.Rect(0, 0, icon_size, self.rect.h)
        else:
            icon_rect = pygame.Rect(0, 0, self.rect.w, self.rect.h)

        # ---- アイコン描画 ----
        if self.raw:
            scaled = pygame.transform.smoothscale(self.raw, (icon_rect.w, icon_rect.h))
            scaled.set_alpha(self.alpha)
            temp.blit(scaled, icon_rect.topleft)
        else:
            pygame.draw.rect(temp, (80, 80, 80, self.alpha), icon_rect)
            pygame.draw.line(
                temp,
                (200, 0, 0, self.alpha),
                icon_rect.topleft,
                icon_rect.bottomright,
                2,
            )
            pygame.draw.line(
                temp,
                (200, 0, 0, self.alpha),
                (icon_rect.right, icon_rect.top),
                (icon_rect.left, icon_rect.bottom),
                2,
            )

        # ---- テキスト描画（アイコン右側） ----
        if has_text:
            text_x = icon_size + 4
            text_area_w = self.rect.w - text_x
            font = self._fit_font(self.text, text_area_w, self.rect.h)
            ts = font.render(self.text, True, tuple(self.text_color))
            ty = (self.rect.h - ts.get_height()) // 2
            temp.blit(ts, (text_x, ty))

        rot = pygame.transform.rotate(temp, self.angle)
        screen.blit(rot, rot.get_rect(center=self.rect.center).topleft)

    def to_dict(self):
        d = super().to_dict()
        d["path"] = self.path
        d["text"] = self.text
        d["text_color"] = list(self.text_color)
        d["show_bg"] = self.show_bg
        return d
