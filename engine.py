"""Headless v0.2 game engine. No console or network I/O."""
from __future__ import annotations

import math
import random
from dataclasses import asdict
from copy import deepcopy

import config as cfg
from battle import get_dodge_chance, get_escape_chance
from content_data import load_content
from enemies import ENEMY_TEMPLATES
from events import RISK_OPTIONS, FREE_EVENT_TEMPLATES, PAID_EVENT_TEMPLATES
from models import PermanentUpgrades, RunState
from shop import SHOP_UPGRADES, build_hero, reset_upgrades

TYPES = ("battle", "battle", "event", "rest", "treasure", "merchant", "elite")
LABELS = {"battle":"戦闘", "event":"遭遇", "rest":"休息", "treasure":"宝箱",
          "merchant":"商人", "elite":"強敵", "boss":"ボス", "start":"出発"}

def make_map(rng):
    layers = [[{"id":"start", "floor":0, "kind":"start", "next":[]}]]
    for floor in range(1, cfg.TOTAL_FLOORS):
        kinds = ["battle", "event", "rest"] if floor == 1 else [rng.choice(TYPES) for _ in range(3)]
        rng.shuffle(kinds)
        layers.append([{"id":f"{floor}-{i}", "floor":floor, "kind":kind, "next":[]}
                       for i, kind in enumerate(kinds)])
    layers.append([{"id":"boss", "floor":cfg.TOTAL_FLOORS, "kind":"boss", "next":[]}])
    for level, following in zip(layers, layers[1:]):
        for i, node in enumerate(level):
            if len(level) == 1 or len(following) == 1:
                node["next"] = [n["id"] for n in following]
            else:
                node["next"] = [following[i]["id"]]
                node["next"].append(following[(i + rng.choice((1, 2))) % 3]["id"])
    return {node["id"]:node for layer in layers for node in layer}

class Game:
    def __init__(self, seed=None):
        self.upgrades = PermanentUpgrades()
        self.run = RunState()
        self.revision = 0
        self.history = []
        self.items = load_content("items.json")
        self.events = load_content("events.json")["choices"]
        self.new_game(seed)

    def new_game(self, seed=None):
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer")
        self.seed = seed if seed is not None else random.SystemRandom().randrange(2**63)
        self.rng = random.Random(self.seed)
        self.hero = build_hero(self.upgrades)
        self.run = RunState(soul_shards=self.run.soul_shards)
        self.nodes = make_map(self.rng)
        self.current = "start"
        self.visited = ["start"]
        self.phase = "route"
        self.enemy = None
        self.event = None
        self.turn = 0
        self.relics = []
        self.messages = ["冒険を開始した。"]
        self.history = []
        self.revision += 1
        return self.get_state()

    def _log(self, message):
        self.messages.append(message)

    def _option(self, key, label, **details):
        return {"id":key, "label":label, **details}

    def _intent(self):
        return "heavy" if self.turn % 3 == 2 else "attack"

    def get_actions(self):
        o = self._option
        h = self.hero
        if self.phase == "route":
            return [o("go:"+n, LABELS[self.nodes[n]["kind"]], node=n,
                      kind=self.nodes[n]["kind"]) for n in self.nodes[self.current]["next"]]
        if self.phase == "battle":
            result = [o("attack","攻撃"), o("guard","防御")]
            if h.potions and h.hp < h.max_hp:
                result.append(o("heal","回復薬"))
            if self.nodes[self.current]["kind"] != "boss":
                result.append(o("escape","逃走", chance=get_escape_chance(h,self.enemy)))
            return result
        if self.phase == "event":
            if isinstance(self.event, dict):
                return [o(f"event:{i}", e["label"], cost=e["cost"], damage=e["damage"],
                          reward=e["reward"], amount=e["amount"])
                        for i,e in enumerate(self.event["options"]) if self.run.gold >= e["cost"]]
            return [o("risk:"+e.key, e.label+"リスク",cost=e.cost,chance=e.success_rate,
                      reward=self.event.reward_kind,amount=e.amount*(4 if self.event.reward_kind=="heal" else 1))
                    for e in RISK_OPTIONS if self.run.gold >= e.cost] + [o("leave","見送る")]
        if self.phase == "rest":
            return [o("rest","HPを回復",amount=math.ceil(h.max_hp*0.35)),o("train","攻撃力+1")]
        if self.phase == "treasure":
            return [o("relic:"+r["id"],r["name"],description=r["description"])
                    for r in self.items["relics"] if r["id"] not in self.relics] + [o("gold","15Gを取得")]
        if self.phase == "merchant":
            p = self.items["potion"]
            return ([o("buy:potion",p["name"],cost=p["price"])] if self.run.gold >= p["price"] else []) + [o("leave","立ち去る")]
        if self.phase == "upgrade":
            return [o("upgrade:"+u.key,u.title,cost=u.cost,amount=u.hero_gain)
                    for u in SHOP_UPGRADES if self.run.soul_shards >= u.cost] + [o("leave","進む")]
        return []

    def get_state(self):
        event = None
        if self.phase == "event":
            event = {"name":self.event["name"],"description":self.event["description"]} if isinstance(self.event,dict) else {"name":self.event.name,"description":self.event.description}
        return {"seed":self.seed,"revision":self.revision,"phase":self.phase,
                "hero":asdict(self.hero),"resources":asdict(self.run),"upgrades":asdict(self.upgrades),
                "map":deepcopy(list(self.nodes.values())), "current":self.current,"visited":list(self.visited),
                "enemy":asdict(self.enemy) if self.enemy is not None else None,
                "intent":self._intent() if self.phase=="battle" else None,"event":event,
                "relics":list(self.relics),"messages":list(self.messages),"actions":self.get_actions()}

    def get_history(self):
        return deepcopy(self.history)

    def _reward(self, kind, amount):
        if kind == "heal":
            amount = self.hero.heal(amount)
        elif kind == "gold":
            self.run.gold += amount
        elif kind == "potion":
            self.hero.potions += amount
        elif kind in ("attack","defense","speed"):
            setattr(self.hero,kind,getattr(self.hero,kind)+amount)
        else:
            raise ValueError("unknown reward")
        self._log(f"{kind}: +{amount}")

    def _enter(self, node):
        self.current = node
        self.visited.append(node)
        n = self.nodes[node]
        kind = n["kind"]
        self.phase = kind
        self._log(LABELS[kind]+"に進んだ。")
        if kind in ("battle","elite","boss"):
            self.phase = "battle"
            self.enemy = self.rng.choice(ENEMY_TEMPLATES).create(n["floor"])
            self.turn = 0
            if kind != "battle":
                self.enemy.name = "Guardian" if kind=="boss" else "Elite "+self.enemy.name
                self.enemy.hp += 8 if kind=="boss" else 5
                self.enemy.attack += 2
                self.enemy.shard_reward += 8
                self.enemy.gold_reward += 6
        elif kind == "event":
            mode = self.rng.randrange(3)
            if mode == 0:
                self.event = self.rng.choice(self.events)
            elif mode == 1:
                event = self.rng.choice(FREE_EVENT_TEMPLATES)
                self._log(event.flavor_text)
                self._reward(event.reward_kind,self.rng.randint(event.min_amount,event.max_amount))
                self.phase = "route"
            else:
                self.event = self.rng.choice(PAID_EVENT_TEMPLATES)

    def _hit(self, attacker, defender, heavy=False, guard=False):
        if self.rng.random() <= get_dodge_chance(attacker.speed,defender.speed):
            self._log("攻撃を回避した。")
            return
        damage = max(cfg.MIN_DAMAGE, attacker.attack + (3 if heavy else 0) - defender.defense +
                     self.rng.randint(cfg.DAMAGE_VARIANCE_MIN,cfg.DAMAGE_VARIANCE_MAX))
        if guard:
            damage = max(1,damage//2)
        defender.hp = max(0,defender.hp-damage)
        self._log(("敵" if attacker is self.enemy else "主人公")+f"の攻撃: {damage}ダメージ")

    def _death(self):
        reset_upgrades(self.upgrades)
        self.phase = "lost"
        self.enemy = None
        self._log("力尽きた。恒久強化を失った。")

    def _battle(self, action):
        h,e = self.hero,self.enemy
        heavy = self._intent()=="heavy"
        if action == "escape":
            if self.rng.random() <= get_escape_chance(h,e):
                targets = [k for k in ("gold","soul_shards") if getattr(self.run,k)>0]
                if targets:
                    k = self.rng.choice(targets)
                    lost = math.ceil(getattr(self.run,k)*cfg.ESCAPE_PENALTY_RATE)
                    setattr(self.run,k,getattr(self.run,k)-lost)
                    self._log(f"逃走: {k} -{lost}")
                else:
                    self._log("逃走した。")
                self.enemy = None
                self.phase = "route"
                return
            self._log("逃走に失敗した。")
            self._hit(e,h,heavy)
        elif action == "guard":
            self._hit(e,h,heavy,guard=True)
        else:
            def player():
                if action == "heal":
                    h.potions -= 1
                    self._reward("heal",self.items["potion"]["heal"])
                else:
                    self._hit(h,e)
            if h.speed >= e.speed:
                player()
                if e.is_alive():
                    self._hit(e,h,heavy)
            else:
                self._hit(e,h,heavy)
                if h.is_alive():
                    player()
        self.turn += 1
        if not h.is_alive():
            self._death()
        elif not e.is_alive():
            self.run.gold += e.gold_reward
            self.run.soul_shards += e.shard_reward
            self._log(f"勝利: {e.gold_reward}G / 欠片{e.shard_reward}")
            self.enemy = None
            if self.current == "boss":
                self.run.soul_shards += cfg.CLEAR_BONUS_SHARDS
                self.phase = "won"
                self._log("最深部を突破した。")
            else:
                self.phase = "upgrade"

    def execute_action(self, action, revision):
        if type(revision) is not int or revision != self.revision:
            raise ValueError("stale revision")
        if not isinstance(action,str) or action not in {a["id"] for a in self.get_actions()}:
            raise ValueError("invalid action")
        self.messages = []
        before = self.phase
        if before == "route":
            self._enter(action[3:])
        elif before == "battle":
            self._battle(action)
        elif before == "event":
            if action.startswith("event:"):
                e = self.event["options"][int(action[6:])]
                self.run.gold -= e["cost"]
                self.hero.take_damage(e["damage"])
                if self.hero.is_alive():
                    self._reward(e["reward"],e["amount"])
            elif action.startswith("risk:"):
                e = next(e for e in RISK_OPTIONS if e.key == action[5:])
                self.run.gold -= e.cost
                if self.rng.random() <= e.success_rate:
                    kind = self.event.reward_kind
                    self._reward(kind,e.amount*(4 if kind=="heal" else 1))
                else:
                    self._log("挑戦に失敗した。")
            self.event = None
            self.phase = "route"
            if not self.hero.is_alive():
                self._death()
        elif before == "rest":
            self._reward("heal",math.ceil(self.hero.max_hp*0.35)) if action=="rest" else self._reward("attack",1)
            self.phase = "route"
        elif before == "treasure":
            if action == "gold":
                self._reward("gold",15)
            else:
                r = next(r for r in self.items["relics"] if r["id"]==action[6:])
                self.relics.append(r["id"])
                self._reward(r["stat"],r["amount"])
            self.phase = "route"
        elif before == "merchant":
            if action == "leave":
                self.phase = "route"
            else:
                self.run.gold -= self.items["potion"]["price"]
                self._reward("potion",1)
        elif before == "upgrade":
            if action == "leave":
                self.phase = "route"
            else:
                u = next(u for u in SHOP_UPGRADES if u.key==action[8:])
                self.run.soul_shards -= u.cost
                setattr(self.upgrades,u.field_name,getattr(self.upgrades,u.field_name)+u.field_gain)
                if u.field_name == "hp":
                    self.hero.max_hp += u.hero_gain
                setattr(self.hero,u.field_name,getattr(self.hero,u.field_name)+u.hero_gain)
                self._log(u.success_message)
        self.revision += 1
        self.history.append({"revision":self.revision,"phase":before,"action":action,
                             "node":self.current,"messages":list(self.messages),
                             "hp":self.hero.hp,"gold":self.run.gold,"shards":self.run.soul_shards})
        return self.get_state()
