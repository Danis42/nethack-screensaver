import re
import time
from pathlib import Path

import nle
import pytest

from autoascend.soko_solver.search import solve

DES = Path(nle.__file__).parent / "nethackdir" / "dat" / "sokoban.des"


def load_levels():
    """The 8 Sokoban levels from NetHack's own level file: floor, boulders, traps, start."""
    levels = {}
    for block in DES.read_text().split("MAZE:")[1:]:
        name = block.split('"')[1]
        rows = block.split("MAP\n", 1)[1].split("ENDMAP", 1)[0].splitlines()
        floor = {(y, x) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "."}
        cell = lambda s: (int(s[1]), int(s[0]))  # (x, y) in the file -> (y, x)
        boulders = {cell(m) for m in re.findall(r'"boulder"\),\((\d+),(\d+)\)', block)}
        traps = {cell(m) for m in re.findall(r'TRAP:"(?:hole|pit)",\((\d+),(\d+)\)', block)}
        start = re.search(r"BRANCH:\((\d+),(\d+)", block) or re.search(r"STAIR:\((\d+),(\d+)\),down", block)
        levels[name] = (frozenset(floor), frozenset(boulders), frozenset(traps), cell(start.groups()))
    return levels


LEVELS = load_levels()

# Known limits of a 10 s search (2026-10-18): the big upper levels from scratch, which the
# stored solutions cover; the solver is the fallback for boards they no longer fit.
TOO_BIG = pytest.mark.xfail(reason="beyond the 10 s search; stored solution covers it", strict=False)
_hard = lambda name: pytest.param(name, marks=[TOO_BIG, pytest.mark.slow])
FROM_START = [_hard(n) if n in ("soko1-1", "soko1-2", "soko2-1", "soko3-2") else n for n in sorted(LEVELS)]


def walkable_from(start, free):
    seen, todo = {start}, [start]
    while todo:
        y, x = todo.pop()
        for n in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if n in free and n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def replay(floor, boulders, traps, player, pushes):
    """Check every push is legal in order; return the traps left unfilled."""
    boulders, traps = set(boulders), set(traps)
    for (by, bx), (dy, dx) in pushes:
        assert (by, bx) in boulders, ("no boulder to push", (by, bx))
        assert (by - dy, bx - dx) in walkable_from(player, floor - boulders - traps), "can't reach push"
        ty, tx = by + dy, bx + dx
        assert (ty, tx) in floor and (ty, tx) not in boulders, ("push blocked", (by, bx), (dy, dx))
        boulders.remove((by, bx))
        player = (by, bx)
        if (ty, tx) in traps:
            traps.remove((ty, tx))
        else:
            boulders.add((ty, tx))
    return traps


def test_all_eight_levels_are_parsed():
    assert len(LEVELS) == 8
    for floor, boulders, traps, start in LEVELS.values():
        assert len(boulders) >= len(traps) > 0 and start in floor and boulders | traps <= floor


@pytest.mark.parametrize("name", FROM_START)
def test_solver_fills_every_trap_from_the_start(name):
    floor, boulders, traps, start = LEVELS[name]
    t = time.monotonic()
    pushes = solve(floor, boulders, traps, start)
    assert pushes is not None, name
    assert replay(floor, boulders, traps, start, pushes) == set()
    assert time.monotonic() - t < 10


def test_disturbed_board_is_still_solved():
    # A boulder gone (destroyed by a monster): there is a spare, so it stays solvable.
    floor, boulders, traps, start = LEVELS["soko4-1"]
    gone = sorted(boulders)[:1]
    pushes = solve(floor, boulders - set(gone), traps, start)
    assert pushes is not None
    assert replay(floor, boulders - set(gone), traps, start, pushes) == set()


def test_unsolvable_board_returns_none_quickly():
    floor, boulders, traps, start = LEVELS["soko4-1"]
    t = time.monotonic()
    assert solve(floor, frozenset(sorted(boulders)[:1]), traps, start) is None  # 1 boulder, 9 pits
    assert time.monotonic() - t < 10


def _stored_solution(name):
    """The stored solution for a level, in the level file's coordinates."""
    from autoascend.soko_solver.maps import maps
    rows = DES.read_text().split(f'MAZE:"{name}"', 1)[1].split("MAP\n", 1)[1].split("ENDMAP", 1)[0].splitlines()
    walls = lambda rs: {(y, x) for y, r in enumerate(rs) for x, c in enumerate(r) if c in "-|"}
    for text, answer in maps.items():
        for shift in (0, -1, 1):
            if {(y, x + shift) for y, x in walls(text.splitlines())} == walls(rows):
                return [((y, x + shift), d) for (y, x), d in answer]
    raise KeyError(name)


def _play_stored(name, steps):
    """Board after the bot's way of replaying the stored solution for `steps` pushes: a push
    whose boulder is missing (it fell into a hole) is skipped."""
    floor, boulders, traps, player = LEVELS[name]
    boulders, traps = set(boulders), set(traps)
    for (by, bx), (dy, dx) in _stored_solution(name)[:steps]:
        dest = (by + dy, bx + dx)
        if (by, bx) not in boulders or dest in boulders or dest not in floor:
            continue
        boulders.remove((by, bx))
        if dest in traps:
            traps.remove(dest)
        else:
            boulders.add(dest)
        player = (by, bx)
    return floor, frozenset(boulders), frozenset(traps), player


@pytest.mark.parametrize("name", [_hard("soko1-1")] + [n for n in sorted(LEVELS) if n != "soko1-1"])
@pytest.mark.parametrize("fraction", [0.5, 0.8])
def test_solver_finishes_a_disturbed_half_played_level(name, fraction):
    floor, boulders, traps, player = _play_stored(name, int(len(_stored_solution(name)) * fraction))
    if not traps:
        pytest.skip("stored solution already done")
    spare = len(boulders) - len(traps)
    if spare > 0:  # a monster destroyed the boulder nearest the remaining traps
        nearest = min(boulders, key=lambda b: min(abs(b[0] - t[0]) + abs(b[1] - t[1]) for t in traps))
        boulders = boulders - {nearest}
    t = time.monotonic()
    pushes = solve(floor, boulders, traps, player)
    assert pushes is not None, (name, fraction, len(traps), "traps left")
    assert replay(floor, boulders, traps, player, pushes) == set()
    assert time.monotonic() - t < 10


def test_live_board_is_read_from_the_level_and_the_screen():
    import numpy as np

    from autoascend.glyph import SS, G
    from autoascend.global_logic import sokoban_board
    floor_glyph = SS.S_room  # screen symbols are glyph numbers already
    objects = np.full((21, 79), SS.S_stone, dtype=np.int16)
    objects[2, 2:6] = floor_glyph
    objects[2, 6] = SS.S_hole
    objects[2, 1] = SS.S_vwall
    objects[2, 3] = -1  # never seen: a boulder has always stood there
    objects[2, 5] = -1  # a scroll of earth has always lain there: never seen bare
    walkable = np.zeros((21, 79), bool)
    walkable[2, 2:6] = True  # the agent knows item squares are walkable
    glyphs = objects.copy()
    glyphs[2, 3] = next(iter(G.BOULDER))
    floor, boulders, traps = sokoban_board(objects, walkable, glyphs)
    assert boulders == {(2, 3)} and traps == {(2, 6)}
    assert floor == {(2, 2), (2, 3), (2, 4), (2, 5), (2, 6)}
