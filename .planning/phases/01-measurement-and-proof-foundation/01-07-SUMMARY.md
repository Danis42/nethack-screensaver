---
phase: 01-measurement-and-proof-foundation
plan: 07
subsystem: fact-ledger
tags: [fact-ledger, nethack-facts, 5.0-source, tranche-1]

requires:
  - phase: 01-04
    provides: facts/FACTS.toml format, scripts/facts.py check --source / report / coverage
provides:
  - "59 ledger entries for the seven rule modules (56 tagged 5.0-source with verified quotes, 3 unverified)"
  - "# fact: citations in prayer.py, castle.py, medusa.py, passtune.py, digging.py, telepathy.py, combat/stair_escape.py (comments only)"
affects: [01-09 research-note tranche and coverage report, Phase 2 work on prayer, Castle, Medusa, digging, telepathy]

actuals:
  tasks: 2
  commits: 2     # MEASURED: git rev-list --count 7296355..9f36588 before the SUMMARY commit
plan_head_before: 72963555777bf8ed67139fdf7ffbfbc5f0064f20
plan_head_after: 9f36588

tech-stack:
  added: []
  patterns:
    - "Quotes are copied by script from the cited source lines (whitespace-normalised), so they are verbatim by construction; check --source then re-verifies them"
    - "A citation that would push a line past 120 columns goes on its own comment line above the code line"

key-files:
  created: []
  modified:
    - facts/FACTS.toml
    - autoascend/prayer.py
    - autoascend/castle.py
    - autoascend/medusa.py
    - autoascend/passtune.py
    - autoascend/digging.py
    - autoascend/telepathy.py
    - autoascend/combat/stair_escape.py

key-decisions:
  - "Prayer messages that differ only by format string (god mood, deafness) are one fact each, quoting the format line"
  - "Facts shared by modules use one id (no-kicking-doors-while-levitating, eel-drowns-levitating-hero, dig-hole-fills-next-to-water)"
  - "Observed-only facts with no bench job (the Castle's screen origin) are unverified, not measured"

requirements-completed: [MEAS-10]

coverage:
  - id: D1
    description: "Every NetHack fact in the seven rule modules has a ledger entry and a # fact: citation; 5.0-source quotes verified"
    requirement: MEAS-10
    verification:
      - kind: command
        ref: ".venv/bin/python scripts/facts.py check --source (exit 0)"
        status: pass
      - kind: unit
        ref: "tests/test_facts.py and the seven modules' tests (54 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Completeness of the fact list per module (that no NetHack fact in these modules was missed)"
    requirement: MEAS-10
    human_judgment: true
    rationale: "The tooling measures citations, not untagged facts; completeness was judged by reading each module"

duration: 6 min
completed: 2026-11-12
---

# Phase 1 Plan 07: Fact tranche 1, bot modules Summary

**The NetHack knowledge in the seven rule modules is now in the ledger. 56 of 59 facts are confirmed by a verbatim quote from the 5.0 source, and the 3 that are not are flagged by `scripts/facts.py report` as unverified facts the bot depends on.**

## Performance

- **Duration:** 6 min (measured between start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 2 (tracer, auto)
- **Executed:** inline in the main session (no executor subagent)

## Per-module tag counts

| Module | Facts cited | 5.0-source | unverified |
|--------|-------------|------------|------------|
| prayer.py | 25 | 24 | 1 |
| castle.py | 9 | 8 | 1 |
| medusa.py | 6 | 6 | 0 |
| passtune.py | 3 | 3 | 0 |
| digging.py | 9 | 8 | 1 |
| telepathy.py | 6 | 6 | 0 |
| combat/stair_escape.py | 4 | 4 | 0 |

Some facts are shared between modules (e.g. `no-kicking-doors-while-levitating` in castle and medusa). The ledger holds 60 entries: 57 5.0-source, 3 unverified (including 01-04's Sokoban fact).

## Unverified facts the bot depends on (`scripts/facts.py report`)

- `prayer-fix-low-hp-feel-better` (prayer.py:23): "You feel better." is **not** a 5.0 prayer message. pray.c prints only "You feel much better." (pray.c:425); "You feel better." comes from artifact.c:1788. The NetHackWiki Prayer page (3.6.6) gives no HP-fix message. The marker can count a non-prayer message as a prayer success.
- `castle-map-screen-origin` (castle.py:36): the (3, 8) screen origin comes from staged seeds 1-6, not traced in the source.
- `dig-hole-here-message` (digging.py:17): "There is a hole here" was not found verbatim; the generic forms are pickup.c:401 and dokick.c:173.

## Findings worth knowing (from the 5.0 source)

- Several prayer markers do not match under **hallucination**: hcolor() gives random colours (golden glow, light blue aura, amber, black glow), and the god-mood words change (pleased as punch, ticklish, full, bummed). `prayer.py` already lists the hallucination wording as deliberately absent.
- The spellbook boon names the book's appearance ("A dusty spellbook appears at your feet!"), so the marker "A spellbook appears at your feet!" matches only some books.
- Medusa sits on the down stairs on medusa-3 and medusa-4 (`des.stair("down", medloc)`); medusa-1 and medusa-2 use fixed coordinates. Whether she is placed on them there was not checked.

## Task Commits

1. **Task 1 (tracer):** `e35a80f` (prayer.py facts)
2. **Task 2:** `9f36588`

## Deviations from Plan

**1. [Rule 3 - Blocking] Coverage key is `path`, not `file`**
- The Task 1 verify script reads coverage rows by `file`; plan 01-04 named the key `path`. The check was run against `path` (prayer.py: 29 citations). No later plan uses `file`.

**2. [Process] Web step limited to facts not found in the source**
- One web check (NetHackWiki Prayer, for "You feel better."). The other two unverified facts are observations or generic-format messages with no single page to check. Their `notes` say no web source was consulted, which the ledger rules allow.

**Total deviations:** 2. **Impact:** none on scope.

## Issues Encountered

`cp` is aliased to `cp -i` in this shell, so a ledger restore after a failed build step silently did nothing and the entries were appended twice. `check` caught it (TOML "declared twice"); the restore was redone with `command cp -f`, and the final ledger has no duplicates (`check --source` exit 0).

## Verification output

- `.venv/bin/python scripts/facts.py check --source`: exit 0.
- `tests/test_facts.py` + the seven modules' tests: 54 passed. Full non-slow suite: 738 passed, 6 skipped, 16 deselected.
- Word diff of every module: 0 removed tokens; every added line is a `# fact:` comment.
- `report` last line: `{"unverified_cited": 3}`.

## User Setup Required

None.

## Next Phase Readiness

Ready for wave 3 (01-06, 01-08, 01-09).

## Self-Check: PASSED
