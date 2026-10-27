import numpy as np

from .maps import maps
from .. import utils

IGNORE = 0
EMPTY = 1
WALL = 2
BOULDER = 3
TARGET = 4


class SokoMap:
    def __init__(self, pos, sokomap):
        self.sokomap = sokomap
        self.pos = pos

    def bfs(self):
        return utils.bfs(*self.pos, walkable=self.sokomap == EMPTY,
                         walkable_diagonally=np.zeros_like(self.sokomap, dtype=bool),
                         can_squeeze=False)

    def move(self, boulder_y, boulder_x, dy, dx):
        assert self.sokomap[boulder_y, boulder_x] == BOULDER
        assert self.sokomap[boulder_y - dy, boulder_x - dx] == EMPTY
        assert self.bfs()[boulder_y - dy, boulder_x - dx] != -1
        assert self.sokomap[boulder_y + dy, boulder_x + dx] in [EMPTY, TARGET]

        self.pos = boulder_y, boulder_x
        self.sokomap[boulder_y, boulder_x] = EMPTY
        if self.sokomap[boulder_y + dy, boulder_x + dx] == EMPTY:
            self.sokomap[boulder_y + dy, boulder_x + dx] = BOULDER
        elif self.sokomap[boulder_y + dy, boulder_x + dx] == TARGET:
            pass
        else:
            assert 0

    def print(self, pos=None):
        mapping = {IGNORE: ' ', EMPTY: '.', WALL: '#', BOULDER: '0', TARGET: '^'}
        for y in range(self.sokomap.shape[0]):
            for x in range(self.sokomap.shape[1]):
                print((mapping[self.sokomap[y, x]] if (y, x) != (pos or self.pos) else '@'), end='')
            print()
        print()


def orientations():
    """Every stored map with its solution, also mirrored: NetHack 5 can flip Sokoban levels
    horizontally, vertically or both (the level files have no "noflip")."""
    for text, answer in maps.items():
        lines = [line for line in text.splitlines() if line]
        height, width = len(lines), max(map(len, lines))
        lines = [line.ljust(width) for line in lines]
        for flip_y in (False, True):
            for flip_x in (False, True):
                rows = lines[::-1] if flip_y else lines
                rows = [row[::-1] for row in rows] if flip_x else rows
                moves = [((height - 1 - y if flip_y else y, width - 1 - x if flip_x else x),
                          (-dy if flip_y else dy, -dx if flip_x else dx)) for (y, x), (dy, dx) in answer]
                yield '\n'.join(rows), moves


def convert_map(text):
    START = -1
    mapping = {'<': EMPTY, '>': START, '.': EMPTY, '?': EMPTY, '+': EMPTY,
               '0': BOULDER, '-': WALL, '|': WALL, ' ': IGNORE, '^': TARGET}
    ret = []
    for line in text.splitlines():
        if not line:
            continue
        ret.append([mapping[l] for l in line])
    ret = np.array(ret)
    assert len(list(zip(*(ret == TARGET).nonzero()))) == 1
    start = list(zip(*(ret == START).nonzero()))
    assert len(start) == 1
    start = start[0]
    ret[ret == START] = EMPTY
    return SokoMap(start, np.array(ret))
