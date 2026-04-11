from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunState:
    soul_shards: int = 0
    gold: int = 0


@dataclass(frozen=True)
class RunResult:
    won: bool
    soul_shards: int
