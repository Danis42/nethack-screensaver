# Food and getting unstuck on NetHack 5 (research, 2026-10-29)

Source: p5-baseline (579c4d5, 2304 games), NetHack 5.0.0 source in reference/, local wiki.

## What the baseline shows

- 579 / 2304 games (25.1%) starve or are killed while fainted.
- 554 of them (96%) carry no food at all at the end. The bot already takes every
  non-corpse food item it sees and eats fresh corpses whenever it is not satiated:
  the problem is supply, not eating.
- Starving games pray 7.1 times each (other games 5.2): prayer is their food source
  until one comes too early.
- 225 (39%) starve on the level where the stuck watch (2500 turns without progress)
  already gave up, a median 1128 turns after that report; 322 starve in the Mines.
  In those 225: downstairs seen but unreachable 91, never seen 94, seen and reachable 40;
  boulders on the level 137, closed doors 41, unexplored frontier 71.
- The bot uses a pick-axe only to break a boulder it cannot push, and never picks one up on purpose.

## NetHack 5 changes that matter (doc/fixes5-0-0.txt, src/mklev.c)

- Monster kills no longer death-drop comestibles (only the corpse), unless the
  monster carried food. In 3.6 death drops were a steady source of rations and other
  food that keeps: a large part of the food supply is gone.
- Bonus items (mklev.c ~1005-1100):
  - the main-dungeon level with the Mines branch always has one filling ration
    (60% food ration, 20% cram, 20% lembas) in a room;
  - every main-dungeon level above the Oracle has a 2/3 chance of a supply chest
    (2/3 chest, 1/3 large box; locked 5/6). Content: 50% potion of healing (half of
    them 2), else one of extra healing, speed, gain energy, enchant weapon, enchant armor,
    confuse monster, scare monster, wand of digging, spellbook of healing; cursed rolls
    add another item; 2/3 chance of one extra random item (food, weapon, armor, ...).
- Niches (closets) still hold food 1/4 of the time.

## Digging rules (src/dig.c dig_check, dighole)

Digging down fails on stairs, ladders, thrones, altars, boulders, the air/water levels
and on hard-floor levels (Can_dig_down: Sokoban, Wizard's Tower, branch bottoms such
as Mines' End, ...). "The <surface> here is too hard to dig in." Digging in a shop makes
the shopkeeper grab the pack; shopkeepers do not let a hero in with a pick-axe.
Applying a pick-axe wields it: re-wield the weapon after the hole.

## Pick-axe sources for a dwarvish Valkyrie

- Dwarvish monsters carry a pick-axe 1/4 of the time (wiki, makemon.c 397), mattocks
  sometimes; but dwarves are generated peaceful towards a dwarvish hero, so the bot
  rarely kills them. A pet may kill a peaceful dwarf.
- 2% of random tools; hardware stores.
- Wand of digging: supply chests (above), random wands. Zapping down makes a hole at once.

## Forcing locks (src/lock.c doforce/forcelock)

#force with the wielded weapon, up to 50 turns. A blade (dagger..saber skills) pries:
contents safe, the blade breaks with 0.8% per failed turn (a +0 blade survives a full
failed attempt 67% of the time). Anything else bashes (the NH5 Valkyrie spear does):
success chance per turn = 2 x large-monster damage die (spear 16%), wakes the level, and
the box is destroyed 1/3 of the time - every potion inside breaks. So: pry with the
starting dagger, never bash a supply chest.

## Probe: pick-axes in stuck-and-starved games

Replayed the first 20 seeds that starved on their stuck level (scratchpad pick_probe.py wraps
Agent.step). A pick-axe or mattock was in the inventory in 4/20 (3 of them thousands of turns
before the stuck watch fired), visible on the map at some point in 8/20, and 10/20 killed at least
one dwarf. The bot never dug down. So a pick is within reach in roughly 40% of these games:
dig-down when stuck is worth building; a pet killing peaceful dwarves would add more.

## Candidate experiments (one at a time)

1. Dig down when stuck (pick-axe, or wand of digging zapped down) - needs a pick
   source; probe on 20 stuck-starved seeds: see below.
2. Open locked chests (#force / kick): supply chests carry healing and digging.
3. Buy food in shops (needs gold pickup and the buy dialog).
4. Make sure the guaranteed Mines-branch ration is found (explore the branch level fully).
