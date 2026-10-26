import numpy as np

from autoascend import boulders


def grid(rows):
    return np.array([[c for c in r] for r in rows])


def test_push_along_corridor_into_unseen():
    # hero side reachable on the left, boulder in a corridor, unseen beyond it
    m = grid(["#####",
              "..0??",
              "#####"])
    b = m == "0"
    seen = m != "?"
    walkable = m == "."
    dis = np.where(walkable, 1, -1)
    none = np.zeros_like(b)
    out = boulders.push_candidates(b, walkable, b, none, seen, dis, set())
    assert out[0] == ((1, 1), (1, 2), (1, 3))


def test_no_push_into_wall_or_other_boulder_or_repeat():
    m = grid([".0#",
              ".00",
              "..."])
    b = m == "0"
    seen = np.ones_like(b)
    walkable = m == "."
    dis = np.where(walkable, 1, -1)
    none = np.zeros_like(b)
    out = boulders.push_candidates(b, walkable, b, none, seen, dis, set())
    assert ((1, 0), (1, 1), (1, 2)) not in out          # another boulder beyond
    assert ((0, 0), (0, 1), (0, 2)) not in out          # wall beyond
    assert ((2, 1), (1, 1), (0, 1)) not in out          # boulder beyond (north)
    tried = {(b_, t) for _, b_, t in out}
    assert boulders.push_candidates(b, walkable, b, none, seen, dis, tried) == []


def test_no_diagonal_push_through_doorway():
    m = grid(["...",
              ".0.",
              "..."])
    b = m == "0"
    seen = np.ones_like(b)
    walkable = m != "0"
    dis = np.where(walkable, 1, -1)
    doors = np.zeros_like(b)
    doors[2, 2] = True
    out = boulders.push_candidates(b, walkable, b, doors, seen, dis, set())
    assert ((0, 0), (1, 1), (2, 2)) not in out
    assert ((0, 1), (1, 1), (2, 1)) in out


def test_nothing_left():
    seen = np.ones((3, 3), bool)
    walkable = np.ones((3, 3), bool)
    dis = np.ones((3, 3), int)
    down = np.zeros((3, 3), bool)
    assert boulders.nothing_left(seen, walkable, dis, down)
    down[1, 1] = True
    assert not boulders.nothing_left(seen, walkable, dis, down)
