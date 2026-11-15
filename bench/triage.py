"""Failure triage (SURV-01): every game ending of a commit's natural games, grouped by system and ranked.

    uv run python -m bench.triage <ref> [--lo 1000 --hi 11000] [--lgen off] [--json]

Groups come from bench/triage_groups.py (recorded fields only, no LLM). The ranking is by expected funnel gain:
for each game, the chance that a game which reached the same last ladder stage goes on to reach the next one,
estimated from all games in the window; summed over a group, it is how many more next-stage arrivals to expect
if that kind of ending were removed. Beside it, the expected Dlvl 10 gain: for games that ended above Dlvl 10,
the share of games that reached their depth and went on to Dlvl 10. Same input, same output.
"""
import argparse
import json
import sys
from collections import defaultdict

from autoascend.ladder import RUNGS

from . import seeds
from .triage_groups import DESCRIPTIONS, NAMES, classify

STAGES = [r.key for r in RUNGS]
STATUS = "draft"  # "draft" until the owner has reviewed the group list once (D-11)


def last_stage(game):
    reached = [i for i, key in enumerate(STAGES) if key in (game.get("ladder") or {})]
    return max(reached) if reached else -1


def next_stage_odds(games):
    """{last stage index: P(reached the next stage | reached this one)}; index -1 means no stage yet."""
    reached = [{i for i, key in enumerate(STAGES) if key in (g.get("ladder") or {})} for g in games]
    odds = {}
    for i in range(-1, len(STAGES) - 1):
        base = [s for s in reached if i == -1 or i in s]
        odds[i] = sum(1 for s in base if i + 1 in s) / len(base) if base else 0.0
    return odds


def dlvl10_odds(games):
    """{depth d: P(max depth >= 10 | max depth >= d)} for d below 10."""
    odds = {}
    for d in range(1, 10):
        base = [g for g in games if g["max_depth"] >= d]
        odds[d] = sum(1 for g in base if g["max_depth"] >= 10) / len(base) if base else 0.0
    return odds


def rank(games):
    stage_odds, deep_odds = next_stage_odds(games), dlvl10_odds(games)
    groups = defaultdict(lambda: {"count": 0, "stage_gain": 0.0, "dlvl10_gain": 0.0, "depth": 0, "seeds": []})
    for g in games:
        row = groups[classify(g)]
        row["count"] += 1
        row["depth"] += g["max_depth"]
        row["stage_gain"] += stage_odds[last_stage(g)]
        if g["max_depth"] < 10:
            row["dlvl10_gain"] += deep_odds[max(1, g["max_depth"])]
        row["seeds"].append(g.get("seed"))
    n = len(games)
    out = []
    for name in NAMES:
        if name not in groups:
            continue
        row = groups[name]
        out.append({"group": name, "description": DESCRIPTIONS[name], "count": row["count"],
                    "share": round(row["count"] / n, 4), "mean_depth": round(row["depth"] / row["count"], 2),
                    "stage_gain": round(row["stage_gain"], 1), "dlvl10_gain": round(row["dlvl10_gain"], 1),
                    "examples": sorted(s for s in row["seeds"] if s is not None)[:3]})
    out.sort(key=lambda r: (-r["stage_gain"], r["group"]))
    return {"status": STATUS, "n": n, "groups": out}


def main(argv=None):
    from . import gitrefs
    from .cli import DATA, REPO
    from .store import Store
    p = argparse.ArgumentParser(prog="python -m bench.triage", description=__doc__.split("\n\n")[0])
    p.add_argument("ref")
    p.add_argument("--lo", type=int, default=seeds.BASELINE_WINDOW[0])
    p.add_argument("--hi", type=int, default=seeds.BASELINE_WINDOW[1])
    p.add_argument("--lgen", default=seeds.USE_LGEN, choices=seeds.LGEN_MODES)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    sha, _ = gitrefs.resolve(REPO, args.ref)
    games = Store(DATA / "results.db").games(sha, rep=0, lo=args.lo, hi=args.hi, lgen_mode=args.lgen)
    out = {"sha": sha, "window": [args.lo, args.hi], "lgen": args.lgen, **rank(games)}
    if args.json:
        print(json.dumps(out, sort_keys=True))
        return 0
    print(f"{out['status']}: {sha} seeds [{args.lo}, {args.hi}) n={out['n']}")
    print(f"{'group':<12}{'games':>7}{'share':>8}{'depth':>7}{'stage gain':>12}{'Dlvl10 gain':>13}  what")
    for r in out["groups"]:
        print(f"{r['group']:<12}{r['count']:>7}{r['share']:>8.1%}{r['mean_depth']:>7}{r['stage_gain']:>12}"
              f"{r['dlvl10_gain']:>13}  {r['description']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
