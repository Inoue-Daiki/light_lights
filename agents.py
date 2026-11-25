"""Reproducible baseline policy comparison; no LLM or network required."""
import argparse
import json
from engine import Game

POLICIES = ("aggressive","cautious","merchant","balanced")

def choose(state, policy):
    actions = state["actions"]
    ids = {a["id"]:a for a in actions}
    h = state["hero"]
    if state["phase"]=="battle":
        threshold = {"aggressive":0.2,"cautious":0.65,"merchant":0.4,"balanced":0.45}[policy]
        if "heal" in ids and h["hp"]/h["max_hp"]<=threshold:
            return "heal"
        if policy=="cautious" and "escape" in ids and h["hp"]<=3:
            return "escape"
        if policy!="aggressive" and state["intent"]=="heavy" and state["enemy"]["hp"]>h["attack"]:
            return "guard"
        return "attack"
    if state["phase"]=="route":
        orders = {"aggressive":["elite","battle","treasure","rest","event","merchant","boss"],
                  "cautious":["rest","treasure","merchant","event","battle","elite","boss"],
                  "merchant":["treasure","merchant","battle","rest","event","elite","boss"],
                  "balanced":["treasure","rest","battle","event","merchant","elite","boss"]}
        return min(actions,key=lambda a:orders[policy].index(a["kind"]))["id"]
    if state["phase"]=="upgrade":
        for key in (("2","3","1","4") if policy=="aggressive" else ("3","2","1","4")):
            if "upgrade:"+key in ids:
                return "upgrade:"+key
    if state["phase"]=="merchant" and h["potions"]<3 and "buy:potion" in ids:
        return "buy:potion"
    if "rest" in ids:
        return "rest" if h["hp"]<h["max_hp"]*0.8 else "train"
    if state["phase"]=="treasure":
        return "gold" if policy=="merchant" else actions[0]["id"]
    if state["phase"]=="event" and policy=="aggressive":
        return actions[0]["id"]
    if "leave" in ids:
        return "leave"
    if state["phase"]=="event":
        return min(actions,key=lambda a:a.get("damage",0)+a.get("cost",0))["id"]
    return actions[0]["id"]

def simulate(seed,policy,limit=500):
    game=Game(seed)
    for _ in range(limit):
        state=game.get_state()
        if not state["actions"]:
            break
        game.execute_action(choose(state,policy),state["revision"])
    return game.phase

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--runs",type=int,default=50)
    p.add_argument("--seed",type=int,default=0)
    args=p.parse_args()
    if args.runs<1:
        p.error("--runs must be positive")
    for policy in POLICIES:
        outcomes=[simulate(args.seed+i,policy) for i in range(args.runs)]
        print(json.dumps({"policy":policy,"runs":args.runs,"wins":outcomes.count("won"),
                          "losses":outcomes.count("lost"),"unfinished":sum(x not in ("won","lost") for x in outcomes)}))

if __name__=="__main__":
    main()
