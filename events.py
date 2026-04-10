from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable

from models import EventOption, Hero, RunState


PromptChoice = Callable[[str, set[str]], str]


RISK_OPTIONS = [
    EventOption("1", "低", 6, 0.9, 1),
    EventOption("2", "中", 10, 0.65, 2),
    EventOption("3", "高", 16, 0.4, 4),
]


def grant_event_reward(hero: Hero, reward_kind: str, reward_amount: int) -> None:
    if reward_kind == "heal":
        healed = hero.heal(reward_amount)
        print(f"HPが{healed}回復した。")
        return
    if reward_kind == "potion":
        hero.potions += reward_amount
        print(f"回復薬を{reward_amount}個獲得した。")
        return
    if reward_kind == "attack":
        hero.attack += reward_amount
        print(f"攻撃力が{reward_amount}上がった。")
        return
    hero.defense += reward_amount
    print(f"防御力が{reward_amount}上がった。")


class Event(ABC):
    name: str

    @abstractmethod
    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        raise NotImplementedError


class FreeEvent(Event):
    pass


class BonusHealEvent(FreeEvent):
    name = "小さな幸運"

    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        del prompt_choice, run_state
        print(f"\nボーナスイベント: {self.name}")
        heal_amount = random.randint(6, 12)
        healed = hero.heal(heal_amount)
        print(f"澄んだ泉を見つけた。HPが{healed}回復した。")


class BonusGoldEvent(FreeEvent):
    name = "小さな幸運"

    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        del hero, prompt_choice
        print(f"\nボーナスイベント: {self.name}")
        gold_amount = random.randint(8, 16)
        run_state.gold += gold_amount
        print(f"落し物の袋を見つけた。所持金を{gold_amount}獲得した。")


class PaidEvent(Event, ABC):
    description: str
    reward_kind: str

    def trigger(self, hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
        print(f"\nイベント: {self.name}")
        print(self.description)
        print("1: 低リスク  2: 中リスク  3: 高リスク  4: 見送る")
        print("高リスクほど報酬量は増えるが、失敗して支払いだけ失う確率が上がる。")

        valid_choices = {option.key for option in RISK_OPTIONS} | {"4"}
        while True:
            choice = prompt_choice("選択: ", valid_choices)
            if choice == "4":
                print("イベントを見送った。")
                return

            option = next(option for option in RISK_OPTIONS if option.key == choice)
            if run_state.gold < option.cost:
                print("所持金が足りない。別の選択をしてください。")
                continue

            run_state.gold -= option.cost
            print(f"{option.label}リスクに挑戦。所持金を{option.cost}支払った。")
            if random.random() <= option.success_rate:
                reward_amount = self.resolve_reward_amount(option.amount)
                grant_event_reward(hero, self.reward_kind, reward_amount)
            else:
                print("失敗した。支払った所持金だけを失った。")
            return

    def resolve_reward_amount(self, base_amount: int) -> int:
        if self.reward_kind == "heal":
            return base_amount * 4
        return base_amount


class MerchantEvent(PaidEvent):
    name = "行商人"
    description = "代金を払えば回復薬を分けてもらえる。"
    reward_kind = "potion"


class ShrineEvent(PaidEvent):
    name = "怪しい祭壇"
    description = "供物を捧げれば力を得られるかもしれない。"
    reward_kind = "attack"


class ForgeEvent(PaidEvent):
    name = "鉄壁の鍛冶台"
    description = "資材を払えば防具を鍛えられる。"
    reward_kind = "defense"


class PilgrimSpringEvent(PaidEvent):
    name = "巡礼の泉"
    description = "硬貨を投げれば癒やしが返ってくることがある。"
    reward_kind = "heal"


FREE_EVENTS: list[FreeEvent] = [BonusHealEvent(), BonusGoldEvent()]
PAID_EVENTS: list[PaidEvent] = [
    MerchantEvent(),
    ShrineEvent(),
    ForgeEvent(),
    PilgrimSpringEvent(),
]


def trigger_event(hero: Hero, run_state: RunState, prompt_choice: PromptChoice) -> None:
    if random.random() < 0.4:
        random.choice(FREE_EVENTS).trigger(hero, run_state, prompt_choice)
        return
    random.choice(PAID_EVENTS).trigger(hero, run_state, prompt_choice)