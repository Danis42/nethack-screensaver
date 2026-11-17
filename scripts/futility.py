"""Futility check for a running bench experiment (02-CHARACTER-PREREG.md, amendment 3).

Reads the job's latest sequential verdict (n, b, c) from the bench database and simulates the rest of
the planned window in blocks of 96 seeds, assuming the true effect from now on equals the MDE. Prints
one JSON line with P(better) and P(worse). The amendment stops a job when P(better) < 0.05.

The simulation keeps the observed discordance rate b + c / n. A fixed RNG seed makes the result repeat.

    uv run python scripts/futility.py 19 [--alpha 0.0167] [--runs 4000]
"""
import argparse
import json
import math
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench.sequential import log_mixture_lr  # noqa: E402

BLOCK = 96


def p_end_better(n0, b0, c0, n_planned, alpha, effect, runs, seed=20261117):
    """Share of simulated continuations that end 'better' and 'worse' at the always-valid bound."""
    bound = math.log(1 / alpha)
    p_disc = (b0 + c0) / n0
    theta = min(1.0, 0.5 + effect / (2 * p_disc))
    rng = np.random.default_rng(seed)
    better = worse = 0
    for _ in range(runs):
        b, c, n = b0, c0, n0
        while n < n_planned:
            k = min(BLOCK, n_planned - n)
            d = int(rng.binomial(k, p_disc))
            x = int(rng.binomial(d, theta))
            b, c, n = b + x, c + d - x, n + k
            if log_mixture_lr(b, c) >= bound:
                if b > c:
                    better += 1
                else:
                    worse += 1
                break
    return better / runs, worse / runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job", type=int)
    ap.add_argument("--alpha", type=float, default=0.05 / 3)
    ap.add_argument("--runs", type=int, default=4000)
    ap.add_argument("--db", default=os.path.join(
        os.environ.get("SCREENS_BENCH_DATA", os.path.expanduser("~/.local/share/screens-bench")), "results.db"))
    args = ap.parse_args()
    row = sqlite3.connect(args.db).execute(
        "select state, json_extract(result, '$.verdict') from jobs where id = ?", (args.job,)).fetchone()
    if row is None or row[1] is None:
        print(json.dumps({"job": args.job, "error": "no verdict yet"}))
        return
    v = json.loads(row[1])
    pb, pw = p_end_better(v["n"], v["b"], v["c"], v["n_planned"], args.alpha, v["mde"], args.runs)
    print(json.dumps({"job": args.job, "state": row[0], "verdict": v["state"], "n": v["n"], "b": v["b"], "c": v["c"],
                      "n_planned": v["n_planned"], "mde": v["mde"], "p_better_at_mde": pb, "p_worse_at_mde": pw,
                      "futile": v["state"] == "open" and pb < 0.05}))


if __name__ == "__main__":
    main()
