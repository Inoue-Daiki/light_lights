"""探索の1ラン（run_once）を実行するオーケストレーションモジュール。"""

from __future__ import annotations

from typing import Literal

from battle import battle
from enemies import create_enemy
from config import CLEAR_BONUS_SHARDS, ROUTE_NAME, SECTION_LABEL, TOTAL_FLOORS
from events import run_event
from models import Hero, PermanentUpgrades, RunResult, RunState
from route import build_map, choose_next, show_map
from shop import build_hero, reset_upgrades, shop_phase
from ui import PromptChoice, clear_screen, wait_for_enter


def _handle_battle_floor(
    floor: int,
    hero: Hero,
    run_state: RunState,
    upgrades: PermanentUpgrades,
    prompt_choice: PromptChoice,
) -> Literal[False] | None:
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
        print("戦闘終了。能力強化を選択できる。")
        wait_for_enter()
        run_state.soul_shards = shop_phase(
            upgrades, run_state.soul_shards, prompt_choice, hero,
        )

    if not hero.is_alive():
        reset_upgrades(upgrades)
        print(
            f"主人公は力尽きた。到達{SECTION_LABEL}は {floor}/{TOTAL_FLOORS}。"
            f"{ROUTE_NAME}で得た能力強化を含むステータスをリセットした。"
        )
        wait_for_enter()
        return False

    return None


def run_once(
    upgrades: PermanentUpgrades,
    soul_shards: int,
    prompt_choice: PromptChoice,
) -> RunResult:
    hero = build_hero(upgrades)
    run_state = RunState(soul_shards=soul_shards)
    rows = build_map(TOTAL_FLOORS)
    path = [rows[0][0]]
    for floor in range(1, len(rows) + 1):
        node = path[-1]
        clear_screen()
        show_map(rows, path)
        print(f"{ROUTE_NAME}・{floor}区目　HP {hero.hp}/{hero.max_hp}　所持金 {run_state.gold}")
        wait_for_enter()
        if node.event:
            run_event(node.event, hero, run_state, prompt_choice)
            wait_for_enter()
        else:
            result = _handle_battle_floor(floor, hero, run_state, upgrades, prompt_choice)
            if result is not None:
                return RunResult(won=result, soul_shards=run_state.soul_shards)
        if floor < len(rows):
            clear_screen()
            show_map(rows, path)
            print(f"HP {hero.hp}/{hero.max_hp}　所持金 {run_state.gold}")
            path.append(choose_next(node, rows[floor], prompt_choice))

    print("町の門をくぐった。頼まれた手紙を届けよう。")
    run_state.soul_shards += CLEAR_BONUS_SHARDS
    print(f"踏破報酬として経験点を{CLEAR_BONUS_SHARDS}獲得。")
    wait_for_enter()
    return RunResult(won=True, soul_shards=run_state.soul_shards)
