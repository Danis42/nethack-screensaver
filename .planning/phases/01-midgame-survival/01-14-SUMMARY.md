---
phase: 01-midgame-survival
plan: 14
subsystem: combat
tags: [rejudge, flee-upstairs, experiment]
requires: [01-13]
provides:
  - "rejudge/flee-upstairs (757aad8): a535f7a's code diff applied onto main, judged once (dropped)"
affects: [01-16]
key-decisions:
  - "flee-upstairs judged once (D-12): no measurable difference, +0.5 [-0.9, +1.9]"
  - "Rebase: GameResult.flee_upstairs field dropped (the counter is in events)"
---

# Plan 01-14 Summary: re-judge flee-upstairs

Job 27 against `3fca503`, rung2 at 2304: no measurable difference, +0.5 [-0.9, +1.9]. Fired in 8 of 22 smoke
games; no deeper metric moved. Main unchanged; both branches stay for 01-16. All three old branches are now
judged once: none kept.
