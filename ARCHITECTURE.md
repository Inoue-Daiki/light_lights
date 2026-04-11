# Light Lights — アーキテクチャドキュメント

## 改善の概要

本リファクタリングで行った変更と、その設計意図をまとめる。

---

## 1. モジュール構成（改善後）

```
main.py          エントリポイント・メインメニュー
config.py    [新] ゲームバランス定数の一元管理
models.py        データ構造（Hero, Enemy, RunState など）
ui.py            画面制御・入力ユーティリティ・共通型エイリアス
battle.py        敵生成・ターン制戦闘ロジック
events.py        イベント定義・イベント発火
progression.py   探索進行・ショップ・恒久強化
```

### 依存関係（上流 → 下流）

```
config.py          ← 定数のみ。他モジュールに依存しない
    ↑
models.py          ← config の定数を参照
    ↑
ui.py              ← 外部依存なし（PromptChoice 型エイリアスを公開）
    ↑
battle.py          ← config, models, ui
events.py          ← config, models, ui
    ↑
progression.py     ← battle, events, config, models, ui
    ↑
main.py            ← models, progression, ui
```

ポイント: **循環参照なし**。依存は常に一方向。

---

## 2. 改善内容の詳細

### 2.1 `config.py` の新設 — マジックナンバーの撲滅

**問題**: 基礎HP `30`、攻撃力 `8`、回復量 `10`、逃走ペナルティ率 `0.3` などの数値が
`battle.py`・`progression.py` に散在し、バランス調整時に変更漏れのリスクがあった。

**対策**: すべてのゲームバランス定数を `config.py` に集約。

| カテゴリ | 定数例 | 旧所在 |
|---|---|---|
| 主人公基礎値 | `BASE_HP`, `BASE_ATTACK`, `BASE_DEFENSE` | `progression.py` 内リテラル |
| 恒久強化係数 | `HP_PER_UPGRADE`, `ATTACK_PER_UPGRADE` | `progression.py` 内リテラル |
| 戦闘バランス | `MIN_DAMAGE`, `DAMAGE_VARIANCE_*` | `battle.py` 内リテラル |
| 敵スケーリング | `ENEMY_HP_PER_FLOOR` 他 | `battle.py` 内リテラル |
| イベント確率 | `EVENT_TRIGGER_CHANCE`, `FREE_EVENT_CHANCE` | `events.py` 内リテラル |
| 踏破報酬 | `CLEAR_BONUS_SHARDS` | `progression.py` 内リテラル |

**効果**: バランス調整は `config.py` を1ファイル変更するだけで完結する。

---

### 2.2 `PromptChoice` 型エイリアスの一元化

**問題**: `Callable[[str, set[str]], str]` の型エイリアスが `battle.py`・`events.py`・
`progression.py` の3箇所で重複定義されていた。

**対策**: `ui.py` に `PromptChoice` を定義し、各モジュールはそこからインポート。

**効果**: 型の一貫性を保証。シグネチャ変更時の修正が1箇所で済む。

---

### 2.3 `os.system` の排除（セキュリティ改善）

**問題**: `ui.py` の `clear_screen()` が `os.system("cls")` を使用。
`os.system` はシェルを経由するため、原理上コマンドインジェクションのリスクがある。

**対策**: `subprocess.run(["cmd", "/c", "cls"])` に変更。
引数リスト形式はシェル解釈を介さないため安全。

---

### 2.4 `run_once` の分割（単一責任の原則）

**問題**: `progression.py` の `run_once` が探索ループ全体（階層表示・イベント・戦闘・
ショップ・死亡処理・踏破処理）を1関数で担っていた。約50行。

**対策**: 戦闘階の処理を `_handle_battle_floor()` に抽出。

```
run_once()
  ├── 階層ループ
  │     ├── show_status() + wait
  │     ├── イベント階 → run_event()
  │     └── 戦闘階 → _handle_battle_floor()
  │           ├── battle()
  │           ├── shop_phase() （勝利時）
  │           └── 死亡処理
  └── 踏破処理
```

**効果**: 各関数の責務が明確になり、テスト・拡張が容易に。

---

### 2.5 デッドコードの除去

**問題**: `events.py` の `trigger_event()` はどこからも呼ばれていなかった
（`progression.py` が `plan_event()` + `run_event()` を直接使用）。

**対策**: 削除。

---

### 2.6 不要な `random.seed()` の除去

**問題**: `main.py` で `random.seed()` を引数なしで呼んでいた。
Python の `random` モジュールは import 時に自動シードされるため冗長。

**対策**: 削除。

---

### 2.7 `del` パターンの除去（コード品質）

**問題**: `events.py` の `FreeEvent` サブクラスで
`del prompt_choice, run_state` のように未使用引数を明示削除していた。
これはリンター警告の回避策だが、可読性を下げる。

**対策**: `del` 文を削除。インターフェース上必要なパラメータは
抽象メソッドのシグネチャとして残すのが正しい設計。

---

## 3. 現在のモジュール別責務

| モジュール | 責務 | 主要な公開関数/クラス |
|---|---|---|
| `config.py` | ゲーム定数の一元管理 | 全定数 |
| `models.py` | データ構造のみ（ロジックは最小限） | `Hero`, `Enemy`, `RunState`, `PermanentUpgrades`, `ShopUpgrade`, etc. |
| `ui.py` | 画面制御・入力型 | `clear_screen()`, `wait_for_enter()`, `PromptChoice` |
| `battle.py` | 戦闘の実行と敵生成 | `battle()`, `create_enemy()` |
| `events.py` | イベントの定義と発火 | `Event` 階層, `plan_event()`, `run_event()` |
| `progression.py` | 探索全体のオーケストレーション | `run_once()`, `shop_phase()`, `build_hero()` |
| `main.py` | エントリポイント・メニューUI | `main()`, `prompt_choice()` |

---

## 4. 設計原則

1. **Single Source of Truth**: 定数は `config.py`、型は定義元モジュール、データ構造は `models.py`
2. **単方向依存**: 循環 import を避け、レイヤー構造を維持
3. **関数の単一責任**: 1関数 = 1つの明確な仕事
4. **安全なシステムコール**: `os.system` ではなく `subprocess.run` を使用
5. **DRY（Don't Repeat Yourself）**: 型エイリアスや定数の重複を排除

---

## 5. 今後の拡張ガイド

### 新しい敵を追加する
`battle.py` の `ENEMY_TEMPLATES` にテンプレートを追加するだけ。

### ゲームバランスを調整する
`config.py` の該当定数を変更。コード変更は不要。

### 新しいイベントを追加する
1. `events.py` で `FreeEvent` または `PaidEvent` を継承したクラスを作成
2. `FREE_EVENTS` または `PAID_EVENTS` リストに追加
3. `get_event_diagram_label()` にダイアグラム用ラベルを追加

### ボス戦を追加する
1. `config.py` にボス関連定数を追加
2. `battle.py` に `create_boss()` を追加
3. `progression.py` の階層ループで最終階をボス戦に分岐

### セーブ機能を追加する
`PermanentUpgrades` と `soul_shards` を JSON でシリアライズする
`save.py` モジュールを新設し、`main.py` から呼び出す。
