---
phase: 02-real-descent
plan: 06
subsystem: descent
tags: [experiment, stuck]
requires: [02-05]
provides:
  - "experiment 12 logged: exp/stuck-2 dropped (free5 +0.6 [-0.2, +1.4] at 2304)"
affects: [02-08]
key-decisions:
  - "Dropped: free5 no measurable difference; Current baseline stays 6502ae3"
  - "Obstacle chosen by replay (deviation): known traps in 1-wide passages (6/10), peacefuls (2/10), boulders none"
---

# Plan 02-06 Summary: clear-way (dropped)

- Change: when stuck and the stairs are cut off only by known traps or peacefuls, cross the traps or wait
  beside the peaceful (1000 turns per level, resumable after fights).
- Job 36: free5 +0.6 [-0.2, +1.4]. Clear-way fired in 252 games and reached the stairs in 168, but most of
  those games got stuck again further down. rung2 +0.9 [+0.2, +1.6] and starved -0.9 are secondary only.
- Next: gap experiment exp/standoff (fight standoff), then 02-07 quest portal.
