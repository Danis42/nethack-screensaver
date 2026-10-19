import numpy as np

from autoascend.global_logic import boulder_pushes


def test_push_from_a_reachable_side_into_free_floor():
    walkable = np.zeros((5, 7), bool)
    walkable[2, 1:6] = True  # a corridor: . . 0 . .
    boulders = np.zeros((5, 7), bool)
    boulders[2, 3] = True
    dis = np.full((5, 7), -1)
    dis[2, 1], dis[2, 2] = 1, 0  # we stand west of the boulder
    assert boulder_pushes(boulders, walkable, dis) == [((2, 2), (0, 1))]  # stand west, push east


def test_no_push_into_a_wall_or_another_boulder():
    walkable = np.zeros((5, 7), bool)
    walkable[2, 1:4] = True
    boulders = np.zeros((5, 7), bool)
    boulders[2, 3] = True  # east of it is rock
    dis = np.full((5, 7), -1)
    dis[2, 2] = 0
    assert boulder_pushes(boulders, walkable, dis) == []
