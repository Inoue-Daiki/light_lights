from __future__ import annotations

from dataclasses import dataclass


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
