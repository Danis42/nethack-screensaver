"""Headless AutoAscend benchmark: catches silent regressions from the port.

Usage: uv run python scripts/benchmark.py -n 50 -j 8
"""
import argparse
import statistics
from collections import Counter
from multiprocessing import Pool

from nethack_screensaver.game import run_game


def _one(strategy):
    return run_game(watchdog_seconds=120, strategy=strategy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=50)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--strategy", default=None,
                    help="pilgrim/daredevil/sightseer/treasure (default: random per game)")
    args = ap.parse_args()

    results = []
    with Pool(args.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, [args.strategy] * args.games), 1):
            results.append(r)
            print(f"[{i}/{args.games}] {r.strategy} {r.role} depth={r.max_depth} score={r.score} "
                  f"turns={r.turns} elb={r.elbereth} :: {r.outcome} :: {r.end_reason[:70]}", flush=True)

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


if __name__ == "__main__":
    main()
