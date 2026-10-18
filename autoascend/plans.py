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
