# エディタ操作ガイド

---

## 共通操作

| キー | 動作 |
|------|------|
| `Ctrl+E` | デザインモード ↔ ロジックモード 切替 |
| `Ctrl+S` | UIデザイン + ロジック を両方保存 |

右上のインジケーターで現在のモードを確認できます。

---

## デザインモード

### 選択・移動・リサイズ

| 操作 | 動作 |
|------|------|
| クリック | Widgetを選択 |
| ドラッグ | AbsoluteLayout内のWidgetを移動 |
| 右下ハンドルをドラッグ | リサイズ |
| `Enter` / `Esc` | 選択解除 |
| `TAB` | プロパティHUD 表示/非表示 |

### Widget追加

| キー | 追加されるWidget |
|------|------|
| `Ctrl+B` | Button |
| `Ctrl+H` | HBox |
| `Ctrl+V` | VBox |
| `Ctrl+L` | AbsoluteLayout |
| `Ctrl+C` | Circle |
| `Ctrl+I` | Image（ファイル選択ダイアログ） |

> 追加先は「選択中がレイアウトならその中」、「それ以外なら親レイアウト」になります。

### コピー＆ペースト

| キー | 動作 |
|------|------|
| `Ctrl+Shift+C` | 選択中Widgetをコピー |
| `Ctrl+Shift+V` | コピーしたWidgetを貼り付け（名前に`_copy`が付く） |
| `Ctrl+M` | ミラーコピー（AbsoluteLayout内で左右反転した位置に複製） |

### 見た目の編集

| キー | 動作 |
|------|------|
| `Ctrl+K` | 色をカラーピッカーで変更 |
| `Ctrl+R` | 15°回転 |
| `Ctrl+G` | Imageの背景ON/OFF |
| `Shift+L` | アルファ値 +15 |
| `Shift+K` | アルファ値 −15 |
| `Shift+R` | 角丸(radius) +5（55でリセット） |
| `Shift+P` | 高さ +5 |
| `Shift+O` | 高さ −5 |
| `Shift+[` | 幅 +5 |
| `Shift+]` | 幅 −5 |
| `Shift+矢印` | 1pxずつ移動（AbsoluteLayout内） |

### テキスト・ID編集（INSERTモード）

`i` キーでINSERTモードに入ります。選択枠がオレンジ色に変わります。

| キー | 動作 |
|------|------|
| `i` | INSERTモードへ（TEXTを編集） |
| `Ctrl+N` | 編集対象を TEXT ↔ ID（name）で切替 |
| 文字入力 | カーソル位置に追加 |
| `Backspace` | 1文字削除 |
| `Enter` / `Esc` | NORMALモードへ戻る |

### 当たり判定

| キー | 動作 |
|------|------|
| `Ctrl+J` | collision_tag をサイクル（none → wall → floor → obstacle → player → trigger） |
| `Ctrl+T` | collision_shape をサイクル（rect ↔ circle） |
| `Ctrl+F` | 当たり判定プレビューオーバーレイ ON/OFF |

タグごとの色：

| タグ | 色 |
|------|----|
| wall | 赤 |
| floor | オレンジ |
| obstacle | 紫 |
| player | 水色 |
| trigger | 緑 |

### 並び順・削除

| キー | 動作 |
|------|------|
| `Ctrl+←` / `Ctrl+→` | HBox内で順番を入れ替え |
| `Ctrl+↑` / `Ctrl+↓` | VBox内で順番を入れ替え |
| `d` | 選択中Widgetを削除 |

---

## ロジックモード（Ctrl+E で切替）

デザインモードで選択中のWidgetに「イベント → 条件 → アクション」のルールを設定します。

### ルール一覧画面

| キー | 動作 |
|------|------|
| `↑` / `↓` | ルールを選択 |
| `a` | 新規ルール追加 |
| `d` | 選択中ルールを削除 |
| `c` | 選択中ルールをコピー |
| `e` または `Enter` | 詳細編集へ |
| `Esc` | ロジックモード終了 |

### ルール詳細編集（e で入る）

`Tab` / `Shift+Tab` で **EVENT → 条件 → アクション** のセクションを移動します。

---

#### EVENTセクション

| キー | 動作 |
|------|------|
| `↑` / `↓` | 行を選択 |
| `Enter` または `→` | イベント種類をサイクル |
| `Enter`（パラメータ行） | テキスト入力で値を直接指定 |

---

#### 条件セクション

| キー | 動作 |
|------|------|
| `a` | 条件を追加 |
| `d` | 選択中の条件を削除 |
| `↑` / `↓` | 条件を選択 |
| `Enter` | **変数名**をテキスト入力 |
| `o` | **演算子**をテキスト入力（候補がHUDに表示されます） |
| `Shift+Enter` | 演算子をサイクル（==, !=, >, >=, <, <=） |
| `Ctrl+Enter` | **値**をテキスト入力 |

---

#### アクションセクション

| キー | 動作 |
|------|------|
| `a` | アクションを追加 |
| `d` | 選択中のアクションを削除 |
| `↑` / `↓` | アクションを選択 |
| `t` | **アクション種類**をテキスト入力（候補がHUDに表示されます） |
| `Shift+Enter` | アクション種類をサイクル |
| `Enter` または `1` | パラメータ1をテキスト入力 |
| `2` | パラメータ2をテキスト入力 |
| `3` | パラメータ3をテキスト入力 |

---

#### テキスト入力中（INPUT状態）

| キー | 動作 |
|------|------|
| 文字入力 | バッファに追加 |
| `Backspace` | 1文字削除 |
| `Enter` | 確定 |
| `Esc` | キャンセル（元の値に戻る） |

> 演算子・アクション種類の入力中は、入力に一致する**候補一覧**がHUDに表示されます。

---

## 利用可能なイベント

| イベント | パラメータ | 説明 |
|----------|-----------|------|
| `on_click` | — | クリック |
| `on_collide` | `with_tag` | collision_tagとの衝突 |
| `on_enter` | `area` | エリア進入 |
| `on_exit` | `area` | エリア退出 |
| `on_var_change` | `var` | 変数変化 |
| `on_timer` | `delay` | 指定秒ごと |
| `on_game_start` | — | ゲーム開始時 |
| `on_state_enter` | `state` | ステート突入 |

---

## 利用可能なアクション

| アクション | パラメータ | 説明 |
|-----------|-----------|------|
| `set_var` | var, op, value | 変数操作（=, +=, -=, *=, /=）|
| `set_visible` | target, visible | 表示/非表示切替 |
| `move_to` | target, x, y | 絶対座標へ移動 |
| `move_by` | target, dx, dy | 相対移動 |
| `play_anim` | target, anim | アニメ再生（要コールバック）|
| `change_scene` | scene | シーン遷移（要コールバック）|
| `spawn` | template, x, y | Widget生成（要コールバック）|
| `destroy` | target | Widget削除 |
| `set_state` | target, state | ステート変更（要コールバック）|
| `play_sound` | sound | 効果音（要コールバック）|
| `emit_event` | event, target | 別イベントを発火 |

---

## Widgetのプロパティ一覧

TABキーで表示されるHUDには、選択中Widgetの以下のプロパティがリアルタイムで表示されます。

### 全Widgetに共通

| プロパティ | 説明 |
|-----------|------|
| `type` | Widgetの種類（Button, Image, Circle, VBox, HBox, AbsoluteLayout）|
| `name` | ID（ロジックのtarget指定に使う） |
| `pos` | レイアウト内の相対座標 (rel_x, rel_y) |
| `size` | 幅・高さ (width, height) |
| `color` | RGB色 |
| `alpha` | 透明度（0〜255）|
| `angle` | 回転角度（度）|
| `radius` | 角丸・円の半径 |
| `weight` | VBox/HBox内での占有比率 |
| `padding` | 子要素との余白 |
| `collision_tag` | 当たり判定タグ |
| `collision_shape` | 当たり判定形状（rect / circle）|

### Button・Image 追加プロパティ

| プロパティ | 説明 |
|-----------|------|
| `text` | 表示テキスト |

### Image 追加プロパティ

| プロパティ | 説明 |
|-----------|------|
| `path` | 画像ファイルパス |
| `show_bg` | 背景色の表示ON/OFF |
