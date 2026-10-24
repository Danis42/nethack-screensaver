---
phase: 01-midgame-survival
plan: 09
subsystem: survival
tags: [rest, hp, food, experiment, bench-fix]
requires: [01-08]
provides:
  - "autoascend/rest.py (food-scaled rest target) on branch exp/rest-to-full (894084d, dropped)"
  - "fix 16a6cb8 on main: turn-stall watchdog and a capped panic list (bench memory safety)"
affects: [01-10, Phase 2]
key-decisions:
  - "Rest target scales with food (owner): full HP with a ration's worth or a safe prayer, 85% otherwise, none when Hungry with nothing"
  - "Dropped: resting trades ant deaths for starvation while food is the bottleneck"
---

# Plan 01-09 Summary: rest before exploring on

Job 21, rung2 at 2304: no measurable difference, -1.5 [-4.2, +1.2]. Starved +2.3 [-0.2, +4.8],
ants -0.5, median 549 rest turns per game. Smoke: rest fired in 20 of 22 games.

Deviation: job 20 (first candidate 6448532) was stopped at 1,278 games. Seed 990 looped on an
empty-bag loot menu with thousands of panics, each kept with its traceback; two workers reached
11 GB and the screen watchdog never fired. Fix 16a6cb8 (seeds 0-21 replay identically to the
baseline) and the branch was rebased and rerun as job 21. The empty-bag menu bug remains.
