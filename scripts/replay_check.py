"""Compare two commits' stored seeded games seed by seed.

Usage: uv run python scripts/replay_check.py <refA> <refB> [--min N] [--seeds N] [--fields f1,f2]
                                              [--skip-end VALUE]...

Exit 0: every compared field matches on every compared seed. Exit 1: some mismatch.
Exit 2: fewer common seeds than --min (or none at all). A field a game lacks on either
side is not compared (older commits did not record it); it is listed once in the summary.
--skip-end VALUE leaves out seeds whose end_reason equals VALUE on either side (a watchdog
ending depends on machine load, not on the seed). --min counts common seeds before skipping.
Read-only: the bench database is only read.
"""
import argparse
import json
import sys
from pathlib import Path

from bench.cli import DATA, REPO
from bench.store import Store
from seeded_report import _sha

FIELDS = ("role", "race", "gender", "alignment", "max_depth", "turns", "score", "end_reason", "rung",
          "ladder", "xp_level", "last_messages", "prayers", "zaps_seen", "hp_at_end", "max_hp_at_end",
          "hunger_at_end", "depth_at_end", "food_at_end", "events")
SHOW = 80


def _show(value):
    text = json.dumps(value, sort_keys=True)
    return text if len(text) <= SHOW else text[:SHOW - 3] + "..."


def main(argv=None):
    ap = argparse.ArgumentParser(prog="replay_check", description=__doc__.split("\n")[0])
    ap.add_argument("ref_a")
    ap.add_argument("ref_b")
    ap.add_argument("--min", type=int, default=1, dest="minimum", help="least number of common seeds")
    ap.add_argument("--seeds", type=int, help="compare seeds 0..N-1 (default: all seeds stored for refA)")
    ap.add_argument("--fields", help="comma separated fields (default: all game fields)")
    ap.add_argument("--skip-end", action="append", default=[], metavar="VALUE",
                    help="leave out seeds whose end_reason equals VALUE on either side (repeatable)")
    ap.add_argument("--data", default=str(DATA), help="directory holding results.db")
    ap.add_argument("--repo", default=str(REPO), help="git repository used to resolve refs")
    args = ap.parse_args(argv)

    store = Store(Path(args.data) / "results.db")
    sha_a, sha_b = _sha(args.repo, args.ref_a), _sha(args.repo, args.ref_b)
    wanted = range(args.seeds) if args.seeds is not None else store.seeds(sha_a)
    games_a, games_b = store.games_by_seed(sha_a, wanted), store.games_by_seed(sha_b, wanted)
    common = sorted(set(games_a) & set(games_b))
    if len(common) < max(args.minimum, 1):
        print(f"missing seeds: A has {len(games_a)}, B has {len(games_b)}, common {len(common)}")
        return 2

    fields = tuple(f.strip() for f in args.fields.split(",") if f.strip()) if args.fields else FIELDS
    skipped = {value: [] for value in args.skip_end}
    not_compared, mismatched, compared = [], 0, 0
    for seed in common:
        a, b = games_a[seed], games_b[seed]
        reason = next((v for v in args.skip_end if v in (a.get("end_reason"), b.get("end_reason"))), None)
        if reason is not None:
            skipped[reason].append(seed)
            continue
        compared += 1
        bad = False
        for field in fields:
            if (field in a) != (field in b):
                if field not in not_compared:
                    not_compared.append(field)
            elif field in a and a[field] != b[field]:
                bad = True
                print(f"seed {seed} {field}: {_show(a[field])} != {_show(b[field])}")
        mismatched += bad
    for value, seeds in skipped.items():
        if seeds:
            print(f"skipped ({value}): {len(seeds)} (seeds {', '.join(map(str, seeds))})")
    summary = f"{compared} seeds compared, {mismatched} mismatched"
    if not_compared:
        summary += f", not compared: {', '.join(not_compared)}"
    print(summary)
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
