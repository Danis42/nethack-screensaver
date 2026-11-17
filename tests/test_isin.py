import numpy as np

from autoascend.isin import any_in, isin


def test_any_in_agrees_with_isin_any_on_random_screens():
    rng = np.random.default_rng(0)
    for _ in range(300):
        a = rng.integers(-5, 400, size=(21, 79)).astype(np.int16)[:, ::rng.integers(1, 3)]  # some non-contiguous
        sets = [frozenset(rng.integers(0, 400, size=rng.integers(1, 6)).tolist()) for _ in range(rng.integers(1, 3))]
        assert any_in(a, *sets) == bool(isin(a, *sets).any())


def test_lists_and_sets_give_the_same_answer_as_frozensets():
    a = np.array([[1, 2], [3, 300]], np.int16)
    assert isin(a, [300], {2}).tolist() == isin(a, frozenset({300}), frozenset({2})).tolist() == [[False, True],
                                                                                                    [False, True]]
    assert any_in(a, [7], {8}) is False and any_in(a, (3,)) is True
