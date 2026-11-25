"""Human CUI client; communicates exclusively through JSON HTTP."""
import argparse
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

LABELS = {"start":"出発","battle":"戦闘","event":"遭遇","rest":"休息","treasure":"宝箱",
          "merchant":"商人","elite":"強敵","boss":"ボス"}

def request(base,path,data=None):
    req = Request(base+path,data=None if data is None else json.dumps(data).encode(),
                  headers={"Content-Type":"application/json"} if data is not None else {})
    with urlopen(req,timeout=5) as response:
        return json.load(response)

def display(s):
    h,r = s["hero"],s["resources"]
    print("\n"+"="*60)
    print(f"HP {h['hp']}/{h['max_hp']}  ATK {h['attack']}  DEF {h['defense']}  SPD {h['speed']}  薬 {h['potions']}  G {r['gold']}  欠片 {r['soul_shards']}")
    if s["phase"] == "route":
        print("分岐マップ（左→右の接続先ID）")
        for n in s["map"]:
            mark = "*" if n["id"]==s["current"] else "+" if n["id"] in s["visited"] else " "
            print(f"{mark}{n['id']:6} {LABELS[n['kind']]:4} -> {', '.join(n['next']) or '-'}")
    if s["enemy"]:
        e=s["enemy"]
        print(f"{e['name']} HP {e['hp']} ATK {e['attack']} DEF {e['defense']} SPD {e['speed']}")
        print("敵の予告:", "強攻撃" if s["intent"]=="heavy" else "通常攻撃")
    if s["event"]:
        print(s["event"]["name"],s["event"]["description"])
    for message in s["messages"]:
        print(message)
    for i,a in enumerate(s["actions"],1):
        print(f"{i}: {a['label']}",a.get("node",""),a.get("description",""),
              f"費用 {a['cost']}" if "cost" in a else "")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8765")
    base=parser.parse_args().url.rstrip("/")
    try:
        while True:
            s=request(base,"/state")
            display(s)
            if not s["actions"]:
                choice=input(f"{s['phase']} / [n]再挑戦 [q]終了: ").strip()
                if choice=="q":
                    break
                if choice=="n":
                    request(base,"/new",{"revision":s["revision"]})
                continue
            choice=input("選択 [q]終了: ").strip()
            if choice=="q":
                break
            if not choice.isascii() or not choice.isdigit() or len(choice)>4 or not 1<=int(choice)<=len(s["actions"]):
                continue
            try:
                request(base,"/action",{"action":s["actions"][int(choice)-1]["id"],"revision":s["revision"]})
            except HTTPError as exc:
                print("操作が拒否された:",exc.read().decode())
    except (KeyboardInterrupt,EOFError):
        pass
    except URLError as exc:
        print("サーバーへの接続エラー:",exc)

if __name__ == "__main__":
    main()
