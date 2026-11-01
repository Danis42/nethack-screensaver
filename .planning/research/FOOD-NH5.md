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

## Where starving games get to (2026-10-30, `6c7bfef`, 599 of 2304 games)

- Reached by starving games: Mines 397, Minetown 141, Oracle 54, Sokoban 16. 192 never reached the Mines.
  Minetown starvers die a median 3838 turns after arriving; 116 of the 141 are still in the Mines.
- Pace (median of games that got there, bot vs yardstick): Mines T3575 vs T1173, Minetown T6922 vs T3538,
  Sokoban T11541 vs T9022. The hero starts with 900 nutrition plus one food ration (800, u_init.c): about 1700 turns.
  The early game is about 2-3x slower than the yardstick, on a food budget that no longer gets death drops.
- Forum:Hunger and Poison agrees: stalling starves; "as long as you keep moving" corpses are plenty from the Mines on.
- Food-shop chance: most Minetown maps 90% (minetn-2,3,4; 5,6 fixed; 7 two 50% rooms; dat/*.lua monkfoodshop). The bot
  has no buy logic, and at most 141 of 599 starvers would reach a shop: a later experiment, not the main lever.
- Sokoban: each of the 8 map files places 4 random food items (`class = "%"`), still true on NetHack 5. Only 16
  starvers get there, because the route does the Mines first.
- Web searches (2026-10-30) found no NetHack 5 food guide; wiki Starvation has no 5.0 section.

Next probe: where the early turns go (turns per level on Dlvl 1-4 and Mines 1-2 by activity). Candidate experiments:
faster early descent; Sokoban entry level's food before the Mines. Food shop after those.

Sources: https://nethackwiki.com/wiki/Forum:Hunger_and_Poison https://nethackwiki.com/wiki/Starvation
https://nethackwiki.com/wiki/NetHack_5.0.0

Probe result (2026-10-30): 25,718 of 58,311 pre-Mines turns (44%, 12 seeds) were searches, driven by trap_search_offset=1.
With offset 0: 11/12 games reach the Mines (was 6/12); not yet benched -> exp/no-trap-search.

## Human ascensions vs the bot (2026-11-01)

72 recorded ascensions on NetHack 3.6 (NLD-NAO, 69 with a readable status line, all roles) vs 58 bot games on `ffe48bd`
(fresh seeds 3000-3059). Median per game, per 1000 turns; nutrition estimated from corpse and food tables, a hero burns about
1000 per 1000 turns.

| Turns | Nutrition human / bot | Non-corpse meals human / bot | Kills human / bot | Hungry share human / bot |
|---|---|---|---|---|
| 0-3000 | 837 / 883 | 0.67 / 0.67 | 17.0 / 13.7 | 4% / 1% |
| 3000-6000 | 953 / 707 | 0.67 / 0.67 | 19.3 / 12.3 | 3% / 7% |
| 6000-10000 | 995 / 538 | 0.75 / 0.25 | 21.3 / 14.0 | 3% / 9% |

- Humans eat about what they burn. The bot matches them for 3000 turns, then runs 300-450 short per 1000 turns.
- Corpses are not the gap: 2.0-2.3 per 1000 turns on both sides, about 0.15 per kill on both sides.
- Rations are: 58 of 72 humans ate a food ration by T10000 (3.9 per game), rations stay 10-13% of their meals; the bot falls
  from 18% to 6% once the starting stock is gone. Humans also kill about 1.5x as much.
- Caveats: 3.6 has death drops that 5.0 mostly removed, so human ration sources may not carry over; humans are all roles
 , only 13 are Valkyries; bot messages are sampled per step; bot cohort at T6000+ is survivors.
- Next: NH5 places food on purpose (a filling item on the Mines branch level, supply chests above the Oracle). Measure how
  much of it the bot collects, then make that one experiment. Scripts were scratchpad only (asc_food.py, bot_food.py, cmp_food.py).

## Why NetHack 5 changed food, and player advice (online, 2026-11-01)

- Dev reasoning, commit 39a7dc1c ("Most monsters no longer deathdrop comestibles other than their corpse"): playtesting found
  too much permafood; with death drops grinding made more food than it used; food should push progress and punish grinding;
  a full playtest ascension still found plenty. Monsters with M2_COLLECT can still drop food. So the design rewards moving on.
- Compensation: ae3e5d28 adds one good food item on the Mines branch level (random room, random floor spot, not the stair
  room as the wiki says; checked in the commit and mklev.c). 87f3b480 adds rations for Monks.
- Community: no thread about 5.0 food found. Search tool cannot reach Reddit; HN and LWN threads do not discuss food. HN:
  "Valkyrie is no longer the easy-mode starting class".
- Advice (wiki, mostly pre-5.0): eat fresh safe corpses early and often; beat the pet to corpses; carry permafood; Sokoban and
  Minetown shops for food; a successful prayer at Weak sets nutrition to 900; each attack costs about a turn of nutrition.
- Untested idea: Mines gnomes are a food source for most heroes, but they are peaceful to a dwarf, so this bot kills less and
  gets fewer corpses there. 340 of 599 starvation deaths were in the Mines; bot kills 12-14 vs human 17-21 per 1000 turns.

## What r/nethack says (9 threads saved by the owner, 2026-11-01; reference/reddit/)

Forum opinion, and none of it is measured. Main findings:
- Nobody in these threads complains about starving on 5.0. Complaints are about the late game: nerfed regeneration (carry healing;
  up to 10 full heals on Astral), weaker Elbereth, monsters looting stashes. One player: early game "a bit easier" than 3.6; turn
  counts rise (30k -> 60k+). Taken with commit 39a7dc1c: food is enough for humans who keep moving.
- Route: several players say a dwarf or gnome goes to Minetown first, because the Mines are much less deadly for them. Do not
  finish either branch in one go: Minetown (shops, temple), Sokoban, then the rest of the Mines. This argues against a plain
  "Sokoban first for a dwarf", which the earlier note floated.
- "Food allows you to play slower"; low-food heroes visit Sokoban's first level only for food. Source check: soko4-1/4-2 place 4
  random `%` items at random spots, so some may need the puzzle solved; reachability unmeasured.
- Prayer: one player starved after spending the first prayer on HP.
- Sokoban deaths: leocrotta, elves. Advice: unburdened, HP 40+, pet, escape item, done by about XL 9-10.
- Elves do not respect Elbereth; in 5.0 you cannot fight on it, blocked monsters attack anyway (ascension plan should note).

## Mines check on `ffe48bd` (2026-11-01, 2304 stored games, 88 traced seeds)

- 540 games starve (23.4%): 190 in the Mines before Minetown, 139 in the main dungeon never having reached the Mines, 107 in the Mines
  past Minetown, 100 in the main dungeon after the Mines, 4 elsewhere. 512 of 540 hold no food at the end.
- Branch food is collected: 71 of 88 seeds showed the branch level; a ration-type item was seen there in 69, picked up in 60.
  Pickup counts rely on a message regex.
- The bot already visits Sokoban before Mines' End (199 of 200 games), so the "Minetown, Sokoban, rest of the Mines" route adds little.
- So the deep-Mines and branch-food ideas are not the lever: 61% of starvers die before Minetown.
