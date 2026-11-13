---
phase: 01-measurement-and-proof-foundation
plan: 16
subsystem: bench
tags: [baseline, a-a, funnel, sokoban, proof-index]

requires:
  - phase: 01-15
    provides: lgen decision, A/A command, pre-registration 539b31eabc1b11c90f7f2b84cb5348a0acf1da63, jobs 7 and 8
provides:
  - "01-BASELINE.md results: aa_result pass, baseline_rows total=10000 own=9600 reused=400, A/A JSON, funnel JSON (901c3a6570859b50fae20c5b28e10347be359dec)"
  - "01-SOKOBAN-CAUSE.md: every Sokoban drop is the unsolvable branch on the entry level (3b84daa2eeeeebb235df727f2a36dc57e3a0f9bd)"
  - "01-PROOF.md: proof index for the five success criteria (acde3b61b766cc8e967105cb15aaa042d6af1b31)"
affects: [Phase 2 (baseline_sha e5b5a7f525bc51b8008f665173600aba80de466d, Sokoban open question)]

actuals:
  tasks: 2
  commits: 3     # MEASURED: 901c3a6, 3b84daa, acde3b6
plan_head_before: 9f2d97f
plan_head_after: acde3b61b766cc8e967105cb15aaa042d6af1b31

key-files:
  created:
    - .planning/phases/01-measurement-and-proof-foundation/01-SOKOBAN-CAUSE.md
    - .planning/phases/01-measurement-and-proof-foundation/01-PROOF.md
  modified:
    - .planning/phases/01-measurement-and-proof-foundation/01-BASELINE.md

key-decisions:
  - "A/A pass by the pre-registered definition: 1,999 of 1,999 compared seeds identical; seed 2073 watchdog on both replicates, listed"
  - "Sokoban zero is a bot failure: all 2,256 drops are sokoban_unsolvable on dunlev 4, none map_not_found; which push fails first is the open Phase 2 question"

requirements-completed: [MEAS-05, MEAS-02, MEAS-03, MEAS-09]

duration: not measured
completed: 2026-11-14
---

# Phase 1 Plan 16: baseline evidence, Sokoban cause, proof index Summary

**Baseline job 7 (10,000 games of commit e5b5a7f525bc51b8008f665173600aba80de466d, 9,600 own and 400 reused) and A/A job 8 (2,000 games, replicate 1) are done. The pre-registered A/A command exits 0: 1,999 of 1,999 compared seeds are identical, and seed 2073 ended with the watchdog on both replicates. The funnel lists all 18 stage keys with Wilson intervals. The Sokoban zero is explained: all 2,256 drops are the unsolvable branch on the entry level. 01-PROOF.md indexes all five success criteria.**

## Task Commits

1. **Task 1:** 901c3a6570859b50fae20c5b28e10347be359dec (A/A verdict, funnel, baseline_rows)
2. **Task 2:** 3b84daa2eeeeebb235df727f2a36dc57e3a0f9bd (Sokoban cause), acde3b61b766cc8e967105cb15aaa042d6af1b31 (proof index)

## Baseline funnel (job 7, n 10,000, marginal reach)

mines 60.8%, minetown 21.4%, oracle 48.2%, sokoban 25.4%, sokoban_solved 0, mines_end 11.6%, dlvl15 6.1%, quest_portal 4.6%, quest 4.2%, medusa 0.77%, castle and everything after it 0. Full rows with intervals in 01-BASELINE.md.

## Claim-check output

- Task 1 results paragraph through `scripts/check_claims.py`: exit 0, no output.
- All five sections of 01-PROOF.md and all six sections of 01-SOKOBAN-CAUSE.md: no output (pass).

## Verification output

- Task 1 verify: `ok pass 10000`
- Task 2 verifies: `ok 5`, `ok`, `ok: bot of main == bot of e5b5a7f525`
- Every test command in 01-PROOF.md: 326 passed; `scripts/facts.py check --source` exit 0; `scripts/lgen_pilot.py --jobs 3 4 5 6 --metric dlvl10` reproduces the committed results.

## Deviations from Plan

**1. [Process] Heading reworded after a claim-checker false positive**
- The criterion 5 heading first named "the started rule" next to "Tool runs". `check_claims.py` blocked it: `START_RE` plus `START_NOUN_RE` (lines 60-61) match a heading that claims nothing. It now reads "the first-game-row rule". No claim was weakened. Follow-up idea: let the checker skip markdown headings.

**Total deviations:** 1. **Impact:** none on scope.

## Next Phase Readiness

Phase 1 plans are all done. Phase 2 experiments name e5b5a7f525bc51b8008f665173600aba80de466d as their baseline and pass an explicit --discordance when the change diverges games more than the pilot's commit B (DEFAULT_DISCORDANCE 0.019).

## Self-Check: PASSED
