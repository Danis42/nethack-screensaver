"""Summaries of stored games: the dashboard and the A/B table of an experiment."""
import statistics
from collections import Counter, defaultdict

from autoascend.ladder import RUNGS

from .metrics import METRICS, evaluate, killer
from .stats import Z95, newcombe


def ladder_rows(games, yardstick=None):
    """Per rung: games reaching it or higher, our median first turn, the real ascenders' median turn."""
    yardstick = yardstick or {}
    laddered = [g for g in games if "ladder" in g]  # older commits did not record it
    rows = []
    for r in RUNGS:
        turns = [g["ladder"][r.key] for g in laddered if r.key in g["ladder"]]
        rows.append({"rung": r.number, "key": r.key, "title": r.title,
                     "hits": sum(g["rung"] >= r.number for g in laddered), "n": len(laddered),
                     "median_turn": statistics.median(turns) if turns else None,
                     "yardstick_turn": yardstick.get(r.yardstick_event)})
    return rows


def summary(games, yardstick=None):
    outcomes = defaultdict(Counter)
    for g in games:
        outcomes[g.get("strategy", "?")][g.get("outcome", "?").split(" on Dlvl")[0]] += 1
    stuck = sorted((g for g in games if g.get("unsticks", 0) > 0), key=lambda g: -g["unsticks"])
    return {
        "games": len(games),
        "metrics": {name: evaluate(m, games) for name, m in METRICS.items()},
        "ladder": ladder_rows(games, yardstick),
        "killers": Counter(k for k in map(killer, games) if k).most_common(15),
        "depths": dict(sorted(Counter(g["max_depth"] for g in games).items())),
        "outcomes": {s: dict(c) for s, c in sorted(outcomes.items())},
        "crashes": [g["end_reason"] for g in games if g["end_reason"].startswith("exception")][-20:],
        "unstuck": [{k: g.get(k) for k in ("role", "max_depth", "turns", "unsticks", "end_reason")}
                    for g in stuck[:10]],
    }


def compare(candidate, baseline):
    """Every metric side by side; rates get a 95% interval (information only, not a verdict)."""
    rows = []
    for name, m in METRICS.items():
        c, b = evaluate(m, candidate), evaluate(m, baseline)
        row = {"metric": name, "description": m.description, "kind": m.kind, "candidate": c, "baseline": b}
        if m.kind == "rate" and c["n"] and b["n"]:
            row["diff"], row["lo"], row["hi"] = newcombe(c["hits"], c["n"], b["hits"], b["n"], Z95)
        rows.append(row)
    return rows
