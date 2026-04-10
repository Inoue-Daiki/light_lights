from __future__ import annotations

import math
import random
from typing import Callable

from models import BattleReward, Enemy, EnemyTemplate, Hero, RunState


PromptChoice = Callable[[str, set[str]], str]


ENEMY_TEMPLATES = [
    EnemyTemplate("Slime", 10, 6, 1),
    EnemyTemplate("Bandit", 14, 7, 2),
    EnemyTemplate("Skeleton", 18, 9, 3),
    EnemyTemplate("Wolf", 16, 10, 2),
    EnemyTemplate("Knight", 22, 11, 4),
]


def clamp_damage(raw_damage: int) -> int:
    return max(1, raw_damage)


def attack_damage(attack: int, defense: int) -> int:
    variance = random.randint(-1, 2)
    return clamp_damage(attack - defense + variance)


def create_enemy(floor: int) -> Enemy:
    template = random.choice(ENEMY_TEMPLATES)
    hp = template.hp + floor * 3
    attack = template.attack + floor
    defense = template.defense + floor // 2
    shard_reward = 8 + floor * 4
    gold_reward = 6 + floor * 3
    return Enemy(
        name=template.name,
        hp=hp,
        attack=attack,
        defense=defense,
        shard_reward=shard_reward,
        gold_reward=gold_reward,
    )


def use_potion(hero: Hero) -> bool:
    if hero.potions <= 0:
        print("回復薬がありません。")
        return False
    hero.potions -= 1
    healed = hero.heal(10)
    print(f"回復薬を使ってHPを{healed}回復した。")
    return True


def perform_hero_attack(hero: Hero, enemy: Enemy) -> None:
    damage = attack_damage(hero.attack, enemy.defense)
    enemy.hp = max(0, enemy.hp - damage)
    print(f"{enemy.name}に{damage}ダメージ。")


def perform_enemy_attack(hero: Hero, enemy: Enemy) -> None:
    enemy_damage = attack_damage(enemy.attack, hero.defense)
    taken = hero.take_damage(enemy_damage)
    print(f"{enemy.name}の攻撃。{taken}ダメージを受けた。")


def apply_escape_penalty(run_state: RunState) -> None:
    penalty_targets: list[tuple[str, int]] = []
    if run_state.soul_shards > 0:
        penalty_targets.append(("欠片", max(1, math.ceil(run_state.soul_shards * 0.3))))
    if run_state.gold > 0:
        penalty_targets.append(("所持金", max(1, math.ceil(run_state.gold * 0.3))))

    if not penalty_targets:
        print("何も持っていなかったため、失うものなく逃げ切った。")
        return

    resource_name, amount = random.choice(penalty_targets)
    if resource_name == "欠片":
        lost_amount = min(run_state.soul_shards, amount)
        run_state.soul_shards -= lost_amount
    else:
        lost_amount = min(run_state.gold, amount)
        run_state.gold -= lost_amount
    print(f"逃走に成功したが、{resource_name}を{lost_amount}失った。")


def battle(
    hero: Hero,
    enemy: Enemy,
    run_state: RunState,
    prompt_choice: PromptChoice,
) -> BattleReward:
    print(f"\n敵が現れた: {enemy.name}")

    while hero.is_alive() and enemy.is_alive():
        print(f"あなた HP {hero.hp}/{hero.max_hp} | {enemy.name} HP {enemy.hp}")
        action = prompt_choice("行動を選択 [a]攻撃 [h]回復 [r]逃走: ", {"a", "h", "r"})

        if action == "r":
            apply_escape_penalty(run_state)
            return BattleReward(0, 0, escaped=True)

        if action == "h":
            if not use_potion(hero):
                continue
        else:
            perform_hero_attack(hero, enemy)

        if not enemy.is_alive():
            print(
                f"{enemy.name}を倒した。欠片を{enemy.shard_reward}、所持金を{enemy.gold_reward}獲得。"
            )
            return BattleReward(enemy.shard_reward, enemy.gold_reward)

        perform_enemy_attack(hero, enemy)

    return BattleReward(0, 0)