"""探索の1ラン（run_once）を実行するオーケストレーションモジュール。"""

from __future__ import annotations

from battle import battle
from enemies import create_enemy
from config import CLEAR_BONUS_SHARDS, ROUTE_NAME, SECTION_LABEL, TOTAL_FLOORS
from events import run_event
from models import Hero, PermanentUpgrades, RunResult, RunState
from route import (
    ClearedStagePlan,
    RouteNode,
    build_branch_options,
    choose_next_route_with_status,
    show_status,
)
from shop import build_hero, reset_upgrades, shop_phase
from ui import PromptChoice, clear_screen, wait_for_enter


def _handle_battle_floor(
    floor: int,
    hero: Hero,
    run_state: RunState,
    upgrades: PermanentUpgrades,
    prompt_choice: PromptChoice,
) -> bool | None:
    """戦闘階の処理。死亡時 False、継続時 None を返す。"""
    enemy = create_enemy(floor)
    reward = battle(hero, enemy, run_state, prompt_choice)
    run_state.soul_shards += reward.soul_shards
    run_state.gold += reward.gold

    if reward.escaped:
        print("戦闘から離脱した。")
        wait_for_enter()
        return None

    if reward.soul_shards > 0:
        print("戦闘終了。恒久強化を選択できる。")
        wait_for_enter()
        run_state.soul_shards = shop_phase(
            upgrades, run_state.soul_shards, prompt_choice, hero,
        )

    if not hero.is_alive():
        reset_upgrades(upgrades)
        print(
            f"主人公は力尽きた。到達{SECTION_LABEL}は {floor}/{TOTAL_FLOORS}。"
            f"{ROUTE_NAME}で得た恒久強化を含むステータスをリセットした。"
        )
        wait_for_enter()
        return False

    return None


def _advance_route(
    hero: Hero,
    run_state: RunState,
    floor: int,
    current_route: RouteNode,
    cleared_plans: ClearedStagePlan,
    prompt_choice: PromptChoice,
) -> RouteNode | None:
    """現在階を踏破済みに記録し、次の分岐を選択して返す。"""
    cleared_plans[floor] = current_route.plan
    return choose_next_route_with_status(
        hero, run_state, floor,
        current_route.plan, cleared_plans,
        current_route.next_routes, prompt_choice,
    )


def run_once(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    prompt_choice: PromptChoice,
) -> RunResult:
    hero = build_hero(upgrades)
    run_state = RunState(soul_shards=soul_shards)
    cleared_plans: ClearedStagePlan = {}
    current_route: RouteNode | None = RouteNode(None, build_branch_options(1))

    print("\n探索開始")
    for floor in range(1, TOTAL_FLOORS + 1):
        if current_route is None:
            break

        clear_screen()
        show_status(
            hero, run_state, floor,
            current_route.plan, cleared_plans, current_route.next_routes,
        )
        wait_for_enter()

        # イベント階
        if current_route.plan is not None:
            run_event(current_route.plan, hero, run_state, prompt_choice)
            wait_for_enter()
            current_route = _advance_route(
                hero, run_state, floor, current_route, cleared_plans, prompt_choice,
            )
            continue

        # 戦闘階
        result = _handle_battle_floor(floor, hero, run_state, upgrades, prompt_choice)
        if result is not None:
            return RunResult(won=result, soul_shards=run_state.soul_shards)

        current_route = _advance_route(
            hero, run_state, floor, current_route, cleared_plans, prompt_choice,
        )

    print("最深部を突破した。探索成功。")
    run_state.soul_shards += CLEAR_BONUS_SHARDS
    print(f"踏破報酬として欠片を{CLEAR_BONUS_SHARDS}獲得。")
    wait_for_enter()
    return RunResult(won=True, soul_shards=run_state.soul_shards)
