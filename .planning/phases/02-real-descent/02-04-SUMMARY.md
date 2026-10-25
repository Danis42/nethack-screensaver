---
phase: 02-real-descent
plan: 04
subsystem: descent
tags: [experiment, mines-end]
requires: [02-03]
provides:
  - "experiment 10 logged: exp/mines-end dropped (rung7 no measurable difference, +0.0 [-0.2, +0.3] at 2304)"
affects: [02-08]
key-decisions:
  - "Dropped: the screen rule fired in 22 of 2304 games; Current baseline stays 6502ae3"
---

# Plan 02-04 Summary: Mines' End on the real bottom (dropped)

- Smoke: 19 seeds with an 8-level Mines, counter fired in 3, no new exception type.
- Job 34 (2304 pairs, rung7): no measurable difference, +0.0 [-0.2, +0.3]; rung6 -0.1, starved +0.0, free5 -0.1.
- Few games still follow FIND_MINES_END; DESC-01 stays met on the measuring side (02-01/02-03), the bot-side
  rule is kept on its branch.
