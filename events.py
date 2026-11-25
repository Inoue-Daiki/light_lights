from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from config import EVENT_TRIGGER_CHANCE, FREE_EVENT_CHANCE
from items import DATA_DIR, ITEMS
from models import EventOption, Hero, RunState
from ui import PromptChoice, clear_screen


RISK_OPTIONS = [
    EventOption("1", "低", 6, 0.9, 1),
    EventOption("2", "中", 10, 0.65, 2),
    EventOption("3", "高", 16, 0.4, 4),
]


def _grant_reward(
    hero: Hero, run_state: RunState, reward_kind: str, reward_amount: int
) -> None:
    """reward_kind: "heal" | "gold" | "potion" | "attack" | "defense" | "speed" """
    if reward_kind == "gold":
        run_state.gold += reward_amount
        print(f"所持金を{reward_amount}獲得した。")
        return
    if reward_kind == "heal":
        healed = hero.heal(reward_amount)
        print(f"HPが{healed}回復した。")
        return
    if reward_kind == "potion":
        key = random.choice(list(ITEMS))
        hero.bag[key] = hero.bag.get(key, 0) + reward_amount
        print(f"{ITEMS[key].name}を{reward_amount}個獲得した。")
        return
    if reward_kind == "attack":
        hero.attack += reward_amount
        print(f"攻撃力が{reward_amount}上がった。")
        return
    if reward_kind == "speed":
        hero.speed += reward_amount
        print(f"素早さが{reward_amount}上がった。")
        return
    hero.defense += reward_amount
    print(f"防御力が{reward_amount}上がった。")


# ── イベント基底 ──


class Event(ABC):
    name: str
    diagram_label: str

    @abstractmethod
    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        raise NotImplementedError


# ── テンプレート ──


@dataclass(frozen=True)
class FreeEventTemplate(Event):
    """リスクなし・コストなしのボーナスイベント。

    新しい無料イベントを追加するには data/events.json の free にエントリを追加する。
    reward_kind: "heal" | "gold" | "potion" | "attack" | "defense" | "speed"
    """

    name: str
    diagram_label: str
    flavor_text: str
    reward_kind: str
    min_amount: int
    max_amount: int

    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        clear_screen()
        print(f"\nボーナスイベント: {self.name}")
        amount = random.randint(self.min_amount, self.max_amount)
        print(self.flavor_text)
        _grant_reward(hero, run_state, self.reward_kind, amount)


@dataclass(frozen=True)
class PaidEventTemplate(Event):
    """所持金を払ってリターンを狙うリスク型イベント。

    新しい有料イベントを追加するには data/events.json の paid にエントリを追加する。
    reward_kind: "heal" | "gold" | "potion" | "attack" | "defense" | "speed"
    """

    name: str
    diagram_label: str
    description: str
    reward_kind: str

    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        clear_screen()
        print(f"\nイベント: {self.name}")
        print(self.description)
        print("1: 低リスク  2: 中リスク  3: 高リスク  4: 見送る")
        print("高リスクほど報酬量は増えるが、失敗して支払いだけ失う確率が上がる。")

        valid_choices = {opt.key for opt in RISK_OPTIONS} | {"4"}
        while True:
            choice = prompt_choice("選択: ", valid_choices)
            if choice == "4":
                print("イベントを見送った。")
                return

            option = next(opt for opt in RISK_OPTIONS if opt.key == choice)
            if run_state.gold < option.cost:
                print("所持金が足りない。別の選択をしてください。")
                continue

            run_state.gold -= option.cost
            print(f"{option.label}リスクに挑戦。所持金を{option.cost}支払った。")
            if random.random() <= option.success_rate:
                amount = option.amount * 4 if self.reward_kind == "heal" else option.amount
                _grant_reward(hero, run_state, self.reward_kind, amount)
            else:
                print("失敗した。支払った所持金だけを失った。")
            return


# ── イベント一覧 ──
_records = json.loads((DATA_DIR / "events.json").read_text(encoding="utf-8"))
FREE_EVENT_TEMPLATES = [FreeEventTemplate(**entry) for entry in _records["free"]]
PAID_EVENT_TEMPLATES = [PaidEventTemplate(**entry) for entry in _records["paid"]]


# ── 公開API ──


def plan_event() -> Event | None:
    if random.random() >= EVENT_TRIGGER_CHANCE:
        return None
    if random.random() < FREE_EVENT_CHANCE:
        return random.choice(FREE_EVENT_TEMPLATES)
    return random.choice(PAID_EVENT_TEMPLATES)


def run_event(
    event: Event,
    hero: Hero,
    run_state: RunState,
    prompt_choice: PromptChoice,
) -> None:
    event.trigger(hero, run_state, prompt_choice)
