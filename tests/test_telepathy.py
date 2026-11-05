from types import SimpleNamespace

from autoascend.telepathy import eye_target


def _mon(name, y, x, dis=3):
    return (dis, y, x, SimpleNamespace(mname=name), 0)


def test_targets_the_nearest_eye_with_a_blindfold():
    assert eye_target([_mon('floating eye', 5, 9, 4), _mon('floating eye', 2, 2, 1)], False, True) == (2, 2)


def test_not_when_telepathic_or_without_blindfold():
    assert eye_target([_mon('floating eye', 5, 9)], True, True) is None
    assert eye_target([_mon('floating eye', 5, 9)], False, False) is None


def test_not_while_another_hostile_is_in_view():
    assert eye_target([_mon('floating eye', 5, 9), _mon('jackal', 6, 6)], False, True) is None


from autoascend.glyph import Hunger
from autoascend.telepathy import may_eat_eye, eye_corpse_squares

EYE_ID = 7


def test_may_eat_eye_unless_satiated_and_overfull():
    assert may_eat_eye(Hunger.NOT_HUNGRY, overfull=False)
    assert may_eat_eye(Hunger.HUNGRY, overfull=True)  # the flag only matters while Satiated
    assert may_eat_eye(Hunger.SATIATED, overfull=False)  # under 1500 nutrition: 10 more cannot choke
    assert not may_eat_eye(Hunger.SATIATED, overfull=True)  # maybe near 2000: eat.c:3138 choke


def test_eye_corpse_squares_fresh_eyes_only():
    corpses = {(3, 4): {EYE_ID: 100}, (5, 5): {EYE_ID: 40, 9: 100}, (6, 6): {9: 100}}
    assert eye_corpse_squares(corpses, EYE_ID, now=120) == [(3, 4)]  # (5, 5) is 80 turns old
    assert eye_corpse_squares(corpses, EYE_ID, now=150) == [(3, 4)]
    assert eye_corpse_squares(corpses, EYE_ID, now=151) == []
