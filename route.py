"""ルート木の生成・ダイアグラム表示・分岐選択を管理するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass

from config import ROUTE_LABEL, ROUTE_NAME, SECTION_LABEL, TOTAL_FLOORS
from events import Event, plan_event
from models import Hero, RunState
from ui import PromptChoice, clear_screen


StagePlan = Event | None
ClearedStagePlan = dict[int, StagePlan]


@dataclass
class RouteNode:
    plan: StagePlan
    next_routes: list[RouteNode]


BranchOptions = list[RouteNode]


# ── ルート木の構築 ──


def build_branch_options(floor: int) -> BranchOptions:
    next_floor = floor + 1
    if next_floor > TOTAL_FLOORS:
        return []
    if next_floor == TOTAL_FLOORS:
        return [RouteNode(None, [])]
    return [
        RouteNode(plan_event(), build_branch_options(next_floor)),
        RouteNode(plan_event(), build_branch_options(next_floor)),
    ]


# ── ダイアグラム表示 ──


def _stage_marker(floor: int, plan: StagePlan, bracket: str) -> str:
    if plan is None:
        marker = "X" if floor == TOTAL_FLOORS else "B"
    else:
        marker = plan.diagram_label
    if bracket == "done":
        return f"[{floor}{marker}]"
    if bracket == "current":
        return f"{{{floor}{marker}}}"
    return f"<{floor}{marker}>"


def _future_options(floor: int, routes: BranchOptions) -> str:
    if not routes:
        return ""
    nf = floor + 1
    return " / ".join(_stage_marker(nf, r.plan, "future") for r in routes)


def format_floor_diagram(
    current_floor: int,
    current_plan: StagePlan,
    cleared_plans: ClearedStagePlan,
    next_options: BranchOptions,
) -> list[str]:
    nodes = [
        _stage_marker(f, cleared_plans[f], "done")
        for f in range(1, current_floor)
    ]
    nodes.append(_stage_marker(current_floor, current_plan, "current"))
    first_line = "-".join(nodes)

    if not next_options:
        return [first_line]

    nf = current_floor + 1
    if len(next_options) == 1:
        only = next_options[0]
        lines = [f"{first_line}-{_stage_marker(nf, only.plan, 'future')}"]
        preview = _future_options(nf, only.next_routes)
        if preview:
            lines.append(f"      その先: {preview}")
        return lines

    first_route, second_route = next_options[0], next_options[1]
    return [
        first_line,
        f"次の{SECTION_LABEL}:",
        f"      ┏1:{_stage_marker(nf, first_route.plan, 'future')}",
        f"      ┃  先: {_future_options(nf, first_route.next_routes) or '-'}",
        f"      ┗2:{_stage_marker(nf, second_route.plan, 'future')}",
        f"         先: {_future_options(nf, second_route.next_routes) or '-'}",
    ]


# ── ステータス表示 ──


def show_status(
    hero: Hero,
    run_state: RunState,
    floor: int,
    current_plan: StagePlan,
    cleared_plans: ClearedStagePlan,
    next_options: BranchOptions,
) -> None:
    print("-" * 44)
    print(f"{ROUTE_LABEL}: {ROUTE_NAME}")
    print(
        f"{SECTION_LABEL}: {floor}/{TOTAL_FLOORS}  "
        f"欠片: {run_state.soul_shards}  所持金: {run_state.gold}"
    )
    lines = format_floor_diagram(floor, current_plan, cleared_plans, next_options)
    print(f"進行: {lines[0]}")
    for line in lines[1:]:
        print(line)
    print(
        "凡例: []踏破済み  {}現在  <>先の区画  "
        "泉回復  袋所持金  商薬  祭攻  鍛防  巡回  風速  B戦闘  X終点"
    )
    if len(next_options) == 2:
        print("分岐: 1 または 2 を選ぶ")
    print(
        f"主人公 HP {hero.hp}/{hero.max_hp}  攻撃力 {hero.attack}  "
        f"防御力 {hero.defense}  素早さ {hero.speed}  回復薬 {hero.potions}"
    )
    print("-" * 44)


# ── 分岐選択 ──


def choose_next_route(
    next_options: BranchOptions,
    prompt_choice: PromptChoice,
) -> RouteNode | None:
    if not next_options:
        return None
    if len(next_options) == 1:
        return next_options[0]
    choice = prompt_choice("次の分岐を選択 [1/2]: ", {"1", "2"})
    print(f"分岐{choice}を選んだ。")
    return next_options[int(choice) - 1]


def choose_next_route_with_status(
    hero: Hero,
    run_state: RunState,
    floor: int,
    current_plan: StagePlan,
    cleared_plans: ClearedStagePlan,
    next_options: BranchOptions,
    prompt_choice: PromptChoice,
) -> RouteNode | None:
    if not next_options:
        return None
    if len(next_options) == 1:
        return next_options[0]
    clear_screen()
    show_status(hero, run_state, floor, current_plan, cleared_plans, next_options)
    return choose_next_route(next_options, prompt_choice)
