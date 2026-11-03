# Telepathy for the Valkyrie (research 2026-11-03, before any code)

## Why
- 95% of 199 human 5.0 ascensions end telepathic, mostly intrinsic (13% via helm/amulet) (MEDUSA-NH5.md).
- Guides: telepathy + towel/blindfold is part of the Quest-entry kit (GUIDE-MAG-R342.md); the standard answer to
  Medusa's ravens and to Medusa herself (blind + telepathy), and it finds Medusa's room and the riders.
- Staged hand game medusa seed 1: blind melee without telepathy -51 HP for 2 ravens; with telepathy ~17 kills.

## Facts (NetHack 5.0.0 source, wiki, online)
- Eating a floating eye corpse ALWAYS grants intrinsic telepathy (eat.c:980 chance 1 vs eye level 2; message
  "You feel a strange mental acuity." eat.c:1075). Only while blind (or with extrinsic) does it show monsters.
- A floating eye leaves a corpse about 1/2 of the time (mon.c:3247) -> on average 2 kills per telepathy.
- Melee on a seen eye: 2/3 chance per non-killing hit of long paralysis (a top early killer; exp 21 stopped the
  bot from doing it). Safe kills: any ranged attack (thrown daggers, junk, rocks, wands, polearm); melee while
  the HERO is blind (blindfold/towel on); reflection or free action. (wiki Floating eye; nethackwiki online.)
- Pets eat the corpse if allowed; the pet has to be kept away (bot mostly ignores its pet).
- Online (reddit r/nethack): players plan eye corpses for telepathy before the dark Mines; no 5.0 change found.

## Candidate rule (not built yet)
When a floating eye is seen and the hero has no telepathy:
1. If a blindfold or towel is known: put it on, melee the eye (safe while blind), take it off, eat the corpse
   (only when not Satiated; a 10-nutrition corpse, eating is 1 turn).
2. Else throw spare daggers/junk from >= 2 squares, collect them after.
3. Never with another hostile adjacent; never in Sokoban (luck) concerns: none for eyes.
Measure first (needs free cores): how often the bot sees a floating eye per game and by which Dlvl, how often it
already eats one by chance ("mental acuity" in messages), whether it carries a blindfold/towel when it meets one.
