import os

import pygame

from .widget import Widget


class Button(Widget):
    def __init__(self, text="", name="Button", **kwargs):
        super().__init__(name=name, **kwargs)
        self.text = text
        base = os.path.dirname(os.path.dirname(__file__))
        self._font_path = os.path.join(base, "fonts", "MPLUSRounded1c-Black.ttf")
        self._font_cache = {}  # サイズ -> Font のキャッシュ

    def _get_font(self, size):
        if size not in self._font_cache:
            try:
                self._font_cache[size] = pygame.font.Font(self._font_path, size)
            except FileNotFoundError:
                self._font_cache[size] = pygame.font.SysFont(None, size)
        return self._font_cache[size]

    def _fit_text(self, text, max_w, max_h, start_size=20):
        """テキストがボックスに収まる最大フォントサイズを返す"""
        padding = 8
        size = start_size
        while size > 6:
            font = self._get_font(size)
            # 改行対応
            lines = text.split("\n")
            line_h = font.get_linesize()
            total_h = line_h * len(lines)
            max_line_w = max(font.size(l)[0] for l in lines)
            if max_line_w <= max_w - padding * 2 and total_h <= max_h - padding * 2:
                return font, lines, line_h
            size -= 1
        return self._get_font(6), text.split("\n"), self._get_font(6).get_linesize()

    def draw(self, screen):
        temp = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(
            temp,
            (*self.color, self.alpha),
            (0, 0, self.rect.w, self.rect.h),
            border_radius=self.radius,
        )
        pygame.draw.rect(
            temp,
            (50, 50, 50, self.alpha),
            (0, 0, self.rect.w, self.rect.h),
            2,
            border_radius=self.radius,
        )

        if self.text:
            font, lines, line_h = self._fit_text(self.text, self.rect.w, self.rect.h)
            total_h = line_h * len(lines)
            start_y = (self.rect.h - total_h) // 2 + line_h // 2
            for i, line in enumerate(lines):
                ts = font.render(line, True, (255, 255, 255))
                x = (self.rect.w - ts.get_width()) // 2
                y = start_y + i * line_h - line_h // 2
                temp.blit(ts, (x, y))

        rot = pygame.transform.rotate(temp, self.angle)
        screen.blit(rot, rot.get_rect(center=self.rect.center).topleft)

    def to_dict(self):
        d = super().to_dict()
        d["text"] = self.text
        return d
