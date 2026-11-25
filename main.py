from __future__ import annotations

from game import run_once
from models import PermanentUpgrades
from shop import get_upgrade_summary, shop_phase
from ui import prompt_choice, wait_for_enter


def show_title() -> None:
    print("=" * 44)
    print("      Light Lights: Roguelite Text RPG")
    print("=" * 44)
    print("主人公の基本パラメータ: HP / 攻撃力 / 防御力")
    print("街道を進み、町の門を目指す。")


def main() -> None:
    upgrades = PermanentUpgrades()
    soul_shards = 0

    show_title()
    wait_for_enter()

    while True:
        print("\nメニュー")
        print("1: 探索に出る")
        print("2: 能力強化を見る")
        print("3: 能力強化をする")
        print("4: 終了")
        choice = prompt_choice("選択: ", {"1", "2", "3", "4"})

        if choice == "4":
            print("ゲームを終了します。")
            return

        if choice == "2":
            print(f"能力強化 {get_upgrade_summary(upgrades)}")
            print(f"所持経験点: {soul_shards}")
            wait_for_enter()
            continue

        if choice == "3":
            soul_shards = shop_phase(upgrades, soul_shards, prompt_choice)
            continue

        result = run_once(upgrades, soul_shards, prompt_choice)
        soul_shards = result.soul_shards
        print(f"現在の累計経験点は {soul_shards}。")


if __name__ == "__main__":
    main()
