---
phase: 01-midgame-survival
plan: 07
subsystem: measurement
tags: [baseline, ladder, killers]
requires: [01-06]
provides:
  - "tag p1-baseline = 0b097073adb3071f8e5c2aea954618a3320a5bc7 (2304 seeds stored)"
  - "PORTING.md: Pilgrim-only baseline (ladders n=576 and n=2304, killer tables), Experiments with Current baseline line"
affects: [01-08, 01-09, 01-10, 01-11, 01-12, 01-13, 01-14, 01-15, 01-16]
key-decisions:
  - "Baseline is the Valkyrie measurement code p1-valk-base (not p1-aa-base / p1-aa2-base): owner fixed the role in 01-06"
  - "Topped up to 2304 seeds now, since 2304 is the last checkpoint"
---

# Plan 01-07 Summary: pilgrim-only baseline

Baseline `0b09707`, 2304 seeds: Mines 73%, Minetown+ 44%, Oracle 30%, Sokoban 18%, solved 15%,
Mines' End 15%, Dlvl 15+ 8%, Quest 1%, Medusa 14 games; nothing deeper.

Killers (all 2304): starved 25.0% of games, ants 8.4%, rays 5.0%, wands 3.9%, killer bees 2.6%;
exceptions 2.1%, watchdog 2.0% (median Dlvl 24). On Dlvl 4-12 (1710 games): starved 24.5%,
ants 10.6%. Starvation is the first target (plan 01-08).

Also: 16 not-comparable notes on older PORTING sections; survival-tuning (`ade24fb`, merged)
deleted with its 3 stashes kept; STATE concerns updated.

Deviation: baseline tag points at `p1-valk-base` because of the owner's Valkyrie decision.
