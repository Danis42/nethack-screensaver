"""Seed-range policy (D-07, D-17, D-22).

The refusal guards against accidental misuse, not an adversary: Claude can still reach the HTTP API, so the
owner reviews jobs by range. Final-range seeds stay untouched until a clean attempt."""
import pytest

from bench import seeds


@pytest.mark.parametrize("seed, name", [
    (0, "tool"), (999, "tool"), (1000, "dev"), (99_999, "dev"), (100_000, "confirm"), (199_999, "confirm"),
    (200_000, "unassigned"), (999_999, "unassigned"), (1_000_000, "final"),
])
def test_range_boundaries_are_half_open_and_exact(seed, name):
    assert seeds.range_of(seed) == name


def test_a_dev_window_is_accepted():
    assert seeds.check_window(1000, 11_000, "baseline") == "dev"


@pytest.mark.parametrize("lo, hi, words", [
    (999, 1100, "tool"), (99_990, 100_010, "two ranges"), (200_000, 200_010, "unassigned"),
    (1_000_000, 1_000_010, "final"), (5, 5, "empty"), (10, 3, "empty"),
])
def test_bad_natural_windows_are_refused(lo, hi, words):
    with pytest.raises(ValueError, match=words):
        seeds.check_window(lo, hi, "baseline")


def test_confirm_needs_a_named_gate():
    with pytest.raises(ValueError, match="gate"):
        seeds.check_window(100_000, 100_500, "baseline")
    assert seeds.check_window(100_000, 100_500, "baseline", gate="phase-2-gate") == "confirm"
    with pytest.raises(ValueError, match="gate"):
        seeds.check_window(100_000, 100_500, "baseline", gate="Phase 2!")


def test_final_is_only_for_clean_attempts():
    assert seeds.check_window(1_000_000, 1_000_001, "clean_attempt") == "final"
    with pytest.raises(ValueError, match="final"):
        seeds.check_window(1000, 1010, "clean_attempt")


def test_tool_kinds_stay_inside_the_tool_block():
    assert seeds.check_window(0, 1000, "staged") == "tool"
    with pytest.raises(ValueError, match="tool"):
        seeds.check_window(900, 1100, "scenario")


def test_check_seed_applies_the_same_rules_to_one_seed():
    seeds.check_seed(1000, "baseline")
    for seed in (999, 1_000_000, 200_000):
        with pytest.raises(ValueError):
            seeds.check_seed(seed, "baseline")
