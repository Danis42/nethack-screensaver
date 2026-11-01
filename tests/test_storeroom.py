import numpy as np

from autoascend.agent import storeroom_chests
from autoascend.glyph import G


def _map(*chests):
    glyphs = np.zeros((21, 79), dtype=np.int16)
    for y, x in chests:
        glyphs[y, x] = min(G.CHEST)
    return glyphs


def test_lone_chest_is_kept():
    assert not storeroom_chests(_map((5, 5))).any()


def test_two_far_chests_are_kept():
    assert not storeroom_chests(_map((5, 5), (5, 40), (15, 70))).any()


def test_a_group_is_avoided():
    assert storeroom_chests(_map((5, 5), (6, 8), (8, 7))).sum() == 3


def test_a_far_chest_stays_out_of_the_group():
    mask = storeroom_chests(_map((5, 5), (6, 8), (8, 7), (15, 70)))
    assert not mask[15, 70] and mask.sum() == 3
