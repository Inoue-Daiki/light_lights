"""街道の分岐と合流。各地点は旅の出発時に一度だけ生成する。"""
from __future__ import annotations

import random
from dataclasses import dataclass

from events import FREE_EVENT_TEMPLATES, Event, plan_event
from ui import PromptChoice


@dataclass(eq=False)
class RouteNode:
    lane: int
    event: Event | None

    @property
    def name(self) -> str:
        return self.event.name if self.event else "戦闘"


def build_map(length: int) -> list[list[RouteNode]]:
    pattern = [(0, 2), (0, 1, 2), (0, 2), (1,)]
    rows = []
    for step in range(length):
        if step in (0, length - 1):
            rows.append([RouteNode(1, None)])
        elif step == 1:
            plans = [None, random.choice(FREE_EVENT_TEMPLATES)]
            random.shuffle(plans)
            rows.append([RouteNode(lane, event) for lane, event in zip((0, 2), plans)])
        else:
            rows.append([RouteNode(lane, plan_event()) for lane in pattern[(step - 1) % 4]])
    return rows


def neighbors(node: RouteNode, row: list[RouteNode]) -> list[RouteNode]:
    return [other for other in row if abs(node.lane - other.lane) <= 1]


def show_map(rows: list[list[RouteNode]], path: list[RouteNode]) -> None:
    print("街道地図   @ 現在地   * 通過   B 戦闘   G 町の門（戦闘）")
    labels = {n.event.diagram_label: n.name for row in rows for n in row if n.event}
    print("   ".join(f"{key} {name}" for key, name in labels.items()))
    for step, row in enumerate(rows, 1):
        line = list(" " * 12)
        for node in row:
            symbol = node.event.diagram_label if node.event else "B"
            if step == len(rows):
                symbol = "G"
            mark = "@" if node is path[-1] else "*" if node in path else " "
            pos = node.lane * 4
            line[pos:pos + 3] = mark + symbol + " "
        print(f"{step:2}  " + "".join(line).rstrip())
        if step == len(rows):
            continue
        links = list(" " * 12)
        for node in row:
            for dest in neighbors(node, rows[step]):
                delta = dest.lane - node.lane
                pos = 1 + (node.lane + dest.lane) * 2
                links[pos] = {0: "|", 1: "\\", -1: "/"}[delta]
        print("    " + "".join(links).rstrip())



def choose_next(node: RouteNode, row: list[RouteNode], prompt: PromptChoice) -> RouteNode:
    options = neighbors(node, row)
    if len(options) == 1:
        return options[0]
    for index, dest in enumerate(options, 1):
        print(f"{index}. {('左', '中央', '右')[dest.lane]}の道　{dest.name}")
    key = prompt("どの道を進む？ ", {str(i) for i in range(1, len(options) + 1)})
    return options[int(key) - 1]
