"""Which staircase to take (pure: no game access, so it can be unit-tested).

`dive_stairs` lists the downstairs a diver may take; it moved here from global_logic.py. The Mines branch
staircase choice (SURV-04) joins it in plan 02-05.
"""
from . import utils
from .glyph import G
from .level import Level


def dive_stairs(dungeon_number, objects, stair_destination, bfs, mines=False):
    """Known, reachable downstairs that stay in this dungeon: the main one, or the Gnomish
    Mines while diving there (`mines`); a diver stuck in the Mines used to climb back out."""
    if dungeon_number != Level.DUNGEONS_OF_DOOM and not (mines and dungeon_number == Level.GNOMISH_MINES):
        return []  # the bot also travels up through branches; diving there would loop
    return [(y, x) for y, x in zip(*utils.isin(objects, G.STAIR_DOWN).nonzero())
            if bfs[y, x] != -1 and
            (stair_destination.get((y, x)) is None or
             stair_destination[(y, x)][0][0] == dungeon_number)]
