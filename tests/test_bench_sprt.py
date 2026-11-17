import math

import pytest

from bench.sequential import NO_EFFECT, judge_sequential
from bench.sprt import bounds, judge_declared, judge_sprt, log_lr, plan, power_report, run, theta1

ARGS = dict(alpha=0.0167, power=0.8, n_planned=6624, mde=0.04, psi=0.46)


def test_theta1_moves_toward_the_improvement():
    assert theta1(0.04, 0.46) == pytest.approx(0.5 + 0.04 / 0.92)
    assert theta1(0.04, 0.46, lower_is_better=True) == pytest.approx(0.5 - 0.04 / 0.92)


def test_theta1_refuses_an_mde_not_below_psi():
    with pytest.raises(ValueError):
        theta1(0.05, 0.05)


def test_log_lr_is_zero_without_data_and_negative_when_balanced():
    assert log_lr(0, 0, 0.6) == 0.0
    assert log_lr(10, 10, 0.6) < 0


def test_bounds_are_wald_lower_and_ville_upper():
    lower, upper = bounds(0.0167, 0.8)
    assert upper == pytest.approx(math.log(1 / 0.0167))
    assert lower == pytest.approx(math.log(0.2 / (1 - 0.0167)))


def test_better_exactly_when_the_upper_bound_is_crossed():
    th1, (_, upper) = theta1(0.04, 0.46), bounds(0.0167, 0.8)
    b = next(k for k in range(1, 1000) if log_lr(k, 0, th1) >= upper)
    assert judge_sprt([(b * 3, b, 0)], **ARGS).state == "better"
    assert judge_sprt([(b * 3, b - 1, 0)], **ARGS).state == "open"


def test_lower_bound_gives_no_win():
    assert judge_sprt([(96, 10, 30)], **ARGS).state == NO_EFFECT


def test_never_worse_even_for_a_large_loss():
    assert judge_sprt([(960, 50, 300)], **ARGS).state == NO_EFFECT


def test_lower_is_better_metric_calls_a_drop_better():
    v = judge_sprt([(960, 0, 60)], alpha=0.05, power=0.8, n_planned=6624, mde=0.04, psi=0.2, lower_is_better=True)
    assert v.state == "better"


def test_open_until_the_cap_then_no_effect():
    lower, upper = bounds(0.0167, 0.8)
    assert lower < log_lr(30, 26, theta1(0.04, 0.46)) < upper
    assert judge_sprt([(120, 30, 26)], **ARGS).state == "open"
    assert judge_sprt([(6624, 30, 26)], **ARGS).state == NO_EFFECT


def test_stops_at_the_first_crossing_look():
    v = judge_sprt([(96, 10, 30), (192, 80, 20)], **ARGS)
    assert (v.state, v.n) == (NO_EFFECT, 96)


class _Metric:
    lower_is_better = False


def test_a_plan_without_a_rule_is_judged_by_the_unchanged_mixture_test():
    declared = {"alpha": 0.05, "n_planned": 384, "mde": 0.1, "psi": 0.3, "power": 0.8}  # jobs 19-21 have no rule
    looks = [(96, 10, 2), (192, 30, 5)]
    v, oriented = judge_declared(looks, declared, _Metric)
    assert not oriented and v == judge_sequential(looks, 0.05, 384, 0.1)


def test_a_plan_with_rule_sprt_is_judged_by_the_sprt():
    declared = {"rule": "sprt", "alpha": 0.0167, "n_planned": 6624, "mde": 0.04, "psi": 0.46, "power": 0.8}
    v, oriented = judge_declared([(96, 10, 30)], declared, _Metric)
    assert oriented and v == judge_sprt([(96, 10, 30)], **ARGS)


def test_plan_reaches_the_power_with_false_wins_under_alpha_and_is_the_smallest_size():
    p = plan(0.04, 0.46, 0.0167, 0.8, reps=2000)
    assert p["rule"] == "sprt" and p["n_planned"] % 96 == 0
    assert 0.75 < p["power_at_mde"] < 0.85 and p["false_better_at_0"] <= 0.0167  # out-of-sample estimates
    assert run(p["n_planned"], 0.46, 0.04, 0.04, 0.0167, 0.8, reps=2000)[0] >= 0.8  # the sizing stream reaches it
    assert p["mean_seeds_at_0"] < p["mean_seeds_at_mde"] < p["n_planned"]
    assert run(p["n_planned"] - 96, 0.46, 0.04, 0.04, 0.0167, 0.8, reps=2000)[0] < 0.8


def test_plan_is_deterministic():
    assert plan(0.04, 0.46, 0.0167, 0.8, reps=500) == plan(0.04, 0.46, 0.0167, 0.8, reps=500)


def test_plan_mixture_is_the_old_plan_and_unknown_rules_are_refused():
    from bench import power
    assert plan(0.03, 0.2, rule="mixture") == power.plan(0.03, 0.2)
    with pytest.raises(ValueError):
        plan(0.04, 0.46, rule="bayes")


def test_power_report_needs_mde_or_n():
    with pytest.raises(ValueError, match="pass mde"):
        power_report(discordance=0.2)
