"""Seed ranges, seed windows and the lgen seed of bench games (standard library only).

Ranges (D-07, D-17): seeds 0-999 are reserved for tools (staged, scenario, rewind games);
dev seeds are 0-99,999 for natural games, confirm seeds 100,000-199,999, and seeds from
1,000,000 up are the final range. The natural baseline plays the window 1,000-10,999 and
the A/A rerun its first 2,000 seeds. A window is half-open: [lo, hi).

lgen is NLE's level-generation seed. A bench lgen game uses seed + LGEN_OFFSET, never 0,
because the NLE fork treats lgen 0 as off. The refusal policy built on these ranges is in
plan 01-10; this module only names them.
"""

DEV = (0, 100_000)
CONFIRM = (100_000, 200_000)
FINAL_LO = 1_000_000
TOOL = (0, 1_000)
BASELINE_WINDOW = (1_000, 11_000)
AA_WINDOW = (1_000, 3_000)
LGEN_OFFSET = 10_000_000
USE_LGEN = "off"  # lgen mode of new jobs; plan 01-15 sets it from the lgen pilot
LGEN_MODES = ("off", "seed")
NATURAL_KINDS = ("baseline", "experiment")
TOOL_KINDS = ("staged", "scenario", "rewind")


def range_of(seed):
    """'tool', 'dev', 'confirm', 'final' or 'unassigned' for one seed."""
    seed = int(seed)
    if TOOL[0] <= seed < TOOL[1]:
        return "tool"
    if DEV[0] <= seed < DEV[1]:
        return "dev"
    if CONFIRM[0] <= seed < CONFIRM[1]:
        return "confirm"
    if seed >= FINAL_LO:
        return "final"
    return "unassigned"


def window(lo, hi):
    """(lo, hi) as ints; ValueError for non-integers, a negative lo or an empty window."""
    try:
        lo_i, hi_i = int(lo), int(hi)
    except (TypeError, ValueError) as e:  # None, "abc", 1.5 strings: not a window
        raise ValueError(f"seed window bounds must be integers, got {lo!r}, {hi!r}") from e
    if isinstance(lo, float) and lo != lo_i or isinstance(hi, float) and hi != hi_i:
        raise ValueError(f"seed window bounds must be integers, got {lo!r}, {hi!r}")
    if lo_i < 0 or lo_i >= hi_i:
        raise ValueError(f"seed window [{lo_i}, {hi_i}) is empty or negative; need 0 <= lo < hi")
    return lo_i, hi_i


def lgen_for(seed, mode):
    """NLE lgen value of a game: None when mode is 'off', seed + LGEN_OFFSET when 'seed'."""
    if mode == "off":
        return None
    if mode == "seed":
        return int(seed) + LGEN_OFFSET
    raise ValueError(f"lgen mode must be one of {LGEN_MODES}, got {mode!r}")
