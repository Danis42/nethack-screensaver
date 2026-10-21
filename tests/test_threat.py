# tests/test_threat.py
import nle.nethack as nh
import pytest

from autoascend.combat import threat


def idx(name):
    return next(i for i in range(nh.NUMMONS) if nh.permonst(i).mname == name)


def test_hit_chance_follows_nethacks_to_hit_roll():
    assert threat.hit_chance(3, 10) == 1.0          # 10 + 10 + 3 = 23 > any d20
    assert threat.hit_chance(0, 10) == pytest.approx(0.95)
    assert threat.hit_chance(3, -5) == pytest.approx(0.45)  # AC -5 counts as -3 on average
    assert threat.hit_chance(0, -30) == 0.0
    assert threat.hit_chance(1, 0) == pytest.approx(0.5)


def test_damage_per_turn_scales_with_dice_and_speed():
    ant = threat.damage_per_turn(idx("soldier ant"), 3, 18, 10)
    assert ant == pytest.approx((2 * 2.5 + 3 * 2.5) * 18 / 12)
    newt = threat.damage_per_turn(idx("newt"), 0, 6, 10)
    assert newt == pytest.approx(0.95 * 1.5 * 6 / 12)
    assert threat.damage_per_turn(idx("soldier ant"), 3, 18, 10, our_speed=16) < ant
    dwarf = threat.damage_per_turn(idx("dwarf"), 2, 6, 10)  # weapon users: monst.c dice only
    assert dwarf == pytest.approx(4.5 * 6 / 12)


def test_passive_and_gaze_attacks_do_no_melee_damage():
    assert threat.damage_per_turn(idx("floating eye"), 2, 1, 10) == 0.0
    assert threat.damage_per_turn(idx("acid blob"), 1, 3, 10) == 0.0


def test_special_attacks():
    for name in ("soldier ant", "werejackal", "chickatrice", "cockatrice", "vampire bat"):
        assert threat.has_special_attack(idx(name)), name
    for name in ("newt", "jackal", "giant bat", "water nymph"):
        assert not threat.has_special_attack(idx(name)), name


def test_unknown_index_is_harmless():
    assert threat.attacks(-1) == () and threat.attacks(10 ** 6) == ()
    assert threat.damage_per_turn(10 ** 6, 5, 12, 10) == 0.0
    assert not threat.has_special_attack(-1)
