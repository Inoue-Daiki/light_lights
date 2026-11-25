"""敵テンプレート定義と敵生成ロジック。

新しい敵を追加するには content/enemies.json にエントリを追加するだけでよい。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from config import (
    ENEMY_ATTACK_PER_FLOOR,
    ENEMY_DEFENSE_PER_FLOOR_DIVISOR,
    ENEMY_GOLD_BASE,
    ENEMY_GOLD_PER_FLOOR,
    ENEMY_HP_PER_FLOOR,
    ENEMY_SHARD_BASE,
    ENEMY_SHARD_PER_FLOOR,
    ENEMY_SPEED_PER_FLOOR_DIVISOR,
)
from models import Enemy
from content_data import load_content


@dataclass(frozen=True)
class EnemyTemplate:
    """敵の基礎スペックを定義するテンプレート。

    create(floor) を呼ぶと、階層スケーリング済みの Enemy インスタンスを返す。
    新しい敵種を追加する場合は ENEMY_TEMPLATES にこのクラスのインスタンスを追加する。
    """

    name: str
    hp: int
    attack: int
    defense: int
    speed: int

    def create(self, floor: int) -> Enemy:
        """階層に応じてスケーリングした Enemy を生成する。"""
        return Enemy(
            name=self.name,
            hp=self.hp + floor * ENEMY_HP_PER_FLOOR,
            attack=self.attack + floor * ENEMY_ATTACK_PER_FLOOR,
            defense=self.defense + floor // ENEMY_DEFENSE_PER_FLOOR_DIVISOR,
            speed=self.speed + floor // ENEMY_SPEED_PER_FLOOR_DIVISOR,
            shard_reward=ENEMY_SHARD_BASE + floor * ENEMY_SHARD_PER_FLOOR,
            gold_reward=ENEMY_GOLD_BASE + floor * ENEMY_GOLD_PER_FLOOR,
        )


# ── 敵テンプレート一覧 ──
# 新しい敵を追加するにはここにエントリを追加する。
ENEMY_TEMPLATES: list[EnemyTemplate] = [
    EnemyTemplate(**entry) for entry in load_content("enemies.json")
]


def create_enemy(floor: int) -> Enemy:
    """ランダムにテンプレートを選び、階層スケーリング済みの Enemy を返す。"""
    return random.choice(ENEMY_TEMPLATES).create(floor)
