from __future__ import annotations

from dataclasses import dataclass

from config import BASE_POTIONS


@dataclass
class PermanentUpgrades:
    hp: int = 0
    attack: int = 0
    defense: int = 0


@dataclass
class RunState:
    soul_shards: int = 0
    gold: int = 0


@dataclass(frozen=True)
class EnemyTemplate:
    name: str
    hp: int
    attack: int
    defense: int


@dataclass(frozen=True)
class BattleReward:
    soul_shards: int
    gold: int
    escaped: bool = False


@dataclass(frozen=True)
class EventOption:
    key: str
    label: str
    cost: int
    success_rate: float
    amount: int


@dataclass(frozen=True)
class ShopUpgrade:
    key: str
    title: str
    cost: int
    field_name: str
    field_gain: int
    hero_gain: int
    preview_text: str
    success_message: str


@dataclass
class Hero:
    max_hp: int
    hp: int
    attack: int
    defense: int
    potions: int = BASE_POTIONS

    def is_alive(self) -> bool:
        return self.hp > 0

    def heal(self, amount: int) -> int:
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def take_damage(self, raw_damage: int) -> int:
        actual = max(0, raw_damage)
        self.hp = max(0, self.hp - actual)
        return actual


@dataclass
class Enemy:
    name: str
    hp: int
    attack: int
    defense: int
    shard_reward: int
    gold_reward: int

    def is_alive(self) -> bool:
        return self.hp > 0