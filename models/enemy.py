from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Enemy:
    name: str
    hp: int
    attack: int
    defense: int
    speed: int
    shard_reward: int
    gold_reward: int

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass(frozen=True)
class BattleReward:
    soul_shards: int
    gold: int
    escaped: bool = False
