---
phase: 01-measurement-and-proof-foundation
plan: 09
subsystem: fact-ledger
tags: [fact-ledger, research-notes, quest-portal, coverage, tranche-1]

requires:
  - phase: 01-05
    provides: quest_portal ladder stage (its detector is now cited)
  - phase: 01-07
    provides: tranche-1 bot-module entries, the entry style
provides:
  - "6 new ledger entries (all 5.0-source): pudding split, cloned monsters' drops, 7 hellfill styles, blade force breakage, quest portal entered message, quest portal level call"
  - "[fact:] markers in .planning/research SUMMARY.md, PITFALLS.md, FEATURES.md"
  - "# fact: citations in autoascend/quest_portal.py and on the quest_portal detector in autoascend/ladder.py (comments only)"
  - "01-FACT-COVERAGE.json: coverage after tranche 1 plus the outcome of all 16 UNVERIFIED marks"
affects: [tranche 2 (next fact-tagging work), Phase 2 Gehennom and item work]

actuals:
  tasks: 2
  commits: 2     # MEASURED: git rev-list --count 4f69b09..1e7e2f9 before the SUMMARY commit
plan_head_before: 4f69b091d1223324c954a4ce36458eda26e299e8
plan_head_after: 1e7e2f9df5e6781ca41bd79292889341a9ee03ab

tech-stack:
  added: []
  patterns:
    - "Non-NetHack UNVERIFIED marks stay in the notes as they are and are listed with a reason in the coverage report"

key-files:
  created:
    - .planning/phases/01-measurement-and-proof-foundation/01-FACT-COVERAGE.json
  modified:
    - facts/FACTS.toml
    - .planning/research/SUMMARY.md
    - .planning/research/PITFALLS.md
    - .planning/research/FEATURES.md
    - autoascend/quest_portal.py
    - autoascend/ladder.py

key-decisions:
  - "Non-NetHack marks go under the report key non_nethack_marks (and tranche_1_marks lists all 16), because coverage() already uses notes for per-note counts"
  - "The XL14 Bell-reachability mark is a play outcome, not a rule; it is listed as non-NetHack and needs games to settle"

requirements-completed: [MEAS-10]

coverage:
  - id: D1
    description: "All 16 research UNVERIFIED marks resolved: 5 tagged facts with markers, 11 listed as non-NetHack with reasons"
    requirement: MEAS-10
    verification:
      - kind: command
        ref: ".venv/bin/python scripts/facts.py check --source (exit 0); 01-FACT-COVERAGE.json tranche_1_marks has 16 entries"
        status: pass
    human_judgment: false
  - id: D2
    description: "Quest portal facts cited from quest_portal.py and the ladder detector; comment-only"
    requirement: MEAS-10
    verification:
      - kind: unit
        ref: "tests/test_facts.py, tests/test_ladder.py, tests/test_quest_portal.py (62 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Classification of each mark as NetHack fact or not"
    requirement: MEAS-10
    human_judgment: true
    rationale: "Judgment by reading each mark; the owner may disagree with a non-NetHack call"

duration: 2 min
completed: 2026-11-12
---

# Phase 1 Plan 09: Fact tranche 1, research notes Summary

**All 16 UNVERIFIED marks in the research notes are resolved. Five were NetHack facts, now confirmed in the 5.0 source; two of them correct the notes: Gehennom filler has 7 styles, not 6, and in 5.0 split puddings drop no death items. The quest-portal stage's messages are cited from the 5.0 source.**

## Performance

- **Duration:** 2 min (measured between start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 2 (tracer, auto)
- **Executed:** inline in the main session (no executor subagent)

## The 16 marks

| File:line | Outcome |
|-----------|---------|
| SUMMARY.md:18 | not NetHack: previous session's unverified claims (process) |
| SUMMARY.md:96 | not NetHack: the fact-ledger method |
| SUMMARY.md:109 | **fact**: `pudding-splits-on-iron-hit`, `cloned-monsters-drop-no-items` |
| SUMMARY.md:149 | **fact**: `hellfill-has-seven-styles` |
| SUMMARY.md:153 | not NetHack: NLE fork-at-arrival spike (tooling) |
| SUMMARY.md:214 | not NetHack: NLE fork survival (tooling) |
| PITFALLS.md:70 | **fact**: `pudding-splits-on-iron-hit`, `cloned-monsters-drop-no-items` |
| PITFALLS.md:206 | not NetHack: LLM latency and cost |
| PITFALLS.md:249 | not NetHack: the fact-ledger method |
| PITFALLS.md:388 | not NetHack: process rule on LLM tables |
| ARCHITECTURE.md:245 | not NetHack: NLE fork spike (tooling) |
| ARCHITECTURE.md:539 | not NetHack: NLE fork fallback (tooling) |
| FEATURES.md:45 | **fact**: `force-lock-blade-may-break` |
| FEATURES.md:171 | **fact**: `hellfill-has-seven-styles` |
| XL14-NH5.md:43 | not a rule: Bell reachability is a play outcome, settled only by games |
| STACK.md:8 | not NetHack: the research confidence tag |

## Tranche 1 totals (plans 01-04, 01-07, 01-09)

Ledger: 66 entries, 63 `5.0-source`, 3 `unverified`, 0 `measured`. Bot-module citations: 71 (coverage totals at `1e7e2f9`: 55 files, 8390 counted literals, 71 citations).

Unverified facts the bot depends on (`scripts/facts.py report`, 3): `castle-map-screen-origin`, `dig-hole-here-message`, `prayer-fix-low-hp-feel-better` (details in 01-07-SUMMARY).

## Findings that correct the research notes

- **Gehennom filler levels:** `dat/hellfill.lua` picks one of **7** styles (lines 320-414, chosen at line 431), not 6.
- **Pudding farming in 5.0:** puddings still split on an iron or metal melee hit (uhitm.c:1608-1625), but cloned monsters never drop a random death item (mon.c:3592-3593) and big clones lose the guaranteed corpse. Farming for items does not work; random-chance corpses of clones remain possible.
- **Forcing locks with a blade:** a non-cursed blade can break on a failed attempt (lock.c:228-236; the source comment gives ~67% survival over 50 attempts at +0).

## Next tranche (from the coverage ranking)

Top ten bot files by uncited numeric literals at `1e7e2f9`:

1. `autoascend/soko_solver/maps.py` (6116 literals; Sokoban map data)
2. `autoascend/objects/data.py` (1442; generated object table)
3. `autoascend/glyph/monflag.py` (194)
4. `autoascend/glyph/screen_symbol_consts.py` (106)
5. `autoascend/agent.py` (74)
6. `autoascend/global_logic.py` (66)
7. `autoascend/character.py` (64)
8. `autoascend/item/item_manager.py` (59)
9. `autoascend/combat/fight_heur.py` (40)
10. `autoascend/item/inventory.py` (32)

Items 1-4 are tables: the ledger rule for tables is one entry per table, with the generator or the 5.0 file as evidence plus a diff test (PITFALLS.md:249), not one entry per literal. Tranche 2 should start with those four, then the rule modules 5-10.

## Task Commits

1. **Task 1 (tracer):** `cb80615`
2. **Task 2:** `1e7e2f9`

## Deviations from Plan

**1. [Rule 3 - Blocking] Non-NetHack marks are under `non_nethack_marks`, not `notes`**
- `coverage()` (plan 01-04) already returns `notes` as the per-research-note counts, so appending marks there would mix two record types. The report keeps `notes` (the plan's verify checks its presence) and adds `tranche_1_marks` (all 16) and `non_nethack_marks` (the 11).

**2. [Process] Task 1's commit carries all six new ledger entries**
- The blade-force and quest-portal entries were written in the same build step; Task 2 adds their markers and citations.

**3. [Process] No web checks were needed**
- Every NetHack mark was found in the 5.0 source, so per D-13 no web step was taken.

**Total deviations:** 3. **Impact:** none on scope.

## Issues Encountered

None.

## Verification output

- `.venv/bin/python scripts/facts.py check --source`: exit 0.
- `tests/test_facts.py tests/test_ladder.py tests/test_quest_portal.py`: 62 passed. Full non-slow suite: 759 passed, 6 skipped, 16 deselected.
- Coverage report check: `ok 55 28` (55 files, 28 research notes).
- `grep -c '# fact:' autoascend/quest_portal.py`: 2. Word diff of `autoascend/`: 0 removed tokens. The Task 2 commit touches only `quest_portal.py` and `ladder.py` among `.py` files.
- `report` last line: `{"unverified_cited": 3}`.

## User Setup Required

None.

## Next Phase Readiness

Wave 3 now has only 01-06 left (the Sokoban detector hand game, which has a human checkpoint).

## Self-Check: PASSED
