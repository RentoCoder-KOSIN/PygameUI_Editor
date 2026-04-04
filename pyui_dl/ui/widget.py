import pygame


class Widget:
    debug_mode = False

    def __init__(self, name="Widget", **kwargs):
        self.name = name
        self.rect = pygame.Rect(0, 0, 100, 50)
        self.children = []
        self.parent = None

        # 座標とサイズ
        self.rel_x = kwargs.get("x", 0)
        self.rel_y = kwargs.get("y", 0)
        self.width = kwargs.get("w", 200)
        self.height = kwargs.get("h", 100)

        # レイアウト
        self.padding = kwargs.get("padding", 5)
        self.weight = kwargs.get("weight", 1.0)

        # 外見
        self.color = kwargs.get("color", [100, 200, 255])
        self.angle = kwargs.get("angle", 0)
        self.alpha = kwargs.get("alpha", 255)
        self.radius = kwargs.get("radius", 0)

        # 当たり判定タグ: "none" / "wall" / "floor" / "obstacle" / "player" / "trigger"
        self.collision_tag = kwargs.get("collision_tag", "none")
        # 当たり判定形状: "rect" / "circle"
        self.collision_shape_type = kwargs.get("collision_shape_type", "rect")

    def find_by_name(self, name):
        if self.name == name:
            return self
        for child in self.children:
            f = child.find_by_name(name)
            if f:
                return f
        return None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return self

    def update_layout(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen):
        for child in self.children:
            child.draw(screen)

    def get_widget_at(self, pos):
        for child in reversed(self.children):
            found = child.get_widget_at(pos)
            if found:
                return found
        if self.rect.collidepoint(pos):
            return self
        return None

    # ------------------------------------------------------------------ #
    #  当たり判定ヘルパー
    # ------------------------------------------------------------------ #

    def to_collision_shape(self):
        """この Widget の現在 rect を CollisionShape（矩形）に変換して返す。

        使い方:
            shape = widget.to_collision_shape()
            if shape.collides_with(other_shape):
                ...
        """
        from pyui_dl.utils.collision import CollisionShape

        return CollisionShape.from_widget(self)

    def collides_with_widget(self, other) -> bool:
        """別の Widget と矩形ベースで衝突しているか判定する。

        使い方:
            if player_widget.collides_with_widget(enemy_widget):
                ...
        """
        return self.rect.colliderect(other.rect)

    def collides_with_point(self, pos: tuple) -> bool:
        """点（マウス座標など）がこの Widget の範囲内にあるか判定する。"""
        return self.rect.collidepoint(pos)

    def get_colliding_widgets(self, candidates) -> list:
        """candidates（Widgetのリスト）の中でこのWidgetと衝突しているものを返す。

        使い方:
            hits = player_widget.get_colliding_widgets(all_enemy_widgets)
        """
        return [
            w for w in candidates if w is not self and self.rect.colliderect(w.rect)
        ]

    def collect_all_widgets(self) -> list:
        """自分と全子孫 Widget をフラットなリストで返す。"""
        result = [self]
        for child in self.children:
            result.extend(child.collect_all_widgets())
        return result

    # ------------------------------------------------------------------ #

    def to_dict(self):
        return {
            "type": type(self).__name__,
            "name": self.name,
            "x": self.rel_x,
            "y": self.rel_y,
            "w": self.width,
            "h": self.height,
            "padding": self.padding,
            "weight": self.weight,
            "color": list(self.color),
            "angle": self.angle,
            "alpha": self.alpha,
            "radius": self.radius,
            "collision_tag": self.collision_tag,
            "collision_shape_type": self.collision_shape_type,
            "children": [c.to_dict() for c in self.children],
        }
