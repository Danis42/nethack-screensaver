# First-ascension character for this bot (research, 2026-11-15)

Question (SURV-06, D-02): which role, race and alignment gives the bot its best chance? Today every game is
`val-hum-fem-neu` (`nethack_screensaver/game.py`). Candidates come from the strong tier of `autoascend/plans.py`
(`ROLE_TIERS["strong"]`: bar, sam, val, mon). The bench A/B decides (plan 02-04); this note only shortlists.

## What the baseline dies of (job 7, e5b5a7f525bc51b8008f665173600aba80de466d, 10,000 games)

From `python -m bench.triage` and read-only queries on job 7's rows:

- Dwarves and gnomes (killer has M2_DWARF or M2_GNOME): 654 deaths, 6.5% (dwarf 191, dwarf king 73, gnome lord 62,
  dwarf queen 58, gnome 52, gnome king 43).
- Monsters faster than the hero ("fast" group): 694; packs ("groups"): 1,190.
- Unicorns: white 286, black 144 (a neutral hero meets two cross-aligned colours).
- Killed while sleeping: 195. Poison named in the end reason: 75.
- Reached Dlvl 10: 38.76% (the winner metric, D-03).

## What each candidate changes, from the 5.0 source

| Character | Changes against val-hum-fem-neu | Source |
|---|---|---|
| val-dwa-fem-law (dwarvish Valkyrie) | Dwarves and gnomes are peaceful to a dwarf: the 654 Mines-native deaths largely go away, and the Mines become safe early. Infravision (half of Mines filler levels are dark). Lawful: unicorns that are hostile become gray and black instead of white and black (same count). Race dwarf sends `plan_for` down the Mines-first route. Same role, so kit and intrinsics (cold resistance, stealth at 3, speed at 7) are unchanged. | [fact:dwarf-race-loves-dwarves-gnomes] [fact:race-peaceful-before-alignment] [fact:dwarf-race-infravision] [fact:role-intrinsics-valkyrie] |
| sam-hum-mal-law (Samurai) | Fast from XL 1 (the Valkyrie waits for XL 7): fewer deaths to monsters it cannot outrun and quicker fights. Human, so Mines natives stay hostile unless the lawful alignment check makes some peaceful; no infravision; Sokoban-first route. | [fact:role-intrinsics-samurai] [fact:human-race-no-intrinsics] |
| mon-hum-mal-neu (Monk) | Fast, sleep resistant and sees invisible from XL 1, poison resistant at XL 3: touches the fast, helpless and poison groups at once. Risk: the bot is built for weapon users; it has only a few Monk special cases (`autoascend/character.py:500,587`, `autoascend/item/inventory.py:1165,1265`), so its fighting and armour choices may hurt a martial artist. | [fact:role-intrinsics-monk] |
| bar-hum-mal-neu (Barbarian), not shortlisted | Poison resistance from XL 1 and speed at 7: poison is only 75 of 10,000 endings, so the gain is small. | [fact:role-intrinsics-barbarian] |

## Earlier evidence (not current numbers)

- `.planning/research/MINES-ENTRY-NH5.md`: most early Mines deaths of human Valkyries are accidental arrivals while
  looking for Sokoban; real 5.0 ascenders almost all go Mines first. A dwarf makes those arrivals far less deadly.
- `.planning/research/ASCENSION-PLAN-NH5.md`: the route there was written for a dwarvish lawful Valkyrie.
- `ROLE_TIERS` comes from about 380 games per role on an older commit (2026-10-18). That is archive history, not a
  measurement on today's bot, and is used only to limit the candidates to the strong tier.

## Shortlist

1. **val-dwa-fem-law**: largest single effect visible in the baseline (6.5% of endings), same role the bot was tuned
   for, and the route the ascension plan assumes.
2. **sam-hum-mal-law**: speed from turn 1, a different and independent lever.
3. **mon-hum-mal-neu**: most intrinsics, highest risk because of the bot's weapon logic.

Each finalist is tested as "character plus its plan" (D-03): the dwarf goes Mines first, the humans Sokoban first.
