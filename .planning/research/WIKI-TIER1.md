# Wiki strategy reading, tier 1 (2026-10-29)

Read (stripped wikitext, reference/nethackwiki): Valkyrie, Dwarf (starting race), Standard strategy,
Why do I keep dying?, Things To Do If You're Going to Die Next Turn, Yet Another Stupid Death,
Nutrition, Corpse, Prayer, Luck, Sacrifice (most), Gnomish Mines, Minetown (watch + strategy),
Mines' End, Sokoban, Fountain, Shopkeeper, Pet (strategy), Elbereth, Digging for victory, Mimic,
Soldier ant, Unicorn, Game stages (early game). Skimmed or not yet: Altar, Trouble, Movement
tactics, Combat, Hit and run, Escape item, Healing, Player's misconceptions, Bad Idea, Role
difficulty, Death drop; tier 2 (late game, ascension kit, item strategy) not started.

## Facts that change what the bot should do (NetHack 5 unless noted)

- Valkyrie: +1 (dwarvish) spear, +0 dagger, +3 small shield, 1-2 food rations; stealth only
  at XL 3 now (was XL 1): early monsters wake more often.
- Dwarvish hero: gnomes and dwarves always generate peaceful, orcs always hostile. A pet may
  kill a peaceful dwarf for its pick-axe without any penalty (Pet, Valkyrie pages).
- Food: Sokoban has 4 comestible stacks per level (16 in the branch, "an excellent place to stock
  up"); Minetown often has a food shop (needs gold); the Mines branch level has a ration
  (FOOD-NH5.md). A successful prayer sets nutrition to 900, which explains the ~890-turn prayer
  cycle of starving games (PRAYER-NH5.md).
- Prayer: wiki advice is 700-1400 turns between prayers; negative Luck, an angry god or a
  timeout above 200 (major trouble) make it fail. Sacrifice lowers the timeout and anger.
- Falling down a hole now deals 1d6 per level fallen: dig down only with HP to spare.
- Elbereth: attacking from it erases it (3.6+); unique monsters ignore it in NetHack 5;
  @ humans, minotaurs, shopkeepers, guards ignore it. Ants respect it ("engrave at first sight").
- Unicorns keep a knight's move away and only fight when the hero steps next to them;
  throwing any gem at a hostile unicorn makes it peaceful. Never chase them (36 baseline deaths).
- Mimics in shops show as "strange object" (]); slow; fight from range or not at all at low XL
  (45 deaths before the Mines).
- Minetown watch turns hostile on: attacking any peaceful in sight, drying a fountain, kicking a
  door open, digging through walls/doors with a pick-axe (warning first). The bot already skips
  Minetown fountains for Excalibur (global_logic.py:743).
- Mines strategy for weak heroes: stay near the up stairs on arrival, retreat up to heal;
  Mines filler levels are 50% dark; lower Mines (below Minetown) have nastier traps.
- Wiki goals: AC about -5 by the end of the Mines, take the Mines' End luckstone.

## Candidate experiments from this reading (after the queue in LADDER-NH5.md)

1. Never step next to a hostile unicorn (treat like the floating eye: no melee approach).
2. Shop mimics: do not walk next to a "strange object" in a shop; no melee with mimics below XL ~8.
3. Food from Sokoban: make sure the pilgrim route picks up all Sokoban comestibles (check whether
   the bot already does; Sokoban is reached by 17% of games).
4. Pet-assisted pick-axe: let the pet fight peaceful dwarves (hard to steer; low priority).
