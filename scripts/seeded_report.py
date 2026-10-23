"""Read-only reports over the seeded bench store.

Usage: uv run python scripts/seeded_report.py <command> ...

Commands:
  verdict <candidate> [--baseline REF] [--metric NAME] [--expect STATE] [--forbid STATE]
      stored verdict of finished experiments (exit 0; 3 = none; 4 = --expect/--forbid violated)

  pairs <candidate> <baseline> --metric NAME [--seeds N]
      paired comparison: n, n10, n01, discordance q, diff, interval, half-width, minimum detectable effect

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
from bench.metrics import METRICS
from bench.stats import CHECKPOINTS, Z95, judge_paired, z_for
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


# pairs


def _points(value, sign=True):
    return f"{value * 100:+.1f}" if sign else f"{value * 100:.1f}"


def _pairs(args):
    store = _store(args)
    cand, base = _sha(args.repo, args.candidate), _sha(args.repo, args.baseline)
    have = store.seeds(cand) & store.seeds(base)
    if args.seeds is not None:
        n = args.seeds
    else:  # the largest checkpoint both commits fully have
        n = next((c for c in sorted(CHECKPOINTS, reverse=True) if set(range(c)) <= have), None)
    if not n or not set(range(n)) <= have:
        missing = sorted(set(range(n or CHECKPOINTS[0])) - have)
        print(f"missing seeds: {len(missing)} of seeds 0..{(n or CHECKPOINTS[0]) - 1} are not stored on both "
              f"sides (first missing: {missing[:5]})")
        return 2
    fn = METRICS[args.metric].fn
    games_c, games_b = store.games_by_seed(cand, range(n)), store.games_by_seed(base, range(n))
    pairs = []
    for seed in range(n):  # exactly as bench/scheduler.py _judge
        try:
            pairs.append((bool(fn(games_c[seed])), bool(fn(games_b[seed]))))
        except KeyError:
            pass
    if not pairs:
        print(f"no game has the fields metric {args.metric} needs")
        return 2
    verdict = judge_paired(pairs, n)
    size = len(pairs)
    n10 = sum(1 for c, b in pairs if c and not b)
    n01 = sum(1 for c, b in pairs if b and not c)
    half = verdict.detectable
    z = z_for(n)
    print(f"candidate {cand[:10]} vs baseline {base[:10]}, metric {args.metric}, seeds 0..{n - 1}")
    print(f"n={size} n10={n10} n01={n01} q={(n10 + n01) / size:.3f}")
    print(f"diff={_points(verdict.diff)} points lo={_points(verdict.lo)} hi={_points(verdict.hi)} "
          f"half-width={_points(half, sign=False)} points mde80={_points(2.8 * half / 1.96, sign=False)} points")
    print(f"verdict={verdict.state} z={z:.3f} ({'95' if z == Z95 else '99'}%)")
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

    p = sub.add_parser("pairs", help="paired comparison of a rate metric over stored seeded games")
    p.add_argument("candidate")
    p.add_argument("baseline")
    p.add_argument("--metric", required=True, choices=sorted(n for n, m in METRICS.items() if m.kind == "rate"))
    p.add_argument("--seeds", type=int, help="seeds 0..N-1 (default: largest checkpoint both have)")
    p.set_defaults(fn=_pairs)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
