"""Read-only reports over the seeded bench store.

Usage: uv run python scripts/seeded_report.py <command> ...

Commands:
  verdict <candidate> [--baseline REF] [--metric NAME] [--expect STATE] [--forbid STATE]
      stored verdict of finished experiments (exit 0; 3 = none; 4 = --expect/--forbid violated)

  pairs <candidate> <baseline> --metric NAME [--seeds N]
      paired comparison: n, n10, n01, discordance q, diff, interval, half-width, minimum detectable effect
  ladder <ref> [--seeds N | --all-games]
      the 17-rung table: games reaching each rung, our median turn, the real ascenders' median turn
  killers <ref> [--seeds N | --all-games] [--min-depth D] [--max-depth D]
      what ended the games: starved, ants, bees, wands, rays, breath, crashes, watchdog, other killers
  deaths <ref> (--killer TEXT | --metric NAME) [--seeds N | --all-games] [--min-depth D] [--max-depth D]
      one row per matching game with the context at the end (hp, hunger, food, prayers, last messages)

--seeds N (default 576) uses exactly the seeded games 0..N-1 of the commit and exits 2 when some are
missing; --all-games uses every stored game of the commit, seeded or not.

The scripts only read the bench database (games, jobs, references): looking at evidence
never changes it. Refs may be branches, tags, short SHAs or full 40-hex SHAs.
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from bench import gitrefs, reference
from bench.cli import DATA, REPO
from bench.metrics import ANTS, METRICS, RAYS, killer
from bench.report import ladder_rows
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


# game selection and table helpers


def _games(args, store, sha):
    """(games, label) for --seeds N (exactly seeds 0..N-1, ordered by seed) or --all-games; None if seeds are missing."""
    if args.all_games:
        return store.games(sha), "all stored games"
    by_seed = store.games_by_seed(sha, range(args.seeds))
    if len(by_seed) < args.seeds:
        missing = sorted(set(range(args.seeds)) - set(by_seed))
        print(f"missing seeds: {sha[:10]} stores {len(by_seed)} of seeds 0..{args.seeds - 1} "
              f"(first missing: {missing[:5]})")
        return None, None
    return [by_seed[seed] for seed in range(args.seeds)], f"seeds 0..{args.seeds - 1}"


def _depth(game):
    return game["depth_at_end"] if "depth_at_end" in game else game.get("max_depth")


def _in_depth(game, args):
    depth = _depth(game)
    if args.min_depth is not None and (depth is None or depth < args.min_depth):
        return False
    return args.max_depth is None or (depth is not None and depth <= args.max_depth)


def _safe(fn, game):
    try:
        return fn(game)
    except KeyError:
        return False


def _num(value):
    if value is None:
        return "-"
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _pct(k, n):
    return f"{100 * k / n:.1f}%" if n else "-"


def _cell(text, width=None):
    """One markdown table cell: no pipes or line breaks, cut to width characters."""
    text = str(text).replace("|", "/").replace("\n", " ")
    return text if width is None or len(text) <= width else text[:width]


def _selection(ap, default_seeds=576):
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--seeds", type=int, default=default_seeds, metavar="N",
                       help=f"use the seeded games 0..N-1 (default {default_seeds})")
    group.add_argument("--all-games", action="store_true", help="use every stored game of the commit")


def _depth_options(ap):
    ap.add_argument("--min-depth", type=int, help="only games whose end depth is at least this")
    ap.add_argument("--max-depth", type=int, help="only games whose end depth is at most this")


# ladder


def _yardstick(store):
    """Median first turn of each timeline event in the real ascensions (as bench/server.py App.yardstick)."""
    milestones = reference.summary(store.references()).get("milestones", [])
    return {m["event"]: m["median_turn"] for m in milestones}


def _ladder(args):
    store = _store(args)
    sha = _sha(args.repo, args.ref)
    games, label = _games(args, store, sha)
    if games is None:
        return 2
    print(f"Commit `{sha}`, n = {len(games)} games ({label})")
    print()
    print("| # | Rung | Reached | Our median turn | Ascenders' median turn |")
    print("|---|------|---------|-----------------|------------------------|")
    for row in ladder_rows(games, _yardstick(store)):
        share = f"{round(100 * row['hits'] / row['n'])}%" if row["n"] else "-"
        print(f"| {row['rung']} | {row['title']} | {row['hits']} ({share}) "
              f"| {_num(row['median_turn'])} | {_num(row['yardstick_turn'])} |")
    return 0


# killers


def _killer_rows():
    """(name, predicate, is_death) per row; the predicates are the bench's own definitions."""
    rays = [r for r in RAYS if r not in ("wand", "blast of")]
    return [
        ("starved", METRICS["starved"].fn, True),
        ("ants", lambda g: killer(g) in ANTS, True),
        ("killer bee", lambda g: killer(g) == "killer bee", True),
        ("wand", lambda g: "wand" in killer(g), True),
        ("rays", lambda g: any(r in killer(g) for r in rays), True),
        ("breath", lambda g: "blast of" in killer(g), True),
        ("exception", METRICS["crashed"].fn, False),
        ("watchdog", lambda g: g["end_reason"] == "watchdog", False),
    ]


def _killers(args):
    store = _store(args)
    games, label = _games(args, store, _sha(args.repo, args.ref))
    if games is None:
        return 2
    games = [g for g in games if "end_reason" in g and _in_depth(g, args)]
    n = len(games)
    deaths = sum(1 for g in games if g["end_reason"].startswith("DEATH"))
    named = _killer_rows()

    def row(name, members, is_death):
        depths = [d for d in map(_depth, members) if d is not None]
        turns = [g["turns"] for g in members if "turns" in g]
        return (f"| {_cell(name)} | {len(members)} | {_pct(len(members), n)} "
                f"| {_pct(len(members), deaths) if is_death else '-'} "
                f"| {_num(statistics.median(depths)) if depths else '-'} "
                f"| {_num(statistics.median(turns)) if turns else '-'} |")

    in_named = set()
    rows = []
    for name, fn, is_death in named:
        members = [i for i, g in enumerate(games) if _safe(fn, g)]
        in_named.update(members)
        rows.append((name, members, is_death))
    unnamed = [i for i, g in enumerate(games) if i not in in_named]
    others = Counter(killer(games[i]) for i in unnamed if killer(games[i]))
    ended = [i for i in unnamed if not killer(games[i])]
    rows.append(("escaped/other endings", ended, False))
    for name, _ in others.most_common(15):
        rows.append((name, [i for i in unnamed if killer(games[i]) == name], True))

    print(f"Commit `{_sha(args.repo, args.ref)}`, n = {n} games ({label}), {deaths} deaths; "
          "rows overlap (a game starved while an ant bit it counts in both)")
    print()
    print("| Ending | Count | % of games | % of deaths | Median depth | Median turns |")
    print("|--------|-------|------------|-------------|--------------|--------------|")
    for name, members, is_death in rows:
        print(row(name, [games[i] for i in members], is_death))
    return 0


# deaths


def _prayers(game):
    prayers = game.get("prayers")
    if prayers is None:
        return "-"
    if not prayers:
        return "0"
    turn, text = prayers[-1][0], prayers[-1][1] if len(prayers[-1]) > 1 else ""
    return f"{len(prayers)} (last t={turn} {_cell(text, 40)})"


def _deaths(args):
    store = _store(args)
    games, label = _games(args, store, _sha(args.repo, args.ref))
    if games is None:
        return 2
    if args.killer is not None:
        wanted = args.killer.lower()
        matches = [g for g in games if "end_reason" in g and wanted in killer(g).lower()]
    else:
        fn = METRICS[args.metric].fn
        matches = [g for g in games if _safe(fn, g)]
    matches = [g for g in matches if _in_depth(g, args)]
    print("| seed | role | turns | depth | rung | end | hp | hunger | food | prayers | zaps | last messages |")
    print("|------|------|-------|-------|------|-----|----|--------|------|---------|------|---------------|")
    for g in matches:
        hp = f"{g['hp_at_end']}/{g['max_hp_at_end']}" if "hp_at_end" in g and "max_hp_at_end" in g else "-"
        zaps = g.get("zaps_seen")
        last = " / ".join(_cell(m, 80) for m in g["last_messages"][-2:]) if g.get("last_messages") else "-"
        cells = [g.get("seed", "-"), g.get("role", "-"), g.get("turns", "-"), _depth(g) if _depth(g) is not None else "-",
                 g.get("rung", "-"), _cell(g.get("end_reason", "-"), 60), hp, g.get("hunger_at_end", "-"),
                 g.get("food_at_end", "-"), _prayers(g), "-" if zaps is None else (
                     zaps if isinstance(zaps, (int, str)) else json.dumps(zaps)), last]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    print()
    print(f"{len(matches)} games")
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

    p = sub.add_parser("ladder", help="games reaching each of the 17 rungs, with median turns")
    p.add_argument("ref")
    _selection(p)
    p.set_defaults(fn=_ladder)

    p = sub.add_parser("killers", help="what ended the games")
    p.add_argument("ref")
    _selection(p)
    _depth_options(p)
    p.set_defaults(fn=_killers)

    p = sub.add_parser("deaths", help="one context row per matching game")
    p.add_argument("ref")
    what = p.add_mutually_exclusive_group(required=True)
    what.add_argument("--killer", metavar="TEXT", help="games whose killer name contains TEXT")
    what.add_argument("--metric", choices=sorted(n for n, m in METRICS.items() if m.kind == "rate"),
                      help="games where this bench rate metric is true")
    _selection(p)
    _depth_options(p)
    p.set_defaults(fn=_deaths)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
