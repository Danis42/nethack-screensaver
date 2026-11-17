"""Where the hero went and what the plan wanted there: a visit log for trigger-gated experiments (bench/triggers.py).

Recording only, like snapshots.py: it reads the observation and the current milestone name and nothing else, so a
seeded game plays the same with or without it (refactor gate). snapshots["visits"] maps "dungeon:level" (NetHack's
dungeon number and level, from blstats) to {"turn": first turn there, "milestones": milestone names held there, in
first-seen order}. A trigger such as "on a Gnomish Mines level while the plan wanted something else" is then a
query over stored baseline games."""
from nethack_screensaver import snapshots


class Recorder(snapshots.Recorder):
    def __init__(self):
        super().__init__()
        self._visits: dict[str, dict] = {}

    def observe(self, obs, rungs=(), milestone=None) -> None:
        super().observe(obs, rungs)
        bl = obs["blstats"]
        if not bl.any():  # the game-over observation is all zero
            return
        key = f"{int(bl[snapshots.DNUM])}:{int(bl[snapshots.DLEVEL])}"
        visit = self._visits.get(key)
        if visit is None:
            visit = self._visits[key] = {"turn": int(bl[snapshots.TIME]), "milestones": []}
        if milestone is not None and milestone not in visit["milestones"]:
            visit["milestones"].append(milestone)

    def result(self) -> dict:
        return {**super().result(), "visits": self._visits}
