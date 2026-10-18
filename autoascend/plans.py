"""Secret strategies: each is an ordered milestone plan aiming at one ending."""
import re
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

    def drop_sokoban(self) -> None:
        self.advance()
        if self.current == Milestone.LOOT_SOKOBAN_PRIZE:
            self.advance()


@dataclass(frozen=True)
class StrategySpec:
    name: str
    title: str
    ending: str
    milestones: tuple[Milestone, ...]


M = Milestone
STRATEGIES = {s.name: s for s in [
    # Sokoban before the Mines: experience and items before the dwarves with mattocks.
    StrategySpec("pilgrim", "Pilgrim", "ascension",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_SOKOBAN, M.SOLVE_SOKOBAN, M.FIND_GNOMISH_MINES,
                  M.FIND_MINETOWN, M.FIND_MINES_END, M.GO_DOWN)),
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

# The Mines are peaceful for dwarves and gnomes, so their pilgrims go there first.
PEACEFUL_MINES_PILGRIM = (M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.FIND_MINETOWN, M.FIND_SOKOBAN,
                          M.SOLVE_SOKOBAN, M.FIND_MINES_END, M.GO_DOWN)

_RACES = {"human": "hum", "elven": "elf", "dwarven": "dwa", "gnomish": "gno", "orcish": "orc"}


def race_from_welcome(text: str) -> str | None:
    """Race from NetHack's welcome ("...You are a lawful dwarven Cavewoman."), if on screen."""
    m = re.search(r"You are an?\s+\w+\s+(?:(?:male|female)\s+)?(\w+)", text)
    return _RACES.get(m.group(1)) if m else None


def plan_for(name: str, race: str | None) -> tuple[Milestone, ...]:
    if name == "pilgrim" and race in ("dwa", "gno"):
        return PEACEFUL_MINES_PILGRIM
    return STRATEGIES[name].milestones


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
