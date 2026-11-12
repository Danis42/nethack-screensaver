"""Seed ranges, seed windows and the lgen seed of bench games (standard library only).

Ranges (D-07, D-17): seeds 0-999 are reserved for tools (staged, scenario, rewind games);
dev seeds are 0-99,999 for natural games, confirm seeds 100,000-199,999, and seeds from
1,000,000 up are the final range. The natural baseline plays the window 1,000-10,999 and
the A/A rerun its first 2,000 seeds. A window is half-open: [lo, hi).

lgen is NLE's level-generation seed. A bench lgen game uses seed + LGEN_OFFSET, never 0,
because the NLE fork treats lgen 0 as off. The refusal policy built on these ranges is in
check_window and check_seed below (D-07, D-17, D-22). They guard against accidental misuse, not an adversary.
"""
import re

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
CLEAN_KIND = "clean_attempt"  # Phase 7; never creatable over HTTP or MCP
GATE_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{0,63}$")


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


def check_window(lo, hi, kind, gate=None):
    """Range name of the window [lo, hi) for a job of this kind, or ValueError naming the rule it breaks.

    Natural jobs play dev seeds (1,000-99,999), or confirm seeds with a gate naming the phase gate (D-22: the gate
    field is the whole authorisation); they never touch the tool block 0-999 (D-17), the unassigned range or the
    final range (D-07). Tool runs stay inside the tool block. Only clean attempts play final seeds."""
    try:
        lo, hi = window(lo, hi)
    except ValueError as e:  # non-integer or empty: say "empty" for the empty case
        raise ValueError(f"{e}; the seed window is empty or malformed") from e
    first, last = range_of(lo), range_of(hi - 1)
    if kind == CLEAN_KIND:
        if first == last == "final":
            return "final"
        raise ValueError(f"clean attempts play final-range seeds (>= {FINAL_LO:,}) only; [{lo}, {hi}) is not final")
    if kind in TOOL_KINDS:
        if hi <= TOOL[1]:
            return "tool"
        raise ValueError(f"tool runs ({kind}) must stay inside the tool block 0-999 (D-17); [{lo}, {hi}) leaves it")
    if kind not in NATURAL_KINDS:
        raise ValueError(f"unknown job kind {kind!r}")
    if lo < TOOL[1]:
        raise ValueError(f"[{lo}, {hi}) touches the reserved tool block 0-999 (D-17); natural jobs start at 1000")
    if first != last:
        raise ValueError(f"[{lo}, {hi}) spans two ranges ({first} and {last}); keep a window inside one range")
    if first == "unassigned":
        raise ValueError(f"[{lo}, {hi}) is in the unassigned range 200,000-999,999 (D-07)")
    if first == "final":
        raise ValueError(f"[{lo}, {hi}) is in the final range (>= {FINAL_LO:,}), kept for the clean attempt (D-07)")
    if first == "confirm" and (gate is None or not GATE_RE.match(str(gate))):
        raise ValueError(f"confirm-range windows need a gate naming the phase gate (D-22), matching {GATE_RE.pattern}")
    return first


def check_seed(seed, kind, gate=None):
    """check_window for the single seed [seed, seed + 1)."""
    return check_window(seed, int(seed) + 1, kind, gate)
