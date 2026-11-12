import math

import numpy as np
import pytest

from bench.sequential import (NO_EFFECT, anytime_p, contiguous_prefix, discordant, judge_sequential,
                              log_mixture_lr, mcnemar_exact)


def test_discordant_counts_candidate_only_and_baseline_only():
    pairs = [(True, False), (False, True), (True, True), (False, False), (True, False)]
    assert discordant(pairs) == (2, 1)


def test_mcnemar_exact_matches_the_binomial_tail():
    assert mcnemar_exact(15, 5) == pytest.approx(0.04138946533203125)


def test_mcnemar_exact_without_discordant_pairs_is_one():
    assert mcnemar_exact(0, 0) == 1.0


def test_mixture_lr_boundary_at_alpha_005():
    # log(1/0.05) = 2.9957: b = 7 stays under it, b = 8 crosses it
    assert log_mixture_lr(7, 0) == pytest.approx(2.7726, abs=1e-4)
    assert log_mixture_lr(8, 0) == pytest.approx(3.3480, abs=1e-4)
    assert log_mixture_lr(7, 0) < math.log(1 / 0.05) < log_mixture_lr(8, 0)


def test_mixture_lr_without_data_is_zero():
    assert log_mixture_lr(0, 0) == 0.0


def test_mixture_lr_stays_finite_for_huge_counts():
    assert math.isfinite(log_mixture_lr(10000, 10000))
    assert math.isfinite(log_mixture_lr(20000, 0))


def test_one_look_just_under_the_bound_is_open():
    assert judge_sequential([(50, 7, 0)], alpha=0.05, n_planned=1000, mde=0.03).state == "open"


def test_one_look_over_the_bound_is_better_or_worse():
    assert judge_sequential([(50, 8, 0)], alpha=0.05, n_planned=1000, mde=0.03).state == "better"
    assert judge_sequential([(50, 0, 8)], alpha=0.05, n_planned=1000, mde=0.03).state == "worse"


def test_last_look_at_the_planned_size_without_crossing_is_no_detectable_effect():
    v = judge_sequential([(500, 5, 5), (1000, 10, 9)], alpha=0.05, n_planned=1000, mde=0.03)
    assert v.state == NO_EFFECT


def test_earlier_look_without_crossing_is_open():
    v = judge_sequential([(500, 5, 5), (900, 10, 9)], alpha=0.05, n_planned=1000, mde=0.03)
    assert v.state == "open"


def test_a_crossing_at_an_earlier_look_is_kept_when_a_later_look_falls_back():
    looks = [(96, 3, 0), (192, 9, 0), (288, 9, 6)]
    v = judge_sequential(looks, alpha=0.05, n_planned=1000, mde=0.03)
    assert v.state == "better"
    assert (v.n, v.b, v.c) == (192, 9, 0)
    assert v.max_log_lr == pytest.approx(log_mixture_lr(9, 0))


def test_max_log_lr_is_the_running_maximum_and_anytime_p_follows():
    looks = [(96, 6, 0), (192, 6, 4), (288, 6, 6)]
    v = judge_sequential(looks, alpha=0.05, n_planned=1000, mde=0.03)
    assert v.state == "open"
    assert v.max_log_lr == pytest.approx(log_mixture_lr(6, 0))
    assert v.log_lr == pytest.approx(log_mixture_lr(6, 6))
    assert v.anytime_p == pytest.approx(min(1.0, math.exp(-v.max_log_lr)))
    assert anytime_p(-1.0) == 1.0
    assert anytime_p(math.log(20)) == pytest.approx(0.05)


def test_verdict_fields_and_as_dict():
    v = judge_sequential([(100, 12, 4)], alpha=0.05, n_planned=1000, mde=0.03)
    assert v.estimate == pytest.approx(0.08)
    assert v.mcnemar_p == pytest.approx(mcnemar_exact(12, 4))
    assert (v.n_planned, v.mde) == (1000, 0.03)
    d = v.as_dict()
    assert d["state"] == v.state and d["b"] == 12 and d["c"] == 4 and d["n"] == 100


def test_estimate_is_zero_without_games():
    assert judge_sequential([(0, 0, 0)], alpha=0.05, n_planned=1000, mde=0.03).estimate == 0.0


def test_contiguous_prefix_stops_at_the_first_gap():
    assert contiguous_prefix({1000, 1001, 1002, 1004}, 1000) == 3
    assert contiguous_prefix(set(), 1000) == 0


def test_false_positive_rate_under_peeking_stays_within_alpha():
    """Null (b ~ Bernoulli(1/2) per discordant pair, psi only changes how many seeds a pair costs),
    a look after every discordant pair up to 500 pairs, fixed seed."""
    alpha, reps, pairs = 0.05, 2000, 500
    bound = math.log(1 / alpha)
    crosses = [[log_mixture_lr(b, t - b) >= bound for b in range(t + 1)] for t in range(pairs + 1)]
    cross = np.array(crosses[1:], dtype=object)  # row t-1 holds the table for t pairs
    rng = np.random.default_rng(20261112)
    b_t = np.cumsum(rng.random((reps, pairs)) < 0.5, axis=1)
    rejected = 0
    for row in b_t:
        if any(cross[t][row[t]] for t in range(pairs)):
            rejected += 1
    assert 0 < rejected / reps <= alpha  # the test must also be able to reject
