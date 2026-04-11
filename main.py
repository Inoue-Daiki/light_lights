from __future__ import annotations

import random

from models import PermanentUpgrades
from progression import get_upgrade_summary, run_once
from ui import wait_for_enter


def prompt_choice(prompt: str, options: set[str]) -> str:
    while True:
        answer = input(prompt).strip().lower()
        if answer in options:
            return answer
        print("入力が不正です。もう一度入力してください。")


def show_title() -> None:
    print("=" * 44)
    print("      Light Lights: Roguelite Text RPG")
    print("=" * 44)
    print("主人公の基本パラメータ: HP / 攻撃力 / 防御力")
    print("戦って欠片を集め、拠点で恒久強化しながら最深部を目指す。")


def main() -> None:
    random.seed()
    upgrades = PermanentUpgrades()
    soul_shards = 0

    show_title()
    wait_for_enter()

    while True:
        print("\nメニュー")
        print("1: 探索に出る")
        print("2: 恒久強化を見る")
        print("3: 終了")
        choice = prompt_choice("選択: ", {"1", "2", "3"})

        if choice == "3":
            print("ゲームを終了します。")
            return

        if choice == "2":
            print(f"恒久強化 {get_upgrade_summary(upgrades)}")
            print(f"所持欠片: {soul_shards}")
            wait_for_enter()
            continue

        won, soul_shards = run_once(upgrades, soul_shards, prompt_choice)
        print(f"現在の累計欠片は {soul_shards}。")
        if won:
            print("次の探索ではさらに奥を目指せる。")


if __name__ == "__main__":
    main()