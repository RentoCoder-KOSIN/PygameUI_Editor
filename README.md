# pyui_dl v1.0.0

Pygame用のUIフレームワーク。ビジュアルエディタでレイアウトを組み、ロジックエディタでイベント駆動のルールを定義し、ランタイムでゲームに組み込めます。

> 操作方法は [EDITOR_OPERATIONS.md](EDITOR_OPERATIONS.md) を参照してください。

---

## セットアップ

```bash
pip install -e .
```

---

## 起動

```bash
# エディタ（幅・高さは省略可）
pyui <ファイル名> <幅> <高さ>

# 例
pyui coin_catch 450 700
```

`data/<ファイル名>.json` と `data/logic_<ファイル名>.json` が自動で読み書きされます。ファイルが存在しない場合は新規作成されます。

---

## ファイル構成

```
data/
  coin_catch.json            ← UIデザイン（エディタで編集）
  logic_coin_catch.json      ← ロジック定義（エディタで編集）

coin_catch_game.py           ← サンプルゲーム本体

pyui_dl/
  ui/
    widget.py      ← Widgetベースクラス・当たり判定ヘルパー
    button.py      ← Button
    image.py       ← Image
    shapes.py      ← Circle
    layout.py      ← VBox / HBox / AbsoluteLayout
  logic/
    models.py      ← データ構造（イベント・アクション定義）
    serializer.py  ← JSON保存/読み込み
    editor.py      ← ロジックエディタUI
    runtime.py     ← ゲーム組み込み用ランタイム
  editor/
    selector.py    ← デザインエディタUI
  utils/
    serializer.py  ← UIのJSON保存/読み込み
    collision.py   ← 当たり判定ユーティリティ
```

---

## ゲームへの組み込み方

```python
from pyui_dl.logic.runtime import LogicRuntime
from pyui_dl.logic.serializer import LogicSerializer
from pyui_dl.utils.serializer import Serializer

# ロード
ui_root = Serializer.load_file("data/my_game.json")
logic   = LogicSerializer.load_file("data/logic_my_game.json")
runtime = LogicRuntime(logic, ui_root)

# 毎フレーム（タイマーイベント更新）
runtime.tick(dt)

# イベント発火
runtime.fire("on_click",   "btn_start")
runtime.fire("on_collide", "player", with_tag="enemy")

# 変数の読み書き
hp = runtime.get("hp", default=100)
runtime.set("hp", hp - 10)

# カスタムアクションへの対応（change_scene / play_anim など）
def on_change_scene(act, source, rt):
    load_scene(act["scene"])

runtime.on_action("change_scene", on_change_scene)
```

---

## ロジックJSON の構造

```json
{
  "global_vars": {
    "hp": 100,
    "score": 0
  },
  "widget_rules": {
    "player": [
      {
        "id": "abc123",
        "label": "ダメージ処理",
        "event": { "type": "on_collide", "with_tag": "enemy" },
        "conditions": [
          { "var": "hp", "op": ">", "value": 0 }
        ],
        "actions": [
          { "type": "set_var",   "var": "hp", "op": "-=", "value": 10 },
          { "type": "play_anim", "target": "player", "anim": "hurt" }
        ]
      }
    ]
  }
}
```

---

## イベント一覧

| イベント | パラメータ | 説明 |
|----------|-----------|------|
| `on_click` | — | クリック |
| `on_collide` | `with_tag` | 指定タグのWidgetと衝突 |
| `on_enter` | `area` | エリアに進入 |
| `on_exit` | `area` | エリアから退出 |
| `on_var_change` | `var` | 変数が変化 |
| `on_timer` | `delay` | 指定秒ごとに発火 |
| `on_game_start` | — | ゲーム開始時 |
| `on_state_enter` | `state` | 指定ステートに突入 |

---

## アクション一覧

| アクション | パラメータ | 説明 |
|-----------|-----------|------|
| `set_var` | `var`, `op`, `value` | 変数操作（`=` `+=` `-=` `*=` `/=`）|
| `set_visible` | `target`, `visible` | Widgetの表示/非表示 |
| `move_to` | `target`, `x`, `y` | 絶対座標へ移動 |
| `move_by` | `target`, `dx`, `dy` | 相対移動 |
| `play_anim` | `target`, `anim` | アニメ再生（要コールバック）|
| `change_scene` | `scene` | シーン遷移（要コールバック）|
| `spawn` | `template`, `x`, `y` | Widgetを生成（要コールバック）|
| `destroy` | `target` | Widgetを削除 |
| `set_state` | `target`, `state` | ステート変更（要コールバック）|
| `play_sound` | `sound` | 効果音再生（要コールバック）|
| `emit_event` | `event`, `target` | 別のイベントを発火 |
