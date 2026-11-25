# Light Lights

コンソールで遊ぶローグライト風テキストRPGです。

Inscryption のローグライトパートや Arknights のローグライトに影響を受けた、リスクと選択を重視するゲームです。

村の郵便屋から手紙を預かり、8区画の街道を抜けて町へ届けます。

## 遊び方

```bash
python main.py
```

地図は上から下へ読みます。@ が現在地、* が歩いた場所です。線でつながる地点にだけ進めます。最初の分かれ道では戦闘か無料イベントを選べます。町の門で最後の戦闘を切り抜ければ配達成功です。

戦闘は a で攻撃、h でかばん、r で逃走。かばんでは道具の説明と回復量を見て番号を選びます。0 で閉じるとターンを消費しません。勝利時の経験点で能力を強化でき、所持金は街道の施設で使えます。

## 敵・道具の編集

- [data/enemies.json](data/enemies.json) に敵の名前、初登場の一言、基礎 HP・攻撃・防御・素早さを記入します。配列に1件追加すると抽選対象になります。区画ごとの補正は `config.py` にあります。
- [data/items.json](data/items.json) に一意のキーと、表示名・説明・回復量（`heal`）・初期個数（`starting_count`）を記入します。初期個数0の道具も行商人から入手できます。編集後にゲームを起動し直してください。

## コード構成

- [main.py](main.py): エントリポイント・メインメニュー
- [config.py](config.py): ゲームバランス定数の一元管理
- [models.py](models/): 純粋データ構造（Hero, Enemy, RunResult など）
- [ui.py](ui.py): 画面制御・入力ユーティリティ・PromptChoice 型
- [enemies.py](enemies.py): 敵テンプレート定義・階層スケーリング・敵生成
- [battle.py](battle.py): ターン制戦闘エンジン
- [events.py](events.py): イベントクラス群とイベント発火
- [shop.py](shop.py): ショップ・恒久強化・主人公構築
- [route.py](route.py): 街道マップの生成・ダイアグラム表示・分岐選択
- [game.py](game.py): 1ランの探索オーケストレーション
- [ARCHITECTURE.md](ARCHITECTURE.md): アーキテクチャドキュメント
