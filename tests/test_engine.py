import unittest
from engine import Game, make_map
from agents import POLICIES, simulate
import random

class EngineTests(unittest.TestCase):
    def test_map_reachable_and_merged(self):
        for seed in range(20):
            nodes=make_map(random.Random(seed))
            seen={"start"}
            pending=["start"]
            while pending:
                node=nodes[pending.pop()]
                for child in node["next"]:
                    self.assertEqual(nodes[child]["floor"],node["floor"]+1)
                    if child not in seen:
                        seen.add(child)
                        pending.append(child)
            self.assertEqual(seen,set(nodes))
            self.assertEqual(nodes["boss"]["next"],[])

    def test_reject_invalid_and_stale_without_mutation(self):
        g=Game(42)
        s=g.get_state()
        for action,revision in [("invalid",s["revision"]),(s["actions"][0]["id"],0)]:
            with self.assertRaises(ValueError):
                g.execute_action(action,revision)
            self.assertEqual(s,g.get_state())
        g.execute_action(s["actions"][0]["id"],s["revision"])
        with self.assertRaises(ValueError):
            g.execute_action(s["actions"][0]["id"],s["revision"])

    def test_state_is_snapshot(self):
        g=Game(2)
        s=g.get_state()
        s["map"][0]["next"].clear()
        s["hero"]["hp"]=0
        self.assertTrue(g.get_actions())
        self.assertGreater(g.hero.hp,0)

    def test_seed_and_replay(self):
        a,b=Game(12),Game(12)
        for _ in range(100):
            s=a.get_state()
            self.assertEqual(s,b.get_state())
            if not s["actions"]:
                break
            action=s["actions"][0]["id"]
            a.execute_action(action,s["revision"])
            b.execute_action(action,s["revision"])
        self.assertEqual(a.get_history(),b.get_history())

    def test_boss_no_escape_and_reward(self):
        g=Game(4)
        g._enter("boss")
        g.hero.attack=1000
        g.hero.speed=1000
        g.enemy.speed=0
        self.assertNotIn("escape",{a["id"] for a in g.get_actions()})
        g.execute_action("attack",g.revision)
        self.assertEqual(g.phase,"won")
        self.assertGreaterEqual(g.run.soul_shards,20)

    def test_heal_not_available_at_full_hp(self):
        g=Game(5)
        g._enter("boss")
        self.assertNotIn("heal",{a["id"] for a in g.get_actions()})
        g.hero.hp-=1
        self.assertIn("heal",{a["id"] for a in g.get_actions()})

    def test_agents_finish(self):
        for policy in POLICIES:
            for seed in range(5):
                self.assertIn(simulate(seed,policy),("won","lost"))

if __name__=="__main__":
    unittest.main()
