---
phase: 01-midgame-survival
reviewed: 2026-10-25T12:40:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - autoascend/agent.py
  - autoascend/exploration_logic.py
  - autoascend/global_logic.py
  - autoascend/level.py
  - autoascend/prayer.py
  - autoascend/soko_solver/search.py
  - autoascend/stats_logger.py
  - bench/mcp_server.py
  - bench/runner.py
  - bench/stats.py
  - nethack_screensaver/fixed_clock.py
  - nethack_screensaver/game.py
  - scripts/benchmark.py
  - scripts/nld_study.py
  - scripts/replay_check.py
  - scripts/seeded_report.py
findings:
  critical: 0
  warning: 1
  info: 4
  total: 5
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-25T12:40:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Scope: every non-test source file changed on main during Phase 1 (`git diff 90a08b3^ main`, 1,702 added lines).
The bot-facing changes are small and sound: the closed-shop-door guard (agent.py, level.py,
exploration_logic.py), the state-only Sokoban budget (global_logic.py, search.py), the panic-history
cap, and the observation-only death context in game.py. The turn-stall watchdog only fires on a
non-zero turn and leaves the itimer path intact. `prayer_outcome` checks failure markers first, and
"is pleased." cannot match "is displeased.". The analysis scripts open the bench store and the NLD
database read-only. No critical issue; one warning about a first-run build race, four minor notes.
Full suite on main: 416 passed, 5 skipped.

## Warnings

### WR-01: Concurrent first build of the time() shim can read a half-written C file

**File:** `nethack_screensaver/fixed_clock.py:49`
**Issue:** `shim_path` writes the C source to a shared name (`fixtime-<digest>.c`) and only the
output .so goes to a per-pid temp file. When several bench workers start at the same time and the cache
is empty, one process can truncate and rewrite the .c file while another one's `cc` is reading it. That
gives a compile error, and `check=True` turns it into a crashed worker start. It only happens on the very
first run after the SOURCE text changes.
**Fix:** write the source to a per-pid temp name too, and compile from that:
```python
src = cache / f"fixtime-{digest}.{os.getpid()}.c"
src.write_text(SOURCE)
subprocess.run([... str(src) ...], check=True)
tmp.replace(lib); src.unlink(missing_ok=True)
```

## Info

### IN-01: judge_paired_numeric gives a zero-width interval for a single pair

**File:** `bench/stats.py:93`
**Issue:** with n == 1, sd is set to 0, so the interval collapses onto the one difference and the verdict
reads "better" or "worse" from a single game. Reachable only through `seeded_report.py pairs --seeds 1`.
The scheduler never uses this function.
**Fix:** raise `ValueError("need at least 2 paired games")` when n < 2.

### IN-02: benchmark.py detects --seeds by substring over the whole command line

**File:** `scripts/benchmark.py:127`
**Issue:** `"--seeds" in " ".join(sys.argv)` also matches an `--out` path containing "--seeds". The
only effect is a needless re-exec with the shim loaded, which is harmless.
**Fix:** `any(a == "--seeds" or a.startswith("--seeds=") for a in sys.argv[1:])`.

### IN-03: meal "open" pattern can count non-food lines

**File:** `scripts/nld_study.py:97`
**Issue:** `^This .+ (?:is|tastes) .+!$` matches any "This X is Y!" line, not only food taste lines.
Such lines are rare in 3.6 and every cohort is measured the same way, so the study's comparisons hold.
Absolute meal counts may run slightly high.
**Fix:** require a food word or the known taste adjectives (delicious, terrible, bland, ...), or match the
NetHack message templates from eat.c.

### IN-04: cohort WHERE clause is interpolated into SQL

**File:** `scripts/nld_study.py:385`
**Issue:** `where` is put into the query with an f-string. Today it only comes from the module's own
COHORTS constants, and the database is opened read-only (`mode=ro`), so nothing is exposed. A future
CLI option that passes user text there would change that.
**Fix:** keep `where` restricted to the COHORTS table (look it up by key, never take raw text).

---

_Reviewed: 
_Reviewer: Claude (inline, gsd-code-reviewer rules)_
_Depth: standard_
