"""
collision.py  ―  pyui_dl 汎用当たり判定モジュール
==========================================================

■ 提供する機能
  - rect_rect(r1, r2)          : 矩形 vs 矩形
  - rect_circle(rect, cx, cy, r): 矩形 vs 円
  - circle_circle(...)         : 円 vs 円
  - point_rect(pos, rect)      : 点 vs 矩形
  - point_circle(pos, cx, cy, r): 点 vs 円

  - CollisionShape             : ウィジェットに付けるヒットボックス記述クラス
  - CollisionWorld             : 複数オブジェクトを登録して一括判定するクラス

■ DQゲームからの使い方（例）
    from pyui_dl.utils.collision import CollisionWorld, CollisionShape

    world = CollisionWorld()
    world.register("player", CollisionShape.rect(100, 200, 50, 50))
    world.register("enemy",  CollisionShape.rect(int(monster.x), CHAR_Y, 50, 50))

    if world.check("player", "enemy"):
        # 衝突！
        ...

    hits = world.query_point(mouse_pos)  # クリック位置に何があるか
"""

import pygame

# ──────────────────────────────────────────────
# 低レベル関数（pygame.Rect / 座標を直接渡す）
# ──────────────────────────────────────────────


def rect_rect(r1: pygame.Rect, r2: pygame.Rect) -> bool:
    """2つの矩形が重なっているか判定する。"""
    return r1.colliderect(r2)


def rect_circle(rect: pygame.Rect, cx: float, cy: float, r: float) -> bool:
    """矩形と円が重なっているか判定する。

    Args:
        rect : pygame.Rect
        cx, cy: 円の中心座標
        r     : 円の半径
    """
    # 矩形の最近傍点を求めてから距離比較
    nearest_x = max(rect.left, min(cx, rect.right))
    nearest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - nearest_x
    dy = cy - nearest_y
    return (dx * dx + dy * dy) <= (r * r)


def circle_circle(
    cx1: float, cy1: float, r1: float, cx2: float, cy2: float, r2: float
) -> bool:
    """2つの円が重なっているか判定する。"""
    dx = cx1 - cx2
    dy = cy1 - cy2
    dist_sq = dx * dx + dy * dy
    return dist_sq <= (r1 + r2) ** 2


def point_rect(pos: tuple, rect: pygame.Rect) -> bool:
    """点が矩形の内側にあるか判定する。"""
    return rect.collidepoint(pos)


def point_circle(pos: tuple, cx: float, cy: float, r: float) -> bool:
    """点が円の内側にあるか判定する。"""
    dx = pos[0] - cx
    dy = pos[1] - cy
    return (dx * dx + dy * dy) <= (r * r)


def overlap_area(r1: pygame.Rect, r2: pygame.Rect) -> int:
    """2矩形の重複面積を返す（重ならない場合は0）。"""
    ix = max(0, min(r1.right, r2.right) - max(r1.left, r2.left))
    iy = max(0, min(r1.bottom, r2.bottom) - max(r1.top, r2.top))
    return ix * iy


# ──────────────────────────────────────────────
# CollisionShape  ―  ヒットボックス記述クラス
# ──────────────────────────────────────────────


class CollisionShape:
    """当たり判定の形状（矩形 or 円）を保持するデータクラス。

    直接インスタンス化せず CollisionShape.rect() / CollisionShape.circle() を使う。
    """

    KIND_RECT = "rect"
    KIND_CIRCLE = "circle"

    def __init__(self, kind: str, **kwargs):
        self.kind = kind
        if kind == self.KIND_RECT:
            self._rect = pygame.Rect(kwargs["x"], kwargs["y"], kwargs["w"], kwargs["h"])
        elif kind == self.KIND_CIRCLE:
            self._cx = kwargs["cx"]
            self._cy = kwargs["cy"]
            self._r = kwargs["r"]
        else:
            raise ValueError(f"Unknown kind: {kind}")

    # ---- ファクトリ ----

    @classmethod
    def rect(cls, x: float, y: float, w: float, h: float) -> "CollisionShape":
        """矩形ヒットボックスを作成する。"""
        return cls(cls.KIND_RECT, x=int(x), y=int(y), w=int(w), h=int(h))

    @classmethod
    def circle(cls, cx: float, cy: float, r: float) -> "CollisionShape":
        """円ヒットボックスを作成する。"""
        return cls(cls.KIND_CIRCLE, cx=cx, cy=cy, r=r)

    @classmethod
    def from_widget(cls, widget) -> "CollisionShape":
        """Widget の現在の rect からそのまま矩形ヒットボックスを作成する。"""
        return cls.rect(widget.rect.x, widget.rect.y, widget.rect.w, widget.rect.h)

    # ---- 更新 ----

    def move_to(self, x: float, y: float) -> None:
        """位置を更新する（毎フレーム呼ぶ用途）。"""
        if self.kind == self.KIND_RECT:
            self._rect.x = int(x)
            self._rect.y = int(y)
        else:
            self._cx = x
            self._cy = y

    def sync_widget(self, widget) -> None:
        """Widget の rect に合わせて位置とサイズを同期する。"""
        if self.kind == self.KIND_RECT:
            self._rect = pygame.Rect(
                widget.rect.x, widget.rect.y, widget.rect.w, widget.rect.h
            )
        else:
            self._cx = widget.rect.centerx
            self._cy = widget.rect.centery

    # ---- 判定 ----

    def collides_with(self, other: "CollisionShape") -> bool:
        """この形状と other が重なっているか判定する。"""
        if self.kind == self.KIND_RECT and other.kind == self.KIND_RECT:
            return rect_rect(self._rect, other._rect)

        if self.kind == self.KIND_CIRCLE and other.kind == self.KIND_CIRCLE:
            return circle_circle(
                self._cx, self._cy, self._r, other._cx, other._cy, other._r
            )

        # 矩形 × 円（どちらが先でも OK）
        if self.kind == self.KIND_RECT and other.kind == self.KIND_CIRCLE:
            return rect_circle(self._rect, other._cx, other._cy, other._r)
        if self.kind == self.KIND_CIRCLE and other.kind == self.KIND_RECT:
            return rect_circle(other._rect, self._cx, self._cy, self._r)

        return False

    def contains_point(self, pos: tuple) -> bool:
        """点がこの形状の内側にあるか判定する。"""
        if self.kind == self.KIND_RECT:
            return point_rect(pos, self._rect)
        return point_circle(pos, self._cx, self._cy, self._r)

    # ---- デバッグ描画 ----

    def draw_debug(self, screen, color=(0, 255, 0), width: int = 1) -> None:
        """当たり判定の形状をデバッグ描画する。"""
        if self.kind == self.KIND_RECT:
            pygame.draw.rect(screen, color, self._rect, width)
        else:
            pygame.draw.circle(
                screen, color, (int(self._cx), int(self._cy)), int(self._r), width
            )

    # ---- プロパティ ----

    @property
    def as_rect(self) -> pygame.Rect:
        """矩形形状の pygame.Rect を返す（矩形のみ有効）。"""
        if self.kind != self.KIND_RECT:
            raise AttributeError("circle shape has no rect")
        return self._rect

    @property
    def center(self) -> tuple:
        """形状の中心座標を返す。"""
        if self.kind == self.KIND_RECT:
            return self._rect.center
        return (self._cx, self._cy)

    def __repr__(self) -> str:
        if self.kind == self.KIND_RECT:
            return f"CollisionShape.rect({self._rect.x},{self._rect.y},{self._rect.w},{self._rect.h})"
        return f"CollisionShape.circle({self._cx},{self._cy},{self._r})"


# ──────────────────────────────────────────────
# CollisionWorld  ―  複数オブジェクトの一括管理
# ──────────────────────────────────────────────


class CollisionWorld:
    """名前付きの CollisionShape を登録して一括で判定するクラス。

    使い方:
        world = CollisionWorld()
        world.register("player", CollisionShape.rect(x, y, w, h))
        world.register("enemy",  CollisionShape.rect(ex, ey, ew, eh))

        # 毎フレーム位置更新
        world.update("player", x=player.x, y=player.y)

        # 判定
        if world.check("player", "enemy"):
            ...

        # 全ペア判定
        for a, b in world.get_all_collisions():
            print(f"{a} と {b} が衝突")
    """

    def __init__(self):
        self._shapes: dict[str, CollisionShape] = {}

    # ---- 登録 / 削除 ----

    def register(self, name: str, shape: CollisionShape) -> None:
        """名前と形状を登録する。同じ名前で呼ぶと上書きされる。"""
        self._shapes[name] = shape

    def unregister(self, name: str) -> None:
        """登録を削除する。"""
        self._shapes.pop(name, None)

    def clear(self) -> None:
        """全登録を削除する。"""
        self._shapes.clear()

    # ---- 更新 ----

    def update(self, name: str, x: float, y: float) -> None:
        """登録済み形状の位置を更新する。"""
        if name in self._shapes:
            self._shapes[name].move_to(x, y)

    def sync_widget(self, name: str, widget) -> None:
        """Widget の rect と同期する。"""
        if name in self._shapes:
            self._shapes[name].sync_widget(widget)

    # ---- 判定 ----

    def check(self, name_a: str, name_b: str) -> bool:
        """2つの登録形状が衝突しているか判定する。"""
        a = self._shapes.get(name_a)
        b = self._shapes.get(name_b)
        if a is None or b is None:
            return False
        return a.collides_with(b)

    def query_point(self, pos: tuple) -> list[str]:
        """点と衝突する全オブジェクト名のリストを返す。"""
        return [
            name for name, shape in self._shapes.items() if shape.contains_point(pos)
        ]

    def get_all_collisions(self) -> list[tuple[str, str]]:
        """衝突しているすべてのペアを返す。O(n²) なので大量登録には注意。"""
        names = list(self._shapes.keys())
        result = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if self._shapes[a].collides_with(self._shapes[b]):
                    result.append((a, b))
        return result

    def get_collisions_with(self, name: str) -> list[str]:
        """指定オブジェクトと衝突している他のオブジェクト名リストを返す。"""
        target = self._shapes.get(name)
        if target is None:
            return []
        return [
            n for n, s in self._shapes.items() if n != name and s.collides_with(target)
        ]

    # ---- デバッグ描画 ----

    def draw_debug(self, screen, color=(0, 255, 0), width: int = 1) -> None:
        """全登録形状をデバッグ描画する。"""
        for shape in self._shapes.values():
            shape.draw_debug(screen, color=color, width=width)


# ──────────────────────────────────────────────
# PhysicsBody  ―  自由移動 + 壁・床・障害物との衝突応答
# ──────────────────────────────────────────────


class PhysicsBody:
    """自由移動するオブジェクトに付ける物理ボディ。

    collision_tag が "wall" / "floor" / "obstacle" の Widget を障害物として
    AABB 軸分離押し戻しで衝突応答する。

    基本的な使い方（ゲーム側 main.py イメージ）::

        from pyui_dl.utils.collision import PhysicsBody

        body = PhysicsBody(x=100.0, y=200.0, w=32, h=48)

        # 毎フレーム
        body.apply_gravity()
        body.move(vx=player_vx)          # vy は省略すると内部の vy を使う
        body.resolve_collisions(ui_root) # ui_root = Widget ツリーのルート

        # 結果を描画座標に反映
        player.x = body.x
        player.y = body.y
        if body.on_ground:
            body.vy = 0   # 着地したら落下速度リセット

    デバッグ描画::

        body.draw_debug(screen)           # 黄色の矩形でボディ位置を表示
    """

    SOLID_TAGS = {"wall", "floor", "obstacle"}

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        w: int = 32,
        h: int = 32,
        gravity: float = 0.5,
        max_fall_speed: float = 20.0,
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.gravity = gravity
        self.max_fall_speed = max_fall_speed
        # 状態フラグ（resolve_collisions 後に参照する）
        self.on_ground = False
        self.hit_wall_left = False
        self.hit_wall_right = False
        self.hit_ceiling = False

    # ---- プロパティ ----

    @property
    def rect(self) -> pygame.Rect:
        """現在位置の pygame.Rect を返す。"""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    # ---- 毎フレーム操作 ----

    def apply_gravity(self) -> None:
        """重力を速度に加算する。move() の前に呼ぶ。"""
        self.vy = min(self.vy + self.gravity, self.max_fall_speed)

    def move(self, vx: float | None = None, vy: float | None = None) -> None:
        """速度を適用して位置を更新する。

        vx / vy を渡すと self.vx / self.vy を上書きしてから移動する。
        省略した場合は現在の self.vx / self.vy をそのまま使う。
        """
        if vx is not None:
            self.vx = vx
        if vy is not None:
            self.vy = vy
        self.x += self.vx
        self.y += self.vy

    def resolve_collisions(self, ui_root) -> list:
        """Widget ツリーを走査し solid タグの Widget と衝突応答する。

        Returns:
            衝突した Widget の name リスト
        """
        self.on_ground = False
        self.hit_wall_left = False
        self.hit_wall_right = False
        self.hit_ceiling = False

        solid_widgets = [
            w
            for w in ui_root.collect_all_widgets()
            if getattr(w, "collision_tag", "none") in self.SOLID_TAGS
        ]

        hit_names = []
        body_rect = self.rect

        for w in solid_widgets:
            if not body_rect.colliderect(w.rect):
                continue
            hit_names.append(w.name)

            ox = self._overlap_x(body_rect, w.rect)
            oy = self._overlap_y(body_rect, w.rect)

            # 重複が小さい軸で押し戻す
            if abs(ox) <= abs(oy):
                self.x += ox
                if ox > 0:
                    self.hit_wall_left = True
                else:
                    self.hit_wall_right = True
                if self.vx * ox < 0:
                    self.vx = 0.0
            else:
                self.y += oy
                if oy > 0:
                    self.hit_ceiling = True
                    if self.vy < 0:
                        self.vy = 0.0
                else:
                    self.on_ground = True
                    if self.vy > 0:
                        self.vy = 0.0

            body_rect = self.rect  # 次の判定に備えて更新

        return hit_names

    # ---- 内部ヘルパー ----

    @staticmethod
    def _overlap_x(a: pygame.Rect, b: pygame.Rect) -> float:
        """a を b から押し出す X 方向の量（符号付き）。"""
        if a.centerx < b.centerx:
            return float(b.left - a.right)  # 左から当たっている → 右へ
        return float(b.right - a.left)  # 右から当たっている → 左へ

    @staticmethod
    def _overlap_y(a: pygame.Rect, b: pygame.Rect) -> float:
        """a を b から押し出す Y 方向の量（符号付き）。"""
        if a.centery < b.centery:
            return float(b.top - a.bottom)  # 上から当たっている → 上へ
        return float(b.bottom - a.top)  # 下から当たっている → 下へ

    # ---- デバッグ描画 ----

    def draw_debug(self, screen, color=(255, 200, 0), width: int = 2) -> None:
        """ボディの矩形をデバッグ描画する（黄色の枠）。"""
        pygame.draw.rect(screen, color, self.rect, width)
