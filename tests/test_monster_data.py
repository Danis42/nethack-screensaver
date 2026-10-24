# tests/test_monster_data.py
import nle.nethack as nh
import pytest

from autoascend.combat.monster_data import MONSTERS

AT_BITE, AT_STNG, AT_WEAP = 2, 6, 254
AD_PHYS, AD_DRST, AD_WERE = 0, 7, 29


def entry(name):
    return next(e for e in MONSTERS if e[0] == name)


def test_table_is_aligned_with_nle_monster_indices():
    assert len(MONSTERS) == nh.NUMMONS
    assert [name for name, _ in MONSTERS] == [nh.permonst(i).mname for i in range(nh.NUMMONS)]


def test_known_attacks():
    assert entry("soldier ant")[1] == ((AT_BITE, AD_PHYS, 2, 4), (AT_STNG, AD_DRST, 3, 4))
    assert entry("newt")[1] == ((AT_BITE, AD_PHYS, 1, 2),)
    assert MONSTERS[[n for n, _ in MONSTERS].index("werejackal")][1] == ((AT_BITE, AD_WERE, 1, 4),)
    assert entry("dwarf")[1] == ((AT_WEAP, AD_PHYS, 1, 8),)
    assert entry("lichen")[1][0][1] == 19  # AD_STCK


def test_generator_refuses_a_misaligned_table():
    from scripts.gen_monster_data import align
    parsed = [("newt", ()), ("jackal", ())]
    assert align(parsed, ["newt", "jackal"]) == parsed
    with pytest.raises(SystemExit, match="fox"):
        align(parsed, ["newt", "fox"])
