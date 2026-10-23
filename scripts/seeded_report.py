"""Read-only reports over the seeded bench store.

Usage: uv run python scripts/seeded_report.py <command> ...

Commands:
  verdict <candidate> [--baseline REF] [--metric NAME] [--expect STATE] [--forbid STATE]
      stored verdict of finished experiments (exit 0; 3 = none; 4 = --expect/--forbid violated)

The scripts only read the bench database (games, jobs, references): looking at evidence
never changes it. Refs may be branches, tags, short SHAs or full 40-hex SHAs.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from bench import gitrefs
from bench.cli import DATA, REPO
from bench.store import Store

FULL_SHA = re.compile(r"[0-9a-f]{40}")
FINISHED = ("done", "stopped")


def _sha(repo, ref):
    """Full SHA of a ref; a 40-hex SHA is used as is, without asking git."""
    if FULL_SHA.fullmatch(ref):
        return ref
    return gitrefs.resolve(repo, ref)[0]


def _store(args):
    return Store(Path(args.data) / "results.db")


# verdict


def _verdict(args):
    store = _store(args)
    candidate = _sha(args.repo, args.candidate)
    baseline = _sha(args.repo, args.baseline) if args.baseline else None
    rows = []
    for job in store.jobs(kind="experiment", limit=100000):  # newest first
        spec = job["spec"]
        if job["state"] not in FINISHED or spec.get("candidate") != candidate:
            continue
        if baseline is not None and spec.get("baseline") != baseline:
            continue
        if args.metric is not None and spec.get("metric") != args.metric:
            continue
        verdict = (job["result"] or {}).get("verdict") or {}
        rows.append({"job": job["id"], "candidate": spec.get("candidate"), "baseline": spec.get("baseline"),
                     "metric": spec.get("metric"), "state": verdict.get("state"),
                     "checkpoint": verdict.get("checkpoint"), "diff": verdict.get("diff"),
                     "lo": verdict.get("lo"), "hi": verdict.get("hi"),
                     "detectable": verdict.get("detectable"), "pairs": verdict.get("pairs")})
    if not rows:
        print("no finished experiment")
        return 3
    for row in rows:
        print(json.dumps(row))
    newest = rows[0]["state"]
    if args.expect is not None and newest != args.expect:
        print(f"expected {args.expect!r}, newest job {rows[0]['job']} says {newest!r}", file=sys.stderr)
        return 4
    if args.forbid is not None and newest == args.forbid:
        print(f"newest job {rows[0]['job']} says forbidden state {newest!r}", file=sys.stderr)
        return 4
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="seeded_report", description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=str(DATA), help="directory holding results.db")
    ap.add_argument("--repo", default=str(REPO), help="git repository used to resolve refs")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("verdict", help="stored verdict of finished experiments for a candidate")
    p.add_argument("candidate")
    p.add_argument("--baseline")
    p.add_argument("--metric")
    p.add_argument("--expect", metavar="STATE", help="exit 4 unless the newest verdict is STATE")
    p.add_argument("--forbid", metavar="STATE", help="exit 4 if the newest verdict is STATE")
    p.set_defaults(fn=_verdict)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
