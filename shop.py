"""ショップ・能力強化・主人公構築を管理するモジュール。"""

from __future__ import annotations

from config import (
    ATTACK_PER_UPGRADE,
    BASE_ATTACK,
    BASE_DEFENSE,
    BASE_HP,
    BASE_SPEED,
    DEFENSE_PER_UPGRADE,
    HP_PER_UPGRADE,
    SHOP_UPGRADE_COST,
    SPEED_PER_UPGRADE,
)
from models import Hero, PermanentUpgrades, ShopUpgrade
from ui import PromptChoice, clear_screen, wait_for_enter


SHOP_UPGRADES = [
    ShopUpgrade(
        "1", "HP強化", SHOP_UPGRADE_COST, "hp", 1,
        HP_PER_UPGRADE, f"+{HP_PER_UPGRADE}",
        f"最大HPが{HP_PER_UPGRADE}上がった。",
    ),
    ShopUpgrade(
        "2", "攻撃力強化", SHOP_UPGRADE_COST, "attack", 1,
        ATTACK_PER_UPGRADE, f"+{ATTACK_PER_UPGRADE}",
        f"攻撃力が{ATTACK_PER_UPGRADE}上がった。",
    ),
    ShopUpgrade(
        "3", "防御力強化", SHOP_UPGRADE_COST, "defense", 1,
        DEFENSE_PER_UPGRADE, f"+{DEFENSE_PER_UPGRADE}",
        f"防御力が{DEFENSE_PER_UPGRADE}上がった。",
    ),
    ShopUpgrade(
        "4", "素早さ強化", SHOP_UPGRADE_COST, "speed", 1,
        SPEED_PER_UPGRADE, f"+{SPEED_PER_UPGRADE}",
        f"素早さが{SPEED_PER_UPGRADE}上がった。",
    ),
]

_EXIT_KEY = str(len(SHOP_UPGRADES) + 1)


# ── 主人公構築 ──


def build_hero(upgrades: PermanentUpgrades) -> Hero:
    max_hp = BASE_HP + upgrades.hp * HP_PER_UPGRADE
    return Hero(
        max_hp=max_hp,
        hp=max_hp,
        attack=BASE_ATTACK + upgrades.attack * ATTACK_PER_UPGRADE,
        defense=BASE_DEFENSE + upgrades.defense * DEFENSE_PER_UPGRADE,
        speed=BASE_SPEED + upgrades.speed * SPEED_PER_UPGRADE,
    )


def get_upgrade_summary(upgrades: PermanentUpgrades) -> str:
    return (
        f"HP+{upgrades.hp * HP_PER_UPGRADE} "
        f"攻撃力+{upgrades.attack * ATTACK_PER_UPGRADE} "
        f"防御力+{upgrades.defense * DEFENSE_PER_UPGRADE} "
        f"素早さ+{upgrades.speed * SPEED_PER_UPGRADE}"
    )


# ── 能力強化リセット ──


def reset_upgrades(upgrades: PermanentUpgrades) -> None:
    upgrades.hp = 0
    upgrades.attack = 0
    upgrades.defense = 0
    upgrades.speed = 0


# ── ショップUI ──


def _show_shop_status(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    hero: Hero | None = None,
) -> None:
    print(f"能力強化 {get_upgrade_summary(upgrades)}")
    if hero is not None:
        print(
            f"主人公 HP {hero.hp}/{hero.max_hp}  攻撃力 {hero.attack}  "
            f"防御力 {hero.defense}  素早さ {hero.speed}  道具 {sum(hero.bag.values())}"
        )
    print(f"現在の経験点: {soul_shards}")


def _apply_to_upgrades(upgrades: PermanentUpgrades, upgrade: ShopUpgrade) -> None:
    current = getattr(upgrades, upgrade.field_name)
    setattr(upgrades, upgrade.field_name, current + upgrade.field_gain)


def _apply_to_hero(hero: Hero, upgrade: ShopUpgrade) -> None:
    if upgrade.field_name == "hp":
        hero.max_hp += upgrade.hero_gain
        hero.hp += upgrade.hero_gain
        return
    current = getattr(hero, upgrade.field_name)
    setattr(hero, upgrade.field_name, current + upgrade.hero_gain)


def _format_options() -> str:
    parts = [
        f"{u.key}: {u.title}({u.preview_text}) 経験点{u.cost}"
        for u in SHOP_UPGRADES
    ]
    parts.append(f"{_EXIT_KEY}: 出発")
    return " | ".join(parts)


def shop_phase(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    prompt_choice: PromptChoice,
    hero: Hero | None = None,
) -> int:
    clear_screen()
    print("\n経験点を使って能力を強化できる。")
    options_by_key = {u.key: u for u in SHOP_UPGRADES}
    valid_choices = set(options_by_key) | {_EXIT_KEY}
    _show_shop_status(upgrades, soul_shards, hero)

    while True:
        print(_format_options())
        choice = prompt_choice("選択: ", valid_choices)
        if choice == _EXIT_KEY:
            return soul_shards

        upgrade = options_by_key[choice]
        if soul_shards < upgrade.cost:
            print("経験点が足りない。")
            _show_shop_status(upgrades, soul_shards, hero)
            continue

        soul_shards -= upgrade.cost
        _apply_to_upgrades(upgrades, upgrade)
        if hero is not None:
            _apply_to_hero(hero, upgrade)
        print(upgrade.success_message)
        _show_shop_status(upgrades, soul_shards, hero)
        wait_for_enter()
