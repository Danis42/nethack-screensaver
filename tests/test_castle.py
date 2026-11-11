import numpy as np

from autoascend import castle

SHAPE = (21, 79)


def seen_courtyard(flipped, x_range):
    """Screen masks (wet, known) after seeing one courtyard of a Castle (map columns x_range)."""
    wet = np.zeros(SHAPE, bool)
    known = np.zeros(SHAPE, bool)
    for y in range(5, 12):
        for x in x_range:
            q = castle.to_screen(flipped, (y, x))
            known[q] = True
            wet[q] = castle.MAP[y][x] == '}'
    return wet, known


def test_frame_from_portcullis_glyph():
    dry = np.zeros(SHAPE, bool)
    assert castle.frame([(11, 14)], dry, dry) is False  # staged seed 1
    assert castle.frame([(11, 64)], dry, dry) is True  # staged seeds 2-6
    assert castle.frame([(5, 30)], dry, dry) is None


def test_frame_from_front_or_back_courtyard():
    for flipped in (False, True):
        for x_range in (range(6), range(57, 63)):
            wet, known = seen_courtyard(flipped, x_range)
            assert castle.frame([], wet, known) is flipped
            known[castle.to_screen(flipped, castle.KEY_SQUARES[0 if x_range.start == 0 else 1])] = False
            assert castle.frame([], wet, known) is None


def test_back_entry_squares_match_the_map():
    assert castle.MAP[8][56] == '+' and castle.MAP[8][57] == '.' and castle.MAP[8][55] == '.'
    assert castle.to_screen(False, castle.DOOR) == (11, 64)  # the '+' seen on staged seed 1
    assert castle.to_screen(True, castle.DOOR) == (11, 14)


def test_outside_ring_joins_both_courtyards_but_not_the_inside():
    for flipped in (False, True):
        mask = castle.outside_mask(flipped, SHAPE)
        assert mask[castle.to_screen(flipped, castle.STAND)]
        assert not mask[castle.to_screen(flipped, castle.TRAP_DOOR)]
        start = castle.to_screen(flipped, (8, 2))  # near courtyard, drawbridge side
        path = castle.float_path(mask, start, castle.to_screen(flipped, castle.STAND))
        assert path is not None and path[0] == start and 60 < len(path) < 100
        assert all(max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1 for a, b in zip(path, path[1:]))


def test_break_candidate_prefers_boulder_next_to_unseen():
    from autoascend import boulders
    b = np.zeros((5, 7), bool)
    b[2, 1] = b[2, 5] = True
    dis = np.full((5, 7), -1)
    dis[2, 2] = 1
    dis[2, 4] = 2
    seen = np.ones((5, 7), bool)
    seen[2, 6] = False
    assert boulders.break_candidate(b, dis, seen) == ((2, 4), (2, 5))
    seen[2, 6] = True
    assert boulders.break_candidate(b, dis, seen) == ((2, 2), (2, 1))
    assert boulders.break_candidate(b, np.full((5, 7), -1), seen) is None
