"""The natural-game funnel: per ladder stage, how many games reached it, with a 95% Wilson interval (MEAS-02).

A stage counts as reached when its key is in the game's stored ladder dict (marginal reach), so a game that reaches
two stages on the same turn counts toward both, and a stage reached without the one before it still counts. Next to
the marginal rate each row carries the conditional rate along the pipeline order: of the games that reached the
previous stage, how many reached this one too. Nothing is dropped silently: games without a ladder field are
excluded and counted; games with a ladder error, a watchdog or an exception ending stay in n and are counted.

Standard library only; the stage list is autoascend.ladder.RUNGS (quest_portal before quest, D-21)."""
from autoascend.ladder import RUNGS

from .stats import Z95, wilson

STAGES = tuple(r.key for r in RUNGS)


def _flags(games):
    return {"ladder_error": sum(1 for g in games if g.get("ladder_error")),
            "watchdog": sum(1 for g in games if g.get("end_reason") == "watchdog"),
            "exception": sum(1 for g in games if str(g.get("end_reason", "")).startswith("exception"))}


def funnel(games, z=Z95):
    """{"n", "excluded": {"no_ladder"}, "flagged": {...}, "rows": [one row per stage, in ladder order]}."""
    laddered = [g for g in games if "ladder" in g]
    n = len(laddered)
    reached = [set(g["ladder"]) for g in laddered]
    rows, prev = [], None
    for r in RUNGS:
        hits = sum(1 for s in reached if r.key in s)
        lo, hi = wilson(hits, n, z) if n else (None, None)
        if prev is None:
            cond_hits, cond_n = hits, n
        else:
            cond_n = sum(1 for s in reached if prev in s)
            cond_hits = sum(1 for s in reached if prev in s and r.key in s)
        rows.append({"key": r.key, "title": r.title, "order": r.number, "hits": hits, "n": n,
                     "rate": hits / n if n else None, "lo": lo, "hi": hi, "prev": prev,
                     "cond_hits": cond_hits, "cond_n": cond_n, "cond_rate": cond_hits / cond_n if cond_n else None})
        prev = r.key
    return {"n": n, "excluded": {"no_ladder": len(games) - n}, "flagged": _flags(laddered), "rows": rows}
