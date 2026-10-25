"""What a level looks like when the stuck watch gives up on it (measuring only: no decisions here)."""
import numpy as np

from . import utils
from .glyph import G

KEEP = 50  # reports kept per game, oldest dropped
MINES = 2


def frontier(seen, walkable, dis):
    """Reachable seen walkable squares with an unseen orthogonal neighbour: where exploring could go on."""
    unseen = ~seen
    beside_unseen = np.zeros_like(seen)
    beside_unseen[1:, :] |= unseen[:-1, :]
    beside_unseen[:-1, :] |= unseen[1:, :]
    beside_unseen[:, 1:] |= unseen[:, :-1]
    beside_unseen[:, :-1] |= unseen[:, 1:]
    return seen & walkable & (dis >= 0) & beside_unseen


def wants_up(dungeon, level, target):
    """True when the way to the target level clearly starts with an up staircase.

    Level numbers grow downwards in every dungeon (Sokoban's level 1 is its top). Leaving the Mines
    goes up into the main dungeon; leaving Sokoban goes down."""
    target_dungeon, target_level = target
    if target_dungeon == dungeon:
        return target_level < level
    return dungeon == MINES


def stuck_report(*, turn, dungeon, level, dlvl, milestone, target, objects, seen, walkable, dis, glyphs):
    """One row: where the bot was stuck, where it wanted to go and what it knew about the way there."""
    down = utils.isin(objects, G.STAIR_DOWN)
    up = utils.isin(objects, G.STAIR_UP)
    return {
        "turn": int(turn), "dungeon": int(dungeon), "level": int(level), "dlvl": int(dlvl),
        "milestone": str(milestone), "target": [int(target[0]), int(target[1])],
        "wants_up": bool(wants_up(int(dungeon), int(level), target)),
        "down_seen": bool(down.any()),
        "down_reachable": bool((down & (dis >= 0)).any()),
        "up_seen": bool(up.any()),
        "up_reachable": bool((up & (dis >= 0)).any()),
        "frontier": int(frontier(seen, walkable, dis).sum()),
        "closed_doors": int(utils.isin(objects, G.DOOR_CLOSED).sum()),
        "boulders": int(utils.isin(glyphs, G.BOULDER).sum()),
    }
