"""What a level looks like when the stuck watch gives up on it (measuring only: no decisions here)."""
import numpy as np

from . import utils
from .glyph import G

KEEP = 50  # reports kept per game, oldest dropped


def frontier(seen, walkable, dis):
    """Reachable seen walkable squares with an unseen orthogonal neighbour: where exploring could go on."""
    unseen = ~seen
    beside_unseen = np.zeros_like(seen)
    beside_unseen[1:, :] |= unseen[:-1, :]
    beside_unseen[:-1, :] |= unseen[1:, :]
    beside_unseen[:, 1:] |= unseen[:, :-1]
    beside_unseen[:, :-1] |= unseen[:, 1:]
    return seen & walkable & (dis >= 0) & beside_unseen


def stuck_report(*, turn, dungeon, level, dlvl, milestone, objects, seen, walkable, dis, glyphs):
    """One row: where the bot was stuck and what it knew about the way down."""
    down = utils.isin(objects, G.STAIR_DOWN)
    return {
        "turn": int(turn), "dungeon": int(dungeon), "level": int(level), "dlvl": int(dlvl),
        "milestone": str(milestone),
        "down_seen": bool(down.any()),
        "down_reachable": bool((down & (dis >= 0)).any()),
        "frontier": int(frontier(seen, walkable, dis).sum()),
        "closed_doors": int(utils.isin(objects, G.DOOR_CLOSED).sum()),
        "boulders": int(utils.isin(glyphs, G.BOULDER).sum()),
    }
