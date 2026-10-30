# A route to ascension for this bot on NetHack 5.0 (research synthesis, 2026-10-29)

Sources: NetHack 5.0.0 source and level files (reference/nethack-5.0.0: dat/*.lua, src/*.c,
doc/fixes5-0-0.txt), local wiki (Castle, Drawbridge, Passtune, Medusa's Island, Valley, Gehennom,
Vlad's/Wizard's/Fake Wizard's Tower, Invocation, Vibrating square, Mysterious force, all Planes,
Astral, Ascension kit/run, Quest, Valkyrie quest, Elbereth, Hallucination, Gas spore, ...), the
NLD-NAO human games (/ssd2/nethackFiles/db/nld.db), our p5-baseline (2304 games), a wizard-mode spike
on our NH5 build, and the older audits ASCENSION-ROUTE-AUDIT.md (3.6), ITEMS-EFFECTS-AUDIT.md,
ASCENSION-KIT-NH5.md.

## Verdict

There is a solid route, and every step of it is something a rule-based bot can do: nothing needs
human judgement that cannot be written as a rule. Each late-game obstacle has a known mechanical answer
(table below), and the late game can now be built and tested without first surviving 20 levels:
wizard mode works on our NH5 build (spike: ^V level teleport to Dlvl 24, ^W wishes, #levelchange to
XL 14, all on turn 1).

The weak point is not the late game, it is survival and growth before it. Today 2.6% of games reach the
Quest portal level and 1 of 2304 reaches Medusa; humans who kill Medusa ascend ~41% of the time
(Valkyries in NLD: 61 ascensions; 148 Medusa kills). So the plan has two tracks that run in parallel:

- Track A (natural bench, rungs 1-8): get many games deep, fed, strong and kitted.
- Track B (staged starts, rungs 9-17): build each late-game skill on a staged level, measured
  separately, so it is ready when Track A games arrive.

## The route, step by step (pilgrim route, dwarvish Valkyrie, lawful)

| Step | What must happen | Bot method (primary / fallback) | NH5 notes |
|---|---|---|---|
| Early (Dlvl 1-4) | survive, find the Mines | explorer fixes; branch-stair glyph; pry supply chests (healing potions) | stealth only at XL 3; no food death drops; Mines branch level has a guaranteed ration |
| Mines to Minetown | gear, pick-axe, food | keep pick-axe (exp 23); pet kills peaceful dwarves for picks; Minetown temple/shops | gnomes/dwarves peaceful to a dwarf |
| Sokoban | prize, 16 food stacks | live solver exists (flipped levels handled); take all food | prize: amulet of reflection 50% overall (soko1-1 25%, soko1-2 75%), else bag of holding |
| Mines' End | luckstone | exact rung exists; pick up the grey stone at the marked spot | 74% of human Val ascenders had it |
| Oracle..Dlvl 20 | XP, AC, wands, poison/fire resistance | eat safe resistance corpses; engrave-ID wands; stop chasing unicorns | potion of healing common, unique price |
| Quest entry | XL 14, alignment >= 20 | XP to 80,000: deep kills, wraiths, potions of gain level (one is in the Castle chest) | entry rule unchanged (quest.h) |
| Valkyrie Quest | Bell of Opening (+ Orb of Fate) | fire resistance first (fire ants/giants on home level); never step on lava; levitation on lava levels; wake Surtur from range, do not cross the drawbridges | quest done by 75% of humans |
| Medusa (Dlvl 21-24) | pass her and the water | going down: dig down on the arrival side (no hardfloor flag on any of the 4 maps; their non_diggable areas cover walls only). Coming back up with the Amulet: arrive on her island; need levitation/flying/water walking AND reflection or a blindfold | maps can be flipped |
| Castle | get in, wand of wishing, trap doors to the Valley | enter: passtune by Mastermind on any non-drum instrument (deterministic, ideal for a bot), or wand of striking at the drawbridge + cross one moat square (levitation / wand of cold / scroll of earth), or levitate to the back door; wand chest is locked, untrapped -> pry with the dagger (#force); trap doors at row 8 lead down | chest also has a potion of gain level; wand has 1 charge, recharge once to 1; map may be mirrored left-right |
| Wishes (2-3 total) | MR, then what is missing | 1: blessed +2 gray dragon scale mail (MR); 2: missing reflection (amulet) or levitation (ring); 3 (Amulet pickup wish in NH5): ring of levitation / life saving | Amulet grants a wish when picked up |
| Valley + Gehennom | descend 20-24 levels | no prayer, no Elbereth, no sacrifice anywhere in Gehennom; dig down through maze levels (floors diggable except special ones); avoid lava (new cave/maze styles with lava/water/iron bars) | filler levels are new in NH5 (hellfill.lua: 6 styles) |
| Vlad's Tower | Candelabrum (+ 7 candles, water walking boots) | up stairs on Gehennom 9-13; kill Vlad (drain resistance helps); candles in two closet chests | three named vampire ladies |
| Wizard's Tower | Book of the Dead | find the fake tower with the portal (dig in through its moat ring: levitation); kill the Wizard in the top level | levelport inside the tower works |
| Vibrating square | invocation | feel "strange vibration"; candelabrum lit + bell rung, then read the book; none cursed | square annotated automatically once found |
| Sanctum | take the Amulet | kill the high priest of Moloch; leave with a cursed potion of gain level or stairs | |
| Climb out | ~45 levels up | mysterious force: a lawful hero is pushed down up to 3 levels 1/4 of the time; no level teleport with the Amulet; Medusa's water again | |
| Planes | four portals | Earth: wands of digging; Air: levitation/flying; Fire: levitation, lava; Water: drift with the bubbles (magical breathing optional); portal detection: confused scroll of gold detection | amulet of flying is new; mindless monsters no longer fear music |
| Astral | offer the Amulet at the lawful altar | find the temples, check the priest's alignment, #offer; avoid the Riders | |

## Keystone items and where a dwarvish Valkyrie gets them

| Need | Used for | Sources (probability where known) |
|---|---|---|
| Pick-axe / wand of digging | stuck levels, Medusa skip, Gehennom descent, Plane of Earth, fake tower | Mines dwarves (1/4 carry one; peaceful -> pet kills), random tools 2%, supply chests (wand of digging), Plane of Earth minotaur/Elvenking |
| Levitation (or flying / water walking) | Medusa on the way up, Castle moat, Wizard's Tower moat, Planes of Air and Fire, Valkyrie quest lava | Perseus statue boots 37.5% overall (25% maps 1/3/4, 75% map 2), ring/potion (random), Vlad's water walking boots (guaranteed), wish |
| Reflection | Medusa, rays, Castle soldiers' wands | Sokoban amulet 50%, Perseus shield of reflection 62.5% (needs the island: after levitation), wish |
| Magic resistance | Gehennom casters, endgame | wish (GDSM) at the Castle; cloak of MR (rare) |
| Unicorn horn | confusion, stun, blindness, hallucination, Pestilence | pet kills a unicorn (the hero must not chase them: 36 baseline deaths) |
| Fire / poison resistance | quest lava, Gehennom fire traps; poison | fire ants/giants (quest home level), red molds; killer bees, soldier ants (corpses now safe-ish: poison no longer instakills in NH5) |
| Luckstone | prayer and wish safety | Mines' End (guaranteed) |
| Lizard corpse | stoning (top late killer of human Valkyries) | lizards (never rot) |
| Tonal instrument | Castle passtune | Minetown shops, random tools; any non-drum instrument works |
| Scrolls of gold detection | Planes portals, vibrating square | random/shops; read confused |
| Food for ~45,000 turns | median human Valkyrie ascension is 45,918 turns | corpses while moving, Sokoban, shops; prayer only every 1000+ turns |

## What the bot cannot do today (capability gaps), in route order

1. Dig down (exp 23 in flight), dig sideways, dig into fake towers.
2. Never pray, engrave Elbereth or sacrifice in Gehennom. (No prayer after a failed prayer: demoted 2026-10-30, it only relabels deaths; see STATE.md.)
3. Apply a unicorn horn; avoid fights while hallucinating; no gas spore kills next to peacefuls.
4. Pry locked chests with the dagger (supply chests, Castle wand chest).
5. Put on rings and amulets; wear armour by property (MR, reflection, levitation, speed), not by AC alone.
6. Read scrolls (identify by price first): gold detection, enchant armour/weapon, remove curse, teleport.
7. Levitation control: put on/take off to cross water and lava, and to pick things up.
8. Play an instrument and solve the passtune Mastermind at the Castle drawbridge.
9. Wish (fixed wish list by what is missing).
10. Quest: talk to the leader at XL 14, fire resistance, lava avoidance, kill Surtur.
11. Gehennom navigation (lava/water/ice/iron bar mazes), Vlad, the Wizard, fake-tower portal.
12. Invocation sequence; Sanctum; the climb (mysterious force); Planes and Astral.

## Human evidence (NLD-NAO, 3.4.3-3.6.x)

- Valkyries: 4363 games, 61 ascended (1.4%). Median ascension 45,918 turns (quartiles 36,557 / 58,772).
- Every Valkyrie ascender killed Medusa; 51/61 had the Sokoban prize; 45/61 the Mines' End luckstone.
- Deaths of Valkyries who reached Gehennom / the Bell: quit, wrath of Moloch (praying in Gehennom),
  cockatrice (petrified by a corpse or the monster), Pestilence with the Amulet, brainlessness (mind
  flayers), green slime, genocide scroll misreads, drowning by eels; after Medusa also minotaurs (mazes,
  ignore Elbereth).

## How to test it

- Natural bench (as now) for rungs 1-8 and every change that touches early/mid play.
- Staged bench for rungs 9-17: an NLE env with wizard=True (the bot's env class forces wizard=False
  today), then ^V to the target level, ^W for the kit, #levelchange for XL. Staged results are reported
  apart from natural-play rates (REQUIREMENTS STAGE-01). NLE's wizkit option does not reach our NH5
  build ("NetHack asked for env variable WIZKIT"); ^W wishes do the same job.

## Updates 2026-10-30

- Wish budget: WISHES-NH5.md replaces the Wishes row below: 2 at the Castle (charge + wrest), 3 with a found charging
  scroll, plus Vlad's throne and the Amulet.
- XL 14 has its own plan, XL14-NH5.md: Castle before the Quest; level jumps; the wand has 1 charge, so the wish count
  below needs checking.
- Early pace and angry peacefuls: FOOD-NH5.md, LADDER-NH5.md.

## Order of work

Track A (now, one experiment at a time on the natural bench): exp 23 dig down; no prayer after a failed
prayer; branch-stair glyph + early explorer; pry chests; unicorns; shop mimics; hallucination/unicorn horn;
gas spores near peacefuls; Sokoban food; then XP growth towards XL 14 (Phase 2/3).
Track B (when the bench is busy and code time is free): staged-start harness first, then Medusa
(dig down / cross with levitation), Castle (passtune solver, chest prying, trap doors), Gehennom descent,
in roadmap order (Phases 4-8).
