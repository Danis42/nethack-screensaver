"""Simulate false positives under repeated checking, and the power of the sequential test (MEAS-06).

    .venv/bin/python scripts/sim_sequential.py --out PATH [--reps 20000] [--seed 20261112]

Null cells (delta = 0) for psi in 0.05, 0.2, 0.4 (psi = chance that a seed is discordant):
  mixture-96seed-blocks    the always-valid test of bench.sequential, a look every 96 seeds up to 10,000
  mixture-every-pair       the same test, a look after every discordant pair up to 2,000 pairs
  legacy-wald-checkpoints  the old design: paired Wald, z99 at 192/384/576/1152 seeds, z95 at 2304
  mcnemar-peek-20pairs     plain exact McNemar at 0.05, peeked every 20 discordant pairs up to 2,000
Looks after every discordant pair do not depend on psi (psi only sets how many seeds a pair costs),
so those cells repeat the same experiment with an independent random stream per psi.
Power cells (delta > 0): the mixture test, a look every 96 seeds: power, stopping seed.

Each null cell records reps, rejections, rate and its binomial standard error; mixture cells also get
bound = alpha + 3 se and ok = rate <= bound. The report is {"seed", "reps", "alpha", "null", "power"}
as JSON at --out, one JSON line per cell on stdout. Before simulating, the vectorised rules are checked
against bench.sequential.log_mixture_lr and bench.stats.judge_paired.

Exit codes: 0 every mixture null cell is within its bound, 1 otherwise.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.special import gammaln
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.sequential import PRIOR_A, log_mixture_lr  # noqa: E402
from bench.stats import CHECKPOINTS, Z95, Z99, judge_paired, z_for  # noqa: E402

ALPHA = 0.05
BOUND = math.log(1 / ALPHA)
NULL_PSI = (0.05, 0.2, 0.4)
POWER_CELLS = ((0.2, 0.03, 4000), (0.2, 0.04, 3000), (0.1, 0.02, 6000), (0.3, 0.05, 3000))
BLOCK = 96
PAIR_LOOKS_MAX = 2000
CHUNK = 2000


def log_lr(b, c, a=PRIOR_A):
    """Vectorised bench.sequential.log_mixture_lr (b + c = 0 gives 0)."""
    b, c = np.asarray(b, dtype=float), np.asarray(c, dtype=float)
    out = (gammaln(b + a) + gammaln(c + a) - gammaln(b + c + 2 * a)
           - (2 * gammaln(a) - gammaln(2 * a)) + (b + c) * math.log(2))
    return np.where(b + c == 0, 0.0, out)


def self_check():
    """The simulation must use the rules the bench uses."""
    for b, c in ((0, 0), (7, 0), (8, 0), (3, 9), (150, 120), (10000, 10000)):
        assert abs(float(log_lr(b, c)) - log_mixture_lr(b, c)) < 1e-9, (b, c)
    rng = np.random.default_rng(1)
    for _ in range(300):
        n = int(rng.choice(CHECKPOINTS))
        pairs = [(bool(x), bool(y)) for x, y in zip(rng.random(n) < 0.3, rng.random(n) < 0.25)]
        n10 = sum(1 for x, y in pairs if x and not y)
        n01 = sum(1 for x, y in pairs if y and not x)
        assert wald_state(n, n10, n01, z_for(n)) == (judge_paired(pairs, n).state in ("better", "worse"))


def wald_state(n, n10, n01, z):
    """True when the paired Wald interval excludes zero (same arithmetic as bench.stats.judge_paired)."""
    diff = (n10 - n01) / n
    half = z * math.sqrt(max(n10 + n01 - n * diff * diff, 0.0)) / n
    return diff - half > 0 or diff + half < 0


def null_cell(design, psi, rejections, reps, with_bound):
    rate = rejections / reps
    se = math.sqrt(rate * (1 - rate) / reps)
    cell = {"design": design, "psi": psi, "reps": reps, "rejections": int(rejections),
            "rate": rate, "se": se}
    if with_bound:
        cell["bound"] = ALPHA + 3 * se
        cell["ok"] = rate <= cell["bound"]
    return cell


def mixture_blocks(rng, reps, psi, n_max):
    """Share of null reps that ever cross, a look every BLOCK seeds up to n_max."""
    nd = rng.binomial(BLOCK, psi, (reps, n_max // BLOCK))
    b = rng.binomial(nd, 0.5)
    nd_cum, b_cum = np.cumsum(nd, axis=1), np.cumsum(b, axis=1)
    return int((log_lr(b_cum, nd_cum - b_cum) >= BOUND).any(axis=1).sum())


def table_cross(pairs_max):
    """cross[t - 1, b]: the mixture test rejects at t discordant pairs with b candidate-only."""
    t = np.arange(1, pairs_max + 1)[:, None]
    b = np.arange(pairs_max + 1)[None, :]
    valid = b <= t
    lr = log_lr(np.where(valid, b, 0), np.where(valid, t - b, 0))
    return valid & (lr >= BOUND)


def exact_reject_table(pairs_max, step):
    """reject[i, b]: exact two-sided McNemar at 0.05 rejects at t = (i + 1) * step pairs with b."""
    t = np.arange(step, pairs_max + 1, step)
    reject = np.zeros((len(t), pairs_max + 1), dtype=bool)
    for i, ti in enumerate(t):
        k = binom.ppf(ALPHA / 2, ti, 0.5)
        k = k if binom.cdf(k, ti, 0.5) <= ALPHA / 2 + 1e-12 else k - 1
        b = np.arange(ti + 1)
        reject[i, :ti + 1] = (b <= k) | (b >= ti - k)
    return reject


def peek_pairs(rng, reps, table, step):
    """Null reps that ever reject, looking after every `step` discordant pairs (table rows)."""
    rows = np.arange(step - 1, PAIR_LOOKS_MAX, step) if step > 1 else np.arange(PAIR_LOOKS_MAX)
    hits = 0
    for start in range(0, reps, CHUNK):
        size = min(CHUNK, reps - start)
        b_cum = np.cumsum(rng.random((size, PAIR_LOOKS_MAX)) < 0.5, axis=1, dtype=np.int16)
        hits += int(table[np.arange(len(rows))[None, :], b_cum[:, rows]].any(axis=1).sum())
    return hits


def legacy(rng, reps, psi):
    """Null reps the checkpoint design calls better or worse at any checkpoint."""
    hit = np.zeros(reps, dtype=bool)
    n10 = np.zeros(reps)
    n01 = np.zeros(reps)
    done = 0
    for n in CHECKPOINTS:
        nd = rng.binomial(n - done, psi, reps)
        b = rng.binomial(nd, 0.5)
        n10, n01, done = n10 + b, n01 + nd - b, n
        diff = (n10 - n01) / n
        z = Z95 if n == CHECKPOINTS[-1] else Z99
        half = z * np.sqrt(np.maximum(n10 + n01 - n * diff * diff, 0.0)) / n
        hit |= (diff - half > 0) | (diff + half < 0)
    return int(hit.sum())


def power_cell(rng, reps, psi, delta, n_max):
    theta = (psi + delta) / (2 * psi)
    blocks = n_max // BLOCK
    nd = rng.binomial(BLOCK, psi, (reps, blocks))
    b = rng.binomial(nd, theta)
    nd_cum, b_cum = np.cumsum(nd, axis=1), np.cumsum(b, axis=1)
    c_cum = nd_cum - b_cum
    crossed = log_lr(b_cum, c_cum) >= BOUND
    first = np.where(crossed.any(axis=1), crossed.argmax(axis=1), blocks - 1)
    rows = np.arange(reps)
    won = crossed.any(axis=1) & (b_cum[rows, first] > c_cum[rows, first])
    stop = (first + 1) * BLOCK
    return {"psi": psi, "delta": delta, "n_max": n_max, "block": BLOCK, "reps": reps,
            "power": float(won.mean()), "mean_stop": float(stop.mean()),
            "median_stop": float(np.median(stop)),
            "median_stop_when_won": float(np.median(stop[won])) if won.any() else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", required=True, help="JSON report path")
    parser.add_argument("--reps", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261112)
    args = parser.parse_args()
    self_check()

    cross_table = table_cross(PAIR_LOOKS_MAX)
    exact_table = exact_reject_table(PAIR_LOOKS_MAX, 20)
    null, power, stream = [], [], 0

    def rng_next():
        nonlocal stream
        stream += 1
        return np.random.default_rng([args.seed, stream])

    for psi in NULL_PSI:
        for design, run, with_bound in (
                ("mixture-96seed-blocks", lambda r: mixture_blocks(r, args.reps, psi, 10000), True),
                ("mixture-every-pair",
                 lambda r: peek_pairs(r, args.reps, cross_table, 1), True),
                ("legacy-wald-checkpoints", lambda r: legacy(r, args.reps, psi), False),
                ("mcnemar-peek-20pairs",
                 lambda r: peek_pairs(r, args.reps, exact_table, 20), False)):
            cell = null_cell(design, psi, run(rng_next()), args.reps, with_bound)
            null.append(cell)
            print(json.dumps({"kind": "null", **cell}), flush=True)
    for psi, delta, n_max in POWER_CELLS:
        cell = power_cell(rng_next(), args.reps, psi, delta, n_max)
        power.append(cell)
        print(json.dumps({"kind": "power", **cell}), flush=True)

    report = {"seed": args.seed, "reps": args.reps, "alpha": ALPHA, "null": null, "power": power}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(c["ok"] for c in null if "ok" in c) else 1


if __name__ == "__main__":
    sys.exit(main())
