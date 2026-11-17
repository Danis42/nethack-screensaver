"""Validate the SPRT decision rule of bench.sprt (quick task 261117-kpa) by simulation.

    uv run python scripts/sim_sprt.py --out PATH [--reps 20000] [--seed 20261117]

Null cells (no true effect): false "better" rate when the declared discordance psi is right and when it is wrong
(true psi 0.05 / 0.2 / 0.46 against declared 0.46 / 0.2), looked at every 96 seeds up to n_planned, plus the worst
case of a look after every discordant pair. Each records reps, false wins, rate, its binomial standard error and
ok = rate <= alpha + 3 se.
Power cells: the SPRT against the mixture test at the character A/B settings and at a small change, both truncated
at their own planned size: P(better) and mean seeds played.

Independent of bench.sprt's own simulator (it only checks its log LR against bench.sprt.log_lr first).
One JSON line per cell on stdout, the full report at --out. Exit 0 when every null cell is ok.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench import power as powerlib, sprt  # noqa: E402
from bench.sequential import log_mixture_lr  # noqa: E402

BLOCK = 96
ALPHA = 0.0167
POWER = 0.8
NULL_CELLS = (  # (true psi, declared psi, mde)
    (0.46, 0.46, 0.04), (0.20, 0.46, 0.04), (0.05, 0.46, 0.04), (0.46, 0.20, 0.04), (0.05, 0.20, 0.02))
POWER_CELLS = ((0.46, 0.04), (0.20, 0.02))  # (psi, mde): character A/B, a smaller change


def simulate(rng, reps, n_max, psi, delta, decide):
    """Per rep: stop at the first block whose cumulative (w, l) makes decide return a verdict. Returns
    (P(better), mean seeds). decide(w, l) -> array of 1 better, -1 stop without win, 0 continue."""
    theta = (psi + delta) / (2 * psi)
    w = np.zeros(reps)
    l = np.zeros(reps)
    alive = np.ones(reps, dtype=bool)
    won = np.zeros(reps, dtype=bool)
    used = np.full(reps, float(n_max))
    for k in range(n_max // BLOCK):
        nd = rng.binomial(BLOCK, psi, reps)
        ww = rng.binomial(nd, theta)
        w += ww
        l += nd - ww
        d = decide(w, l)
        stop = alive & (d != 0)
        won |= alive & (d == 1)
        used[stop] = (k + 1) * BLOCK
        alive &= ~stop
        if not alive.any():
            break
    return float(won.mean()), float(used.mean())


def sprt_decide(mde, psi_declared):
    th1 = sprt.theta1(mde, psi_declared)
    lower, upper = sprt.bounds(ALPHA, POWER)
    sw, sl = math.log(2 * th1), math.log(2 * (1 - th1))

    def decide(w, l):
        lr = w * sw + l * sl
        return np.where(lr >= upper, 1, np.where(lr <= lower, -1, 0))
    return decide


def mixture_decide(w, l):
    from scipy.special import gammaln
    lr = gammaln(w + 1) + gammaln(l + 1) - gammaln(w + l + 2) + (w + l) * math.log(2)
    return np.where((lr >= math.log(1 / ALPHA)) & (w > l), 1, np.where(lr >= math.log(1 / ALPHA), -1, 0))


def every_pair_null(rng, reps, pairs, mde, psi_declared):
    """Worst case: a look after every discordant pair (psi does not matter then, only the coin)."""
    th1 = sprt.theta1(mde, psi_declared)
    lower, upper = sprt.bounds(ALPHA, POWER)
    steps = np.where(rng.random((reps, pairs)) < 0.5, math.log(2 * th1), math.log(2 * (1 - th1)))
    path = np.cumsum(steps, axis=1)
    up = path >= upper
    down = path <= lower
    first_up = np.where(up.any(axis=1), up.argmax(axis=1), pairs)
    first_down = np.where(down.any(axis=1), down.argmax(axis=1), pairs)
    return int((first_up < first_down).sum())


def check_against_bench():
    th1 = sprt.theta1(0.04, 0.46)
    for b, c in ((0, 0), (5, 3), (120, 90)):
        mine = b * math.log(2 * th1) + c * math.log(2 * (1 - th1))
        assert abs(mine - sprt.log_lr(b, c, th1)) < 1e-9
    w, l = np.array([7.0, 8.0]), np.array([0.0, 0.0])
    ref = [log_mixture_lr(7, 0), log_mixture_lr(8, 0)]
    from scipy.special import gammaln
    got = gammaln(w + 1) + gammaln(l + 1) - gammaln(w + l + 2) + (w + l) * math.log(2)
    assert np.allclose(got, ref)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261117)
    args = ap.parse_args()
    check_against_bench()
    rng = np.random.default_rng(args.seed)
    report = {"seed": args.seed, "reps": args.reps, "alpha": ALPHA, "power": POWER, "block": BLOCK,
              "null": [], "power_cells": []}
    ok = True
    for psi_true, psi_decl, mde in NULL_CELLS:
        n_planned = sprt.sample_size(mde, psi_decl, ALPHA, POWER, BLOCK)
        p, mean_n = simulate(rng, args.reps, n_planned, psi_true, 0.0, sprt_decide(mde, psi_decl))
        fp = round(p * args.reps)
        se = math.sqrt(ALPHA * (1 - ALPHA) / args.reps)
        cell = {"looks": "every 96 seeds", "psi_true": psi_true, "psi_declared": psi_decl, "mde": mde,
                "n_planned": n_planned, "reps": args.reps, "false_better": fp, "rate": fp / args.reps, "se": se,
                "bound": ALPHA + 3 * se, "ok": fp / args.reps <= ALPHA + 3 * se, "mean_seeds": mean_n}
        ok &= cell["ok"]
        report["null"].append(cell)
        print(json.dumps(cell))
    for psi_decl, mde in ((0.46, 0.04), (0.20, 0.02)):
        reps = min(args.reps, 20000)
        fp = every_pair_null(rng, reps, 4000, mde, psi_decl)
        se = math.sqrt(ALPHA * (1 - ALPHA) / reps)
        cell = {"looks": "every discordant pair", "pairs": 4000, "psi_declared": psi_decl, "mde": mde, "reps": reps,
                "false_better": fp, "rate": fp / reps, "se": se, "bound": ALPHA + 3 * se,
                "ok": fp / reps <= ALPHA + 3 * se}
        ok &= cell["ok"]
        report["null"].append(cell)
        print(json.dumps(cell))
    for psi, mde in POWER_CELLS:
        n_sprt = sprt.sample_size(mde, psi, ALPHA, POWER, BLOCK)
        n_mix = powerlib.sequential_sample_size(mde, psi, ALPHA, POWER, BLOCK)
        for delta in (0.0, mde / 2, mde):
            s_p, s_n = simulate(rng, args.reps, n_sprt, psi, delta, sprt_decide(mde, psi))
            m_p, m_n = simulate(rng, args.reps, n_mix, psi, delta, mixture_decide)
            cell = {"psi": psi, "mde": mde, "delta": delta, "sprt": {"n_planned": n_sprt, "p_better": s_p,
                    "mean_seeds": s_n}, "mixture": {"n_planned": n_mix, "p_better": m_p, "mean_seeds": m_n},
                    "seed_ratio_mixture_over_sprt": m_n / s_n}
            report["power_cells"].append(cell)
            print(json.dumps(cell))
    report["ok"] = ok
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
