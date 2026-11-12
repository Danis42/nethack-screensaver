import pytest

from bench import power
from bench.power import (DEFAULT_DISCORDANCE, mcnemar_mde, mcnemar_power, plan, sequential_mde,
                         sequential_power, sequential_sample_size)


@pytest.mark.parametrize("n, psi, expected", [(400, 0.05, 0.0321), (1000, 0.2, 0.0404),
                                              (2000, 0.3, 0.0348), (10000, 0.4, 0.0178)])
def test_exact_mcnemar_mde_matches_the_research_table(n, psi, expected):
    assert mcnemar_mde(n, psi) == pytest.approx(expected, abs=5e-4)


def test_exact_power_rises_with_n_and_with_delta():
    assert mcnemar_power(500, 0.2, 0.03) < mcnemar_power(1000, 0.2, 0.03) < mcnemar_power(2000, 0.2, 0.03)
    assert mcnemar_power(1000, 0.2, 0.02) < mcnemar_power(1000, 0.2, 0.04) < mcnemar_power(1000, 0.2, 0.06)


def test_exact_power_without_an_effect_is_at_most_alpha():
    assert 0 < mcnemar_power(1000, 0.2, 0.0) <= 0.05


def test_exact_power_at_the_mde_is_the_target():
    mde = mcnemar_mde(1000, 0.2)
    assert mcnemar_power(1000, 0.2, mde) == pytest.approx(0.8, abs=0.01)


def test_sequential_power_matches_the_research_run_and_is_deterministic():
    p = sequential_power(4000, 0.2, 0.03, block=96)
    assert p == pytest.approx(0.83, abs=0.04)
    assert sequential_power(4000, 0.2, 0.03, block=96) == p


def test_sequential_power_without_an_effect_stays_small():
    assert sequential_power(4000, 0.2, 0.0, block=96) <= 0.05


def test_sequential_sample_size_is_the_smallest_block_multiple_reaching_the_power():
    n = sequential_sample_size(0.03, 0.2, block=96)
    assert n % 96 == 0
    assert sequential_power(n, 0.2, 0.03, block=96) >= 0.8
    assert sequential_power(n - 96, 0.2, 0.03, block=96) < 0.8


def test_sequential_mde_at_the_sized_n_is_close_to_the_declared_mde():
    n = sequential_sample_size(0.03, 0.2, block=96)
    assert sequential_mde(n, 0.2, block=96) == pytest.approx(0.03, abs=0.003)


def test_sample_size_refuses_when_the_cap_is_too_small():
    with pytest.raises(ValueError):
        sequential_sample_size(0.005, 0.2, n_cap=1000)


def test_plan_has_the_declared_fields():
    p = plan(0.03, 0.2)
    assert set(p) == {"test", "mde", "psi", "alpha", "power", "block", "n_planned", "mcnemar_mde_at_n"}
    assert p["test"] == "msprt-beta1" and p["n_planned"] % 96 == 0
    assert (p["mde"], p["psi"], p["alpha"], p["power"], p["block"]) == (0.03, 0.2, 0.05, 0.8, 96)
    assert p["mcnemar_mde_at_n"] == pytest.approx(mcnemar_mde(p["n_planned"], 0.2), abs=1e-9)


def test_default_discordance_is_unset_until_the_pilot():
    assert DEFAULT_DISCORDANCE is None


@pytest.mark.parametrize("call", [
    lambda: mcnemar_power(0, 0.2, 0.03),
    lambda: mcnemar_power(100, 0.0, 0.0),
    lambda: mcnemar_power(100, 1.5, 0.03),
    lambda: mcnemar_mde(100, 0.0),
    lambda: sequential_power(0, 0.2, 0.03),
    lambda: sequential_sample_size(0.3, 0.2),
    lambda: sequential_sample_size(0.0, 0.2),
    lambda: plan(0.03, 0.0),
])
def test_invalid_inputs_raise(call):
    with pytest.raises(ValueError):
        call()


def test_module_documents_its_notation():
    assert "psi" in power.__doc__ and "delta" in power.__doc__
