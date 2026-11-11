"""The Castle's back entry (NetHack 5.0.0 dat/castle.lua; .planning/STATE.md 2026-11-11).

Facts:
- the Castle is the bottom of the Dungeons of Doom: no down stairs, no digging down; its trap doors (castle.lua
  des.trap("trap door", 40..55, 8)) are the way to the Valley (trap.c Can_fall_thru: Is_stronghold);
- the trap door at map (55,8) lies right behind the locked back door at (56,8), which opens on the far courtyard;
  the courtyards and the moat ring round the castle walls, so a levitating hero floats from the drawbridge side to
  the far courtyard ("enter via the back entry", castle.lua header);
- no kicking open doors while levitating (dokick.c:921): land on (57,8) first;
- the map is drawn at a fixed place, (y 3, x 8) on the screen (staged seeds 1-6), and may be mirrored left-right
  (level flag noflipy only); the raised drawbridge shows on its portcullis square, map (6,8) (display.c:2394);
- levitation does not stop the moat's giant eels drowning the hero (uhitm.c:3389).
"""
import numpy as np

MAP = (
    "}}}}}}}}}.............................................}}}}}}}}}",
    "}-------}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}-------}",
    "}|.....|-----------------------------------------------|.....|}",
    "}|.....+...............................................+.....|}",
    "}-------------------------------+-----------------------------}",
    "}}}}}}|........|..........+...........|.......S.S.......|}}}}}}",
    ".....}|........|..........|...........|.......|.|.......|}.....",
    ".....}|........------------...........---------S---------}.....",
    ".....}|...{....+..........+.........\\.S.................+......",
    ".....}|........------------...........---------S---------}.....",
    ".....}|........|..........|...........|.......|.|.......|}.....",
    "}}}}}}|........|..........+...........|.......S.S.......|}}}}}}",
    "}-------------------------------+-----------------------------}",
    "}|.....+...............................................+.....|}",
    "}|.....|-----------------------------------------------|.....|}",
    "}-------}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}-------}",
    "}}}}}}}}}.............................................}}}}}}}}}",
)
WIDTH = len(MAP[0])
ORIGIN = (3, 8)  # screen (y, x) of map (0, 0)
PORTCULLIS = (8, 6)  # map (y, x) where the raised drawbridge glyph shows
STAND, DOOR, TRAP_DOOR = (8, 57), (8, 56), (8, 55)  # map (y, x) of the back entry


# Both courtyards are lit (castle.lua des.region(00,05,05,11) and (57,05,62,11)) and framed by moat; the portcullis
# (the raised drawbridge's glyph) is in the dark wall beyond the moat and is seldom seen (staged seed 1). The hero
# arrives on the west side whether the map is mirrored or not (staged seeds 1 and 6), so the courtyard in view may
# be the front or the back one: the square mid-way along its castle side tells them apart, moat (the raised
# drawbridge looks like moat) at the front, floor at the back.
COURTYARDS = tuple((y, x) for y in range(5, 12) for x in list(range(6)) + list(range(57, WIDTH)))
COURTYARD_SEEN = 12  # moat squares seen where the map has them
KEY_SQUARES = ((8, 5), (8, 57))


def frame(drawbridge_positions, wet, known):
    """'flipped' bool from the seen drawbridge glyphs [(y, x)], or from the seen squares (screen masks: water,
    known) of a courtyard and its key square; None if neither matches the Castle."""
    for y, x in drawbridge_positions:
        if y - ORIGIN[0] != PORTCULLIS[0]:
            continue
        if x - ORIGIN[1] == PORTCULLIS[1]:
            return False
        if x - ORIGIN[1] == WIDTH - 1 - PORTCULLIS[1]:
            return True
    for flipped in (False, True):
        if not any(known[to_screen(flipped, p)] for p in KEY_SQUARES):
            continue
        moat = wrong = 0
        for p in COURTYARDS:
            q = to_screen(flipped, p)
            if known[q]:
                if bool(wet[q]) != (MAP[p[0]][p[1]] == '}'):
                    wrong += 1
                elif wet[q]:
                    moat += 1
        if moat >= COURTYARD_SEEN and wrong == 0:
            return flipped
    return None


def to_screen(flipped, pos):
    y, x = pos
    return ORIGIN[0] + y, ORIGIN[1] + (WIDTH - 1 - x if flipped else x)


def outside_mask(flipped, shape):
    """Screen mask of the map squares outside the castle walls: courtyards, moat and the rows past the moat."""
    start = (8, 1)
    seen = {start}
    todo = [start]
    while todo:
        y, x = todo.pop()
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if 0 <= ny < len(MAP) and 0 <= nx < WIDTH and (ny, nx) not in seen and MAP[ny][nx] in '.}':
                    seen.add((ny, nx))
                    todo.append((ny, nx))
    mask = np.zeros(shape, bool)
    for pos in seen:
        mask[to_screen(flipped, pos)] = True
    return mask


def float_path(passable, start, goal):
    """Shortest 8-connected path [start, ..., goal] over passable squares, or None."""
    h, w = passable.shape
    prev = {start: None}
    todo = [start]
    for pos in todo:
        if pos == goal:
            path = []
            while pos is not None:
                path.append(pos)
                pos = prev[pos]
            return path[::-1]
        y, x = pos
        for ny in range(max(0, y - 1), min(h, y + 2)):
            for nx in range(max(0, x - 1), min(w, x + 2)):
                if passable[ny, nx] and (ny, nx) not in prev:
                    prev[(ny, nx)] = pos
                    todo.append((ny, nx))
    return None
