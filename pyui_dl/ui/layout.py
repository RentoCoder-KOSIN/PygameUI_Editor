import pygame

from pyui_dl.ui.widget import Widget


class VBox(Widget):
    def update_layout(self, x, y, w, h):
        super().update_layout(x, y, w, h)
        if not self.children:
            return
        total_w = sum(max(0.1, c.weight) for c in self.children)
        avail_h = h - (self.padding * (len(self.children) + 1))
        curr_y = y + self.padding
        for child in self.children:
            child_h = (max(0.1, child.weight) / total_w) * avail_h
            child.update_layout(x + self.padding, curr_y, w - self.padding * 2, child_h)
            curr_y += child_h + self.padding

    def draw(self, screen):
        if Widget.debug_mode:
            s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            s.fill((0, 100, 255, 30))
            screen.blit(s, self.rect.topleft)
            pygame.draw.rect(screen, (0, 100, 255), self.rect, 1)
        super().draw(screen)


class HBox(Widget):
    def update_layout(self, x, y, w, h):
        super().update_layout(x, y, w, h)
        if not self.children:
            return
        total_w = sum(max(0.1, c.weight) for c in self.children)
        avail_w = w - (self.padding * (len(self.children) + 1))
        curr_x = x + self.padding
        for child in self.children:
            child_w = (max(0.1, child.weight) / total_w) * avail_w
            child.update_layout(curr_x, y + self.padding, child_w, h - self.padding * 2)
            curr_x += child_w + self.padding

    def draw(self, screen):
        if Widget.debug_mode:
            s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            s.fill((0, 255, 100, 30))
            screen.blit(s, self.rect.topleft)
            pygame.draw.rect(screen, (0, 255, 100), self.rect, 1)
        super().draw(screen)


class AbsoluteLayout(Widget):
    def update_layout(self, x, y, w, h):
        super().update_layout(x, y, w, h)
        for child in self.children:
            child.update_layout(
                self.rect.x + child.rel_x,
                self.rect.y + child.rel_y,
                child.width,
                child.height,
            )

    def draw(self, screen):
        if Widget.debug_mode:
            s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            s.fill((255, 50, 50, 20))
            screen.blit(s, self.rect.topleft)
            pygame.draw.rect(screen, (255, 50, 50), self.rect, 1)
        super().draw(screen)
