"""Secret strategies: each is an ordered milestone plan aiming at one ending."""
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Sequence


class Milestone(IntEnum):
    BE_ON_FIRST_LEVEL = auto()
    FIND_GNOMISH_MINES = auto()
    FIND_MINETOWN = auto()
    FIND_SOKOBAN = auto()
    SOLVE_SOKOBAN = auto()
    FIND_MINES_END = auto()
    GO_DOWN = auto()
    EXPLORE_MINETOWN = auto()
    LOOT_SOKOBAN_PRIZE = auto()
    RETURN_TO_SURFACE = auto()
    LEAVE_DUNGEON = auto()
    DIVE = auto()  # GO_DOWN, but take every known downstairs at once


class Plan:
    def __init__(self, milestones: Sequence[Milestone]):
        self._milestones = tuple(milestones)
        self._index = 0

    @property
    def current(self) -> Milestone:
        return self._milestones[self._index]

    def advance(self) -> None:
        # The last milestone (GO_DOWN, LEAVE_DUNGEON) ends the game by itself.
        self._index = min(self._index + 1, len(self._milestones) - 1)

    def can_bail_out(self) -> bool:
        return Milestone.RETURN_TO_SURFACE in self._milestones[self._index + 1:]

    def bail_out(self) -> None:
        """Give up the rest of the route and head home (only plans that have a way home)."""
        if self.can_bail_out():
            self._index = self._milestones.index(Milestone.RETURN_TO_SURFACE)

    def dive_instead(self) -> None:
        """Abandon the rest of the route and head down: a stuck character starves otherwise."""
        self._milestones = self._milestones[:self._index + 1] + (Milestone.DIVE,)
        self._index += 1

    def drop_sokoban(self) -> None:
        self.advance()
        if self.current == Milestone.LOOT_SOKOBAN_PRIZE:
            self.advance()


class ProgressWatch:
    """Notices a character that has seen no new level and no new milestone for `limit` turns.

    Stuck characters (a blocked way home, an endless search for Sokoban) lived on prayer
    until one came too early and they starved."""
    QUIET = (Milestone.BE_ON_FIRST_LEVEL, Milestone.DIVE)

    def __init__(self, limit: int):
        self.limit = limit
        self._levels = set()
        self._milestone = None
        self._since = None

    def stuck(self, level, milestone: Milestone, turn: int) -> bool:
        if level not in self._levels or milestone != self._milestone or self._since is None:
            self._levels.add(level)
            self._milestone = milestone
            self._since = turn
        return milestone not in self.QUIET and turn - self._since > self.limit


@dataclass(frozen=True)
class StrategySpec:
    name: str
    title: str
    ending: str
    milestones: tuple[Milestone, ...]


M = Milestone
STRATEGIES = {s.name: s for s in [
    # Mines before Sokoban: tried the other way round (2026-10-18), most pilgrims then died
    # searching Dlvl 6-10 for the Sokoban stairs at XL 3-5.
    StrategySpec("pilgrim", "Pilgrim", "ascension",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.FIND_MINETOWN, M.FIND_SOKOBAN,
                  M.SOLVE_SOKOBAN, M.FIND_MINES_END, M.GO_DOWN)),
    StrategySpec("daredevil", "Daredevil", "escape in celestial disgrace",
                 (M.BE_ON_FIRST_LEVEL, M.DIVE)),
    StrategySpec("sightseer", "Sightseer", "escape the dungeon",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.FIND_MINETOWN, M.EXPLORE_MINETOWN,
                  M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)),
    StrategySpec("treasure", "Treasure hunter", "escape with loot",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_SOKOBAN, M.SOLVE_SOKOBAN, M.LOOT_SOKOBAN_PRIZE,
                  M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)),
]}
DEFAULT_PLAN = STRATEGIES["pilgrim"].milestones


# How well this bot does per role (mean max depth over ~380 games, 2026-10-18).
ROLE_TIERS = {
    "strong": ("bar", "sam", "val", "mon"),
    "middle": ("cav", "kni", "pri", "ran"),
    "weak": ("arc", "tou", "rog", "hea", "wiz"),
}
# Hard strategies go to strong roles more often; every strategy stays possible for everyone.
TIER_WEIGHTS = {
    "strong": {"pilgrim": 35, "treasure": 35, "sightseer": 15, "daredevil": 15},
    "middle": {"pilgrim": 25, "treasure": 25, "sightseer": 25, "daredevil": 25},
    "weak": {"pilgrim": 10, "treasure": 10, "sightseer": 40, "daredevil": 40},
}


def choose_strategy(role: str, rng) -> str:
    tier = next((t for t, roles in ROLE_TIERS.items() if role in roles), "middle")
    weights = TIER_WEIGHTS[tier]
    names = sorted(weights)
    return rng.choices(names, weights=[weights[n] for n in names])[0]
