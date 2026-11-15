"""Which staircase to take (pure: no game access, so it can be unit-tested).

`dive_stairs` lists the downstairs a diver may take; it moved here from global_logic.py.
`wants_mines` and `mines_exit` decide when and where to leave an unwanted Mines level (SURV-04, D-06, D-07).
The Mines stairs cannot be told apart before first use ([fact:branch-stairs-shown-only-after-use]), so the
bot finds out on arrival and climbs straight back up.
"""
from . import utils
from .glyph import G
from .level import Level
from .plans import Milestone

# Milestones whose plan wants the hero in the Gnomish Mines. DIVE counts: a diver that lands in the Mines dives
# them until Mines' End (global_logic._diving_in_mines).
MINES_MILESTONES = frozenset({Milestone.FIND_GNOMISH_MINES, Milestone.FIND_MINETOWN, Milestone.EXPLORE_MINETOWN,
                              Milestone.FIND_MINES_END, Milestone.DIVE})


def wants_mines(milestone):
    return milestone in MINES_MILESTONES


def mines_exit(level, bfs):
    """The nearest reachable known upstairs of a Mines level, or None. Every Mines upstairs leads towards the
    Dungeons of Doom (Mines level 1's leads there directly)."""
    ups = [(int(bfs[y, x]), (y, x)) for y, x in zip(*utils.isin(level.objects, G.STAIR_UP).nonzero())
           if bfs[y, x] != -1]
    return min(ups)[1] if ups else None


def dive_stairs(dungeon_number, objects, stair_destination, bfs, mines=False):
    """Known, reachable downstairs that stay in this dungeon: the main one, or the Gnomish
    Mines while diving there (`mines`); a diver stuck in the Mines used to climb back out."""
    if dungeon_number != Level.DUNGEONS_OF_DOOM and not (mines and dungeon_number == Level.GNOMISH_MINES):
        return []  # the bot also travels up through branches; diving there would loop
    return [(y, x) for y, x in zip(*utils.isin(objects, G.STAIR_DOWN).nonzero())
            if bfs[y, x] != -1 and
            (stair_destination.get((y, x)) is None or
             stair_destination[(y, x)][0][0] == dungeon_number)]
