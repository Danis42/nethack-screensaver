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
  insects <ref> [--seeds N | --all-games]
      ant and killer bee deaths: per killer, prayer unused (A1), poison (A2), and the tactic rule
  zappers <ref> [--seeds N | --all-games]
      wand and ray deaths: divine (Z1), warned zaps (Z2), breath (Z3), unwarned (Z4), and the tactic rule
  stuck <ref> [--seeds N | --all-games] [--rows BUCKET]
      stuck-watch reports: games ending stuck at Dlvl 5+ by cause bucket, events by milestone and
      dungeon, end types, watchdog stacks; --rows lists the games of one bucket
  deaths <ref> (--killer TEXT | --metric NAME) [--seeds N | --all-games] [--min-depth D] [--max-depth D]
      one row per matching game with the context at the end (hp, hunger, food, prayers, last messages)

--seeds N (default 576) uses exactly the seeded games 0..N-1 of the commit and exits 2 when some are
missing; --all-games uses every stored game of the commit, seeded or not.

The scripts only read the bench database (games, jobs, references): looking at evidence
never changes it. Refs may be branches, tags, short SHAs or full 40-hex SHAs.
"""
import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from bench import gitrefs, reference
from bench.cli import DATA, REPO
from autoascend.prayer import prayer_outcome
from bench.metrics import ANTS, METRICS, RAYS, ended_stuck, killer
from bench.report import ladder_rows
from bench.stats import CHECKPOINTS, Z95, judge_paired, judge_paired_numeric, z_for

Z_BY_CONFIDENCE = {80: 1.2815515655446004, 95: Z95, 99: 2.5758293035489004}
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
    metric = METRICS[args.metric]
    games_c, games_b = store.games_by_seed(cand, range(n)), store.games_by_seed(base, range(n))
    cast = bool if metric.kind == "rate" else float
    pairs = []
    for seed in range(n):  # exactly as bench/scheduler.py _judge
        try:
            pairs.append((cast(metric.fn(games_c[seed])), cast(metric.fn(games_b[seed]))))
        except KeyError:
            pass
    if not pairs:
        print(f"no game has the fields metric {args.metric} needs")
        return 2
    z = z_for(n) if args.confidence is None else Z_BY_CONFIDENCE[args.confidence]
    values = [v for pair in pairs for v in pair]
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    if metric.kind != "rate":
        verdict = judge_paired_numeric(pairs, n, z=z)
        print(f"candidate {cand[:10]} vs baseline {base[:10]}, metric {args.metric} (numeric), seeds 0..{n - 1}")
        print(f"n={len(pairs)} mean={mean:.3f} sd={sd:.3f}")
        print(f"diff={verdict.diff:+.3f} lo={verdict.lo:+.3f} hi={verdict.hi:+.3f} "
              f"half-width={verdict.detectable:.3f} standardized={verdict.detectable / sd if sd else 0:.4f}")
        print(f"verdict={verdict.state} z={z:.3f}")
        return 0
    verdict = judge_paired(pairs, n, z=z)
    size = len(pairs)
    n10 = sum(1 for c, b in pairs if c and not b)
    n01 = sum(1 for c, b in pairs if b and not c)
    half = verdict.detectable
    print(f"candidate {cand[:10]} vs baseline {base[:10]}, metric {args.metric}, seeds 0..{n - 1}")
    print(f"n={size} n10={n10} n01={n01} q={(n10 + n01) / size:.3f}")
    print(f"diff={_points(verdict.diff)} points lo={_points(verdict.lo)} hi={_points(verdict.hi)} "
          f"half-width={_points(half, sign=False)} points mde80={_points(2.8 * half / 1.96, sign=False)} points")
    print(f"sd={sd:.3f} standardized={half / sd if sd else 0:.4f}")
    label = args.confidence or ('95' if z == Z95 else '99')
    print(f"verdict={verdict.state} z={z:.3f} ({label}%)")
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


# starvation

STARVATION_WINDOW = 1000  # turns before the end in which a prayer counts as part of the starvation


def _prayer_list(game):
    """[(turn, outcome)] from the stored prayers; [] when none were stored."""
    return [(turn, prayer_outcome(text.split(" | ")))
            for turn, text in ((p[0], p[1] if len(p) > 1 else "") for p in game.get("prayers") or [])]


def _starvation_bucket(game):
    end = game["turns"]
    recent = [(t, o) for t, o in _prayer_list(game) if t >= end - STARVATION_WINDOW]
    food = game.get("food_at_end", -1)
    if any(o == "failed" for _, o in recent):
        return "failed-prayer"
    if food > 0:
        return "food-carried"
    if food == 0 and any(o == "success" for _, o in recent):
        return "prayer-cooldown"
    if food == 0 and "prayers" in game and not recent and end > STARVATION_WINDOW + 300:
        return "prayer-unused"
    return "other"


def _starvation_tags(game):
    reason, depth = game["end_reason"], _depth(game)
    return {
        "fainted-kill": "while fainted" in reason or "fainted from lack of food" in reason,
        "starved": "starved" in reason,
        "early": game["turns"] < 4500 and depth is not None and depth <= 4,
        "long": game["turns"] >= 6000,
        "stuck": game.get("stuck_diving", 0) > 0 or game.get("unsticks", 0) > 0,
    }


STARVATION_BUCKETS = ("failed-prayer", "food-carried", "prayer-cooldown", "prayer-unused", "other")


def _starvation(args):
    store = _store(args)
    sha = _sha(args.repo, args.ref)
    games, label = _games(args, store, sha)
    if games is None:
        return 2
    games = [g for g in games if _safe(METRICS["starved"].fn, g)]
    n = len(games)
    by_bucket = {b: [g for g in games if _starvation_bucket(g) == b] for b in STARVATION_BUCKETS}
    tags = ("fainted-kill", "starved", "early", "long", "stuck")
    print(f"Commit `{sha}`, n = {n} starvation games ({label}); prayers count if within "
          f"{STARVATION_WINDOW} turns of the end")
    print()
    print("| Bucket | Games | % of starvation games | Median turns | Median depth | Top roles | "
          + " | ".join(tags) + " |")
    print("|" + "---|" * (6 + len(tags)))
    for bucket, members in by_bucket.items():
        depths = [d for d in map(_depth, members) if d is not None]
        roles = ", ".join(r for r, _ in Counter(g.get("role", "?") for g in members).most_common(3))
        counts = [sum(_starvation_tags(g)[t] for g in members) for t in tags]
        print(f"| {bucket} | {len(members)} | {_pct(len(members), n)} "
              f"| {_num(statistics.median(g['turns'] for g in members)) if members else '-'} "
              f"| {_num(statistics.median(depths)) if depths else '-'} | {roles or '-'} | "
              + " | ".join(map(str, counts)) + " |")
    failed = by_bucket["failed-prayer"]
    if failed:
        per_game = [sum(o == "failed" for _, o in _prayer_list(g)) for g in failed]
        gaps = []
        for g in failed:
            prayers = _prayer_list(g)
            first = next(i for i, (_, o) in enumerate(prayers) if o == "failed")
            if first > 0:
                gaps.append(prayers[first][0] - prayers[first - 1][0])
        print()
        print(f"failed prayers per game: 1 -> {sum(c == 1 for c in per_game)}, "
              f"2+ -> {sum(c >= 2 for c in per_game)}")
        print("median gap from the previous prayer to the first failed one: "
              + (f"{_num(statistics.median(gaps))} turns" if gaps else "-"))
    return 0


# insects

INSECTS = ANTS + ("killer bee",)
INSECT_PRAYER_WINDOW = 1000  # a prayer this close to the end counts as used against the insects


def _insect_prayer_unused(game):
    end = game["turns"]
    return end > 300 and not any(turn >= end - INSECT_PRAYER_WINDOW for turn, _ in _prayer_list(game))


def _insect_poison(game):
    return any("poison" in m.lower() for m in game.get("last_messages") or [])


def _insect_tactic(a1, a2):
    """The rule, fixed before reading the numbers (plan 01-10)."""
    if a1 >= 0.40:
        return "pray-earlier"
    if a2 >= 0.25:
        return "poison-resistance"
    return "close-door"


def _insects(args):
    store = _store(args)
    sha = _sha(args.repo, args.ref)
    games, label = _games(args, store, sha)
    if games is None:
        return 2
    insect = [g for g in games if "end_reason" in g and killer(g) in INSECTS]
    fainted = [g for g in insect if _safe(METRICS["starved"].fn, g)]
    fought = [g for g in insect if not _safe(METRICS["starved"].fn, g)]
    band = [g for g in games if "end_reason" in g and g.get("outcome") != "escaped"
            and _depth(g) is not None and 4 <= _depth(g) <= 12]
    print(f"Commit `{sha}`, {len(games)} games ({label}); {len(insect)} insect deaths, "
          f"{len(fainted)} of them killed while fainted by an insect (excluded below)")
    print()
    print("| Killer | Games | % of all games | % of Dlvl 4-12 deaths | Median depth | Median XL |")
    print("|---|---|---|---|---|---|")
    for name in INSECTS:
        members = [g for g in fought if killer(g) == name]
        depths = [d for d in map(_depth, members) if d is not None]
        xls = [g["xp_level"] for g in members if "xp_level" in g]
        in_band = sum(1 for g in members if _depth(g) is not None and 4 <= _depth(g) <= 12)
        print(f"| {name} | {len(members)} | {_pct(len(members), len(games))} | {_pct(in_band, len(band))} "
              f"| {_num(statistics.median(depths)) if depths else '-'} "
              f"| {_num(statistics.median(xls)) if xls else '-'} |")
    n = len(fought)
    a1 = sum(_insect_prayer_unused(g) for g in fought) / n if n else 0.0
    a2 = sum(_insect_poison(g) for g in fought) / n if n else 0.0
    print()
    print(f"A1 prayer unused (no prayer in the last {INSECT_PRAYER_WINDOW} turns, turns > 300): {_pct(round(a1 * n), n)}")
    print(f"A2 poison in the last messages: {_pct(round(a2 * n), n)}")
    print(f"tactic: {_insect_tactic(a1, a2)}")
    return 0


# zappers

ZAPPER_CLASSES = ("Z1 divine", "Z2 warned", "Z3 breath", "Z4 unwarned")


def _zapper_class(game):
    name, end = killer(game), game["turns"]
    if ("lightning" in name or "disintegration" in name) and any(t >= end - 10 for t, _ in _prayer_list(game)):
        return "Z1 divine"
    if "blast of" in name:
        return "Z3 breath"
    zaps = game.get("zaps_seen")
    earlier = (game.get("last_messages") or [])[:-1]
    if (isinstance(zaps, int) and zaps >= 2) or any(re.search(r"\bzaps\b", m) for m in earlier):
        return "Z2 warned"
    return "Z4 unwarned"


def _zapper_tactic(shares, failure_pause_on_main):
    """The rule, fixed before reading the numbers (plan 01-11)."""
    if shares["Z1 divine"] >= 0.30 and not failure_pause_on_main:
        return "stop-praying-after-failure"
    if shares["Z3 breath"] > max(shares["Z2 warned"], shares["Z4 unwarned"]):
        return "leave-breath-line"
    return "leave-zap-line"


def _failure_pause_on_main(repo):
    import subprocess
    return subprocess.run(["git", "-C", str(repo), "grep", "-q", "prayer_failed_turn", "main", "--",
                           "autoascend/agent.py"]).returncode == 0


def _zappers(args):
    store = _store(args)
    sha = _sha(args.repo, args.ref)
    games, label = _games(args, store, sha)
    if games is None:
        return 2
    zapped = [g for g in games if "end_reason" in g and any(r in killer(g) for r in RAYS)]
    band = [g for g in games if "end_reason" in g and _depth(g) is not None and 4 <= _depth(g) <= 12]
    n = len(zapped)
    by_class = {c: [g for g in zapped if _zapper_class(g) == c] for c in ZAPPER_CLASSES}
    print(f"Commit `{sha}`, {len(games)} games ({label}); {n} wand and ray deaths")
    print()
    print("| Class | Games | % of zapper deaths | % of all games | % of Dlvl 4-12 deaths | Median depth | Median XL | Top killers |")
    print("|---|---|---|---|---|---|---|---|")
    for c, members in by_class.items():
        depths = [d for d in map(_depth, members) if d is not None]
        xls = [g["xp_level"] for g in members if "xp_level" in g]
        in_band = sum(1 for g in members if _depth(g) is not None and 4 <= _depth(g) <= 12)
        top = ", ".join(f"{k} {v}" for k, v in Counter(killer(g) for g in members).most_common(3))
        print(f"| {c} | {len(members)} | {_pct(len(members), n)} | {_pct(len(members), len(games))} "
              f"| {_pct(in_band, len(band))} | {_num(statistics.median(depths)) if depths else '-'} "
              f"| {_num(statistics.median(xls)) if xls else '-'} | {_cell(top) or '-'} |")
    shares = {c: len(m) / n if n else 0.0 for c, m in by_class.items()}
    print()
    print(f"tactic: {_zapper_tactic(shares, _failure_pause_on_main(args.repo))}")
    return 0


# stuck

STUCK_BUCKETS = ("stairs-unreachable", "stairs-reachable", "explore-left", "no-way-found")
DUNGEON_NAMES = {0: "Doom", 2: "Mines", 4: "Sokoban"}


def _stuck_bucket(report):
    """Why the stuck watch gave up on a level, first match wins; "stairs" are the ones the bot needed
    (up stairs when its target was above, else down stairs)."""
    way = "up" if report.get("wants_up") else "down"
    if report[f"{way}_seen"] and not report[f"{way}_reachable"]:
        return "stairs-unreachable"
    if report[f"{way}_reachable"]:
        return "stairs-reachable"
    if report["frontier"] > 0:
        return "explore-left"
    return "no-way-found"


def _end_type(game):
    reason = game["end_reason"]
    if reason == "watchdog":
        return "watchdog"
    if _safe(METRICS["starved"].fn, game):
        return "starved"
    if reason.startswith("DEATH"):
        return "death"
    return "exception" if reason.startswith("exception") else "other"


def _last_bucket(game):
    return _stuck_bucket(game["stuck_reports"][-1]) if game["stuck_reports"] else "no-report"


def _stuck(args):
    store = _store(args)
    sha = _sha(args.repo, args.ref)
    games, label = _games(args, store, sha)
    if games is None:
        return 2
    recorded = [g for g in games if "stuck_reports" in g and "level_at_end" in g]
    failing = [g for g in recorded if ended_stuck(g)]
    if args.rows:
        for g in failing:
            if _last_bucket(g) == args.rows:
                last = g["stuck_reports"][-1] if g["stuck_reports"] else {}
                print(f"seed={g.get('seed')} dlvl={g['depth_at_end']} milestone={last.get('milestone', '-')} "
                      f"bucket={args.rows} end={_cell(g['end_reason'], 70)}")
        return 0
    n, k = len(recorded), len(failing)
    print(f"Commit `{sha}`, {len(games)} games ({label}); {len(games) - n} not recorded (older commit); "
          f"free5 {_pct(n - k, n)} ({n - k} of {n}); ended stuck at Dlvl 5+: {k}")
    print()
    print("Games ending stuck at Dlvl 5+, by the cause of their last stuck report (the tactic rules read this):")
    print()
    print("| Bucket | Games | % of stuck endings | Median Dlvl | closed doors > 0 | boulders > 0 | going up |")
    print("|---|---|---|---|---|---|---|")
    for bucket in STUCK_BUCKETS + ("no-report",):
        members = [g for g in failing if _last_bucket(g) == bucket]
        lasts = [g["stuck_reports"][-1] for g in members if g["stuck_reports"]]
        median = _num(statistics.median(g["depth_at_end"] for g in members)) if members else "-"
        print(f"| {bucket} | {len(members)} | {_pct(len(members), k)} | {median} "
              f"| {sum(r['closed_doors'] > 0 for r in lasts)} | {sum(r['boulders'] > 0 for r in lasts)} "
              f"| {sum(bool(r.get('wants_up')) for r in lasts)} |")
    events = [r for g in recorded for r in g["stuck_reports"]]
    for title, key in (("milestone", lambda r: r["milestone"]),
                       ("dungeon", lambda r: DUNGEON_NAMES.get(r["dungeon"], "other"))):
        print()
        print(f"All stuck events by {title} and bucket ({len(events)} events in {sum(bool(g['stuck_reports']) for g in recorded)} games):")
        print()
        print(f"| {title} | events | median Dlvl | " + " | ".join(STUCK_BUCKETS) + " |")
        print("|" + "---|" * (3 + len(STUCK_BUCKETS)))
        for name, _ in Counter(map(key, events)).most_common():
            rows = [r for r in events if key(r) == name]
            buckets = Counter(map(_stuck_bucket, rows))
            print(f"| {name} | {len(rows)} | {_num(statistics.median(r['dlvl'] for r in rows))} | "
                  + " | ".join(str(buckets[b]) for b in STUCK_BUCKETS) + " |")
    print()
    print("Stuck endings by end type: " + ", ".join(f"{t} {c}" for t, c in Counter(map(_end_type, failing)).most_common()))
    hung = [g for g in recorded if g["end_reason"] == "watchdog"]
    if hung:
        print()
        print(f"Watchdog games ({len(hung)}) by their innermost 3 frames:")
        print()
        print("| Games | Median Dlvl | Frames (innermost last) |")
        print("|---|---|---|")
        groups = Counter(" < ".join(g.get("watchdog_stack", [])[-3:]) or "(no stack)" for g in hung)
        for frames, count in groups.most_common(10):
            members = [g for g in hung if (" < ".join(g.get("watchdog_stack", [])[-3:]) or "(no stack)") == frames]
            print(f"| {count} | {_num(statistics.median(g['depth_at_end'] for g in members))} | {_cell(frames)} |")
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

    p = sub.add_parser("pairs", help="paired comparison of a metric (rate or numeric) over stored seeded games")
    p.add_argument("candidate")
    p.add_argument("baseline")
    p.add_argument("--metric", required=True, choices=sorted(METRICS))
    p.add_argument("--confidence", type=int, choices=sorted(Z_BY_CONFIDENCE),
                   help="interval level (default: the bench's, 99%% early, 95%% at the last checkpoint)")
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

    p = sub.add_parser("starvation", help="starvation games split into cause buckets (prayers, food)")
    p.add_argument("ref")
    _selection(p)
    p.set_defaults(fn=_starvation)

    p = sub.add_parser("insects", help="ant and killer bee deaths, prayer and poison shares, the tactic rule")
    p.add_argument("ref")
    _selection(p)
    p.set_defaults(fn=_insects)

    p = sub.add_parser("zappers", help="wand and ray deaths by class, and the tactic rule")
    p.add_argument("ref")
    _selection(p)
    p.set_defaults(fn=_zappers)

    p = sub.add_parser("stuck", help="stuck-watch reports: stuck endings by cause, events, watchdog stacks")
    p.add_argument("ref")
    _selection(p)
    p.add_argument("--rows", choices=STUCK_BUCKETS + ("no-report",), help="list the stuck-ending games of one bucket")
    p.set_defaults(fn=_stuck)

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
