from unittest import TestCase
from unittest.mock import Mock, patch

import battle
import game
import route
from enemies import ENEMY_TEMPLATES
from items import ITEMS
from models import BattleReward, Hero, PermanentUpgrades, RunState


class JourneyTests(TestCase):
    def replace(self, target, name, value):
        stub = patch.object(target, name, value)
        stub.start()
        self.addCleanup(stub.stop)

    def test_street_map_has_forks_and_rejoins(self):
        rows = route.build_map(8)
        assert len(rows) == 8
        assert sum(node.event is None for node in rows[1]) == 1
        for row, following in zip(rows, rows[1:]):
            accessible = [route.neighbors(node, following) for node in row]
            assert all(accessible)
            assert set.union(*map(set, accessible)) == set(following)
        assert route.neighbors(rows[1][0], rows[2])[1] is rows[2][1]
        assert route.neighbors(rows[1][1], rows[2])[0] is rows[2][1]


    def test_cancel_then_use_item(self):
        hero = Hero(20, 1, 100, 10, 30)
        key = next(iter(hero.bag))
        count = hero.bag[key]
        enemy = ENEMY_TEMPLATES[0].create(1)
        self.replace(battle, "clear_screen", Mock())
        self.replace(battle.random, "random", lambda: 0.99)
        counter = Mock()
        self.replace(battle, "perform_enemy_attack", counter)
        reward = battle.battle(hero, enemy, RunState(), Mock(side_effect=["h", "0", "h", "1", "a"]))
        assert reward == BattleReward(enemy.shard_reward, enemy.gold_reward)
        assert hero.hp == min(hero.max_hp, 1 + ITEMS[key].heal)
        assert hero.bag[key] == count - 1
        counter.assert_called_once()


    def test_deliver_letter(self):
        for name in ("clear_screen", "wait_for_enter", "run_event"):
            self.replace(game, name, Mock())
        self.replace(game, "_handle_battle_floor", Mock(return_value=None))
        result = game.run_once(PermanentUpgrades(), 3, lambda prompt, options: "1")
        assert result.won and result.soul_shards == 3 + game.CLEAR_BONUS_SHARDS
