"""Summaries of stored games: the dashboard and the A/B table of an experiment."""
from collections import Counter, defaultdict

from .metrics import METRICS, evaluate, killer
from .stats import Z95, newcombe


def summary(games):
    outcomes = defaultdict(Counter)
    for g in games:
        outcomes[g.get("strategy", "?")][g.get("outcome", "?").split(" on Dlvl")[0]] += 1
    stuck = sorted((g for g in games if g.get("unsticks", 0) > 0), key=lambda g: -g["unsticks"])
    return {
        "games": len(games),
        "metrics": {name: evaluate(m, games) for name, m in METRICS.items()},
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
