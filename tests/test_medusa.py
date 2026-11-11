import numpy as np

from autoascend import medusa
from autoascend.medusa import crossing_target, landing_square

STAIRS, MEDUSA = {7}, {9}


def test_stairs_first_then_medusa_then_nothing():
    g = np.zeros((21, 79), np.int16)
    assert crossing_target(g, STAIRS, MEDUSA) is None
    g[10, 60] = 9
    assert crossing_target(g, STAIRS, MEDUSA) == (10, 60)
    g[12, 50] = 7
    assert crossing_target(g, STAIRS, MEDUSA) == (12, 50)


def test_landing_square_is_dry_and_nearest():
    walkable = np.zeros((21, 79), bool)
    wet = np.zeros((21, 79), bool)
    walkable[10, 58:63] = True
    wet[10, 60] = True
    assert landing_square(walkable, wet, (10, 60)) in ((10, 59), (10, 61))
    assert landing_square(walkable, wet, (10, 62)) == (10, 62)


def test_stall_landing_here_if_dry_else_a_dry_neighbour():
    walkable = np.ones((5, 5), bool)
    wet = np.zeros((5, 5), bool)
    assert medusa.stall_landing(walkable, wet, (2, 2)) == (2, 2)
    wet[2, 2] = True
    wet[1, :] = True
    wet[2, 1] = wet[2, 3] = True
    assert medusa.stall_landing(walkable, wet, (2, 2)) in {(3, 1), (3, 2), (3, 3)}
    wet[3, :] = True
    assert medusa.stall_landing(walkable, wet, (2, 2)) is None


def test_landing_square_must_be_reachable_over_water():
    walkable = np.zeros((21, 79), bool)
    wet = np.zeros((21, 79), bool)
    wet[5, 10:20] = True  # the hero floats in a channel
    walkable[5, 9] = True  # dry square at the channel's end, far from the target
    walkable[8, 21] = True  # dry square next to the target, behind a wall (nothing passable between)
    assert landing_square(walkable, wet, (8, 22)) == (8, 21)
    assert landing_square(walkable, wet, (8, 22), (5, 15)) == (5, 9)
