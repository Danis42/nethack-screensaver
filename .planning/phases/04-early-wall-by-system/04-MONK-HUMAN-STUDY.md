# Phase 4: How human Monks ascend (dumplog study, 2026-11-17)

Purpose: check the Phase 4 plans (04-01 no shield, 04-02 cross-aligned unicorns, 04-03 descent pacing, 04-04 food)
against what human players who actually ascended a Monk did. Counts, not impressions. Web pages were not used as
evidence; every rule claim below cites the 5.0 source in `reference/nethack-5.0.0/`.

## Method

- **Sources (public xlogfiles, hardfought.org):**
  - `https://www.hardfought.org/xlogfiles/nethack50/xlogfile` (14,784 games, 7 Monk ascensions, all `version=5.0.0`)
  - `https://www.hardfought.org/xlogfiles/nethack37/xlogfile` (237,039 games, 105 Monk ascensions, `3.7.0`)
  - `https://www.hardfought.org/xlogfiles/nethack36/xlogfile` (48,344 games, 57 Monk ascensions, 3.6.1-3.6.7)
  - NAO was not used: hardfought alone gave enough games, and it is the only server with 5.0 games.
- **Selection:** `death=ascended` and `role=Mon`. Taken: all 7 NetHack 5.0 games, the 45 most recent 3.7.0 games and
  the 28 most recent 3.6.x games by `endtime` = **80 games, 37 players**. Versions from the dumplog header:
  5.0.0: 7, 3.7.0: 45, 3.6.3: 20, 3.6.2: 6, 3.6.7: 2. All 80 are human (Monk is human-only).
  Alignment: neutral 41, lawful 20, chaotic 19.
- **Dumplogs:** `bench.importers.dumplog_url` pattern
  (`https://www.hardfought.org/userdata/{i}/{name}/nethack/dumplog/{starttime}.nh.txt`); older ones 301-redirect to
  hardfought's S3 archive and still load. Fetched with `bench.importers.fetch` (1 request/second, its generic
  User-Agent, cache). 80 of 80 downloaded.
- **Parsing:** `bench.importers.sections` plus small regexes: worn items (`(being worn)`, rings `(on ... hand)`),
  `Final Status` ("empty handed" / "wielding ..."), `Vanquished creatures` (white/gray/black unicorn counts),
  `Voluntary challenges` (vegan/vegetarian, weaponless, Elbereth), `Final Attributes`, `Major events` (turn of each
  milestone; present in the 52 games from 3.7/5.0 only). The XL at an event is the last *rank* line before it, so it
  is a lower bound in rank bands (ranks at XL 3, 6, 10, 14, 18, ...).
- **Scripts and data (scratch, not in the repo):**
  `/tmp/claude-1000/-home-user-screens/e674b00c-1ba1-47ac-ac8f-c0480aa60ed4/scratchpad/monk-study/code/`
  (`xlogs.py`, `fetch_dl.py`, `analyze.py`, `report.py`, `cross.py`, `uni.py`, `pace.py`, `food.py`), parsed rows in
  `.../monk-study/dl/rows.json`.
- Dumplog URLs below are shortened to the part after `https://www.hardfought.org/userdata/`.

### Biases to keep in mind

1. **A dumplog shows the end state on the Astral Plane, not the early game.** Endgame gear (dragon scale mail,
   shield of reflection, a wielded cockatrice corpse for Astral) says little about turns 1-10,000, which is where
   the bot dies. Only `Major events` (3.7/5.0) and conducts cover the whole game.
2. **Player concentration:** rebatela 16 games, oh6 12, Cropper 8, Grouchy 5. Player-level counts are given for the
   main findings.
3. Survivors only: these are ascensions, not all Monk games. What winners do is not proof it is what makes them win.
4. Only 7 games are NetHack 5.0; most are 3.7.0 (close to 5.0) and 3.6.x (older rules).

## Rules in 5.0 that matter here (source)

- Monk to-hit: `uhitm.c:397-401`. With **any body armour** (`uarm`, dragon scales/scale mail included) the Monk loses
  `urole.spelarmr` to hit; for the Monk that is **20** (`role.c:271`). The +(XL/3 + 2) bonus needs no weapon and no
  shield (`!uwep && !uarms`).
- Extra martial-arts strike: `uhitm.c:733-752` `double_punch()`, only with `!uwep && !uarms` (20-80% at Skilled+).
- Unarmed special hits (staggering blow etc.): `uhitm.c:1779` `hmd.unarmed = !uwep && !uarm && !uarms`, used at
  `uhitm.c:1827`.
- The game prints the suit penalty in the status: `insight.c:1252-1257`, set by `worn.c:138`
  (`tux_penalty = uarm && Role_if(PM_MONK) && spelarmr`). One 5.0 dumplog shows it:
  "You had a huge penalty to hit (-20) due to your dragon scales." (`o/oh6/nethack/dumplog/1778021929.nh.txt`).
- Meat: `eat.c:1376-1384` `violated_vegetarian()`: a Monk gets "You feel guilty." and `adjalign(-1)` on each
  non-vegetarian meal. `eat.c:2699-2701`: food-smell warning "unhealthy" for a Monk who has kept vegetarian so far.
  That is all: -1 alignment per meal, no Luck penalty.
- Fasting: `attrib.c:541-543`: being Weak exercises Wisdom for a Monk; Satiated abuses it (`attrib.c:533-535`).
- Vegetarian food: `include/mondata.h:232-241` (`vegan`/`vegetarian`: blobs, jellies, fungi, vortices, lights,
  elementals except stalker, most golems, noncorporeal; puddings except black pudding). Lizard and floating eye are
  **not** vegetarian.

## Q1. Armour at the end: shield, suit, other slots (N = 80)

| Slot | Worn | What (games) |
|---|---|---|
| **Shield** | **39/80** (14 of 37 players) | small shield 20, shield of reflection 16, shield of shock resistance 2 (5.0 only), elven shield 1 |
| Body armour (suit) | 54/80 (26 of 37 players) | silver DSM 24, gray DSM 22, yellow DSM 3, blue DSM/scales 3, white DSM 1, green scales 1. **No non-dragon suit in any game.** |
| Cloak slot | 80/80 | **robe 56**, cloak of magic resistance 15, cloak of protection 6, oilskin 2, displacement 1 |
| Helm | 80/80 | elven leather helm 27, helm of brilliance 43 (25 + 18 "tempered", 3.7), helm of opposite alignment 5, telepathy 2, dwarvish iron helm 2, cornuthaum 1 |
| Gloves | 79/80 | gauntlets of power 40, gauntlets of dexterity 32, leather gloves 7 |
| Boots | 80/80 | speed boots 73, water walking 4, jumping 2, elven 1 |
| Shirt | 72/80 | Hawaiian shirt / T-shirt (enchanted for AC) |
| Eyes | 77/80 | the Eyes of the Overworld (Monk quest artifact) |
| Amulet | 79/80 | reflection 32, life saving 28, Eye of the Aethiopica 10, flying 8, guarding 1 |

By version, shield worn: 5.0 4/7, 3.7 17/45, 3.6 18/28. Suit worn: 5.0 4/7, 3.7 31/45, 3.6 19/28.

**Shield goes with a weapon, not with martial arts.** Weapon/shield/suit at the end:

| End state | Games |
|---|---|
| Bare-handed, no shield, no suit (full martial arts) | 8 |
| Bare-handed + suit, no shield | 22 |
| Bare-handed + shield (with or without suit) | 6 |
| Wielding a weapon (any shield/suit) | 28 (22 of them with a shield) |
| Wielding a cockatrice/chickatrice corpse (Astral trick) | 16 (11 with a shield; 13 of the 16 are one player, rebatela) |

So 33 of the 39 shield wearers also wield something; only 6/80 combine bare hands with a shield.

Examples:
- Full martial arts (no weapon, shield or suit): `M/MoonPig/nethack/dumplog/1730875194.nh.txt` (3.7),
  `t/talon/nethack/dumplog/1753582009.nh.txt` (3.7), `B/Bugpowder/nethack/dumplog/1731701077.nh.txt` (3.7),
  `c/chip/nethack/dumplog/1565831020.nh.txt` (3.6)
- Weapon + shield: `o/oh6/nethack/dumplog/1790290641.nh.txt` (5.0, broadsword, shield of shock resistance, GDSM),
  `s/samiam/nethack/dumplog/1792585335.nh.txt` (5.0, mace, SoR, BDSM), `M/MHL/nethack/dumplog/1562654278.nh.txt` (3.6)
- Bare hands + DSM, no shield: `C/Cropper/nethack/dumplog/1793923688.nh.txt` (5.0, SDSM),
  `s/samiam/nethack/dumplog/1773343631.nh.txt` (3.7), `H/Hill/nethack/dumplog/1568363072.nh.txt` (3.6)
- Bare hands + shield: `s/srp1/nethack/dumplog/1793159269.nh.txt` (5.0, SoR, no suit),
  `A/Azoxey/nethack/dumplog/1692152588.nh.txt` (3.7)

## Q2. Do they wield a weapon?

| Measure | Count |
|---|---|
| Empty-handed at the end | 36/80 (29 of 37 players have at least one such game) |
| Wielding a real weapon at the end | 28/80 (10 of 37 players); mostly artifacts: Grayswandir 5, Magicbane 3, Excalibur 3, Fire Brand 2, Dragonbane 2, Demonbane 2, others 1 each |
| Wielding a cockatrice/chickatrice corpse | 16/80 (Astral tactic, 13 by one player) |
| Kept "never hit with a wielded weapon" for the whole game | 14/80 |
| Martial arts skill at the end (Skills section: 5.0 and some 3.7) | Grand Master 11/11 shown, including weapon users |

By version, wielding a weapon: 5.0 4/7, 3.7 15/45, 3.6 9/28. The weapons are late finds (sacrifice gifts
like "bestowed with Ogresmasher/Trollsbane" at T19,060+, wishes, Excalibur); nothing in the logs shows an
early switch away from martial arts. 66/80 broke the weaponless conduct at some point, but that includes a single hit
with a wielded corpse or pick-axe, so it does not show *when* or *how much* they fought with weapons.

## Q3. Unicorns

Vanquished lists (all 80 have one); co-aligned colour = white (lawful), gray (neutral), black (chaotic), using the
final alignment from the xlog.

| Measure | Count |
|---|---|
| Games with at least one **cross-aligned** unicorn killed | **80/80**; 635 kills in total, median 7 per game |
| Games with at least one **co-aligned** unicorn killed | 26/80 (14 of 37 players); 70 kills in total |
| ... of those, alignment changed during the game (helm of opposite alignment / conversion) | 6 of the 26 |
| Carried a unicorn horn at the end | 80/80 |
| Carried a luckstone at the end | 78/80 |
| Luck at the end: "extremely lucky" / "very lucky" / "lucky" | 68 / 10 / 2 |

By version, co-aligned kills: 5.0 4/7, 3.7 16/45, 3.6 6/28.

- Every winner killed cross-aligned unicorns; it is the standard source of the unicorn horn (80/80 carry one).
- Gem throwing is **not visible** in dumplogs (no event or conduct for it). The high Luck (78/80 lucky+, 78/80 with a
  luckstone) fits gifts to co-aligned unicorns or sacrificing, but cannot be attributed from these logs.
- Dumplogs do not show **when** the unicorns died, or how many times the player fled one. Nothing here says whether
  humans fight unicorns at XL 3-8, which is when the bot dies to them.

Examples (many cross-aligned kills): `o/oh6/nethack/dumplog/1727505955.nh.txt` (neutral; 17 white, 10 black, also
3 gray), `S/Smello/nethack/dumplog/1770733406.nh.txt` (neutral; 13 white, 8 black, 0 gray),
`s/samiam/nethack/dumplog/1792585335.nh.txt` (5.0, lawful; 3 gray, 3 black, 0 white).
No co-aligned kill: `r/rebatela/nethack/dumplog/1565781680.nh.txt`, `s/spazm/nethack/dumplog/1781791227.nh.txt`.

## Q4. Descent pace (Major events: 52 games from 3.7.0 and 5.0.0)

Turn and rank band at the first time each milestone is logged (quartiles; rank band = XL is at least this):

| Milestone | n | Turn q25 / median / q75 | XL band at that time |
|---|---|---|---|
| Enter Gnomish Mines (branch on Dlvl 2-4) | 52/52 | 505 / 777 / 1,306 | XL 1-2: 27, XL 3-5: 21, XL 6+: 4 |
| Reach Minetown (Mines 3-4 levels down) | 51/52 | 1,861 / 2,710 / 3,522 | XL<6: 10, **XL 6+: 41** |
| Enter Sokoban (up from Dlvl 6-9) | 52/52 | 5,175 / 6,562 / 8,180 | XL<6: 1, XL 6-9: 45, XL 10+: 6 |
| Mines' End luckstone (Dlvl 10-13) | 48/52 | 5,807 / 7,545 / 11,512 | XL 6-9: 26, XL 10+: 22 |
| Sokoban prize | 46/52 | 8,410 / 9,765 / 11,224 | XL 6-9: 12, XL 10+: 34 |
| Big room (Dlvl 10-12) | 20/52 | 10,286 / 12,608 / 14,958 | XL 6-9: 3, XL 10+: 17 |
| Kill Medusa (Dlvl 21-24) | 50/52 | 19,570 / 24,042 / 30,396 | XL 10-13: 18, XL 14+: 32 |
| Enter Gehennom | 52/52 | 23,514 / 29,541 / 37,595 | XL 10-13: 5, XL 14+: 47 |
| Ascend | 52/52 | 33,551 / 43,940 / 58,069 | XL 18+ (median band 18) |

Rank milestones: XL 3 by about turn 700-1,100; XL 6 median turn 2,068 (q25-q75 1,569-2,539); XL 10 median turn 9,255
(8,358-10,325); XL 14 median turn 21,018. Over all 80 games: turns at the end q25/median/q75 = 38,853 / 44,125 /
55,345; maximum depth 48 / 49 / 51.

Route: **52/52 entered the Mines before Sokoban.** Mines' End came after Sokoban in 31 of 48 games (the luckstone is
often a second Mines trip). The typical early route is: Mines at XL 1-3 around turn 800, Minetown at XL 6+ around
turn 2,700, then back up to Sokoban at XL 6-9 around turn 6,500, Dlvl 10+ only at XL 10.

Examples: `S/StCugel/nethack/dumplog/1767656251.nh.txt` (Mines T1,638, XL6 T1,989, Minetown T2,267, Sokoban
T6,376, Mines' End T8,864, XL10 T9,463), `s/samiam/nethack/dumplog/1773343631.nh.txt` (XL6 T2,162, Mines T2,484,
Minetown T3,033, Sokoban T5,415), `o/oh6/nethack/dumplog/1774037216.nh.txt` (Mines T2,112, XL6 T3,845, Minetown T3,893,
Mines' End T7,190, Sokoban T10,041), `B/Bugpowder/nethack/dumplog/1731701077.nh.txt` (Mines T503, Minetown T2,093,
Sokoban T4,368, Mines' End T10,051).

Gap: the logs do not show the deepest Dungeons level per turn, only these milestones. 3.6 dumplogs have no
Major events.

## Q5. Food

| Measure | Count |
|---|---|
| Kept vegetarian all game | 19/80 (12 strict vegan + 7 vegetarian; 12 of 37 players) |
| Ate meat at some point | 61/80 |
| Foodless | 0/80 |
| Carried any food at the end (inventory or bags) | 80/80 |
| Lizard corpse | 64/80 (51 in main inventory) |
| K-/C-rations | 43/80 |
| Lembas wafers | 42/80 |
| Food rations | 41/80 |
| Sprig of wolfsbane / garlic | 39/80 |
| Fruit/veg | 25/80; eggs 19, royal jelly 16, tins 15, tripe 14, fortune cookies 11, cram 9 |
| Ring of slow digestion carried | 46/80 (17 worn on Astral) |

By version, vegetarian: 5.0 1/7, 3.7 15/45, 3.6 3/28. Vegan examples: `j/jonosmalls88/nethack/dumplog/1757419405.nh.txt`,
`o/oh6/nethack/dumplog/1765054455.nh.txt`, `t/tonethack/nethack/dumplog/1559347235.nh.txt`.

Telepathy at the end: 68/80 (55/61 meat eaters, 13/19 vegetarians; the source for vegetarians is not visible in the
dumplogs, and floating eyes are not vegetarian per `mondata.h:232-241`).

## Q6. Other consistent habits

| Measure | Count |
|---|---|
| Never engraved Elbereth | 52/80 (5.0 4/7, 3.7 27/45, 3.6 21/28) |
| Engraved Elbereth | 28/80, median about 11 times, one game 491 |
| Intrinsics at the end (all 80): poison, sleep and shock resistance, fast (79 "very fast"), magic resistance | 80/80 |
| Reflection | 71/80 |
| Piously aligned at the end | 76/80 (4 "fervently") |
| Robe in the cloak slot | 56/80 |

Prayer counts are not in the dumplogs.

## What this means for the bot's plans

- **04-01 (Monk wears no shield).** Consistent with humans **for a bare-handed Monk**: only 6/80 winners combine bare
  hands with a shield; the shield (39/80) almost always comes with a wielded weapon or an Astral cockatrice corpse,
  and those shields are endgame items (shield of reflection, small shield). **Difference:** humans are not "never a
  shield" players. About a third switch late to an artifact weapon plus shield. That is a late-game choice the bot
  does not need now; "no shield while bare-handed" is the right early rule. Second difference: **54/80 winners wear
  dragon scale mail** and 22 of them still fight bare-handed, taking the -20 to-hit penalty (`uhitm.c:398-399`,
  `role.c:271`). The bot's "Monk wears no suit" rule (inventory.py:1265) is right early (to-hit is what an XL 1-10
  Monk lacks), but is not what humans end with; a later phase may want "DSM is worth it once XL and Luck are high".
  No winner wore any non-dragon suit.
- **04-02 (do not chase cross-aligned unicorns).** **Humans do something different:** every one of the 80 winners
  killed cross-aligned unicorns (median 7 per game), and all 80 carry a unicorn horn. Not chasing them is still a
  reasonable *early* survival rule for the bot (the dumplogs do not show at what XL humans kill them, and a unicorn's
  line-avoiding movement, `monmove.c:1939-1948`, makes chasing slow and dangerous at low XL). But a permanent "avoid
  unicorns" rule would cost the bot its main unicorn-horn source; plan a later "fight unicorns when strong / cornered
  in a dead end" rule. 26/80 even killed co-aligned unicorns, a Luck cost humans accept late with a luckstone; the
  bot should keep leaving peaceful ones alone.
- **04-03 (pace the descent).** Humans pace by XL, matching the plan's idea. Numbers to use: Mines entry at XL 1-3
  (turn ~800), Minetown at XL 6+ (41/51), Sokoban at XL 6-9, Dlvl 10+ (Mines' End, Big room) at XL 6-9 in about half
  the games and XL 10+ in the rest, Medusa at XL 14+ in 32/50. Roughly: Dlvl ~= XL or a bit less in the early game;
  "4 levels below XL" (the bot's too_deep group) is far outside the human pattern. **Difference:** humans enter the
  Mines first (52/52) and early (median turn 777), and go back up to Sokoban at XL 6-9; Mines' End is often a second
  trip after Sokoban (31/48).
- **04-04 (food).** Humans carry food all the time (80/80) and a wide mix: lizard corpse (64/80), rations/lembas, and
  in 46/80 a ring of slow digestion. **Difference from the guilt rule:** 61/80 winners eat meat; in 5.0 the cost is only
  -1 alignment per meal (`eat.c:1376-1384`), and 76/80 still end piously aligned. A vegetarian rule is not needed for
  winning; the bot should eat safe corpses as food. Keeping a lizard corpse is a near-universal habit worth copying
  (it is also the stoning cure).
- **Other (Phase 4 safety, SURV-05):** Elbereth is optional for winners (52/80 never used it); the
  robe is the usual cloak (56/80, it also helps spellcasting, `spell.c:2191-2195`); speed boots (73/80), gauntlets of
  power/dexterity, and a helm of brilliance or elven leather helm are the standard late kit.

## Gaps

- Dumplogs show the end state on the Astral Plane; early-game gear and fights are not visible. ttyrecs would be
  needed for that and were not studied.
- No timing for unicorn kills, gem throws or prayers.
- Pace data is from 3.7.0 and 5.0.0 only (52 games); rank bands make XL a lower bound.
- Only 7 games are 5.0. 3.6 rules differ in places (e.g. Elbereth); this study did not check each difference.
- 37 players; a few (rebatela 16, oh6 12, Cropper 8) shape the totals, especially the corpse-wielding (13/16 rebatela).
