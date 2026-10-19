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
