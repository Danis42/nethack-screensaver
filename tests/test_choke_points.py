import numpy as np

from autoascend.combat.fight_heur import choke_point_bonus


def _level(rows):
    walkable = np.array([[c != '#' for c in row] for row in rows])
    no_diagonal = np.array([[c == '+' for c in row] for row in rows])
    return walkable, no_diagonal


ROOM_AND_DOOR = [
    "##########",
    "#.....####",
    "#.....####",
    "#.....+...",
    "#.....####",
    "##########",
]


def test_doorway_scores_highest_and_open_floor_lowest():
    bonus = choke_point_bonus(*_level(ROOM_AND_DOOR))
    door = bonus[3, 6]
    assert door >= np.nanmax(bonus[1:5, 1:6])
    assert bonus[2, 3] < bonus[3, 5] < door  # room centre < next to the door < doorway


def test_bonus_slopes_towards_the_doorway():
    bonus = choke_point_bonus(*_level(ROOM_AND_DOOR))
    # greedy one-step moves from the room must lead to the door
    assert bonus[3, 3] < bonus[3, 4] < bonus[3, 5] < bonus[3, 6]


def test_walls_get_no_bonus():
    bonus = choke_point_bonus(*_level(ROOM_AND_DOOR))
    assert np.isnan(bonus[0, 0])


def test_squares_along_a_wall_get_no_bonus_of_their_own():
    walkable, no_diagonal = _level(["#" * 12] + ["#" + "." * 10 + "#"] * 9 + ["#" * 12])
    bonus = choke_point_bonus(walkable, no_diagonal)
    assert bonus[1, 5] == 0 and bonus[5, 5] == 0  # wall edge and centre alike
    assert bonus[1, 1] > 0  # corner


def _monsters(*names):
    from autoascend.glyph import MON
    return [(1, 0, i, MON.permonst(MON.from_name(n)), 0) for i, n in enumerate(names)]


def test_fast_pack_needs_two_fast_melee_monsters():
    from autoascend.combat.fight_heur import fast_pack
    assert fast_pack(_monsters('soldier ant', 'soldier ant'))
    assert fast_pack(_monsters('killer bee', 'fire ant', 'newt'))
    assert not fast_pack(_monsters('soldier ant', 'gnome lord'))
    assert not fast_pack(_monsters('dwarf', 'hill orc', 'hill orc'))
