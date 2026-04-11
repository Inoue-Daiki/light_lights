# Light Lights — アーキテクチャドキュメント

## モジュール構成

```
config.py    ゲームバランス定数の一元管理（他モジュールに依存しない最上流）
models.py    純粋なデータ構造（Hero, Enemy, RunState, RunResult など）
ui.py        画面制御・入力ユーティリティ・PromptChoice 型エイリアス
enemies.py   敵テンプレート定義・階層スケーリング・敵生成
battle.py    ターン制戦闘エンジン
events.py    イベント階層クラスとイベント発火
shop.py      ショップ・恒久強化・主人公構築
route.py     ルート木の生成・ダイアグラム表示・分岐選択
game.py      1ランの探索ループ（オーケストレーション）
main.py      エントリポイント・メインメニュー
```

### 依存グラフ（上流 → 下流）

```
config.py          定数のみ。依存なし
    ↑
models.py          config
    ↑
ui.py              stdlib のみ
    ↑
enemies.py         config, models
battle.py          config, models, ui
events.py          config, models, ui
shop.py            config, models, ui
    ↑
route.py           config, events, models, ui
    ↑
game.py            battle, config, enemies, events, models, route, shop, ui
    ↑
main.py            game, models, shop, ui
```

**循環参照なし** — 依存は常に一方向。

---

## 設計原則

1. **Single Source of Truth** — 定数は `config.py`、型は定義元モジュール、データ構造は `models.py`
2. **単方向依存** — 循環 import を避け、レイヤー構造を維持
3. **単一責任** — 1モジュール = 1つの明確な領域、1関数 = 1つの仕事
4. **安全なシステムコール** — `os.system` ではなく `subprocess.run` を使用
5. **DRY** — 型エイリアスや定数の重複を排除

---

## モジュール別責務

| モジュール | 責務 | 主な公開API |
|---|---|---|
| `config.py` | ゲーム定数の一元管理 | 全定数 |
| `models.py` | 純粋データ構造 | `Hero`, `Enemy`, `RunState`, `RunResult`, `PermanentUpgrades` |
| `ui.py` | 画面制御・入力型 | `clear_screen()`, `wait_for_enter()`, `PromptChoice` |
| `enemies.py` | 敵テンプレート・生成 | `EnemyTemplate`, `ENEMY_TEMPLATES`, `create_enemy()` |
| `battle.py` | 戦闘エンジン | `battle()` |
| `events.py` | イベント定義と発火 | `Event` 階層, `plan_event()`, `run_event()` |
| `shop.py` | ショップ・恒久強化・主人公構築 | `shop_phase()`, `build_hero()`, `get_upgrade_summary()` |
| `route.py` | ルート木・ダイアグラム・分岐 | `build_branch_options()`, `show_status()`, `choose_next_route_with_status()` |
| `game.py` | 1ランのオーケストレーション | `run_once()` |
| `main.py` | エントリポイント・メインメニュー | `main()` |

---

## 主な改善内容

### God Module の分割（旧 `progression.py` → `shop.py` + `route.py` + `game.py`）

旧 `progression.py` は ~370行でショップ・ルート生成・ダイアグラム表示・分岐選択・
探索ループ・死亡処理を全て担っていた。3つの単一責任モジュールに分割：

- **`shop.py`** — 主人公構築 (`build_hero`)、恒久強化の購入と表示、リセット処理
- **`route.py`** — ルート木の再帰的生成、ダイアグラムのフォーマット、分岐UI
- **`game.py`** — 探索ループの制御フロー（イベント/戦闘/踏破の振り分けのみ）

### `diagram_label` のクラス属性化

旧：`get_event_diagram_label()` がクラス名文字列を辞書で引く脆いパターン。
新：各 `Event` サブクラスに `diagram_label` クラス属性を持たせ、直接参照。

### `RunResult` 型の導入

旧：`run_once()` → `tuple[bool, int]`（意味が不明確）。
新：`RunResult(won=..., soul_shards=...)` で意味が自明。

### 戦闘ループの整理

`battle()` から `_show_battle_status()` と `_victory_reward()` を抽出し、
ループ本体をアクション判定・ターン実行のみに集中させた。

### 不要コードの除去

- `reset_hero_status()` — 死亡後にヒーローは参照されないため不要だった
- `get_event_diagram_label()` — クラス属性に置き換え
- 旧 `progression.py` の重複ロジック

---

## 拡張ガイド

### 新しい敵を追加する
`enemies.py` の `ENEMY_TEMPLATES` にエントリを追加。

### ゲームバランスを調整する
`config.py` の該当定数を変更。コード変更は不要。

### 新しいイベントを追加する
1. `events.py` の `FREE_EVENT_TEMPLATES` または `PAID_EVENT_TEMPLATES` にエントリを追加する
2. 無料イベントは `FreeEventTemplate`、有料イベントは `PaidEventTemplate` を使用する

### ボス戦を追加する
1. `config.py` にボス関連定数を追加
2. `battle.py` に `create_boss()` を追加
3. `game.py` の階層ループで最終階をボス戦に分岐

### セーブ機能を追加する
`PermanentUpgrades` と `soul_shards` を JSON でシリアライズする
`save.py` モジュールを新設し、`main.py` から呼び出す。
