---
status: complete
phase: 01-midgame-survival
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md, 01-06-SUMMARY.md, 01-07-SUMMARY.md, 01-08-SUMMARY.md, 01-09-SUMMARY.md, 01-10-SUMMARY.md, 01-11-SUMMARY.md, 01-12-SUMMARY.md, 01-13-SUMMARY.md, 01-14-SUMMARY.md, 01-15-SUMMARY.md, 01-16-SUMMARY.md]
started: 2026-10-25T12:26:40Z
updated: 2026-10-25T12:35:20.681Z
---

## Current Test

[testing complete]

## Tests

### 1. Seeded game takes its moon from the seed; unseeded keeps the real clock
expected: Seeded game takes its moon from the seed; unseeded keeps the real clock
result: pass
source: automated
coverage_id: 01-01 D1

### 2. One seed replays frame for frame across fresh processes
expected: One seed replays frame for frame across fresh processes (different PYTHONHASHSEED) and A,B orders
result: pass
source: automated
coverage_id: 01-01 D2

### 3. Every result carries its death context; observer is observation-only
expected: Every result carries its death context and the observer is observation-only
result: pass
source: automated
coverage_id: 01-01 D3

### 4. Live Sokoban solving stops on a fixed state budget only
expected: Live Sokoban solving stops on a fixed state budget only; same pushes under any load
result: pass
source: automated
coverage_id: 01-02 D1

### 5. Live Sokoban budget worst case stays near the old 10 s limit
expected: Live budget worst case stays near the old 10 s limit (measured, recorded beside the constant)
result: pass
source: automated
coverage_id: 01-02 D2

### 6. Bench workers run with PYTHONHASHSEED=0
expected: Bench workers run with PYTHONHASHSEED=0
result: pass
source: automated
coverage_id: 01-02 D3

### 7. verdict looks up a stored verdict by ref (exit codes 0/3/4)
expected: verdict looks up a finished experiment's stored verdict by ref with exit codes 0/3/4
result: pass
source: automated
coverage_id: 01-03 D1

### 8. replay_check compares two commits seed by seed
expected: replay_check compares two commits seed by seed and exits 0/1/2
result: pass
source: automated
coverage_id: 01-03 D2

### 9. pairs computes the paired comparison as judge_paired does
expected: pairs computes the paired comparison exactly as bench/stats.py judge_paired does
result: pass
source: automated
coverage_id: 01-03 D3

### 10. ladder prints the 17-rung table
expected: ladder prints the 17-rung table for seeds 0..N-1 and reproduces 2653410's 634 / 309 of 1152
result: pass
source: automated
coverage_id: 01-03 D4

### 11. killers and deaths print killer tables and per-death rows
expected: killers and deaths print killer tables and per-death context rows
result: pass
source: automated
coverage_id: 01-03 D5

### 12. benchmark.py plays chosen seeds and reports any GameResult field
expected: benchmark.py plays chosen seeds and reports any GameResult field including events counters
result: pass
source: automated
coverage_id: 01-03 D6

### 13. Human food and prayer study reads sensibly
expected: 01-HUMAN-STUDY.md compares humans who got through Dlvl 4-12 with humans who starved there, on the same yardsticks as the bot. The numbers look plausible to you, and the conclusion (bot starvation is a food-supply / stuck-level problem, not prayer timing) follows from them.
result: pass

### 14. Experiment log is complete and readable
expected: autoascend/PORTING.md "### Experiments" has one entry per experiment (starvation-1/2, rest-to-full, ants-bees, zappers, shop-door, and the three rejudge branches). Each gives the change, the job, the verdict with its interval, and a plain decision (kept / dropped). Only exp/shop-door is kept.
result: pass

### 15. Phase 1 done bar is met and you accept it
expected: autoascend/PORTING.md "### Phase 1 result (SURV-06)" shows five paired verdicts p1-final vs p1-baseline (jobs 28-32), all "better" (rung2 +3.1 [+0.8, +5.4]), and the line "Phase 1 result: met". You accept a 1-3 point gain from one kept change as meeting the phase goal.
result: pass

### 16. Screensaver still plays normally on the final code
expected: Start the screensaver (bin/nethack-screensaver, or wait for it to trigger). A dwarvish Valkyrie game starts and the bot plays on its own, going down the dungeon; no crash or freeze in the first few minutes, and nothing new in ~/.local/state/nethack-screensaver/player.log.
result: pass

### 17. Old branches are gone, archive tags remain
expected: `git branch` lists no threat-model, choke-points or flee-upstairs branches (plain or rejudge/); `git tag -l 'archive/*'` lists six archive tags, matching the SHAs in PORTING.md "### Branch cleanup (D-13)".
result: pass

## Summary

total: 17
passed: 17
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
