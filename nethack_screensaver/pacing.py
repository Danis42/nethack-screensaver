"""Smart pacing: fast-forward boring stretches, normal speed for the good parts."""
import nle.nethack as nh
import numpy as np

QUIET_FRAMES = 10  # boring frames in a row before fast-forwarding
HOSTILE_RADIUS = 2
UNEXPLORED = nh.GLYPH_CMAP_OFF  # S_stone: never seen

X, Y, HP, MAXHP, DNUM, DLVL = 0, 1, 10, 11, 23, 24

_MONSTER = np.array([nh.glyph_is_monster(g) and not nh.glyph_is_pet(g)
                     for g in range(nh.MAX_GLYPH)])


def _hostile_near(glyphs, y, x) -> bool:
    y0, x0 = max(0, y - HOSTILE_RADIUS), max(0, x - HOSTILE_RADIUS)
    near = _MONSTER[glyphs[y0:y + HOSTILE_RADIUS + 1, x0:x + HOSTILE_RADIUS + 1]].copy()
    near[y - y0, x - x0] = False  # the player
    return bool(near.any())


class Pacer:
    """Interesting = exploring new map, a monster nearby (unless farming), or low HP."""

    def __init__(self):
        self._seen = {}  # (dungeon, level) -> most map cells ever seen there
        self._level = None
        self._quiet = 0

    def update(self, obs) -> bool:
        """Feed one frame; True means fast-forward it."""
        bl, glyphs = obs["blstats"], obs["glyphs"]
        level = (int(bl[DNUM]), int(bl[DLVL]))
        if level != self._level:
            self._level, self._quiet = level, 0
        cells = int((glyphs != UNEXPLORED).sum())
        exploring = cells > self._seen.get(level, 0)
        self._seen[level] = max(cells, self._seen.get(level, 0))
        fight = not obs.get("farming") and _hostile_near(glyphs, int(bl[Y]), int(bl[X]))
        interesting = exploring or fight or bl[HP] * 2 < bl[MAXHP]
        self._quiet = 0 if interesting else self._quiet + 1
        return self._quiet >= QUIET_FRAMES
