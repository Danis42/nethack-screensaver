---
phase: 01-midgame-survival
plan: 10
subsystem: survival
tags: [ants, bees, poison-resistance, experiment]
requires: [01-08]
provides:
  - "scripts/seeded_report.py insects subcommand (prayer and poison shares, tactic rule)"
  - "poison_corpse_ok on branch exp/ants-bees (9ca4f31, dropped)"
affects: [01-11, Phase 2]
key-decisions:
  - "Tactic by rule: poison-resistance (A2 poison 26.4% >= 25%, A1 prayer unused 24.4% < 40%)"
  - "Dropped: worse on rung2; insect deaths unchanged (253 vs 253)"
---

# Plan 01-10 Summary: ants and bees

Job 22, rung2 at 2304: worse, -1.5 [-2.6, -0.3]. Insect deaths unchanged (253 on both sides), ants
+0.3, dlvl10 -1.1. Crashes fell (watchdog 26 vs 46), which is why `died` rose +1.1. Smoke: the corpse
rule fired in 8 of 22 insect-death seeds. Eating the corpses comes too late to stop the swarm that kills
the bot; the poison HP cost and eating turns cost depth elsewhere.

Follow-ups: fight ants from a corridor or doorway (the close-door tactic), Elbereth against soldier
ants (they respect it), Phase 2 food supply.
