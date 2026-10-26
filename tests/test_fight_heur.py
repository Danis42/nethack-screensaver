from types import SimpleNamespace

from autoascend.combat.fight_heur import drop_floating_eye_melee


def _mon(name, y, x):
    return (1, y, x, SimpleNamespace(mname=name), 0)


def test_drops_melee_on_floating_eye():
    monsters = [_mon("floating eye", 5, 6), _mon("jackal", 4, 5)]
    actions = [(-94, ("melee", 0, 1)), (16, ("melee", -1, 0)), (3, ("move", 1, 0))]
    assert drop_floating_eye_melee(actions, monsters, (5, 5), blind=False) == actions[1:]


def test_keeps_floating_eye_melee_when_blind():
    monsters = [_mon("floating eye", 5, 6)]
    actions = [(-94, ("melee", 0, 1))]
    assert drop_floating_eye_melee(actions, monsters, (5, 5), blind=True) == actions


def test_keeps_ranged_attacks_on_floating_eye():
    monsters = [_mon("floating eye", 5, 7)]
    actions = [(11, ("ranged", 0, 1))]
    assert drop_floating_eye_melee(actions, monsters, (5, 5), blind=False) == actions


def _standoff_agent(pos=(5, 5)):
    from types import SimpleNamespace

    from autoascend.agent import Agent
    agent = Agent.__new__(Agent)
    agent._monster_since = {}
    agent.blstats = SimpleNamespace(time=100, y=pos[0], x=pos[1])
    agent.current_level = lambda: SimpleNamespace(key=lambda: (0, 3))
    agent.events = []
    agent.stats_logger = SimpleNamespace(log_event=agent.events.append)
    return agent


def test_monster_standing_still_stops_the_standoff():
    from autoascend.agent import STANDOFF_TURNS
    agent = _standoff_agent()
    nymph = (2, 7, 5, object(), 400)
    assert agent._coming_monsters([nymph]) == [nymph]
    agent.blstats.time += STANDOFF_TURNS
    assert agent._coming_monsters([nymph]) == []
    assert agent.events == ['standoff_ignored']


def test_moving_monster_keeps_the_fight():
    from autoascend.agent import STANDOFF_TURNS
    agent = _standoff_agent()
    agent._coming_monsters([(2, 7, 5, object(), 400)])
    agent.blstats.time += STANDOFF_TURNS
    moved = (2, 7, 6, object(), 400)
    assert agent._coming_monsters([moved]) == [moved]


def test_adjacent_still_monster_is_fought():
    from autoascend.agent import STANDOFF_TURNS
    agent = _standoff_agent()
    jelly = (1, 6, 5, object(), 300)
    agent._coming_monsters([jelly])
    agent.blstats.time += STANDOFF_TURNS
    assert agent._coming_monsters([jelly]) == [jelly]


def test_drops_bare_handed_melee_on_cockatrices_only():
    from autoascend.combat.fight_heur import drop_bare_handed_cockatrice_melee
    from autoascend.glyph import MON
    cockatrice = (1, 5, 6, SimpleNamespace(mname="chickatrice", mlet=chr(MON.S_COCKATRICE)), 0)
    jackal = (1, 4, 5, SimpleNamespace(mname="jackal", mlet="d"), 0)
    actions = [(50, ("melee", 0, 1)), (16, ("melee", -1, 0)), (3, ("move", 1, 0))]
    assert drop_bare_handed_cockatrice_melee(actions, [cockatrice, jackal], (5, 5), True) == actions[1:]
    assert drop_bare_handed_cockatrice_melee(actions, [cockatrice, jackal], (5, 5), False) == actions
