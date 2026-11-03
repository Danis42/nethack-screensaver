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
