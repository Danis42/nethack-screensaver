"""Plan 04-02: below XL 10 the bot keeps away from hostile unicorns and fights one only when cornered."""
from types import SimpleNamespace

import numpy as np

from autoascend.combat import fight_heur, unicorns

HERO = (5, 5)


def _mon(name, y, x):
    return (1, y, x, SimpleNamespace(mname=name, mmove=24, mlet='u'), 0)


def _agent(monsters, xl, walkable=None, hp=40):
    walkable = np.ones((11, 11), bool) if walkable is None else walkable
    inventory = SimpleNamespace(get_ranged_combinations=lambda: [], get_best_ranged_set=lambda **_: (None, None),
                                items=[], engraving_below_me='', items_below_me=[])
    return SimpleNamespace(blstats=SimpleNamespace(y=HERO[0], x=HERO[1], hitpoints=hp, max_hitpoints=hp,
                                                   experience_level=xl),
                           current_level=lambda: SimpleNamespace(walkable=walkable),
                           get_visible_monsters=lambda: monsters, inventory=inventory, can_engrave=lambda: False)


def _best(agent):
    dis = np.full(agent.current_level().walkable.shape, -1)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if (dy or dx) and agent.current_level().walkable[HERO[0] + dy, HERO[1] + dx]:
                dis[HERO[0] + dy, HERO[1] + dx] = 1
    heatmap, actions = fight_heur.get_priorities(agent)
    actions += fight_heur.get_move_actions(agent, dis, heatmap)
    return max(actions, key=lambda a: a[0])[1]


def test_only_hostile_unicorns_below_xl_10_are_avoided():
    agent = _agent([], xl=9)
    assert unicorns.avoided(agent, SimpleNamespace(mname='white unicorn'))
    assert not unicorns.avoided(agent, SimpleNamespace(mname='jackal'))
    assert not unicorns.avoided(agent, object())  # a monster stand-in without a name
    agent.blstats.experience_level = unicorns.ENGAGE_XL
    assert not unicorns.avoided(agent, SimpleNamespace(mname='black unicorn'))


def test_below_xl_10_an_adjacent_unicorn_is_fought_as_before():
    # it attacks twice a turn anyway; stepping away let the route lead straight back in (seed 7432)
    unicorn = _mon('white unicorn', 5, 6)
    assert _best(_agent([unicorn], xl=7)) == ('melee', 0, 1)


def test_below_xl_10_the_bot_does_not_walk_up_to_a_unicorn():
    unicorn = _mon('black unicorn', 5, 8)
    action = _best(_agent([unicorn], xl=7))
    assert action[0] == 'move' and max(abs(5 + action[1] - 5), abs(5 + action[2] - 8)) > 1


def test_from_xl_10_the_bot_engages_as_before():
    unicorn = _mon('white unicorn', 5, 6)
    assert _best(_agent([unicorn], xl=10)) == ('melee', 0, 1)
    far = _mon('white unicorn', 5, 8)
    action = _best(_agent([far], xl=10))
    assert action in (('move', 0, 1), ('move', -1, 1), ('move', 1, 1))


def test_a_far_unicorn_does_not_keep_the_bot_in_a_fight():
    from autoascend.agent import Agent
    agent = Agent.__new__(Agent)
    agent._monster_since = {}
    agent.blstats = SimpleNamespace(time=100, y=5, x=5, experience_level=7)
    agent.current_level = lambda: SimpleNamespace(key=lambda: (0, 3))
    agent.stats_logger = SimpleNamespace(log_event=lambda _: None)
    far, near = _mon('white unicorn', 5, 8), _mon('white unicorn', 5, 6)
    assert agent._coming_monsters([far, near]) == [near]
    agent.blstats.experience_level = 10
    assert agent._coming_monsters([far]) == [far]
