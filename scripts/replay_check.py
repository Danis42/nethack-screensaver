"""Compare two commits' stored seeded games seed by seed.

Usage: uv run python scripts/replay_check.py <refA> <refB> [--min N] [--seeds N] [--fields f1,f2]
                                              [--skip-end VALUE]... [--skip-both VALUE]...
                                              [--rep-a R] [--rep-b R] [--lo N --hi N] [--lgen off|seed] [--json]

A/A (plan 01-15): replay_check.py <A> <A> --rep-b 1 --lo 1000 --hi 3000 --lgen <mode> --min 2000
                  --skip-both watchdog --json

Exit 0: every compared field matches on every compared seed. Exit 1: some mismatch.
Exit 2: fewer common seeds than --min (or none at all). A field a game lacks on either
side is not compared (older commits did not record it); it is listed once in the summary.
--skip-end VALUE leaves out seeds whose end_reason equals VALUE on either side (a watchdog
ending depends on machine load, not on the seed). --skip-both VALUE leaves out only seeds where
BOTH sides end with VALUE; one side alone is compared and counts as a mismatch (the A/A rule).
--min counts common seeds before skipping. --rep-a/--rep-b pick the replicate of each side
(default 0), --lo/--hi a half-open seed window, --lgen the lgen mode of both sides; --json adds one
final JSON line {compared, identical, mismatched, mismatched_seeds, skipped, common}.
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
    ap.add_argument("--skip-both", action="append", default=[], metavar="VALUE",
                    help="leave out seeds whose end_reason equals VALUE on both sides (repeatable)")
    ap.add_argument("--rep-a", type=int, default=0, help="replicate of refA's games (default 0)")
    ap.add_argument("--rep-b", type=int, default=0, help="replicate of refB's games (default 0)")
    ap.add_argument("--lo", type=int, help="first seed of the compared window")
    ap.add_argument("--hi", type=int, help="end of the compared window, exclusive")
    ap.add_argument("--lgen", choices=["off", "seed"], help="lgen mode of both sides (default: any)")
    ap.add_argument("--json", action="store_true", help="print one final JSON summary line")
    ap.add_argument("--data", default=str(DATA), help="directory holding results.db")
    ap.add_argument("--repo", default=str(REPO), help="git repository used to resolve refs")
    args = ap.parse_args(argv)

    store = Store(Path(args.data) / "results.db")
    sha_a, sha_b = _sha(args.repo, args.ref_a), _sha(args.repo, args.ref_b)
    key_a, key_b = {"lgen_mode": args.lgen, "rep": args.rep_a}, {"lgen_mode": args.lgen, "rep": args.rep_b}
    wanted = range(args.seeds) if args.seeds is not None else store.seeds(sha_a, args.lo, args.hi, **key_a)
    if args.lo is not None or args.hi is not None:
        wanted = [s for s in wanted if (args.lo is None or s >= args.lo) and (args.hi is None or s < args.hi)]
    games_a, games_b = store.games_by_seed(sha_a, wanted, **key_a), store.games_by_seed(sha_b, wanted, **key_b)
    common = sorted(set(games_a) & set(games_b))
    if len(common) < max(args.minimum, 1):
        print(f"missing seeds: A has {len(games_a)}, B has {len(games_b)}, common {len(common)}")
        if args.json:
            print(json.dumps({"compared": 0, "identical": 0, "mismatched": 0, "mismatched_seeds": [],
                              "skipped": {v: [] for v in args.skip_both + args.skip_end}, "common": len(common),
                              "error": "too few common seeds"}))
        return 2

    fields = tuple(f.strip() for f in args.fields.split(",") if f.strip()) if args.fields else FIELDS
    skipped = {value: [] for value in args.skip_end + args.skip_both}
    not_compared, mismatched, compared, bad_seeds = [], 0, 0, []
    for seed in common:
        a, b = games_a[seed], games_b[seed]
        reason = next((v for v in args.skip_end if v in (a.get("end_reason"), b.get("end_reason"))), None)
        if reason is None:
            reason = next((v for v in args.skip_both if a.get("end_reason") == v == b.get("end_reason")), None)
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
        if bad:
            bad_seeds.append(seed)
    for value, seeds in skipped.items():
        if seeds:
            print(f"skipped ({value}): {len(seeds)} (seeds {', '.join(map(str, seeds))})")
    summary = f"{compared} seeds compared, {mismatched} mismatched"
    if not_compared:
        summary += f", not compared: {', '.join(not_compared)}"
    print(summary)
    if args.json:
        print(json.dumps({"compared": compared, "identical": compared - mismatched, "mismatched": mismatched,
                          "mismatched_seeds": bad_seeds, "skipped": skipped, "common": len(common)}))
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
