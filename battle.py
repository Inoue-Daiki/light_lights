from __future__ import annotations

import math
import random

from config import (
    DAMAGE_VARIANCE_MAX,
    DAMAGE_VARIANCE_MIN,
    ENEMY_ATTACK_PER_FLOOR,
    ENEMY_DEFENSE_PER_FLOOR_DIVISOR,
    ENEMY_GOLD_BASE,
    ENEMY_GOLD_PER_FLOOR,
    ENEMY_HP_PER_FLOOR,
    ENEMY_SHARD_BASE,
    ENEMY_SHARD_PER_FLOOR,
    ESCAPE_PENALTY_RATE,
    MIN_DAMAGE,
    POTION_HEAL_AMOUNT,
)
from models import BattleReward, Enemy, EnemyTemplate, Hero, RunState
from ui import PromptChoice


ENEMY_TEMPLATES = [
    EnemyTemplate("Slime", 10, 6, 1),
    EnemyTemplate("Bandit", 14, 7, 2),
    EnemyTemplate("Skeleton", 18, 9, 3),
    EnemyTemplate("Wolf", 16, 10, 2),
    EnemyTemplate("Knight", 22, 11, 4),
]


def clamp_damage(raw_damage: int) -> int:
    return max(MIN_DAMAGE, raw_damage)


def attack_damage(attack: int, defense: int) -> int:
    variance = random.randint(DAMAGE_VARIANCE_MIN, DAMAGE_VARIANCE_MAX)
    return clamp_damage(attack - defense + variance)


def create_enemy(floor: int) -> Enemy:
    template = random.choice(ENEMY_TEMPLATES)
    hp = template.hp + floor * ENEMY_HP_PER_FLOOR
    attack = template.attack + floor * ENEMY_ATTACK_PER_FLOOR
    defense = template.defense + floor // ENEMY_DEFENSE_PER_FLOOR_DIVISOR
    shard_reward = ENEMY_SHARD_BASE + floor * ENEMY_SHARD_PER_FLOOR
    gold_reward = ENEMY_GOLD_BASE + floor * ENEMY_GOLD_PER_FLOOR
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
    healed = hero.heal(POTION_HEAL_AMOUNT)
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
        penalty_targets.append(("欠片", max(1, math.ceil(run_state.soul_shards * ESCAPE_PENALTY_RATE))))
    if run_state.gold > 0:
        penalty_targets.append(("所持金", max(1, math.ceil(run_state.gold * ESCAPE_PENALTY_RATE))))

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