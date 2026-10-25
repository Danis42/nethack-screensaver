---
phase: 01-midgame-survival
plan: 12
subsystem: combat
tags: [rejudge, threat-model, experiment]
requires: [01-11]
provides:
  - "rejudge/threat-model (8284811): fdf6b48's code diff applied onto main, judged once (dropped)"
affects: [01-16]
key-decisions:
  - "threat-model judged once on the seeded bench (D-12): no measurable difference, +0.3 [-1.2, +1.7]"
---

# Plan 01-12 Summary: re-judge threat-model

Job 25 against `3fca503`, rung2 at 2304: no measurable difference, +0.3 [-1.2, +1.7]; dlvl10 -1.6 [-3.2, -0.0]
leans worse. Main unchanged; `threat-model` and `rejudge/threat-model` stay for 01-16. The rebase applied the
branch's code diff against its merge base (docs history files left out); 440 tests passed.
