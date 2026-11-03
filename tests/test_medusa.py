import numpy as np

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
