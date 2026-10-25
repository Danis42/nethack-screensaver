"""The Quest portal level: telling it from its message, and where to step next to find the portal.

On the first arrival at the level holding the Quest's magic portal (Dlvl 11-16) NetHack 3.6 pages the
quest leader's call (verified on NLD-NAO human games, 2026-10-25, 40 games with maxlvl >= 12):

    You receive a faint telepathic message from <leader>:
    Your help is urgently needed at <place>!
    Look for a ...ic transporter.
    You couldn't quite make out that last message.

Entering the portal: "You activated a magic portal!  You feel dizzy for a moment, but the sensation
passes." Later visits print a reminder, seen 450+ times in 150 human games with maxlvl >= 12
(NLD-NAO, 2026-10-25): "You again sense <leader> pleading for help." ("the Norn" for Valkyries; the Rogue's
leader is "demanding your attendance").

The portal is a hidden trap that fires when the hero steps on its square, seen or not, so the hunt walks
onto every reachable square of the level, then searches dead ends for hidden passages.
"""
from collections import deque

import numpy as np

PORTAL_MESSAGES = ("faint telepathic message from", "ic transporter", "You again sense ")
ENTERED_MESSAGE = "You activated a magic portal!"
DEAD_END_SEARCHES = 10  # searches per dead end before the hunt gives up on it


def is_portal_level_message(message: str) -> bool:
    return any(words in message for words in PORTAL_MESSAGES)


def _distances(walkable, pos):
    dis = np.full(walkable.shape, -1, dtype=np.int32)
    dis[pos] = 0
    queue = deque([pos])
    while queue:
        y, x = queue.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < walkable.shape[0] and 0 <= nx < walkable.shape[1] and walkable[ny, nx] \
                        and dis[ny, nx] == -1:
                    dis[ny, nx] = dis[y, x] + 1
                    queue.append((ny, nx))
    return dis


def dead_ends(walkable):
    """Walkable squares with at most one walkable orthogonal neighbour."""
    padded = np.pad(walkable, 1).astype(np.int32)
    neighbours = padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]
    return walkable & (neighbours <= 1)


def next_portal_square(walkable, visited, searched, pos):
    """Nearest reachable walkable square not stood on yet; when none is left, the nearest dead end searched
    fewer than DEAD_END_SEARCHES times; None when both are exhausted."""
    dis = _distances(walkable, tuple(pos))
    reachable = dis >= 0
    for candidates in (reachable & ~visited, reachable & dead_ends(walkable) & (searched < DEAD_END_SEARCHES)):
        if candidates.any():
            ys, xs = candidates.nonzero()
            i = int(np.argmin(dis[ys, xs]))
            return int(ys[i]), int(xs[i])
    return None
