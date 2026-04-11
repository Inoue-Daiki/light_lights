"""敵テンプレート定義と敵生成ロジック。

新しい敵を追加するには ENEMY_TEMPLATES にエントリを追加するだけでよい。
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
    EnemyTemplate("Slime",    hp=10, attack= 6, defense=1, speed=4),
    EnemyTemplate("Bandit",   hp=14, attack= 7, defense=2, speed=5),
    EnemyTemplate("Skeleton", hp=18, attack= 9, defense=3, speed=4),
    EnemyTemplate("Wolf",     hp=16, attack=10, defense=2, speed=7),
    EnemyTemplate("Knight",   hp=22, attack=11, defense=4, speed=3),
]


def create_enemy(floor: int) -> Enemy:
    """ランダムにテンプレートを選び、階層スケーリング済みの Enemy を返す。"""
    return random.choice(ENEMY_TEMPLATES).create(floor)
