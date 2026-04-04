"""
coin_catch_game.py  ―  コインキャッチゲーム（サンプルゲーム）
=============================================================

  python coin_catch_game.py

  ← → キー でプレイヤーを動かし、コインをキャッチしよう。
  爆弾に当たるとライフが減る。ライフ 0 でゲームオーバー。
  スコアが 100 を超えるとスピードアップ！

このファイルは data/coin_catch.json（デザイン）と
data/logic_coin_catch.json（ロジック）を読み込み、
LogicRuntime を使ってゲームロジックを動かすサンプルです。
"""

import os
import random
import sys

import pygame

# パスを通す（同ディレクトリにある pyui_dl を使う）
sys.path.insert(0, os.path.dirname(__file__))

from pyui_dl.logic.models import LogicData
from pyui_dl.logic.runtime import LogicRuntime
from pyui_dl.logic.serializer import LogicSerializer
from pyui_dl.ui.widget import Widget
from pyui_dl.utils.serializer import Serializer

# ── 定数 ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 450, 700
FPS = 60
PLAYER_SPEED = 5
COIN_NAMES = ["coin_1", "coin_2", "coin_3"]
BOMB_NAMES = ["bomb_1", "bomb_2"]


def _get_jp_font(size):
    candidates = [
        "pyui_dl/fonts/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return pygame.font.Font(p, size)
    return pygame.font.SysFont(None, size)


def reset_objects(ui_root, runtime):
    """コイン・爆弾をランダム位置にリセット（画面上部）。"""
    for name in COIN_NAMES:
        w = ui_root.find_by_name(name)
        if w:
            w.rel_x = random.randint(20, SCREEN_W - 70)
            w.rel_y = random.randint(-300, -60)
    for name in BOMB_NAMES:
        w = ui_root.find_by_name(name)
        if w:
            w.rel_x = random.randint(20, SCREEN_W - 70)
            w.rel_y = random.randint(-500, -100)
    ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("コインキャッチ ゲーム")
    clock = pygame.time.Clock()
    font_l = _get_jp_font(36)
    font_m = _get_jp_font(22)
    font_s = _get_jp_font(16)

    # ── データ読み込み ─────────────────────────────
    ui_path = os.path.join("data", "coin_catch.json")
    logic_path = os.path.join("data", "logic_coin_catch.json")
    ui_root = Serializer.load_file(ui_path)
    logic = LogicSerializer.load_file(logic_path)
    Widget.debug_mode = False

    ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)

    # ── ランタイム ─────────────────────────────────
    runtime = LogicRuntime(logic, ui_root)
    reset_objects(ui_root, runtime)

    # ── ゲーム状態 ─────────────────────────────────
    # コイン・爆弾の落下速度（ランタイム変数と連動）
    obj_speeds = {name: 0.0 for name in COIN_NAMES + BOMB_NAMES}

    def refresh_speeds():
        base = runtime.get("speed", 2.0)
        for n in COIN_NAMES:
            obj_speeds[n] = base + random.uniform(0, 1.0)
        for n in BOMB_NAMES:
            obj_speeds[n] = base * 0.8 + random.uniform(0, 0.5)

    refresh_speeds()

    # ── メインループ ───────────────────────────────
    while True:
        dt = clock.tick(FPS) / 1000.0

        game_over = runtime.get("game_over", False)

        # ─ イベント処理 ─
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and game_over:
                    runtime.fire("on_click", "btn_restart")
                    reset_objects(ui_root, runtime)
                    refresh_speeds()

        if not game_over:
            # ─ プレイヤー操作 ─
            player = ui_root.find_by_name("player")
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.rel_x = max(0, player.rel_x - PLAYER_SPEED)
            if keys[pygame.K_RIGHT]:
                player.rel_x = min(SCREEN_W - player.width, player.rel_x + PLAYER_SPEED)
            ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)

            # ─ オブジェクトを落下させる ─
            for name in COIN_NAMES + BOMB_NAMES:
                w = ui_root.find_by_name(name)
                if not w:
                    continue
                w.rel_y += obj_speeds[name]
                # 画面下を超えたらリセット（コインを逃した場合）
                if w.rel_y > SCREEN_H:
                    w.rel_x = random.randint(20, SCREEN_W - 70)
                    w.rel_y = random.randint(-300, -60)
            ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)

            # ─ 衝突判定 & ロジック発火 ─
            player_w = ui_root.find_by_name("player")
            for name in COIN_NAMES:
                w = ui_root.find_by_name(name)
                if w and w.rel_y > 0 and player_w.rect.colliderect(w.rect):
                    runtime.fire("on_collide", name, with_tag="player")
                    # 取得後ランダム位置へ
                    w.rel_x = random.randint(20, SCREEN_W - 70)
                    w.rel_y = random.randint(-400, -80)
                    obj_speeds[name] = runtime.get("speed", 2.0) + random.uniform(
                        0, 1.0
                    )
                    ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)

            for name in BOMB_NAMES:
                w = ui_root.find_by_name(name)
                if w and w.rel_y > 0 and player_w.rect.colliderect(w.rect):
                    runtime.fire("on_collide", name, with_tag="player")
                    w.rel_x = random.randint(20, SCREEN_W - 70)
                    w.rel_y = random.randint(-500, -100)
                    obj_speeds[name] = runtime.get("speed", 2.0) * 0.8
                    ui_root.update_layout(0, 0, SCREEN_W, SCREEN_H)

            # ─ スコアに応じてスピードアップ ─
            score = runtime.get("score", 0)
            new_speed = 2.0 + score // 50 * 0.5
            if new_speed != runtime.get("speed", 2.0):
                runtime.set("speed", new_speed)
                refresh_speeds()

            # ─ ライフ 0 でゲームオーバー ─
            if runtime.get("life", 3) <= 0:
                runtime.set("game_over", True)

            # ─ UI ラベル更新 ─
            sl = ui_root.find_by_name("score_label")
            ll = ui_root.find_by_name("life_label")
            if sl and hasattr(sl, "text"):
                sl.text = f"スコア: {runtime.get('score', 0)}"
            if ll and hasattr(ll, "text"):
                life = runtime.get("life", 3)
                ll.text = "♥ " * life + "♡ " * (3 - life)

        # ─ 描画 ─
        screen.fill((20, 20, 40))

        # 背景星（静的装飾）
        rng = random.Random(42)
        for _ in range(60):
            sx = rng.randint(0, SCREEN_W)
            sy = rng.randint(0, SCREEN_H)
            br = rng.randint(100, 200)
            pygame.draw.circle(screen, (br, br, br), (sx, sy), 1)

        ui_root.draw(screen)

        # コイン・爆弾のラベル描画
        for name in COIN_NAMES:
            w = ui_root.find_by_name(name)
            if w and 0 < w.rel_y < SCREEN_H:
                lbl = font_s.render("コイン", True, (255, 230, 80))
                screen.blit(
                    lbl, (w.rect.centerx - lbl.get_width() // 2, w.rect.bottom + 2)
                )
        for name in BOMB_NAMES:
            w = ui_root.find_by_name(name)
            if w and 0 < w.rel_y < SCREEN_H:
                lbl = font_s.render("爆弾", True, (255, 120, 120))
                screen.blit(
                    lbl, (w.rect.centerx - lbl.get_width() // 2, w.rect.bottom + 2)
                )

        # ゲームオーバー画面
        if game_over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            go_surf = font_l.render("ゲームオーバー", True, (255, 80, 80))
            sc_surf = font_m.render(
                f"最終スコア: {runtime.get('score', 0)}", True, (255, 255, 255)
            )
            rst_surf = font_m.render("R キーでリスタート", True, (80, 255, 160))

            screen.blit(go_surf, (SCREEN_W // 2 - go_surf.get_width() // 2, 260))
            screen.blit(sc_surf, (SCREEN_W // 2 - sc_surf.get_width() // 2, 320))
            screen.blit(rst_surf, (SCREEN_W // 2 - rst_surf.get_width() // 2, 370))

        # 操作説明（常時表示）
        if not game_over:
            hint = font_s.render("← → キーで移動", True, (150, 150, 200))
            screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 30))

        pygame.display.flip()


if __name__ == "__main__":
    main()
