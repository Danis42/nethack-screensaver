# Feature Research: abilities an NetHack 5.0 ascension needs vs. what the bot can do

**Domain:** rule-based NetHack bot (AutoAscend on NLE 1.3.0 / NetHack 5.0), goal = one clean ascension
**Researched:** 2026-11-12
**Confidence:** MEDIUM-HIGH. Route facts and NH5 rules come from the existing notes, which cite the 5.0 source.
Bot status was verified by reading and grepping `autoascend/` on `main` (fb5faa2); wiring was checked by finding callers,
not just definitions. Rates come from archived bench runs (not re-measured today; the live bench DB is empty).
Nothing here is a new measurement.

This file consolidates `.planning/research/` (ROUTE-AUDIT, PLAN-NH5, PLAYBOOK-NH5, KIT, MEDUSA, MEDUSA-RETURN, WISHES,
XL14, FOOD, PRAYER, SURVIVAL, AC-GAP, TELEPATHY, LADDER, REWIND-20, MINES-ENTRY, hand-games). It does not redo them.

**Character the bot plays:** `val-hum-fem-neu` (`nethack_screensaver/game.py:40`), a human neutral Valkyrie. God = Odin.
Mines gnomes/dwarves are hostile (fights, but free pick-axes). No Excalibur (fountain.c:404 is lawful-only). Some older notes
still say "dwarvish, lawful"; the playbook and code say human neutral. Treat the code as truth.

## How to read the status columns

- **HAVE** = in `main`, wired into the strategy loop (a caller exists).
- **PART** = exists but unwired, only handles one case, or depends on an item the bot rarely holds.
- **NONE** = no code. Grep found nothing.
- Many notes say "BUILT on feat/...". That is true only for items that are on `main` now. The feature branches are gone
  from the local repo (only `main`; old branches are in `archive/screens-all-branches.bundle`). I verified every BUILT claim
  against `main` below. Where a claim holds only as "primitive exists, nobody calls it", it is marked PART.
- "Staged" results (castle 8/20, medusa crossing 4/10) are test-tool numbers, not natural-game rates. Natural play today:
  1.1% see Medusa, 0 of 146k stored games passed her.

---

## The two walls (separated, as the project asks)

### EARLY WALL: survival and growth, Dlvl 1 to about 12 (fixed by system, not by monster)

Evidence: 24% of games never enter the Mines; starvation 334 of 2304 (14.5%) in the `72ca0b6` baseline (was 25% before
exp 37); close calls are 68% of deaths in the 20-seed rewind study; humans match the bot on XL/HP to Dlvl 10-12, but AC
plateaus at -3/-4 (humans -13 at Dlvl 20).

| # | Capability | Why it blocks | Status on main | Evidence in code | Difficulty | Depends on |
|---|-----------|---------------|----------------|------------------|-----------|-----------|
| E1 | Eat corpses fast, keep non-corpse food | food is supply-limited, not eating-limited; NH5 removed death drops | HAVE | `eat_corpses_from_ground`, `eat_from_inventory`, `edible_inventory_food` (agent.py) | - | - |
| E2 | Early pace (turns per level) | bot is 2-3x slower than humans on a food budget of ~1700 turns + corpses | PART | `trap_search_offset=0` is now passed (global_logic.py:1270 area, exp "no-trap-search"); no measurement on main | M | bench baseline |
| E3 | Find the Mines branch (branch-stair glyph) | 24% never enter; bot cannot tell Mines stairs | NONE | `glyph/nh5.py` maps `S_brdnstair`->`S_dnstair`; no "branch" notion | L | glyph map change |
| E4 | Explorer finishes levels (frontier left in 100/261 stuck-Mines cases; boulders, closed doors) | stuck -> starve | PART | `exploration_logic.py`, `push_boulders`, stuck watch (2500 turns) | M-H | replays of stuck seeds |
| E5 | Dig down when stuck | "a bot that can dig down is never stuck"; pick within reach in ~40% of stuck-starved games | PART | `_dig_down_when_stuck`, `Agent.dig_down`, `digging.py`; keeps ONE identified non-cursed pick-axe only (`global_logic.py:185`); mattock excluded; no deliberate pick-axe hunting; fires only in DIVE milestone | M | pick-axe source, E4 |
| E6 | Supply chests above Oracle (healing potions, wand of digging, enchant armor) | free healing and a dig wand | PART | `force_lock_below_me`, `untrap_container_below_me`, `storeroom_chests`, `check_containers`; "pry with known uncursed spare blade" policy: a non-cursed blade can break when forcing [fact:force-lock-blade-may-break] | L-M | blade ownership |
| E7 | Buy food / shop interaction (#pay, price check, buy) | food shops in 90% of Minetowns; shopkeeper anger = 5.1% of deaths | NONE | no `PAY`/`CHAT` command use anywhere | M | gold pickup (HAVE), shop code (PART: `shop_sell.py` sells-test only) |
| E8 | Permafood reserve rule (keep 2, buy when short) | humans: rations 10-13% of meals; bot falls from 18% to 6% | NONE | `eat_from_inventory` eats at Hungry; no reserve target | L | E7 |
| E9 | Prayer discipline: failed-prayer lockout | 24% of games have a failed prayer; 33 wrath deaths | NONE (data says low value for score, but required later) | `pray()` only records `last_prayer_turn`; `prayer.py` classifies outcomes for stats only | L | - |
| E10 | Never pray in Gehennom | praying there always angers; top human Gehennom death | NONE | no dungeon check in `prayer_trouble`/`pray` | L | Gehennom detection (G1) |
| E11 | HP management / escape: quaff healing, stair escape, Elbereth | 2/3 of deaths are close calls | PART | quaff <1/3 HP (`emergency_strategy`); Elbereth written in fight (`fight_heur.elbereth_action`) but emergency-path Elbereth commented out; `stair_escape.py` only from Dlvl 21; no retreat items | M | - |
| E12 | Don't melee passive-damage monsters | 89 deaths = 3.4% (spotted jelly 33, energy vortex 26, fire elemental 11 ...) | PART | only floating eye, blue jelly, brown mold, gas spore, acid blob avoided (`ONLY_RANGED_SLOW_MONSTERS`) | L | monster table |
| E13 | Don't engage unicorns | unicorns kill ~3% (gray 20, black 16, white 26 in samples) | NONE (bug: engages at HP>=15) | `combat/movement_priority.py` | L | - |
| E14 | Don't anger peacefuls (shopkeepers, Watch) | 69 shopkeeper + 48 Watch deaths = 5.1% | PART | closed-shop sign (`reads_closed_shop`), mimic gate; no "no ranged line through a peaceful", no #pay before leaving | M | E7 |
| E15 | Telepathy from floating eye | 95% of 5.0 ascenders; needed for Medusa ravens | HAVE | `eat_eye_corpse`, `get_telepathy` (blindfold-melee), `telepathy.py`; 48/100 games gained it | - | blindfold in 15% of games |
| E16 | Ranged-ray safety (zap along a line with a wall behind) | hand game: bounce hit zapper HP 14->2 | NONE | `Agent.zap`, no bounce check | L | - |
| E17 | Hallucination handling (don't attack peacefuls while hallucinating) | ~10 Watch deaths | PART | unicorn horn use; `monster_tracker` skips peaceful detection when hallucinating | L-M | - |
| E18 | AC growth: enchant armor, gloves, body armor, cloaks | AC stops at -3 while humans reach -13; bot reads only known-ID scrolls | PART | `item/scrolls.py` (read safe-unknown groups), `read_scrolls`, price-ID in `item_manager`; AC cause still open (AC-GAP-NH5 correction) | M | scroll ID, supply |
| E19 | Altar BUC test before wearing found armor | unknown-BUC items are treated as UNCURSED (`item_manager.py:241`), cursed gear gets worn | PART | `identify_items_on_altar` exists; the unknown->uncursed rule still on | L-M | Minetown altar |
| E20 | Priest protection (donate gold) | 2400-4000 gold needed at XL 8; ~1% of arrivals can pay | NONE | no #chat | M, low payoff | gold |

**Reading:** The early wall is mostly 15 small, independent rules (E3, E9, E10, E13, E12, E16 are each a day-sized fix) plus
two real systems: the explorer (E4) and shop/food (E7+E8). It is NOT a case for per-monster patches; E12/E13/E16 are
class-wide rules. Note that survival bugs still cap the funnel: with infinite lives no seed passed Medusa (REWIND-20), so the
early wall can only be declared fixed by the natural-game funnel, not by one rate.

### LATE WALL: missing abilities (the bot has never done these in a natural game)

---

## Capability gap matrix by stage

Difficulty: **L** = a day or less, pure rule; **M** = a few days, new strategy plus tests; **H** = new subsystem, needs staged
harness and iteration; **VH** = unknown unknowns, multi-session. Difficulty is my estimate (MEDIUM confidence).

### Stage 1: Mines, Sokoban, Minetown, Mines' End (rungs 1-6)

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| Solve Sokoban (live solver, flipped maps) | HAVE | `soko_solver/`, `solve_sokoban_strategy` | - | - | 25% reach Sokoban or Mines' End |
| Take Sokoban prize (reflection amulet 50%, else bag of holding) and wear it | HAVE | `prize_pickups`, `accessories.AMULET_RANK` | - | - | prize is the cheapest reflection source |
| Sokoban food (4 `%` items per map in NH5) | PART | gather_items picks food; reachability unmeasured | L | - | |
| Mines' End luckstone | PART | rung detector only (`ladder._mines_end`); luckstone pickup relies on generic gem/gray-stone pickup, `item_priority` has no luckstone rule; kicking-test for loadstone not seen | M | - | Luck matters for prayer and wishes |
| Minetown temple: altar BUC test, sacrifice at co-aligned altar | HAVE | `identify_items_on_altar`, `offer_corpses`, `can_sacrify` | - | altar alignment (neutral) | |
| Excalibur dip | HAVE (useless) | `dip_for_excalibur` | - | - | **Anti-feature in NH5 for a neutral hero**: wastes turns, corpse risk |
| Pick-axe acquisition from hostile dwarves | PART | kills dwarves; keeps only identified non-cursed pick-axe | L-M | E5 | add mattock + auto-ID by name |
| Pet use (let pet kill, keep pet near) | NONE | "bot mostly ignores pet" | H, low payoff | - | unicorn kills by pet are a nice-to-have |

### Stage 2: Mid-game kit, Dlvl 5-20 (rung 7-8, "XL 10-11, AC well below 0")

Targets are the human medians (SURVIVAL-NH5): at Medusa AC -14, XL 13, HP 110; Castle AC -17, XL 14, HP 119.

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| AC to about -10 by Dlvl 15 | PART | see E18-E20 | M-H | scroll ID, supply, altar test | the single largest survival lever by the data |
| Magic resistance | NONE (source) | `wishes.next_wish` asks for GDSM only if a wish happens | - | Castle wand (C2) | cloak of MR is a random find; no pure-bot source before the Castle |
| Reflection | PART | wears amulet/armor if identified (`_reflection_from_armor`, accessories); no Perseus statue visit; wish list has it | M | Sokoban prize 50%, wish | |
| Poison resistance | NONE | `_is_corpse_editable` rejects ALL poisonous corpses (agent.py:1631) so the bot never gains it by eating killer bees / soldier ants | L | decision on 5.0 poison rules (notes: poison no longer instakills in NH5) | ring of poison res worn only if identified |
| Fire resistance | NONE | needed for the Valkyrie Quest (fire ants/giants) | M | corpse policy for fire ants/red molds, quest | |
| Cold res | HAVE (innate for Valkyrie) | - | - | - | |
| Sleep resistance | NONE | Valkyrie has none | M | - | elven mithril/amulet; matters for Gehennom sleep traps |
| Shock res / drain res / free action | PART | rings worn only if identified (`RING_RANK`); orange/black DSM in NH5 give free action/drain res | M | ring ID | |
| Telepathy | HAVE | E15 | - | - | |
| Speed | PART | Valkyrie is intrinsically Fast at XL 7; speed boots only if found/identified | - | - | NH5: wand/potion speed is weaker |
| Unicorn horn: use | HAVE | `use_unicorn_horn`, `apply_unicorn_horn`, sickness path in `emergency_strategy` | - | - | NH5 horn no longer restores attributes |
| Unicorn horn: acquire | NONE | pets kill unicorns; bot should not chase | M | pet management | do not build chase logic |
| Lizard corpse (stoning cure) | HAVE | `is_kept_stoning_cure`, `emergency_strategy` | - | - | |
| Levitation source | PART | use is HAVE (`start_levitation`, `stop_levitation`, `levitating`); a source needs identified ring/boots/potion; unknown rings are never tried | M-H | ring ID by price/engrave test, Perseus statue, wish | the Castle back entry and Medusa crossing both stand on this |
| Digging tool in inventory | PART | E5 | M | - | |
| Wand use: attack wands, engrave-ID | HAVE | `wand_engrave_identify`, `usable_offensive_wand` | - | - | wand of cold (Medusa/Castle) not special-cased |
| Healing reserve policy (NH5 regen is nerfed; "up to 10 full heals on Astral") | PART | keeps healing potions; no stockpile target, no use of bag | M | - | |
| XL 10-14 growth | PART | median XL 7, XL11+ 51/2304, XL14 1/2304 | H | wraiths, gain level, Castle | XL14 plan below |
| Eat wraith corpses at once, quaff gain level at XL>=11 only | NONE | no wraith rule; `wishes.WISH_DEFAULT` asks for gain level potions | L | recognise gain-level potion (price 300) | a jump is worth the whole gap to the next XL threshold |
| Scroll ID (price groups, read-test) | PART | `shop_sell.py`, `scrolls.should_read` | M | shops (E7) | |
| Gold detection (confused) for portals / vibrating square | NONE | no confusion source or scroll logic | M | scroll ID | needed on Planes and for the VS |

### Stage 3: Medusa (Dlvl 21-24) (rung 9)

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| Dig down on arrival (skips water, island, gaze) | PART | `_deep_dig_due`/`_dig_deep` (Dlvl >= 21, pick-axe or wand); `dig_square` refuses squares with water/unknown within 1 (medusa-3 has 0/16 dry squares, medusa-4 6/51) | M | pick-axe, **clear attackers first** | digging under attack never progresses (dig.c:1355); no "kill the swarm first" rule seen in `_dig_down_when_stuck` |
| Cross by levitation (blindfold peek for target, land dry, stop levitating) | PART | `_cross_medusa` + `medusa.py`; requires levitation source AND reflection; staged 4/10 | M-H | levitation source | eels still drown a levitating hero (uhitm.c:3389) |
| Wand of cold / freeze a path | NONE | - | M | wand ID | |
| Reflection or blindfold for her gaze | PART | crossing requires reflection; blindfold in 96% of human ascensions, bot has it in ~15% of eye encounters | M | tool pickup | |
| Fight ravens (map 3) / crowd | PART | telepathy + blindfold route exists (E15); Elbereth fails vs crowds (monmove.c:918); no crowd rule | H | telepathy, healing | |
| Eel/drowning escape | HAVE | `water_holder`, `grip_land`, `grip_elbereth` in `emergency_strategy` | - | - | |
| Stair escape to rest | HAVE (Dlvl>=21) | `combat/stair_escape.py` | - | - | |
| Kill Medusa | NONE | only needed if the dig is impossible or on the return trip | H | reflection or blindfold + telepathy | |
| Return trip up (Castle `<` -> Medusa island -> level above) | PART | `Inventory.rise_one_level` (cursed gain level) written but **no caller**; no walk-to-Castle-upstairs | M | 1-2 cursed potions of gain level (wish) | needed for the Quest and for the final climb |

### Stage 4: Castle and wand of wishing (rung 10)

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| Recognise Castle (drawbridge, mirrored map) | HAVE | `castle.frame`, `_castle_candidate` | - | - | |
| Back entry: float round the moat, land, kick the back door, step on trap door | HAVE | `_pass_castle`, `_castle_breakout`, `castle.py` | - | levitation source | **This route skips the castle interior: no wand, no chest.** Staged 8/20 |
| Break out of the boulder mazes at the Castle | HAVE | `_castle_breakout` | - | pick-axe | |
| Front entry: passtune Mastermind (solver, tune playing) | PART | `passtune.Solver` pure + tested; `Inventory.play_tune` written; **neither is called**; no walk to the bridge, no instrument pickup rule | M | tonal instrument (Minetown/random) | deterministic, best bot-friendly entry per notes |
| Front entry: wand of striking at the bridge | NONE | - | M | striking wand ID | |
| Inside: garrison, throne room, dragons | NONE | - | VH | MR, reflection, AC <= -15 | 17 soldiers + lieutenant, ~27 throne-room monsters, 4 dragons |
| Find the wand chest in a corner tower (burned Elbereth + scare monster scroll) | NONE | - | H | interior fight; do NOT pick up scare monster carelessly | NH5: scare monster no longer works on @ / uniques |
| Pry the wand chest (#force with dagger) | PART | `force_lock_below_me` generic | L | - | |
| Zap wand: wish; answer the prompt | PART | prompt handler fires (`agent.py:535`, `wishes.next_wish`: MR, reflection, levitation, else 2 blessed gain level); no code that zaps it | L | wand ID by position | |
| Wrest the last wish (zap until "You wrest", mean 121 zaps) | NONE | - | L | cleared room | do it BEFORE any recharge decision per notes |
| Recharge once with a found charging scroll | NONE | - | L | scroll ID | 1:1 only, second recharge destroys it |
| Castle wish order (2 blessed gain level -> 2 cursed gain level -> MR) | NONE | current list is the generic fallback | L | wand | |
| Kill eels from shore for XP (+1000 each) | NONE | drowning risk | M | levitation-less eel fight safety | |
| Trap doors to the Valley | HAVE | `_pass_castle` | - | - | |

### Stage 5: Valkyrie Quest and the Bell (between Castle and Gehennom, per the plan)

The Bell of Opening exists only as the Quest artifact reward from Lord Surtur's level; it cannot be wished for. **The Quest is
table stakes for the invocation.** A cheaper bypass exists in NH5 (kill the leader) but costs Luck -4 forever and god anger.

| Capability | Status | Evidence | Difficulty | Depends on |
|-----------|--------|----------|-----------|-----------|
| XL 14 + alignment >= 20 | NONE | median XL 7; XL14 in 1/2304; alignment never logged | VH | wraiths, Castle XP, wished gain-level potions |
| Find the Quest portal, enter, leave | HAVE (just step in/out) | `quest_portal.py`, `portal_hunt`, `leave_quest` | - | portal level message |
| Talk to leader (#chat), accept | NONE | no CHAT command | L-M | XL 14 |
| Quest home/locate/filler levels (fire ants, fire giants, lava on ice) | NONE | - | H | fire resistance, lava avoidance, levitation |
| Kill Lord Surtur (island in lava, drawbridges), take the Bell | NONE | - | H-VH | fire res, ranged damage |
| Return up past Medusa to the Quest portal level | PART | `rise_one_level` unwired | M | cursed potions |

### Stage 6: Valley and Gehennom mazes (rung 11)

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| Know it is Gehennom (dungeon number, hot level, no prayer/Elbereth/sacrifice) | NONE | `Level` class has DOOM/MINES/QUEST/SOKOBAN only; `ladder.py` knows dungeon ids but the agent does not | L | - | prerequisite to many rules |
| No prayer, no Elbereth, no sacrifice, no floor-potion pickup in Gehennom | NONE | E10 | L | G1 | NH5: Gehennom is "hot", potions on the floor break |
| Valley: walk east->west to `>` at far west, locked doors, morgues, temple of Moloch | NONE | explore only | M-H | MR/AC, kicking/#force | hardfloor: cannot dig |
| Dig down through maze/filler levels | PART | `dig_down` works on any diggable floor; `_deep_dig_due` is limited to `DUNGEONS_OF_DOOM`; plan's last milestone has a `TODO` target (`(DoD,100)`) | M | pick-axe/wand of digging, **monsters interrupt** | lair walls undiggable, floor diggable; Wizard's Tower levels and Vibrating Square level not |
| Lava / water / ice / iron-bar mazes (NH5 hellfill: 6 styles) | NONE (7 styles in 5.0 [fact:hellfill-has-seven-styles]) | `digging.WET` includes lava, but path planning for lava/iron bars not checked | M-H | - | new in NH5 |
| Fight Gehennom monsters (minotaurs ignore Elbereth, liches, demons, Pestilence) | NONE | combat heuristics are generic | VH | MR, AC <= -20, HP 150+ | |
| Special lairs: Juiblex swamp, Orcus town (wand of death), Asmodeus, Baalzebub | NONE | all via dig-down | M | MR, dig tool | dig past them where floor allows |
| Fire/poison/sleep/drain protection | NONE | - | M-H | items | |

### Stage 7: Vlad's Tower (rung 12)

| Capability | Status | Evidence | Difficulty | Depends on |
|-----------|--------|----------|-----------|-----------|
| Find the branch (second up stair on Gehennom 9-13) | NONE | `stair_destination` map exists; Gehennom absent | M | dig-down skips levels, so the branch must be found by stairs |
| 3 ladder levels up, kill Vlad (vampire lord, drain res helps) | NONE | - | H | MR/AC, drain res |
| Chests for candles (4-8 wax + 4-8 tallow, need 7), open/force | PART | generic chest code | M | - |
| Take Candelabrum | NONE | - | L | Vlad dead |
| Vlad's throne wish (#sit, acid up to 80 HP) | NONE | no SIT command | M | HP >> 80 |
| Candle fallback: Izchak's lighting shop in Minetown | NONE | no shop buying | M | E7 |

### Stage 8: Wizard's Tower and the Book (rung 13)

| Capability | Status | Evidence | Difficulty | Depends on |
|-----------|--------|----------|-----------|-----------|
| Identify the fake tower with the portal; dig through moat ring with levitation; step on the portal | NONE | - | H | levitation, dig tool |
| Three-level tower (hardfloor, noteleport), ladders | NONE | - | H | - |
| Kill the Wizard (hell hound, vampire lord, krakens) and take the Book | NONE | - | VH | MR, AC, HP |
| Survive the Wizard's harassment afterwards | NONE | - | H | - |

### Stage 9: Invocation and Sanctum (rungs 14-15)

| Capability | Status | Evidence | Difficulty | Depends on |
|-----------|--------|----------|-----------|-----------|
| Reach the bottom, find the vibrating square ("strange vibration"; confused gold detection) | PART | `ladder.py` detects the message only; no search routine | M | G1, scroll logic |
| Invocation sequence on the square (candelabrum lit with 7 candles, ring Bell, read Book; none cursed) | NONE | no APPLY on bell/candelabrum, no spellbook read | L (script) | all three items; remove curse |
| Enter Sanctum, kill high priest of Moloch, take Amulet (NH5: a wish on pickup) | NONE | wish prompt handler exists | H | MR |

### Stage 10: The climb, Elemental Planes, Astral (rungs 15-17)

| Capability | Status | Evidence | Difficulty | Depends on | Notes |
|-----------|--------|----------|-----------|-----------|-------|
| ~45 levels up with the Amulet | PART | `RETURN_TO_SURFACE` walks up known stairs | H | stairs on each level | **dug-down levels have unknown `<`**: each must be explored while the Wizard harasses; Valley/Castle exit needs the stairs path. Inference, MEDIUM |
| Mysterious force (neutral hero is pushed down) | NONE | - | L | - | keep going |
| Medusa's water on the way up | PART | `rise_one_level` unwired | M | cursed gain level (2nd) or levitation | |
| Dlvl 1 up to Plane of Earth; dig through | PART | dig tool used; `Level.PLANE=1000 # TODO` | H | pick/wand, portal search in solid rock | |
| Air (levitate/fly; amulet of flying is new in NH5), Fire (lava, fire res), Water (bubbles) | NONE | - | VH | levitation/flying, fire res | each plane needs its own movement model |
| Astral: find the co-aligned (neutral for this hero) temple, check priest alignment, #offer Amulet | PART | `OFFER` command used for corpses (global_logic.py:1114) | M-H | Riders, Angels, player monsters | co-aligned altar = neutral for `val-hum-fem-neu` |

---

## Feature Landscape (requirements view)

### Table Stakes (needed for any ascension, regardless of method)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Food/pace system: shop buying (E7), permafood reserve (E8), faster early descent (E2), explorer completes levels (E4) | 14.5% starve; NH5 removed death drops; stuck is the dominant starvation path | M-H | E4 needs replays of stuck seeds; E7 is the only brand-new interaction |
| Class-wide safety rules: E9 prayer lockout, E10 no-Gehennom prayer, E12 passive monsters, E13 unicorns, E16 ray bounce, E14 peacefuls | cheap, each removes a few % of deaths | L each | do as ONE "safety rules" phase, tested by scenarios, not per-monster hacks |
| Branch-stair glyph for the Mines (E3) | 24% never enter the Mines | L | 1-file change plus an explorer hook |
| AC growth to about -10 by Dlvl 15 (E18-E19) | the only measured strength gap vs humans; ascenders read enchant armor 3x and wear DSM | M-H | scroll ID plus altar BUC test; cause not fully known |
| A levitation source and a dig tool, reliably | Castle back entry, Medusa crossing, Gehennom descent, Plane of Earth, Wizard's Tower all stand on these two items | M-H | the bot USES both but rarely OWNS them; add ring ID, mattock handling, Perseus statue |
| Reflection and magic resistance | Medusa gaze, Castle wands, Gehennom casters, Sanctum | M | MR realistically only via wish (see differentiators) |
| Wire the existing primitives: `play_tune`/`Solver` (front Castle entry), `rise_one_level` (Medusa return), wish-prompt order | already written and unit-tested, no caller | L-M each | cheapest progress per hour in the whole matrix |
| Gehennom awareness (dungeon id, no prayer/Elbereth/sacrifice) and dig-down loop through mazes | nothing exists past the Castle trap door | M | then Valley walk (M-H) |
| Medusa: dig-down with "clear attackers first" and dry-square choice; crossing as fallback | 0 natural passes; staged hand games show digging under attack never progresses | M-H | needs telepathy + blindfold for map 3 |
| XL 14 plan (Castle XP, wraiths, gain-level potions) and the Quest (leader, Surtur, Bell) | Bell of Opening exists only from the Quest; cannot be wished | VH | single largest unknown after the Castle |
| Vlad's Tower (Candelabrum + 7 candles), Wizard's Tower (Book) | invocation items; cannot be wished | H-VH | |
| Invocation script, Sanctum kill, Amulet | final steps | L (script) + H (priest fight) | |
| The climb, Planes, Astral | final steps | H-VH | Planes need per-plane movement |
| Each late stage testable alone | project requirement | M | staging.py/scenario_run.py exist; add per-stage start kits and success predicates |

### Differentiators (make it much more likely)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Castle interior to the wand of wishing | the only reliable source of MR (GDSM), 2 cursed gain-level potions for the Medusa return/climb, 2 blessed for XL 14; 4-5 wishes in the game (WISHES-NH5) | VH (interior fight) | `_pass_castle` goes AROUND the Castle and forfeits all of this; decide explicitly. A staged tester can use a wizard-mode wish to test the rest regardless |
| Front entry by passtune | deterministic; no levitation needed; lets the bot reach the interior | M | solver and play primitive exist; need walk-to-bridge loop and an instrument |
| Wrest + recharge procedure | +1 to +2 wishes | L | |
| Vlad throne wish | 1 more wish | M | HP floor >80 |
| Excellent AC via protection (priest) and enchant armor | humans: 79% read enchant armor, 31% buy protection | M, gold-limited | buy only if gold allows; do not farm gold |
| Pet kills a unicorn for the horn | status-effect cure | H, low priority | not needed if healing is stocked |
| Stairs-first level sampling ("down then up at once") | MAG-342 tip: learn the level, spawn monsters at lower XL | L-M | |
| Wand of cold / frost horn for water crossing | 78% of human ascenders | M | ID via engrave |
| Stethoscope, bag of holding crisis play | humans apply stethoscope in 14 of 35 crises | L, low value | |

### Anti-Features (do not build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Excalibur dip for the neutral Valkyrie (`dip_for_excalibur`) | impossible in NH5 for non-lawful (fountain.c:404); costs turns and cursed-sword risk | remove from the exploration preempt list |
| Per-monster special-case fixes as the main method | caused last session's whack-a-mole | class-level rules (passive, unicorn, ray, peaceful) with scenario tests |
| Chasing unicorns for a horn | 36 baseline deaths | gems thrown at unicorns (pacify) are optional and cheap if ever needed |
| Elbereth as the main defence | NH5: scared monsters boxed in "panic attack"; no effect on @, minotaurs, shopkeepers; does not work in Gehennom; erased when attacking | stairs retreat, healing, ranged |
| Praying as a food source / prayer-after-failure | first failure ~6.7% per cycle; wrath is death | food system |
| Kill the Quest leader to skip XL 14 | Luck -4 for the rest of the game, god anger, guardians hostile; wishes come out cursed | last resort only, do all wishing first |
| Rewind, reseed, staged starts counted as the ascension | project definition | test tools only |
| Learning/LLM in the loop for tactical decisions | breaks determinism and A/A bench comparisons | LLM offline as analyst (decided by research, outside this file) |
| Full spellcasting | Valkyrie has none; code for healers is commented out | skip |
| Wishing for a scroll of charging | spends the wish it returns | wish for the end item |
| Sacrifice-for-gift weapon plan, pet-herding systems | long payoff, many dependencies | use the spear/dagger; take what is found |

## Feature Dependencies

```
Gehennom awareness (G1) ──requires──> Level/dungeon ids in Agent
    └──enables──> no-prayer / no-Elbereth rules, dig-down loop, Valley walk, Vlad branch finding

Levitation source ──requires──> ring/boots ID (price, engrave), or wish, or Perseus boots
    ├──enables──> Medusa crossing (also needs reflection, blindfold)
    ├──enables──> Castle back entry
    ├──enables──> Wizard's Tower moat, Planes of Air/Fire, Quest lava
Dig tool ──requires──> pick-axe (hostile dwarves) or wand of digging (chests)
    ├──enables──> stuck escape, Medusa skip, Gehennom descent, Plane of Earth, castle boulder breakout
Telepathy (HAVE) + blindfold ──enables──> Medusa ravens, Medusa herself

Castle interior ──requires──> MR + reflection + AC <= -15 + HP ~120 (fight 17 soldiers, throne room, dragons)
    └──yields──> wand of wishing (1 charge + wrest + recharge) + chest potion of gain level
        ├──wish 1: blessed gain level x2 (XL 14) or MR
        ├──wish 2: cursed gain level x2 (Medusa return + final climb)
        └──wish 3 (found charging scroll): MR before Gehennom
MR without the wand ──requires──> cloak of MR (random) -- not plannable

Quest ──requires──> XL 14 + alignment 20 ──requires──> Castle XP + gain level
    ├──requires──> fire resistance + lava handling
    └──yields──> Bell of Opening (needed for invocation, cannot be wished)
Medusa return up ──requires──> cursed gain level (or levitation + reflection/blindfold)

Vlad (Candelabrum) + Wizard (Book) + Quest (Bell) ──require──> Gehennom survival (MR, AC)
Invocation ──requires──> all three items + 7 candles + vibrating square + none cursed
Sanctum/Amulet ──requires──> Invocation + MR
Climb + Planes + Astral ──requires──> Amulet + cursed gain level or levitation + dig tool + fire res + levitation/flying

Early wall fixes (food, safety, explorer) ──gate──> every natural-game measurement of the above
```

### Dependency Notes

- **Every late stage after Medusa assumes MR.** No bot code or plan obtains MR without the Castle wand or a random cloak.
  The cheapest honest answer is: either build the Castle interior fight (VH) or accept that Gehennom survival is a coin flip.
  This is the core requirements decision for the Castle phase.
- **Digging skips levels, which hurts the climb**: stairs on dug-through levels are unknown. Either remember where the
  hero arrived and search for `<` on the way up, or prefer stairs where cheap.
- **Items that cannot be wished for** (Bell, Candelabrum, Book) force three independent boss fights (Surtur, Vlad, Wizard).
  They are table stakes, not options.
- **Gehennom potions break on the floor** in NH5: do not plan to pick up potions there.

## NetHack 5.0 specifics that change the plan (from the existing notes)

| Topic | NH5 rule | Effect on the bot |
|-------|----------|-------------------|
| Food | monsters no longer death-drop comestibles; Mines branch level has one filling item; supply chests above the Oracle (2/3 chance); Sokoban maps place 4 random food items | corpses and placed food are the supply; early pace matters |
| Poison | poison no longer instakills (ASCENSION-PLAN) | the `M1_POIS` corpse ban is overcautious; the bot is missing a free resistance |
| Wand of wishing | 1 charge, recharge only to 1:1; Castle chest also has a potion of gain level | 2 reliable wishes (charge + wrest), 3 with a found charging scroll |
| Amulet of Yendor | grants a wish when picked up | wish for levitation or life saving |
| Quest | killing the leader opens the Quest (`killed_leader`) | last-resort bypass, Luck -4 permanently |
| Valkyrie | no starting long sword; Excalibur lawful only | do not dip; weapon is the +1 spear/dagger |
| Branch stairs | own glyph (`S_brdnstair`) | bot currently maps it to plain stairs |
| Elbereth | does not work in Gehennom/Planes; attacking from it erases it; boxed-in monsters attack anyway | not a Castle/Medusa/Gehennom defence |
| Scare monster scroll | no longer works on @ humans or uniques | Castle chest scroll is not a Castle guard against soldiers |
| Gehennom | "hot" (floor potions break); new hellfill styles (lava/water/ice/bars) | movement/pathing risk, new |
| Healing | natural regen nerfed at high levels, more potions of healing early | stock healing, carry for Astral |
| DSM colours | orange +free action, yellow +stoning, black +drain res; gold DSM new | a shiny wish can add a second resistance later |
| Speed | potion/wand speed weaker; speed boots matter | |
| Amulet of flying | new; replaces levitation on Plane of Air | wish alternative |
| Unicorn horn | no longer restores attributes | fine for the bot |
| Digging | hole in a Medusa square next to water fills with water (dig.c:606); dig under attack never progresses (dig.c:1355) | `dig_square` already checks water; add "no attackers" |
| Gains | `pluslvl(FALSE)` sets XP to the new threshold: a gain level at XL 13 is worth 40,000 XP | drink late |
| Levitation | '>' does not work while levitating; no kicking doors while levitating; eels still drown | already encoded in medusa.py/castle.py |

## MVP Definition (recommended phase structure for requirements)

Recommended ordering, with reasons. "Table stakes first, wire what exists, then the unknowns."

### Phase A: Foundation and early wall (must come first)
- [ ] Fresh natural-game baseline plus per-stage funnel (project requirement)
- [ ] Food/pace: E2, E3, E4, E7, E8
- [ ] Safety rules as one class-level set: E9, E10, E12, E13, E14, E16, E17
- [ ] Gehennom awareness (G1) as an early cheap enabler (dungeon id; used later)
- [ ] Refactor agent.py/global_logic.py to a testable shape before the late-game modules land

### Phase B: Mid-game strength
- [ ] AC growth (scroll ID, altar BUC, enchant armor, gloves/body armor), levitation source and ring ID, dig tool upkeep (mattock)
- [ ] Poison/fire resistance corpse policy, wraith rule, gain-level discipline
- [ ] Reach Medusa in a measurable share of natural games (target: a funnel bar, not a guess)

### Phase C: Medusa and Castle
- [ ] Medusa dig-down with attacker-clearing and dry-square choice; crossing fallback; Medusa return via `rise_one_level` wired
- [ ] Castle decision: back-entry only (cheap) vs front entry + interior + wishes (the real MR source); wire passtune and play_tune
- [ ] Wand zap/wrest/recharge procedure and Castle wish order (can be staged-tested in wizard mode)

### Phase D: Quest and Gehennom
- [ ] XL 14 plan (Castle XP + potions) and the Valkyrie Quest to the Bell
- [ ] Gehennom descent loop, Valley walk, lava/water/iron-bar mazes
- [ ] Vlad's Tower, Wizard's Tower

### Phase E: Endgame
- [ ] Invocation script, Sanctum, climb, Planes, Astral offer

### Defer
- Pet management, unicorn horn acquisition, protection racket, Vlad throne wish, wand of cold crossing, stethoscope/crisis tools, Excalibur (never).

## Research flags for phases

| Phase | Needs deeper phase-specific research? | Why |
|-------|----------------------------------------|-----|
| A | No for E3/E9/E10/E12/E13/E16; yes for E4 (explorer stuck replays) | data exists; explorer cause not found |
| B | Yes for AC cause | AC-GAP correction left the cause open |
| C Medusa | Yes | staged only; crossing 4/10; attack-clearing rule untested |
| C Castle | Yes | interior fight and wish order never tried; Elbereth-ignorer bug open in CONCERNS.md |
| D Quest | Yes | no code; XL 14 is the largest unmeasured step |
| D Gehennom/Vlad/Wizard | Yes | no code; NH5 hellfill levels new |
| E | Partial | Planes movement models need per-plane study |

## Sources

- `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md`
- `.planning/research/`: ASCENSION-ROUTE-AUDIT (3.6 level data), ASCENSION-PLAN-NH5, ASCENSION-PLAYBOOK-NH5, ASCENSION-KIT-NH5,
  MEDUSA-NH5, MEDUSA-RETURN-NH5, WISHES-NH5, XL14-NH5, FOOD-NH5, PRAYER-NH5, SURVIVAL-NH5, AC-GAP-NH5, TELEPATHY-NH5,
  STRENGTH-PER-DEPTH, MINES-ENTRY-NH5, LADDER-NH5, REWIND-20, GUIDE-MAG-R342; `.planning/hand-games/`
- Bot code verified on `main` (fb5faa2): `autoascend/agent.py`, `global_logic.py`, `castle.py`, `medusa.py`, `digging.py`,
  `passtune.py`, `ladder.py`, `plans.py`, `item/{inventory,wishes,scrolls,accessories}.py`, `combat/*`, `glyph/nh5.py`, `level.py`
- NetHack 5.0 source claims are as cited in those notes (dig.c, pray.c, monmove.c, uhitm.c, objnam.c ...); not re-checked here
- Confidence flags: bot-status statements HIGH (code read); difficulty ratings MEDIUM (my estimate); rates quoted from archived bench runs MEDIUM (live DB empty)
