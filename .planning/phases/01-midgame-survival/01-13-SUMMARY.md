---
phase: 01-midgame-survival
plan: 13
subsystem: combat
tags: [rejudge, choke-points, experiment]
requires: [01-12]
provides:
  - "rejudge/choke-points (339a63c): b31e926's code diff applied onto main, judged once (dropped)"
affects: [01-16]
key-decisions:
  - "choke-points judged once (D-12): no measurable difference, +1.2 [-0.1, +2.5]; screen at 384 had +2.9"
---

# Plan 01-13 Summary: re-judge choke-points

Job 26 against `3fca503`, rung2 at 2304: no measurable difference, +1.2 [-0.1, +2.5]. dlvl6 and dlvl10 +0.3,
exceptions 63 vs 50. Main unchanged; both branches stay for 01-16.
