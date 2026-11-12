"""scripts/lgen_pilot.py: the pre-registered lgen pilot computations on synthetic games."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))  # same as test_seeded_scripts.py

import lgen_pilot  # noqa: E402
from bench.metrics import METRICS  # noqa: E402
from bench.stats import Z95, wilson  # noqa: E402

DLVL10 = METRICS["dlvl10"]


def _g(seed, depth=5, **extra):
    return {"seed": seed, "max_depth": depth, "end_reason": "DEATH: killed by a newt", "turns": 100 + seed,
            "ladder": {}, **extra}


def test_pair_by_seed_ignores_order_and_counts_unpaired_seeds():
    a = [_g(s) for s in (3, 1, 2, 9)]
    b = [_g(s) for s in (2, 3, 1, 7)]
    random.Random(1).shuffle(b)
    pairs, unpaired = lgen_pilot.pair_by_seed(a, b)
    assert [s for s, _, _ in pairs] == [1, 2, 3] and unpaired == 2
    assert all(ga["seed"] == gb["seed"] == s for s, ga, gb in pairs)


def test_no_discordance():
    pairs, _ = lgen_pilot.pair_by_seed([_g(s) for s in range(50)], [_g(s) for s in range(50)])
    r = lgen_pilot.mode_summary(pairs, DLVL10)
    assert r["psi"] == 0.0 and r["psi_lo"] == 0.0 and r["psi_hi"] > 0 and r["mcnemar_p"] == 1.0
    assert r["mixture_state"] not in ("better", "worse") and r["identical_share"] == 1.0


def test_ten_of_a_hundred_discordant():
    a = [_g(s, depth=12 if s in (90, 91) else 5) for s in range(100)]  # A only: 2 seeds
    b = [_g(s, depth=12 if 80 <= s < 88 else 5) for s in range(100)]  # B only: 8 seeds
    pairs, _ = lgen_pilot.pair_by_seed(a, b)
    r = lgen_pilot.mode_summary(pairs, DLVL10)
    assert (r["n"], r["b"], r["c"], r["psi"]) == (100, 8, 2, 0.1)
    assert (r["psi_lo"], r["psi_hi"]) == wilson(10, 100, Z95)
    assert r["identical_share"] == 0.9


def test_paired_psi_difference_over_the_same_seeds():
    a = [_g(s) for s in range(40)]
    b_off = [_g(s, depth=12 if s < 10 else 5) for s in range(40)]  # 10 discordant with lgen off
    b_on = [_g(s, depth=12 if s < 4 else 5) for s in range(41)]  # 4 discordant with lgen on (seed 40 unpaired)
    off, _ = lgen_pilot.pair_by_seed(a, b_off)
    on, _ = lgen_pilot.pair_by_seed(a + [_g(40)], b_on)
    r = lgen_pilot.paired_psi_difference(off, on, DLVL10)
    assert r["n"] == 40 and r["psi_off"] == 0.25 and r["psi_on"] == 0.1
    assert abs(r["diff"] - (-0.15)) < 1e-12 and r["lo"] < r["diff"] < r["hi"] < 0


def test_stage_shift_flags_only_judged_stages_whose_interval_excludes_zero():
    off = [_g(s, ladder={"mines": 1, **({"oracle": 2} if s < 60 else {})}) for s in range(100)]
    on = [_g(s, ladder={"mines": 1, **({"oracle": 2} if s < 20 else {}), **({"minetown": 3} if s < 3 else {})})
          for s in range(100)]
    rows = {r["key"]: r for r in lgen_pilot.stage_shift(off, on)}
    assert len(rows) == 18
    assert rows["mines"]["hits_off"] == rows["mines"]["hits_on"] == 100 and not rows["mines"]["shifted"]
    assert rows["oracle"]["judged"] and rows["oracle"]["shifted"] and rows["oracle"]["hi"] < 0
    assert not rows["minetown"]["judged"] and not rows["minetown"]["shifted"]  # 3 hits: below 20
