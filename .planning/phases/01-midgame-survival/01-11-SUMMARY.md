---
phase: 01-midgame-survival
plan: 11
subsystem: survival
tags: [wands, rays, shopkeepers, experiment, kept]
requires: [01-08]
provides:
  - "scripts/seeded_report.py zappers subcommand (classes Z1-Z4, tactic rule)"
  - "Level.closed_shop_door: never kick a door behind a Closed for inventory engraving (kept, 3fca503)"
  - "branch exp/zappers (d7d5e6b): leave the zap line of a known zapper, dropped (no measurable difference)"
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

Experiment 6 (`exp/zappers` rebased, `d7d5e6b`): no measurable difference at 2304, +0.1 [-0.8, +0.9]; dropped.
Over 2304 seeds shopkeeper deaths fell from 118 to 34. The rest come from other anger paths (Keystone Kops
after shop theft, fighting a shopkeeper that was already hostile).
