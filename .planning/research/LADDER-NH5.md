# Where the ladder leaks (research, 2026-10-29)

Source: p5-baseline (579c4d5, 2304 games). Games grouped by highest rung reached.

| Highest rung | Games | XL | max HP | turns | End causes (top) |
|---|---|---|---|---|---|
| 0 (never in the Mines) | 552 | 5 | 52 | 5544 | starve 190, giant+small mimic 45, wand 23, wrath 21, rothe 11 |
| 1 Mines | 671 | 7 | 69 | 7790 | starve 227, rothe 25, crash 25, soldier ant 19, eye 16, black unicorn 16 |
| 2 Minetown | 383 | 8 | 77 | 9468 | starve 90, mumak 16, watch captain 15, gray unicorn 15, soldier ant 14 |
| 3 Oracle | 297 | 8 | 84 | 11394 | starve 33, wolf 10, leocrotta 10, Green-elf 9, crash 9 |
| 4 Sokoban | 76 | 9 | 92 | 15732 | starve 11, crash 6, gray unicorn 5, pyrolisk 5 |
| 6 Mines' End | 214 | 9 | 90 | 13341 | starve 23, leocrotta 11, troll 9, crash 7 |
| 7 Dlvl 15+ | 50 | 10 | 101 | 16036 | rock troll 4, giant mummy 3, elf-lady 3, zruty 3 |
| 8 Quest portal | 60 | 9 | 97 | 15048 | fire ant 7, crash 6, winged gargoyle 4, rock troll 3 |

## Biggest leak: 24% never enter the Gnomish Mines

- 552 games; median depth 3, turn 5544; milestone at the end FIND_GNOMISH_MINES 253, DIVE 261
  (gave up after 2500 stuck turns), BE_ON_FIRST_LEVEL 38.
- 261 stuck reports while looking for the Mines, on Dlvl 1 (26), 2 (78), 3 (78), 4 (53), 5 (25).
  100 of them still had reachable unexplored frontier (the explorer gave up early),
  140 had boulders, 41 closed doors.
- NetHack 5 shows branch staircases with their own glyph (S_brdnstair / S_brupstair);
  autoascend/glyph/nh5.py maps them to plain stairs, so the bot cannot tell which downstairs
  goes to the Mines. Candidate: keep the branch glyph as "Mines stairs" (only branch on Dlvl 2-4
  besides Sokoban's up branch on the Oracle+1 level), go straight to it.
  Today exploration_logic explores Dlvl 2-4 and walks unexplored stairs in random order
  (explore_stairs), so the glyph mostly saves wrong-way trips; it does not fix the 100 stuck
  cases with reachable frontier left, which is an explorer problem of its own (needs replays).
- The Mines branch level also holds a guaranteed ration (FOOD-NH5.md).

## Other leaks worth a look

- Mimics kill 45 weak (XL 5) heroes before the Mines, usually in shops ("for sale" next to
  "You hit the small mimic"): do not melee mimics at low XL, or leave shops.
- Watch deaths ~28 (13 "watch captain", 5 "while praying", 10 "hallucinogen-distorted watch...";
  12 more "watchdog" ends are the bench timeout, not the watch). Hypothesis: while hallucinating
  the monster tracker skips peaceful detection (monster_tracker.update: `if not hallu`), so the
  bot attacks the peaceful watch and Minetown turns hostile. Needs a replay of one of these seeds.
- Unicorns (gray 20, black 16): a lawful Valkyrie fights cross-aligned unicorns; strong in melee.
- Wrath of Tyr 33: PRAYER-NH5.md.
