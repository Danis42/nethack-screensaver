"""Headless AutoAscend benchmark: catches silent regressions from the port.

Usage: uv run python scripts/benchmark.py -n 50 -j 8
"""
import argparse
import statistics
from collections import Counter
from multiprocessing import Pool

from nethack_screensaver.game import run_game


def _one(_):
    return run_game(watchdog_seconds=120)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=50)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    args = ap.parse_args()

    results = []
    with Pool(args.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, range(args.games)), 1):
            results.append(r)
            print(f"[{i}/{args.games}] {r.role} depth={r.max_depth} score={r.score} turns={r.turns} :: {r.end_reason[:80]}", flush=True)

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


if __name__ == "__main__":
    main()
