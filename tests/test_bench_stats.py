import pytest

from bench.stats import CHECKPOINTS, Z95, judge, newcombe, wilson


def test_wilson_interval_stays_inside_0_and_1():
    lo, hi = wilson(0, 10, Z95)
    assert lo == pytest.approx(0.0, abs=1e-12) and 0.25 < hi < 0.35
    lo, hi = wilson(10, 10, Z95)
    assert 0.65 < lo < 0.75 and hi == pytest.approx(1.0)


def test_newcombe_matches_the_published_example():
    # Newcombe (1998), method 10, example (a): 56/70 vs 48/80
    diff, lo, hi = newcombe(56, 70, 48, 80, Z95)
    assert diff == pytest.approx(0.2, abs=1e-12)
    assert lo == pytest.approx(0.0524, abs=1e-4)
    assert hi == pytest.approx(0.3339, abs=1e-4)


def test_the_lucky_choke_point_run_is_not_a_win():
    # 286 vs 262 of 576 reached Dlvl 6+; the repeat run showed it was noise
    assert judge(286, 576, 262, 576, 576).state == "open"


def test_a_big_effect_is_called_early():
    v = judge(330, 576, 262, 576, 576)
    assert v.state == "better" and v.lo > 0
    assert judge(262, 576, 330, 576, 576).state == "worse"


def test_no_difference_is_only_declared_at_the_last_checkpoint():
    assert judge(500, 1152, 500, 1152, CHECKPOINTS[-1]).state == "no measurable difference"
    assert judge(100, 192, 100, 192, 192).state == "open"


def test_verdict_reports_the_smallest_detectable_difference():
    v = judge(500, 1152, 500, 1152, CHECKPOINTS[-1])
    assert 0.03 < v.detectable < 0.05
    assert v.as_dict() == {"state": v.state, "checkpoint": CHECKPOINTS[-1], "diff": v.diff, "lo": v.lo,
                           "hi": v.hi, "detectable": v.detectable}


def test_empty_sides_are_rejected():
    with pytest.raises(ValueError):
        judge(0, 0, 5, 10, 192)


def _pairs(n10, n01, n11, n00):
    return [(True, False)] * n10 + [(False, True)] * n01 + [(True, True)] * n11 + [(False, False)] * n00


def test_paired_interval_matches_a_hand_computed_example():
    from bench.stats import judge_paired
    # n = 100, candidate-only 15, baseline-only 5: d = 0.10, se = sqrt(20 - 100 * 0.01) / 100
    v = judge_paired(_pairs(15, 5, 30, 50), CHECKPOINTS[-1])
    assert v.diff == pytest.approx(0.10)
    assert v.lo == pytest.approx(0.10 - Z95 * 19 ** 0.5 / 100)
    assert v.hi == pytest.approx(0.10 + Z95 * 19 ** 0.5 / 100)
    assert v.state == "better" and v.checkpoint == CHECKPOINTS[-1]


def test_pairs_cancel_shared_luck():
    from bench.stats import judge_paired
    # same 25% rate on both sides, games agree except 4 swaps each way: interval is narrow
    v = judge_paired(_pairs(4, 4, 284, 860), CHECKPOINTS[-1])
    assert v.diff == 0 and v.state == "no measurable difference" and v.detectable < 0.01
    assert judge_paired(_pairs(0, 0, 10, 182), 192).state == "open"  # no discordant pairs, early


def test_paired_needs_games():
    from bench.stats import judge_paired
    with pytest.raises(ValueError):
        judge_paired([], 192)
