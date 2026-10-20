"""Per-game metrics the bench server compares. Adding one takes one line in METRICS.

A metric function gets one stored game (the GameResult JSON of whichever commit played it)
and returns a bool (rate) or a number (median). A game that lacks a field the function
needs (KeyError) is skipped for that metric only, so new metrics also work on old games."""
import statistics
from dataclasses import dataclass
from typing import Any, Callable

ANTS = ("soldier ant", "giant ant", "fire ant")
RAYS = ("wand", "magic missile", "bolt of", "death ray", "blast of")


def killer(game):
    """What killed the character ('soldier ant'), or '' when nothing did."""
    reason = game["end_reason"]
    if "killed by " not in reason:
        return ""
    name = reason.split("killed by ", 1)[1].split(",")[0].strip()
    for article in ("a ", "an ", "the "):
        if name.startswith(article):
            return name[len(article):]
    return name


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    kind: str  # "rate" or "median"
    fn: Callable[[dict], Any]


METRICS = {m.name: m for m in [
    Metric("dlvl6", "reached Dlvl 6+", "rate", lambda g: g["max_depth"] >= 6),
    Metric("dlvl10", "reached Dlvl 10+", "rate", lambda g: g["max_depth"] >= 10),
    Metric("escaped", "escaped the dungeon", "rate", lambda g: g["outcome"].startswith("escaped")),
    Metric("crashed", "bot crashed", "rate", lambda g: g["end_reason"].startswith("exception")),
    Metric("died", "died", "rate", lambda g: g["end_reason"].startswith("DEATH")),
    Metric("starved", "starved, or killed while fainted", "rate",
           lambda g: "starved" in g["end_reason"] or "fainted from lack of food" in g["end_reason"]),
    Metric("ants", "killed by an ant", "rate", lambda g: killer(g) in ANTS),
    Metric("rays", "killed by a wand or ray", "rate", lambda g: any(r in killer(g) for r in RAYS)),
    Metric("unstuck", "needed the unstick safety net", "rate", lambda g: g["unsticks"] > 0),
    Metric("depth", "max depth", "median", lambda g: g["max_depth"]),
    Metric("turns", "turns played", "median", lambda g: g["turns"]),
    Metric("score", "score", "median", lambda g: g["score"]),
]}


def evaluate(metric, games):
    values = []
    for game in games:
        try:
            values.append(metric.fn(game))
        except KeyError:
            pass
    skipped = len(games) - len(values)
    if metric.kind == "rate":
        hits = sum(bool(v) for v in values)
        return {"n": len(values), "skipped": skipped, "hits": hits,
                "rate": hits / len(values) if values else None}
    return {"n": len(values), "skipped": skipped,
            "median": statistics.median(values) if values else None}
