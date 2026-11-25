from __future__ import annotations

from dataclasses import dataclass, field

from items import starting_bag


@dataclass
class PermanentUpgrades:
    hp: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0


@dataclass
class Hero:
    max_hp: int
    hp: int
    attack: int
    defense: int
    speed: int
    bag: dict[str, int] = field(default_factory=starting_bag)

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
