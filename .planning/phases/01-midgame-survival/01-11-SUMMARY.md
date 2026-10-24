---
phase: 01-midgame-survival
plan: 11
subsystem: survival
tags: [wands, rays, shopkeepers, experiment, kept]
requires: [01-08]
provides:
  - "scripts/seeded_report.py zappers subcommand (classes Z1-Z4, tactic rule)"
  - "Level.closed_shop_door: never kick a door behind a Closed for inventory engraving (kept, 3fca503)"
  - "branch exp/zappers (36588cb): leave the zap line of a known zapper, not yet judged"
affects: [01-12, 01-15]
key-decisions:
  - "93 of 2304 baseline games (4.0%) die to angry shopkeepers; 9 of 10 replays kicked a closed shop's door"
  - "First kept experiment of the phase: rung2 +3.1 [+0.8, +5.4] at 384, dlvl6 +4.7, dlvl10 +2.1"
---

# Plan 01-11 Summary: wand and ray users

The zap-line idea (`exp/zappers`) missed the largest group: named zappers, angry shopkeepers on Dlvl 2-5. Long
message replays showed the bot reads "Closed for inventory", finds the door locked and kicks it in. Experiment 5
(`exp/shop-door`) stops that and is the phase's first keeper: better on rung2 at 384 games, wand and ray deaths
-4.2 points. New current baseline `3fca503`.

Next: rebase `exp/zappers` onto the new baseline and judge it against the remaining wand and ray deaths
(Keystone Kops after shop theft are a second, smaller shopkeeper path).
