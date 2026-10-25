"""Headless AutoAscend benchmark: catches silent regressions from the port.

Usage: uv run python scripts/benchmark.py -n 50 -j 8
       uv run python scripts/benchmark.py --seeds 0-21 --field events.rest_turns -j 8

--seeds plays exactly those seeded games (the bench's games: same seed, same game) and replaces -n;
--field NAME (repeatable, dotted for dicts such as events.rest_turns) prints NAME=value after each
game and "NAME>0: k of n games" at the end.
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import asdict
from multiprocessing import Pool

from nethack_screensaver import fixed_clock
from nethack_screensaver.game import run_game


def parse_seeds(text):
    """'0-21' -> [0..21], '5' -> [5], '0,3,7' -> [0, 3, 7]; parts can be mixed ('0-2,5')."""
    seeds = []
    for part in text.split(","):
        part = part.strip()
        if re.fullmatch(r"\d+", part):
            seeds.append(int(part))
        elif m := re.fullmatch(r"(\d+)\s*-\s*(\d+)", part):
            low, high = int(m[1]), int(m[2])
            if high < low:
                raise ValueError(f"empty seed range {part!r}")
            seeds.extend(range(low, high + 1))
        else:
            raise ValueError(f"cannot read seeds {text!r}: bad part {part!r} (use 0-21, 5 or 0,3,7)")
    return seeds


def field_value(result, dotted):
    """result['events']['rest_turns'] for 'events.rest_turns'; None when any step is missing."""
    value = result
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _positive(value):
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return value is not None and value > 0


def _one(job):
    strategy, seed = job
    if seed is None:
        return run_game(watchdog_seconds=120, strategy=strategy)
    return run_game(watchdog_seconds=120, strategy=strategy, seed=seed)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=None, help="unseeded games to play (default 50)")
    ap.add_argument("--seeds", help="play these seeded games instead of -n, e.g. 0-21, 5 or 0,3,7")
    ap.add_argument("--field", action="append", default=[], metavar="NAME",
                    help="also print this GameResult field per game (dotted for dicts, e.g. events.rest_turns)")
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--strategy", default=None,
                    help="pilgrim/daredevil/sightseer/treasure/random (default: pilgrim)")
    ap.add_argument("--out", help="also write every result as a JSON line to this file")
    args = ap.parse_args(argv)

    if args.seeds is not None:
        if args.strategy is not None:
            ap.error("--seeds plays the default route; it cannot be combined with --strategy")
        if args.games is not None:
            ap.error("--seeds replaces -n; give one of them")
        try:
            jobs = [(None, seed) for seed in parse_seeds(args.seeds)]
        except ValueError as e:
            ap.error(str(e))
    else:
        jobs = [(args.strategy, None)] * (50 if args.games is None else args.games)

    if args.seeds is not None and not fixed_clock.preloaded():
        print("note: fixed_clock shim not loaded; seeded games may not replay the bench's games", file=sys.stderr)
    results = []
    with Pool(args.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, jobs), 1):
            results.append(r)
            row = asdict(r)
            if args.out:
                with open(args.out, "a") as f:
                    f.write(json.dumps(row) + "\n")
            extra = (f" seed={r.seed}" if args.seeds is not None else "") + "".join(
                f" {name}={field_value(row, name)}" for name in args.field)
            print(f"[{i}/{len(jobs)}] {r.strategy} {r.role} depth={r.max_depth} score={r.score} "
                  f"turns={r.turns} xl={r.xp_level} elb={r.elbereth}{extra} :: {r.outcome} :: {r.end_reason[:70]}",
                  flush=True)

    exc = [r for r in results if r.end_reason.startswith("exception")]
    wd = [r for r in results if r.end_reason == "watchdog"]
    print()
    print(f"games            : {len(results)}")
    print(f"median score     : {statistics.median(r.score for r in results)}")
    print(f"median max depth : {statistics.median(r.max_depth for r in results)}")
    print(f"median turns     : {statistics.median(r.turns for r in results)}")
    print(f"exceptions       : {len(exc)}")
    print(f"watchdog         : {len(wd)}")
    for reason, n in Counter(r.end_reason.split(":", 1)[1].strip()[:60] for r in exc).most_common(5):
        print(f"  {n}x {reason}")
    for name in sorted({r.strategy for r in results}):
        rs = [r for r in results if r.strategy == name]
        print(f"\n{name}: {len(rs)} games, median depth {statistics.median(r.max_depth for r in rs)}")
        for o, n in Counter(r.outcome.split(" on Dlvl")[0] for r in rs).most_common():
            print(f"  {n}x {o}")
    if args.field:
        print()
        rows = [asdict(r) for r in results]
        for name in args.field:
            print(f"{name}>0: {sum(_positive(field_value(row, name)) for row in rows)} of {len(rows)} games")


if __name__ == "__main__":
    if any(a == "--seeds" or a.startswith("--seeds=") for a in sys.argv[1:]):
        fixed_clock.ensure_preloaded()  # seeded games need the pinned start time to replay the bench's games
    main()
