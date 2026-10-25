---
phase: 02-real-descent
plan: 03
subsystem: measurement
tags: [baseline, stuck, ladder]
requires: [02-01, 02-02]
provides:
  - "scripts/seeded_report.py stuck: buckets, events by milestone/dungeon, end types, watchdog stacks"
  - "p2-baseline = 6502ae3 (job 33, 2304 games); PORTING '## Phase 2: real descent' with Current baseline line"
affects: [02-04, 02-05, 02-06, 02-07, 02-08]
key-decisions:
  - "replay_check exit 1 accepted: its single mismatch (seed 689) is a source line number in a crash text; without end_reason 0 of 2255 differ"
  - "02-05 rule result: no bucket >= 35% -> frontier-first"
---

# Plan 02-03 Summary: Phase 2 baseline and stuck diagnosis

## Deviation

- **Gate exit 1 instead of 0:** seed 689 ends with the same crash, but the text names
  `global_logic.py:458` versus `:476` (the file grew 18 lines). Rerun without `end_reason`: 2255 compared,
  0 mismatched. Play is unchanged.

## Results (2304 games)

- Ladder: rung6 Mines' End 395 (17%), rung7 Dlvl 15+ 210 (9.1%), rung8 Quest 38 (1.6%).
- free5 82.2%; 410 stuck endings at Dlvl 5+: explore-left 27.6%, stairs-unreachable 26.1%,
  stairs-reachable 24.9%, no-way-found 19.3%, no-report 2.2%.
- DESC-01: seed 0 (9-level Mines) rung 6 at turn 12583, seed 2 (8-level) at turn 13010.
- Watchdog (49): exploration searches on deep levels (median Dlvl 24).

## Next

02-04 (exp/mines-end, rung7), then 02-05 with frontier-first.
