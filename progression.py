from __future__ import annotations

from battle import battle, create_enemy
from config import (
    ATTACK_PER_UPGRADE,
    BASE_ATTACK,
    BASE_DEFENSE,
    BASE_HP,
    CLEAR_BONUS_SHARDS,
    DEFENSE_PER_UPGRADE,
    HP_PER_UPGRADE,
    SHOP_UPGRADE_COST,
    TOTAL_FLOORS,
)
from events import Event, get_event_diagram_label, plan_event, run_event
from models import Hero, PermanentUpgrades, RunState, ShopUpgrade
from ui import PromptChoice, clear_screen, wait_for_enter
FloorEventPlan = dict[int, Event | None]


SHOP_UPGRADES = [
    ShopUpgrade("1", "HP強化", SHOP_UPGRADE_COST, "hp", 1, HP_PER_UPGRADE, f"+{HP_PER_UPGRADE}", f"最大HPが恒久的に{HP_PER_UPGRADE}上がった。"),
    ShopUpgrade("2", "攻撃力強化", SHOP_UPGRADE_COST, "attack", 1, ATTACK_PER_UPGRADE, f"+{ATTACK_PER_UPGRADE}", f"攻撃力が恒久的に{ATTACK_PER_UPGRADE}上がった。"),
    ShopUpgrade("3", "防御力強化", SHOP_UPGRADE_COST, "defense", 1, DEFENSE_PER_UPGRADE, f"+{DEFENSE_PER_UPGRADE}", f"防御力が恒久的に{DEFENSE_PER_UPGRADE}上がった。"),
]


def build_hero(upgrades: PermanentUpgrades) -> Hero:
    max_hp = BASE_HP + upgrades.hp * HP_PER_UPGRADE
    return Hero(
        max_hp=max_hp,
        hp=max_hp,
        attack=BASE_ATTACK + upgrades.attack * ATTACK_PER_UPGRADE,
        defense=BASE_DEFENSE + upgrades.defense * DEFENSE_PER_UPGRADE,
    )


def get_upgrade_summary(upgrades: PermanentUpgrades) -> str:
    return (
        f"HP+{upgrades.hp * HP_PER_UPGRADE} 攻撃力+{upgrades.attack * ATTACK_PER_UPGRADE} 防御力+{upgrades.defense * DEFENSE_PER_UPGRADE}"
    )


def build_floor_event_plan() -> FloorEventPlan:
    floor_events: FloorEventPlan = {1: None, TOTAL_FLOORS: None}
    for floor in range(2, TOTAL_FLOORS):
        floor_events[floor] = plan_event()
    return floor_events


def format_floor_diagram(current_floor: int, floor_events: FloorEventPlan) -> str:
    nodes: list[str] = []
    for floor in range(1, TOTAL_FLOORS + 1):
        planned_event = floor_events.get(floor)
        if planned_event is None:
            marker = "X" if floor == TOTAL_FLOORS else "B"
        else:
            marker = get_event_diagram_label(planned_event)
        if floor < current_floor:
            nodes.append(f"[{floor}{marker}]")
            continue
        if floor == current_floor:
            nodes.append(f"{{{floor}{marker}}}")
            continue
        nodes.append(f"<{floor}{marker}>")
    return "-".join(nodes)


def show_status(
    hero: Hero,
    run_state: RunState,
    floor: int,
    floor_events: FloorEventPlan,
) -> None:
    print("-" * 44)
    print(
        f"階層: {floor}/{TOTAL_FLOORS}  欠片: {run_state.soul_shards}  所持金: {run_state.gold}"
    )
    print(f"進行: {format_floor_diagram(floor, floor_events)}")
    print("凡例: []踏破済み  {}現在  <>先の階層  泉回復  袋所持金  商薬  祭攻  鍛防  巡回  B戦闘  X最終階")
    print(
        f"主人公 HP {hero.hp}/{hero.max_hp}  攻撃力 {hero.attack}  防御力 {hero.defense}  回復薬 {hero.potions}"
    )
    print("-" * 44)


def show_shop_status(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    hero: Hero | None = None,
) -> None:
    print(f"恒久強化 {get_upgrade_summary(upgrades)}")
    if hero is not None:
        print(
            f"主人公 HP {hero.hp}/{hero.max_hp}  攻撃力 {hero.attack}  防御力 {hero.defense}  回復薬 {hero.potions}"
        )
    print(f"現在の欠片: {soul_shards}")


def apply_shop_upgrade(upgrades: PermanentUpgrades, upgrade: ShopUpgrade) -> None:
    current_value = getattr(upgrades, upgrade.field_name)
    setattr(upgrades, upgrade.field_name, current_value + upgrade.field_gain)


def apply_upgrade_to_hero(hero: Hero, upgrade: ShopUpgrade) -> None:
    if upgrade.field_name == "hp":
        hero.max_hp += upgrade.hero_gain
        hero.hp += upgrade.hero_gain
        return
    current_value = getattr(hero, upgrade.field_name)
    setattr(hero, upgrade.field_name, current_value + upgrade.hero_gain)


def format_shop_options() -> str:
    parts = [
        f"{upgrade.key}: {upgrade.title}({upgrade.preview_text}) 欠片{upgrade.cost}"
        for upgrade in SHOP_UPGRADES
    ]
    parts.append("4: 出発")
    return " | ".join(parts)


def shop_phase(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    prompt_choice: PromptChoice,
    hero: Hero | None = None,
) -> int:
    clear_screen()
    print("\n拠点に戻った。欠片で恒久強化ができる。")
    options_by_key = {upgrade.key: upgrade for upgrade in SHOP_UPGRADES}
    valid_choices = set(options_by_key) | {"4"}
    show_shop_status(upgrades, soul_shards, hero)

    while True:
        print(format_shop_options())
        choice = prompt_choice("選択: ", valid_choices)
        if choice == "4":
            return soul_shards

        upgrade = options_by_key[choice]
        if soul_shards < upgrade.cost:
            print("欠片が足りない。")
            show_shop_status(upgrades, soul_shards, hero)
            continue

        soul_shards -= upgrade.cost
        apply_shop_upgrade(upgrades, upgrade)
        if hero is not None:
            apply_upgrade_to_hero(hero, upgrade)
        print(upgrade.success_message)
        show_shop_status(upgrades, soul_shards, hero)
        wait_for_enter()


def reset_permanent_upgrades(upgrades: PermanentUpgrades) -> None:
    upgrades.hp = 0
    upgrades.attack = 0
    upgrades.defense = 0


def reset_hero_status(hero: Hero, upgrades: PermanentUpgrades) -> None:
    base_hero = build_hero(upgrades)
    hero.max_hp = base_hero.max_hp
    hero.hp = base_hero.hp
    hero.attack = base_hero.attack
    hero.defense = base_hero.defense
    hero.potions = base_hero.potions


def _handle_battle_floor(
    floor: int,
    hero: Hero,
    run_state: RunState,
    upgrades: PermanentUpgrades,
    prompt_choice: PromptChoice,
) -> bool | None:
    """戦闘階の処理。死亡なら False、踏破継続なら None を返す。"""
    enemy = create_enemy(floor)
    battle_reward = battle(hero, enemy, run_state, prompt_choice)
    run_state.soul_shards += battle_reward.soul_shards
    run_state.gold += battle_reward.gold

    if battle_reward.escaped:
        print("戦闘から離脱した。")
        wait_for_enter()
        return None

    if battle_reward.soul_shards > 0:
        print("戦闘終了。恒久強化を選択できる。")
        wait_for_enter()
        run_state.soul_shards = shop_phase(
            upgrades, run_state.soul_shards, prompt_choice, hero,
        )

    if not hero.is_alive():
        reset_permanent_upgrades(upgrades)
        reset_hero_status(hero, upgrades)
        print(
            f"主人公は力尽きた。到達階層は {floor}/{TOTAL_FLOORS}。恒久強化を含むステータスをリセットした。"
        )
        wait_for_enter()
        return False

    return None


def run_once(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    prompt_choice: PromptChoice,
) -> tuple[bool, int]:
    hero = build_hero(upgrades)
    run_state = RunState(soul_shards=soul_shards)
    floor_events = build_floor_event_plan()

    print("\n探索開始")
    for floor in range(1, TOTAL_FLOORS + 1):
        clear_screen()
        show_status(hero, run_state, floor, floor_events)
        wait_for_enter()

        planned_event = floor_events.get(floor)
        if planned_event is not None:
            run_event(planned_event, hero, run_state, prompt_choice)
            wait_for_enter()
            continue

        result = _handle_battle_floor(floor, hero, run_state, upgrades, prompt_choice)
        if result is not None:
            return result, run_state.soul_shards

    print("最深部を突破した。探索成功。")
    run_state.soul_shards += CLEAR_BONUS_SHARDS
    print(f"踏破報酬として欠片を{CLEAR_BONUS_SHARDS}獲得。")
    wait_for_enter()
    return True, run_state.soul_shards