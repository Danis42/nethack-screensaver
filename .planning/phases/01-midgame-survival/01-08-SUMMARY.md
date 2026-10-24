---
phase: 01-midgame-survival
plan: 08
subsystem: survival
tags: [starvation, prayer, exploration, experiment]
requires: [01-04, 01-07]
provides:
  - "scripts/seeded_report.py starvation subcommand (buckets and tags)"
  - "PORTING.md: Starvation diagnosis, Killer order (D-07), experiments 1 and 2"
  - "branches exp/starvation-1 (a8e8065) and exp/starvation-2 (9ca5d8b), both dropped and kept for reference"
affects: [01-09, 01-10, 01-11, Phase 2]
key-decisions:
  - "Starvation is a food-supply problem, not a prayer-timing one: 567 of 576 baseline starvers carried no food"
  - "Most starvers are stuck: median 3,900 turns since their last new level; this is Phase 2 (Real Descent) work"
  - "Experiment 2 skipped the 20% bucket rule on purpose (recorded deviation) to test the food-supply diagnosis"
---

# Plan 01-08 Summary: starvation

Diagnosis (baseline `0b09707`, 576 starvers): almost none carry food. Starvers kill 5.3 monsters per
1000 turns against 14.0 for long survivors and eat a similar share of corpses, so they get fewer
corpses; most are stuck on a level whose way on is hidden (median 3,900 turns since the last new level).
Killer order for the rest of the phase: starvation, rest to HP (01-09), ants and bees, wand and ray users,
then the three old branches.

| # | Branch | Change | Verdict on rung2 @ 2304 | Decision |
|---|--------|--------|-------------------------|----------|
| 1 | `exp/starvation-1` | no prayer for 1000 turns after a failed one | +0.0 [-0.2, +0.2] | dropped (starved +0.7, worse) |
| 2 | `exp/starvation-2` | dead-end search bonus at the far wall of unseen map sides | -1.1 [-3.9, +1.7] | dropped (fires on every level, reshuffles games) |

SURV-02 is addressed by the done rule (judged experiments on the top in-scope causes, intervals logged);
starvation is not reduced. Follow-ups: the far-side search only when nothing is left to visit (Phase 2);
whether the bot picks up Sokoban and Minetown food, and whether the pet eats the corpses first (guides,
2026-10-24 research).

Deviation: job 18 was interrupted at 1,517 games (bench server killed under memory pressure); job 19
resumed it from the stored games.
