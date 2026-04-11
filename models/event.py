from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventOption:
    key: str
    label: str
    cost: int
    success_rate: float
    amount: int
