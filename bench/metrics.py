"""Per-game metrics the bench server compares. Adding one takes one line in METRICS.

A metric function gets one stored game (the GameResult JSON of whichever commit played it)
and returns a bool (rate) or a number (median). A game that lacks a field the function
needs (KeyError) is skipped for that metric only, so new metrics also work on old games."""
import statistics
from dataclasses import dataclass
from typing import Any, Callable

from autoascend.ladder import RUNGS

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


def ended_stuck(game):
    """The game ended on a Dlvl 5+ level it could not leave: the watchdog, the unstick safety net, or a
    stuck-watch report on the level it ended on. KeyError for games older than these fields."""
    if game["depth_at_end"] < 5:
        return False
    if game["end_reason"] == "watchdog" or game["unsticks"] > 0:
        return True
    reports, here = game["stuck_reports"], (game["dungeon_at_end"], game["level_at_end"])
    return bool(reports) and (reports[-1]["dungeon"], reports[-1]["level"]) == here


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    kind: str  # "rate" or "median"
    fn: Callable[[dict], Any]
    lower_is_better: bool = False  # diff stays candidate - baseline; only the better/worse label flips


METRICS = {m.name: m for m in [
    Metric("dlvl6", "reached Dlvl 6+", "rate", lambda g: g["max_depth"] >= 6),
    Metric("dlvl10", "reached Dlvl 10+", "rate", lambda g: g["max_depth"] >= 10),
    Metric("escaped", "escaped the dungeon", "rate", lambda g: g["outcome"].startswith("escaped")),
    Metric("crashed", "bot crashed", "rate", lambda g: g["end_reason"].startswith("exception"), lower_is_better=True),
    Metric("hung", "ended on the watchdog", "rate", lambda g: g["end_reason"] == "watchdog", lower_is_better=True),
    Metric("shopkeeper", "killed by a shopkeeper", "rate", lambda g: "shopkeeper" in g["end_reason"],
           lower_is_better=True),
    Metric("mimic", "killed by a mimic", "rate", lambda g: "mimic" in g["end_reason"], lower_is_better=True),
    Metric("died", "died", "rate", lambda g: g["end_reason"].startswith("DEATH"), lower_is_better=True),
    Metric("starved", "starved, or killed while fainted", "rate",
           lambda g: "starved" in g["end_reason"] or "fainted from lack of food" in g["end_reason"],
           lower_is_better=True),
    Metric("petrified", "turned to stone", "rate", lambda g: "petrified" in g["end_reason"], lower_is_better=True),
    Metric("poisoned", "killed by poison or a poisonous corpse", "rate", lambda g: "poison" in g["end_reason"],
           lower_is_better=True),
    Metric("eye", "killed while frozen by a floating eye's gaze", "rate",
           lambda g: "floating eye's gaze" in g["end_reason"], lower_is_better=True),
    Metric("ants", "killed by an ant", "rate", lambda g: killer(g) in ANTS, lower_is_better=True),
    Metric("rays", "killed by a wand or ray", "rate", lambda g: any(r in killer(g) for r in RAYS),
           lower_is_better=True),
    Metric("unstuck", "needed the unstick safety net", "rate", lambda g: g["unsticks"] > 0, lower_is_better=True),
    Metric("free5", "did not end stuck on a Dlvl 5+ level (higher is better)", "rate",
           lambda g: not ended_stuck(g)),
    Metric("depth", "max depth", "median", lambda g: g["max_depth"]),
    Metric("turns", "turns played", "median", lambda g: g["turns"]),
    Metric("score", "score", "median", lambda g: g["score"]),
] + [Metric(f"stage_{r.key}", f"reached {r.title}", "rate", lambda g, k=r.key: k in g["ladder"]) for r in RUNGS]}


def orient(state, metric):
    """Verdict label from the metric's point of view: for a lower-is-better rate a drop is "better"."""
    if metric.lower_is_better:
        return {"better": "worse", "worse": "better"}.get(state, state)
    return state


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
