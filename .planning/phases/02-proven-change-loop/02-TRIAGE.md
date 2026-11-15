# Phase 2: Failure triage (SURV-01)

Baseline: job 7, commit e5b5a7f525bc51b8008f665173600aba80de466d, dev seeds 1,000-10,999, lgen off.
Command: `uv run python -m bench.triage e5b5a7f525bc51b8008f665173600aba80de466d --lo 1000 --hi 11000`
Rules: `bench/triage_groups.py` (first match wins, recorded fields only, no LLM).

## Groups (owner-reviewed 2026-11-15)

Reviewed once by the owner (D-11), approved without changes. Groups are listed by expected gain (rules are tried in the order of `GROUPS` in the code); the count is
how many baseline games end in each group. Three example games each (lowest seeds).

### melee (1917 games, 19.2%)

killed in melee by a monster its level should handle: fights it lost anyway

- seed 1014: `DEATH: killed by a mumak` (Dlvl 8, XL 6); last message: "The mumak butts!--More--"
- seed 1015: `DEATH: killed by a troll` (Dlvl 11, XL 9); last message: "You see here a rock piercer corpse.  The troll hits!--More--"
- seed 1027: `DEATH: killed by a dwarf lord` (Dlvl 7, XL 7); last message: "The dwarf lord hits again!--More--"

### starvation (1393 games, 13.9%)

starved, or killed while fainted from hunger: food supply and eating

- seed 1004: `DEATH: starved to death` (Dlvl 5, XL 4); last message: "You can hear again.  You faint from lack of food.--More--"
- seed 1017: `DEATH: killed by a sasquatch, while fainted from lack of food` (Dlvl 11, XL 8); last message: "The sasquatch hits!--More--"
- seed 1023: `DEATH: killed by an elf mummy, while fainted from lack of food` (Dlvl 9, XL 8); last message: "The elf mummy hits!--More--"

### groups (1190 games, 11.9%)

killed by a monster that comes in groups (ants, bees, elves, soldiers, Mines natives)

- seed 1000: `DEATH: killed by a fire ant` (Dlvl 8, XL 7); last message: "The fire ant bites!  The fire ant bites again!  You're on fire!--More--"
- seed 1006: `DEATH: killed by a Green-elf` (Dlvl 12, XL 9); last message: "The Green-elf swings her elven broadsword.  The Green-elf hits!--More--"
- seed 1009: `DEATH: killed by a dwarf zombie` (Dlvl 1, XL 1); last message: "The orc zombie hits!  The dwarf zombie misses!  The dwarf zombie hits!--More--"

### too_deep (996 games, 10.0%)

killed in melee 4+ levels deeper than its experience level: descends too fast

- seed 1002: `DEATH: killed by a sergeant` (Dlvl 13, XL 9); last message: "The sergeant swings her mace.  The sergeant hits!--More--"
- seed 1005: `DEATH: killed by a piranha` (Dlvl 16, XL 10); last message: "The piranha bites!--More--"
- seed 1007: `DEATH: killed by an elf mummy` (Dlvl 13, XL 9); last message: "The elf mummy hits!--More--"

### fast (694 games, 6.9%)

killed by a monster faster than an unhasted hero: cannot run away from it

- seed 1018: `DEATH: killed by a mountain centaur` (Dlvl 10, XL 9); last message: "The mountain centaur misses!  The mountain centaur kicks!--More--"
- seed 1041: `DEATH: killed by a leocrotta` (Dlvl 11, XL 8); last message: "The leocrotta hits!  The leocrotta hits!--More--"
- seed 1056: `DEATH: killed by a quasit` (Dlvl 12, XL 9); last message: "Valkyrie, your life force is running out.  The quasit bites!--More--"

### ranged (623 games, 6.2%)

killed by wands, rays, missiles or explosions: no answer to ranged attacks

- seed 1028: `DEATH: killed by a wand` (Dlvl 5, XL 4); last message: "You hear a nearby zap.  The wand hits you!--More--"
- seed 1033: `DEATH: killed by a magic missile zapped by a titan` (Dlvl 24, XL 10); last message: "The magic missile hits you!--More--"
- seed 1035: `DEATH: killed by an elven arrow` (Dlvl 7, XL 6); last message: "You are hit by the 1st elven arrow!--More--"

### strong (530 games, 5.3%)

killed by a monster 3+ difficulty above its experience level: fights it should avoid

- seed 1003: `DEATH: killed by a gnome king` (Dlvl 5, XL 3); last message: "The gnome king swings his mace.  The gnome king hits!--More--"
- seed 1067: `DEATH: killed by an Elvenking` (Dlvl 7, XL 6); last message: "The Elvenking swings his elven broadsword.  The Elvenking hits!--More--"
- seed 1068: `DEATH: killed by a queen bee` (Dlvl 11, XL 8); last message: "The queen bee stings!--More--"

### stuck (682 games, 6.8%)

ended on a Dlvl 5+ level it could not leave (stuck explorer)

- seed 1001: `DEATH: killed by a xorn` (Dlvl 25, XL 11); last message: "The xorn hits again!  The xorn hits again!  The xorn bites!--More--"
- seed 1013: `DEATH: killed by a giant ant` (Dlvl 5, XL 7); last message: "The imp hits!  The jackal bites!  The giant ant bites!--More--"
- seed 1016: `DEATH: killed by an ogre queen` (Dlvl 16, XL 9); last message: "The ogre queen hits!--More--"

### unicorns (376 games, 3.8%)

killed by a unicorn: fights unicorns it should leave alone

- seed 1084: `DEATH: killed by a white unicorn` (Dlvl 7, XL 6); last message: "The white unicorn butts!  The white unicorn kicks!--More--"
- seed 1086: `DEATH: killed by a black unicorn` (Dlvl 5, XL 5); last message: "The black unicorn butts!--More--"
- seed 1104: `DEATH: killed by a black unicorn` (Dlvl 7, XL 5); last message: "The black unicorn butts!  The black unicorn kicks!--More--"

### prayer (387 games, 3.9%)

killed while praying: prayed when it could not help (timeout, wrong trouble)

- seed 1011: `DEATH: killed by a tiger, while praying` (Dlvl 8, XL 8); last message: "You begin praying to Odin.  The tiger hits!--More--"
- seed 1024: `DEATH: killed by a vampire, while praying` (Dlvl 20, XL 10); last message: "The vampire hits!--More--"
- seed 1040: `DEATH: killed by a leocrotta, while praying` (Dlvl 9, XL 9); last message: "The leocrotta misses!  The leocrotta bites!--More--"

### angered (274 games, 2.7%)

killed by the watch, a shopkeeper, a priest or its god: angered someone it should not

- seed 1051: `DEATH: killed by the wrath of Odin` (Dlvl 3, XL 6); last message: "The voice of Odin thunders: "Thou hast angered me."--More--"
- seed 1063: `DEATH: killed by the wrath of Odin` (Dlvl 3, XL 4); last message: "The voice of Odin booms out: "Thou hast angered me."--More--"
- seed 1197: `DEATH: killed by Ms. Kediri, the shopkeeper` (Dlvl 8, XL 8); last message: "You hit it.  It hits!  It hits again!  It hits!  It hits again!--More--"

### helpless (254 games, 2.5%)

killed while asleep, frozen or paralysed: walked into a disabling attack

- seed 1010: `DEATH: killed by a hallucinogen-distorted homunculus, while frozen by a gelatinous cube` (Dlvl 12, XL 7); last message: "The balrog kicks!  Lord British bites!--More--"
- seed 1021: `DEATH: killed by a killer bee, while sleeping` (Dlvl 4, XL 8); last message: "The killer bee's sting was poisoned!--More--"
- seed 1113: `DEATH: killed by a sergeant, while frozen by a potion` (Dlvl 13, XL 8); last message: "The sergeant swings his mace.  The sergeant hits!--More--"

### passive (203 games, 2.0%)

killed by passive or engulfing monsters (jellies, molds, blobs, vortices)

- seed 1008: `DEATH: killed by a spotted jelly` (Dlvl 11, XL 9); last message: "You are splashed by the spotted jelly's acid!--More--"
- seed 1135: `DEATH: killed by a chameleon imitating a spotted jelly` (Dlvl 12, XL 9); last message: "You are splashed by the spotted jelly's acid!--More--"
- seed 1151: `DEATH: killed by a spotted jelly` (Dlvl 5, XL 5); last message: "You are splashed by the spotted jelly's acid!--More--"

### aborted (167 games, 1.7%)

NetHack ended the game for lack of progress (ABORTED)

- seed 1019: `ABORTED: the Fighter St:17 Dx:14 Co:18 In:8 Wi:9 Ch:11 Neutral S:1733 Dlvl:6 $:14 HP:87(87` (Dlvl 6, XL 9); last message: "Where do you want to be teleported?  (For instructions type a '?')"
- seed 1193: `ABORTED: the Woman-at-arms St:18/04 Dx:16 Co:17 In:7 Wi:9 Ch:7 Neutral S:56 Dlvl:7 $:0 HP:` (Dlvl 7, XL 12); last message: "Where do you want to be teleported?  (For instructions type a '?')"
- seed 1281: `ABORTED: the Fighter St:18/03 Dx:11 Co:18 In:8 Wi:8 Ch:11 Neutral S:2 Dlvl:3 $:69 HP:65(65` (Dlvl 3, XL 6); last message: "You see here a crossbow bolt."

### stoning (117 games, 1.2%)

turned to stone by touching or fighting a cockatrice/chickatrice

- seed 1156: `DEATH: petrified by a cockatrice` (Dlvl 12, XL 9); last message: "The cockatrice bites!  The cockatrice touches you!--More--"
- seed 1164: `DEATH: petrified by a cockatrice` (Dlvl 12, XL 9); last message: "You hit the cockatrice!  Your limbs have turned to stone.--More--"
- seed 1220: `DEATH: petrified by a chickatrice` (Dlvl 12, XL 10); last message: "The chickatrice bites!  The chickatrice touches you!--More--"

### bad_food (80 games, 0.8%)

ate something harmful: rotten or poisonous corpses, cockatrice meat

- seed 1292: `DEATH: poisoned by a rotted rothe corpse` (Dlvl 4, XL 7); last message: "There are several objects here.--More--"
- seed 1404: `DEATH: poisoned by a rotted hill orc corpse` (Dlvl 8, XL 7); last message: "You see here a cave spider corpse.--More--"
- seed 1507: `DEATH: poisoned by a rotted gnome corpse` (Dlvl 5, XL 6); last message: "This dwarf corpse is tough.  You are at Death's door.--More--"

### other (41 games, 0.4%)

anything else

- seed 1233: `DEATH: fell into a pit` (Dlvl 4, XL 3); last message: "You fall into a pit!--More--"
- seed 1413: `DEATH: poisoned by a scorpion` (Dlvl 10, XL 8); last message: "The scorpion stings!  The scorpion's sting was poisoned!--More--"
- seed 1489: `DEATH: fell into a pit` (Dlvl 1, XL 1); last message: "You fall into a pit!--More--"

### bot_crash (74 games, 0.7%)

the bot crashed (Cyclic Panic or another exception)

- seed 1139: `exception: RuntimeError: Cyclic Panic: ["AssertionError at agent.py:593 update < agent.py:` (Dlvl 5, XL 7); last message: "There is a cave spider corpse named #old here; eat it? [ynq] (n)"
- seed 1209: `exception: RuntimeError: Cyclic Panic: ['OverflowError at global_logic.py:130 add_item < g` (Dlvl 7, XL 9); last message: "All monsters currently shown on the map:"
- seed 1318: `exception: RuntimeError: Cyclic Panic: ["ValueError at monster_tracker.py:30 take_all_mons` (Dlvl 12, XL 8); last message: "What do you want to look at:"

### watchdog (2 games, 0.0%)

the game stopped changing the screen for 120 s (watchdog)

- seed 2073: `watchdog` (Dlvl 1, XL 1); last message: "Showing known terrain and traps only...  (For instructions type a '?')"
- seed 10846: `watchdog` (Dlvl 1, XL 1); last message: "All monsters currently shown on the map:"

