"""Boulder pushes outside Sokoban (standard library + numpy only, no game access).

Walking into a boulder pushes it one square when the square beyond is free (hack.c moverock): not a wall,
not another boulder, not a monster. A diagonal push cannot pass a doorway. The bot's path search treats
every boulder as a wall, so a level whose only way on is behind a boulder looked like a dead end: 160 of
the 315 stuck starvers in baseline 6a840f2 had a boulder in view when the stuck watch gave up.
"""
import numpy as np

from .stuck import frontier

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def nothing_left(seen, walkable, dis, down):
    """No reachable unexplored edge and no reachable down staircase: the level looks finished."""
    return not frontier(seen, walkable, dis).any() and not (down & (dis >= 0)).any()


def push_candidates(boulders, walkable, blocked, doors, seen, dis, tried):
    """(stand, boulder, beyond) triples, best first: stand where the path search reaches, boulder next to it,
    beyond free. Pushes towards unseen squares come first, then the nearest. `blocked` marks squares a
    boulder cannot enter (monsters, other boulders), `walkable` the known floor; `tried` holds (boulder, beyond)
    pairs already done."""
    h, w = boulders.shape
    out = []
    for by, bx in zip(*np.nonzero(boulders)):
        for dy, dx in DIRECTIONS:
            sy, sx, ty, tx = by - dy, bx - dx, by + dy, bx + dx
            if not (0 <= sy < h and 0 <= sx < w and 0 <= ty < h and 0 <= tx < w):
                continue
            # boulders block sight, so the square beyond is often unseen: worth one try (a failed push costs a turn)
            if dis[sy, sx] < 0 or blocked[ty, tx] or (seen[ty, tx] and not walkable[ty, tx]):
                continue
            if dy and dx and (doors[sy, sx] or doors[by, bx] or doors[ty, tx]):
                continue
            if ((int(by), int(bx)), (int(ty), int(tx))) in tried:
                continue
            ay, ax = ty + dy, tx + dx
            opens = not seen[ty, tx] or (0 <= ay < h and 0 <= ax < w and not seen[ay, ax])
            out.append((not opens, int(dis[sy, sx]), (int(sy), int(sx)), (int(by), int(bx)), (int(ty), int(tx))))
    out.sort()
    return [c[2:] for c in out]


def break_candidate(boulders, dis, seen):
    """(stand, boulder) for breaking a boulder with a pick-axe: stand where the path search reaches, next to the
    boulder; boulders next to unseen squares first, then the nearest. None if no boulder is next to a reached
    square."""
    h, w = boulders.shape
    best = None
    for by, bx in zip(*np.nonzero(boulders)):
        opens = any(0 <= by + dy < h and 0 <= bx + dx < w and not seen[by + dy, bx + dx] for dy, dx in DIRECTIONS)
        for dy, dx in DIRECTIONS:
            sy, sx = by + dy, bx + dx
            if 0 <= sy < h and 0 <= sx < w and dis[sy, sx] >= 0:
                key = (not opens, int(dis[sy, sx]))
                if best is None or key < best[0]:
                    best = (key, ((int(sy), int(sx)), (int(by), int(bx))))
    return None if best is None else best[1]
