"""The true dungeon layout of the running NetHack game, read from its memory.

Only measuring code may use this (the ascension ladder, the bench). The bot decides from the screen
alone and must never import it (Phase 2 CONTEXT D-04): an ascension found by reading memory would
not count.

NLE loads libnethack from a memfd (``/memfd:nle.so``), one copy per env, so a process can hold
several games. The copy is picked by the game's (core, disp) seeds, which each copy keeps in
``nle_seeds``; neither address order nor inode numbers follow creation order. Symbol offsets come
from ``nm`` on the installed library; the struct layouts are NetHack 3.6's (dungeon.h), verified on
NLE 1.3.0.
"""
import ctypes
import functools
import os
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

MEMFD = "/memfd:nle.so"
DUNGEON_SIZE = 56  # struct dungeon: dname[24] proto[15] boneid d_flags(4) entry/num/reached(int8) ledger/depth(int32)
NAME_LEN = 24
NUM_DUNLEVS = 45
DEPTH_START = 52
TOPOLOGY_MINES_DNUM = 42  # dungeon_topology: 20 d_levels, then tower, sokoban, mines, quest dnums
TOPOLOGY_QUEST_DNUM = 43
TOPOLOGY_MINEEND = 52  # d_mineend_level (dnum, dlevel)
MINES_NAME = "The Gnomish Mines"
SYMBOLS = ("dungeons", "n_dgns", "dungeon_topology", "nle_seeds")


class TruthUnavailable(Exception):
    """The layout could not be read (no NLE game in this process, unknown library, odd values)."""


@dataclass(frozen=True)
class DungeonTruth:
    mines_levels: int
    mines_end: tuple[int, int]  # (dnum, dlevel) of Mines' End
    quest_dnum: int
    quest_depth_start: int


@functools.cache
def _symbols() -> dict[str, int]:
    import nle
    lib = Path(nle.__file__).with_name("libnethack.so")
    try:
        out = subprocess.run(["nm", "-D", "--defined-only", lib], capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise TruthUnavailable(f"nm failed on {lib}: {e}") from e
    symbols = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in SYMBOLS:
            symbols[parts[2]] = int(parts[0], 16)
    if len(symbols) != len(SYMBOLS):
        raise TruthUnavailable(f"symbols missing in {lib}: {sorted(symbols)}")
    return symbols


def _game_base(seeds, seeds_offset) -> int:
    starts = {}  # memfd inode -> lowest mapped address (the load base of that copy)
    with open(f"/proc/{os.getpid()}/maps") as maps:
        for line in maps:
            if MEMFD in line:
                fields = line.split()
                start = int(fields[0].split("-")[0], 16)
                starts[fields[4]] = min(start, starts.get(fields[4], start))
    if not starts:
        raise TruthUnavailable("no NLE game loaded in this process")
    for base in starts.values():  # same seeds in two copies means the same dungeon, so any match will do
        if struct.unpack("QQ", ctypes.string_at(base + seeds_offset, 16)) == tuple(seeds):
            return base
    raise TruthUnavailable(f"no loaded game has seeds {tuple(seeds)}")


def read(seeds) -> DungeonTruth:
    """Layout of the game whose (core, disp) seeds are given (``Nethack.get_current_seeds()[:2]``)."""
    symbols = _symbols()
    base = _game_base(seeds, symbols["nle_seeds"])
    n_dgns = ctypes.c_int.from_address(base + symbols["n_dgns"]).value
    if not 1 <= n_dgns <= 16:
        raise TruthUnavailable(f"n_dgns {n_dgns}")
    table = ctypes.string_at(base + symbols["dungeons"], DUNGEON_SIZE * n_dgns)
    topology = ctypes.string_at(base + symbols["dungeon_topology"], DUNGEON_SIZE)
    mines, quest = topology[TOPOLOGY_MINES_DNUM], topology[TOPOLOGY_QUEST_DNUM]
    if not (mines < n_dgns and quest < n_dgns):
        raise TruthUnavailable(f"dnums mines {mines} quest {quest} of {n_dgns}")

    def entry(dnum):
        return table[dnum * DUNGEON_SIZE:(dnum + 1) * DUNGEON_SIZE]

    name = entry(mines)[:NAME_LEN].split(b"\0")[0].decode(errors="replace")
    levels = struct.unpack_from("b", entry(mines), NUM_DUNLEVS)[0]
    end = tuple(topology[TOPOLOGY_MINEEND:TOPOLOGY_MINEEND + 2])
    if name != MINES_NAME or not 2 <= levels <= 12 or end != (mines, levels):
        raise TruthUnavailable(f"unexpected Mines entry {name!r} levels {levels} end {end}")
    return DungeonTruth(mines_levels=levels, mines_end=end, quest_dnum=quest,
                        quest_depth_start=struct.unpack_from("i", entry(quest), DEPTH_START)[0])
