import pygame

from .widget import Widget


class Circle(Widget):
    def draw(self, screen):
        temp = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        center = (self.rect.w // 2, self.rect.h // 2)
        radius = min(self.rect.w, self.rect.h) // 2
        pygame.draw.circle(temp, (*self.color, self.alpha), center, radius)
        rot = pygame.transform.rotate(temp, self.angle)
        screen.blit(rot, rot.get_rect(center=self.rect.center).topleft)
        super().draw(screen)
