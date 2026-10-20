"""Summary of imported real ascensions (the yardstick for the ascension ladder)."""
import re
import statistics
from collections import Counter, defaultdict

from .importers import parse_dumplog

_REPEAT = re.compile(r"\s*\(\d+(st|nd|rd|th) time\)$")


def _spread(values):
    if not values:
        return {"median": None, "q1": None, "q3": None}
    if len(values) == 1:
        return {"median": values[0], "q1": values[0], "q3": values[0]}
    q1, _, q3 = statistics.quantiles(values, n=4)
    return {"median": statistics.median(values), "q1": q1, "q3": q3}


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def summary(refs, min_share=0.5):
    n = len(refs)
    if not n:
        return {"ascensions": 0}
    achieved = Counter(a for r in refs for a in set(r["record"].get("achievements", [])))
    dumps = [parse_dumplog(r["dumplog"]) for r in refs if r["dumplog"]]
    timelines = [d["events"] for d in dumps if d["events"]]
    first_turns = defaultdict(list)
    for events in timelines:
        first = {}
        for turn, text in events:
            first.setdefault(_REPEAT.sub("", text), turn)  # "killed Famine (2nd time)" -> first kill
        for event, turn in first.items():
            first_turns[event].append(turn)
    milestones = sorted(({"event": e, "median_turn": statistics.median(t), "share": len(t) / len(timelines)}
                         for e, t in first_turns.items() if len(t) / len(timelines) >= min_share),
                        key=lambda m: m["median_turn"])
    out = {
        "ascensions": n,
        "with_dumplog": len(dumps),
        "with_timeline": len(timelines),
        "turns": _spread(sorted(int(r["record"].get("turns", 0)) for r in refs)),
        "roles": Counter(r["role"] for r in refs).most_common(),
        "achievements": sorted(((a, c / n) for a, c in achieved.items()), key=lambda x: -x[1]),
        "milestones": milestones,
    }
    if dumps:
        m = len(dumps)
        wands = Counter(w for d in dumps for w in d["wands"])
        out.update(reflection=sum(d["reflection"] for d in dumps) / m,
                   magic_resistance=sum(d["magic_resistance"] for d in dumps) / m,
                   bag_of_holding=sum(d["bag_of_holding"] for d in dumps) / m,
                   xl=_median([d["xl"] for d in dumps]), ac=_median([d["ac"] for d in dumps]),
                   wands=[(w, c / m) for w, c in wands.most_common(10)])
    return out
