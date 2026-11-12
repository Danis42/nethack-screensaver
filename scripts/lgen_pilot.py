"""lgen pilot analysis (MEAS-04): paired discordance of commits A and B with lgen off and on.

Usage: uv run python scripts/lgen_pilot.py --jobs A_OFF A_SEED B_OFF B_SEED [--metric dlvl10] [--also m1,m2]

Each job is a baseline job of the bench; its spec gives the commit, seed window, lgen mode and env, and its natural
rows (rep 0) are read through the store's keyed reads. Read-only: the bench database is only read.

Computations, as pre-registered in .planning/phases/01-measurement-and-proof-foundation/01-LGEN-PILOT.md:
- per lgen mode, A vs B paired by seed on the metric: b (A fails, B succeeds), c (A succeeds, B fails),
  psi = (b + c) / n with a 95% Wilson interval, exact McNemar p, the mixture (mSPRT) verdict at the full n, and
  the share of seeds whose results are identical on replay_check's FIELDS;
- psi_on - psi_off over the seeds present in all four jobs, with a 95% Wald interval on the mean of the per-seed
  difference of the discordance indicators;
- for commit A, per stage key, reach on vs off on the same seeds with a 95% Wald interval on the per-seed
  difference; stages with >= 20 hits in either mode whose interval excludes 0 are flagged.
Prints one JSON object per line.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from autoascend.ladder import RUNGS
from bench.cli import DATA
from bench.metrics import METRICS
from bench.sequential import judge_sequential, mcnemar_exact
from bench.stats import Z95, wilson
from bench.store import Store
from replay_check import FIELDS

STAGE_MIN_HITS = 20


def pair_by_seed(games_a, games_b):
    """([(seed, game_a, game_b)] in seed order, number of seeds present on one side only)."""
    a = {g["seed"]: g for g in games_a}
    b = {g["seed"]: g for g in games_b}
    common = sorted(set(a) & set(b))
    return [(s, a[s], b[s]) for s in common], len(set(a) ^ set(b))


def _outcome(metric, game):
    try:
        return bool(metric.fn(game))
    except KeyError:  # a game without the metric's field: not compared
        return None


def _identical(ga, gb):
    return all(ga.get(f) == gb.get(f) for f in FIELDS if f in ga and f in gb)


def mode_summary(pairs, metric, alpha=0.05):
    """Discordance of A vs B on one metric over paired games."""
    outcomes = [(_outcome(metric, ga), _outcome(metric, gb)) for _, ga, gb in pairs]
    outcomes = [(x, y) for x, y in outcomes if x is not None and y is not None]
    n = len(outcomes)
    b = sum(1 for x, y in outcomes if y and not x)  # B succeeds where A fails
    c = sum(1 for x, y in outcomes if x and not y)
    lo, hi = wilson(b + c, n, Z95)
    verdict = judge_sequential([(n, b, c)], alpha, n, 0.0).as_dict() if n else None
    return {"n": n, "b": b, "c": c, "psi": (b + c) / n if n else None, "psi_lo": lo, "psi_hi": hi,
            "mcnemar_p": mcnemar_exact(b, c),
            "mixture_state": verdict["state"] if verdict else None,
            "identical_share": sum(_identical(ga, gb) for _, ga, gb in pairs) / len(pairs) if pairs else None}


def _wald_mean(values, z=Z95):
    n = len(values)
    if n == 0:
        return None, None, None
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else 0.0
    half = z * math.sqrt(var / n)
    return mean, mean - half, mean + half


def paired_psi_difference(pairs_off, pairs_on, metric):
    """psi_on - psi_off over the seeds paired in both modes, with a 95% Wald interval on the per-seed difference."""
    def disc(pairs):
        out = {}
        for s, ga, gb in pairs:
            x, y = _outcome(metric, ga), _outcome(metric, gb)
            if x is not None and y is not None:
                out[s] = int(x != y)
        return out
    off, on = disc(pairs_off), disc(pairs_on)
    seeds = sorted(set(off) & set(on))
    diff, lo, hi = _wald_mean([on[s] - off[s] for s in seeds])
    return {"n": len(seeds), "psi_off": sum(off[s] for s in seeds) / len(seeds) if seeds else None,
            "psi_on": sum(on[s] for s in seeds) / len(seeds) if seeds else None,
            "diff": diff, "lo": lo, "hi": hi}


def stage_shift(games_off, games_on, min_hits=STAGE_MIN_HITS):
    """Commit A's stage reach with lgen on vs off on the same seeds, per stage key."""
    pairs, _ = pair_by_seed([g for g in games_off if "ladder" in g], [g for g in games_on if "ladder" in g])
    rows = []
    for r in RUNGS:
        off = [int(r.key in ga["ladder"]) for _, ga, _ in pairs]
        on = [int(r.key in gb["ladder"]) for _, _, gb in pairs]
        diff, lo, hi = _wald_mean([y - x for x, y in zip(off, on)])
        judged = max(sum(off), sum(on)) >= min_hits
        rows.append({"key": r.key, "n": len(pairs), "hits_off": sum(off), "hits_on": sum(on), "diff": diff,
                     "lo": lo, "hi": hi, "judged": judged,
                     "shifted": bool(judged and lo is not None and (lo > 0 or hi < 0))})
    return rows


def _job_games(store, job_id):
    job = store.job(job_id)
    if job is None or job["kind"] != "baseline":
        raise SystemExit(f"job {job_id} is not a baseline job")
    spec = job["spec"]
    return spec, store.games(spec["sha"], rep=int(spec.get("replicate", 0)), lgen_mode=spec["lgen"],
                             env_id=spec.get("env_id"), lo=spec["seeds"]["lo"], hi=spec["seeds"]["hi"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lgen_pilot", description=__doc__.split("\n")[0])
    ap.add_argument("--jobs", type=int, nargs=4, required=True, metavar=("A_OFF", "A_SEED", "B_OFF", "B_SEED"))
    ap.add_argument("--metric", default="dlvl10")
    ap.add_argument("--also", default="", help="comma separated further rate metrics")
    ap.add_argument("--data", default=str(DATA), help="directory holding results.db")
    args = ap.parse_args(argv)

    store = Store(Path(args.data) / "results.db")
    (sa, a_off), (_, a_on), (sb, b_off), (_, b_on) = (_job_games(store, j) for j in args.jobs)
    pairs_off, lost_off = pair_by_seed(a_off, b_off)
    pairs_on, lost_on = pair_by_seed(a_on, b_on)
    print(json.dumps({"jobs": args.jobs, "commit_a": sa["sha"], "commit_b": sb["sha"], "metric": args.metric,
                      "games": [len(a_off), len(a_on), len(b_off), len(b_on)], "unpaired": [lost_off, lost_on]}))
    for name in [args.metric] + [m for m in args.also.split(",") if m]:
        metric = METRICS[name]
        for mode, pairs in (("off", pairs_off), ("seed", pairs_on)):
            print(json.dumps({"metric": name, "lgen": mode, **mode_summary(pairs, metric)}))
        print(json.dumps({"metric": name, "psi_difference": paired_psi_difference(pairs_off, pairs_on, metric)}))
    print(json.dumps({"stage_shift_commit_a": stage_shift(a_off, a_on)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
