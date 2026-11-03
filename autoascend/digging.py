"""Digging down to leave a level the bot is stuck on (no game access here: choices and message reading).

Rules from NetHack 5 dig.c: applying an unwielded pick-axe wields it first; digging down stops once at a
pit and a second application turns the pit into a hole; stairs, altars, fountains, thrones, boulders and
hard-floor levels (Sokoban, branch bottoms such as Mines' End) cannot be dug through; digging inside a shop
makes the shopkeeper grab the pack. A dwarvish mattock is two-handed and cannot be applied with a shield.
"""
import nle.nethack as nh
import numpy as np

from . import objects as O
from .glyph import G, SS
from .item import flatten_items

DIGGABLE_FLOOR = frozenset(G.FLOOR - {SS.S_ndoor})
UNDIGGABLE = ('too hard to dig in', 'too hard to dig through')
FELL = ('You dig a hole through', 'You fall through', 'There is a hole here')


def dig_tool(items, empty_wands=()):
    """An identified, charged wand of digging (instant), else a non-cursed pick-axe, else None."""
    pick = None
    for item in flatten_items(items):
        if not item.is_unambiguous():
            continue
        if item.object == O.from_name("digging", nh.WAND_CLASS) and str(item) not in empty_wands:
            return item
        if item.object == O.from_name('pick-axe') and item.status != item.CURSED and pick is None:
            pick = item
    return pick


WET = (SS.S_pool, SS.S_water, SS.S_lava, SS.S_lavawall)


def _near(mask):
    """Squares with a True square among their 8 neighbours or on themselves."""
    padded = np.pad(mask, 1)
    h, w = mask.shape
    return np.logical_or.reduce([padded[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
                                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)])


def dig_square(objects, shop, dis, here):
    """Nearest reachable plain floor square outside shops (the hero's own square first), or None.

    Never next to water or lava: dig.c:606 fillholetyp fills the hole with water (a moat square is enough) and the
    hero falls in (staged medusa, map 3). On a level with known water an unexplored neighbour may be water too."""
    wet = np.isin(objects, WET)
    risky = wet | (objects == SS.S_stone) if wet.any() else wet
    ok = np.isin(objects, list(DIGGABLE_FLOOR)) & ~shop & (dis >= 0) & ~_near(risky)
    if ok[here]:
        return here
    if not ok.any():
        return None
    ys, xs = ok.nonzero()
    best = int(np.argmin(dis[ys, xs]))
    return int(ys[best]), int(xs[best])


def dig_outcome(message):
    """What one application of the pick said: 'fell', 'undiggable', 'pit' (apply again) or 'stopped'."""
    if any(text in message for text in FELL):
        return 'fell'
    if any(text in message for text in UNDIGGABLE):
        return 'undiggable'
    if 'you dig a pit in the' in message.lower():
        return 'pit'
    return 'stopped'
