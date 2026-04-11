from __future__ import annotations

import math
import random

from config import (
    DAMAGE_VARIANCE_MAX,
    DAMAGE_VARIANCE_MIN,
    DODGE_BASE_CHANCE,
    DODGE_MAX_CHANCE,
    DODGE_MIN_CHANCE,
    DODGE_SPEED_STEP,
    ENEMY_SPEED_PER_FLOOR_DIVISOR,
    ENEMY_ATTACK_PER_FLOOR,
    ENEMY_DEFENSE_PER_FLOOR_DIVISOR,
    ENEMY_GOLD_BASE,
    ENEMY_GOLD_PER_FLOOR,
    ENEMY_HP_PER_FLOOR,
    ENEMY_SHARD_BASE,
    ENEMY_SHARD_PER_FLOOR,
    ESCAPE_BASE_CHANCE,
    ESCAPE_MAX_CHANCE,
    ESCAPE_MIN_CHANCE,
    ESCAPE_PENALTY_RATE,
    ESCAPE_SPEED_STEP,
    MIN_DAMAGE,
    POTION_HEAL_AMOUNT,
)
from models import BattleReward, Enemy, EnemyTemplate, Hero, RunState
from ui import PromptChoice


ENEMY_TEMPLATES = [
    EnemyTemplate("Slime", 10, 6, 1, 4),
    EnemyTemplate("Bandit", 14, 7, 2, 5),
    EnemyTemplate("Skeleton", 18, 9, 3, 4),
    EnemyTemplate("Wolf", 16, 10, 2, 7),
    EnemyTemplate("Knight", 22, 11, 4, 3),
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
    speed = template.speed + floor // ENEMY_SPEED_PER_FLOOR_DIVISOR
    shard_reward = ENEMY_SHARD_BASE + floor * ENEMY_SHARD_PER_FLOOR
    gold_reward = ENEMY_GOLD_BASE + floor * ENEMY_GOLD_PER_FLOOR
    return Enemy(
        name=template.name,
        hp=hp,
        attack=attack,
        defense=defense,
        speed=speed,
        shard_reward=shard_reward,
        gold_reward=gold_reward,
    )


def get_escape_chance(hero: Hero, enemy: Enemy) -> float:
    speed_diff = hero.speed - enemy.speed
    chance = ESCAPE_BASE_CHANCE + speed_diff * ESCAPE_SPEED_STEP
    return max(ESCAPE_MIN_CHANCE, min(ESCAPE_MAX_CHANCE, chance))


def get_dodge_chance(attacker_speed: int, defender_speed: int) -> float:
    speed_diff = defender_speed - attacker_speed
    chance = DODGE_BASE_CHANCE + speed_diff * DODGE_SPEED_STEP
    return max(DODGE_MIN_CHANCE, min(DODGE_MAX_CHANCE, chance))


def use_potion(hero: Hero) -> bool:
    if hero.potions <= 0:
        print("回復薬がありません。")
        return False
    hero.potions -= 1
    healed = hero.heal(POTION_HEAL_AMOUNT)
    print(f"回復薬を使ってHPを{healed}回復した。")
    return True


def perform_hero_attack(hero: Hero, enemy: Enemy) -> None:
    if random.random() <= get_dodge_chance(hero.speed, enemy.speed):
        print(f"{enemy.name}は素早く攻撃をかわした。")
        return
    damage = attack_damage(hero.attack, enemy.defense)
    enemy.hp = max(0, enemy.hp - damage)
    print(f"{enemy.name}に{damage}ダメージ。")


def perform_enemy_attack(hero: Hero, enemy: Enemy) -> None:
    if random.random() <= get_dodge_chance(enemy.speed, hero.speed):
        print("あなたは素早く攻撃をかわした。")
        return
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


def try_escape(hero: Hero, enemy: Enemy, run_state: RunState) -> bool:
    if random.random() <= get_escape_chance(hero, enemy):
        apply_escape_penalty(run_state)
        return True
    print("逃走に失敗した。敵に隙を見せてしまった。")
    return False


def battle(
    hero: Hero,
    enemy: Enemy,
    run_state: RunState,
    prompt_choice: PromptChoice,
) -> BattleReward:
    print(f"\n敵が現れた: {enemy.name}")

    while hero.is_alive() and enemy.is_alive():
        escape_rate = int(get_escape_chance(hero, enemy) * 100)
        hero_dodge_rate = int(get_dodge_chance(enemy.speed, hero.speed) * 100)
        enemy_dodge_rate = int(get_dodge_chance(hero.speed, enemy.speed) * 100)
        first_actor = "あなた" if hero.speed >= enemy.speed else enemy.name
        print(
            f"あなた HP {hero.hp}/{hero.max_hp}  素早さ {hero.speed} | {enemy.name} HP {enemy.hp}  素早さ {enemy.speed}"
        )
        print(
            f"先手: {first_actor}  回避率 あなた {hero_dodge_rate}% / {enemy.name} {enemy_dodge_rate}%  逃走成功率: {escape_rate}%"
        )
        action = prompt_choice("行動を選択 [a]攻撃 [h]回復 [r]逃走: ", {"a", "h", "r"})

        if action == "r":
            if try_escape(hero, enemy, run_state):
                return BattleReward(0, 0, escaped=True)
            perform_enemy_attack(hero, enemy)
            continue

        if action == "h":
            if hero.potions <= 0:
                print("回復薬がありません。")
                continue

        hero_acts_first = hero.speed >= enemy.speed
        if hero_acts_first:
            if action == "h":
                use_potion(hero)
            else:
                perform_hero_attack(hero, enemy)

            if not enemy.is_alive():
                print(
                    f"{enemy.name}を倒した。欠片を{enemy.shard_reward}、所持金を{enemy.gold_reward}獲得。"
                )
                return BattleReward(enemy.shard_reward, enemy.gold_reward)

            perform_enemy_attack(hero, enemy)
            continue

        perform_enemy_attack(hero, enemy)
        if not hero.is_alive():
            break

        if action == "h":
            use_potion(hero)
            continue

        perform_hero_attack(hero, enemy)
        if not enemy.is_alive():
            print(
                f"{enemy.name}を倒した。欠片を{enemy.shard_reward}、所持金を{enemy.gold_reward}獲得。"
            )
            return BattleReward(enemy.shard_reward, enemy.gold_reward)

    return BattleReward(0, 0)