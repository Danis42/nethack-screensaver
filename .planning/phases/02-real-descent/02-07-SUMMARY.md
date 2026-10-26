---
phase: 02-real-descent
plan: 07
subsystem: descent
tags: [experiment, quest]
requires: [02-06]
provides:
  - "experiment 14 logged: exp/quest-portal kept (rung8 +6.2 [+1.8, +10.7] at 192, job 38)"
affects: [02-08]
key-decisions:
  - "Kept: rung8 better; Current baseline 6a840f2"
  - "The scheduler ended the job at 192 (99% interval clear of zero), as the protocol allows"
---

# Plan 02-07 Summary: Quest portal on purpose (kept)

- Change: the bot recognizes the quest leader's call (wording taken from NLD-NAO games). On that level it walks
  every reachable square, then searches dead ends, with a 1500-turn cap. In the Quest it steps off the
  arrival portal and back on, then resumes the route.
- Smoke on 22 seeds that reached Dlvl 14+: message seen in 20, Quest entered in 10, hunt given up in 8.
  Recorded deliberate entry: seed 112 (`quest_portal_level_seen`, `entered`, `left` = 1).
- Job 38: rung8 +6.2 [+1.8, +10.7] at 192 pairs. rung7, rung9, died and starved show no measurable
  change. Crashes 6 vs 6, same types.
- Merged to main `6a840f2`; PORTING.md experiment 14.
- Gave up in 8 of 22 smoke games: the portal can sit behind a hidden passage, or on a square the hunt never
  reached in 1500 turns. A later change could make the hunt better.
