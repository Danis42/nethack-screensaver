"""Crossing Medusa's water by levitation (.planning/research/MEDUSA-NH5.md).

Digging needs a square with no water within 1 (dig.c:606); medusa-3 has none at the arrival (0 of 16 squares), so
the hero levitates across. NetHack's travel command paths over water while levitating. Facts (NetHack 5.0.0):
- the down stairs are under Medusa (dat/medusa-*.lua: des.stair("down", medloc)); she sleeps there;
- '>' does not work while levitating (do.c:1154): land first;
- levitation does NOT stop an eel from drowning the hero (uhitm.c:3389 checks only swimming/amphibious/breathless);
- reflection turns her gaze back on her (mhitu.c) as long as she can see the hero.
"""
import numpy as np


def crossing_target(glyphs, stairs_down_glyphs, medusa_glyphs):
    """(y, x) to levitate to: the down stairs if seen, else Medusa (she sleeps on them), else None."""
    for wanted in (stairs_down_glyphs, medusa_glyphs):
        ys, xs = np.nonzero(np.isin(glyphs, list(wanted)))
        if len(ys):
            return int(ys[0]), int(xs[0])
    return None


def landing_square(walkable, wet, target):
    """The walkable, dry square nearest to target (the target itself first), or None."""
    ok = walkable & ~wet
    if ok[target]:
        return target
    ys, xs = np.nonzero(ok)
    if not len(ys):
        return None
    d = np.maximum(abs(ys - target[0]), abs(xs - target[1]))
    i = int(np.argmin(d))
    return int(ys[i]), int(xs[i])
