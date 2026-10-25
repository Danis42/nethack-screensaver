---
phase: 02-real-descent
plan: 05
subsystem: descent
tags: [experiment, stuck]
requires: [02-03]
provides:
  - "### Stuck diagnosis (DESC-03) in PORTING: rule applied, frontier-first chosen"
  - "experiment 11 logged: exp/stuck-1 dropped (free5 +0.9 [-0.4, +2.2] at 2304)"
affects: [02-06, 02-08]
key-decisions:
  - "Dropped: free5 no measurable difference; Current baseline stays 6502ae3"
  - "Replays found two larger time sinks: searching dead ends in the Mines, and the fight standoff with monsters that never come (branch exp/standoff built for a gap experiment)"
---

# Plan 02-05 Summary: frontier-first (dropped)

- Rule: no bucket >= 35% -> frontier-first (explore-left 27.6% largest).
- Smoke 22 seeds: fired in 15, no new exception type. Job 35: free5 +0.9 [-0.4, +2.2]; fired in 719 games;
  watchdog 44 vs 49 (replays during the job did not inflate it).
- Replays (seeds 2242, 75, 896): about 60% of one stuck window went to searches in the Mines; two of six stuck
  seeds lost 1100-1350 turns standing two squares from a monster that never came (asleep nymph, spotted jelly).
