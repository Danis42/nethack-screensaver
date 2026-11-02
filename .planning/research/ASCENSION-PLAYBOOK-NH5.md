# Ascension playbook: human Valkyrie, NetHack 5.0, pilgrim route (2026-11-02)

The whole route from turn 1 to Astral, stage by stage, as rules that a bot (or Claude playing by hand) can follow.
Written before Part 1b-1g of Phase 02.2 so the code is built against it. Built from: ASCENSION-PLAN-NH5.md (route and
keystone items), WISHES-NH5.md, XL14-NH5.md, MEDUSA-RETURN-NH5.md, FOOD-NH5.md, PRAYER-NH5.md, MINES-ENTRY-NH5.md,
STRENGTH-PER-DEPTH.md, AC-GAP-NH5.md, REWIND-20.md, the NetHack 5.0.0 source and the local wiki.

How to read it: each stage has a goal, the condition to start it, the rules, the condition to leave it, and the bot's
status today (HAVE = in main, BUILT = on a branch and staged-tested, MISSING). Numbers marked (data) come from bench
games or human ascensions; numbers marked (start value) are first guesses to be replaced by measured stage requirements
(owner rule: no guessed thresholds survive measurement).

Character: val-hum-fem-neu (experiment 37). Neutral, so the god is **Odin** and co-aligned altars are neutral. Human, so
Mines gnomes, dwarves and hobbits are hostile: fights in the Mines, but dwarves' pick-axes are free to take.

---

## 0. Rules for the whole game

### Food (top killer: starvation was 25% of games before exp 37)
- NetHack 5 removed food death drops: food comes from corpses, placed food, Sokoban, shops (FOOD-NH5.md).
- Eat fresh safe corpses whenever not Satiated; beat the pet to them. Lizard corpses are medicine, never food. HAVE.
- Keep 2 permanent food items (rations, lembas, cram, tins); buy them in Minetown when short. MISSING.
- Ring of slow digestion: wear it as soon as it is identified. BUILT (1a).
- Pray for hunger only when Weak and the prayer timeout is safe (about 1000 turns since the last one). HAVE.

### Prayer (PRAYER-NH5.md)
- Safe only with Luck >= 0, god not angry, timeout low. Fixes: HP < 1/7 (or < 6), Weak, stoning, sliming, strangling,
  food poisoning, illness, lava. HAVE (HP, hunger, deadly conditions).
- After a failed prayer ("You feel that Odin is displeased" / "Thou hast angered me"): no prayer until a sacrifice at
  a neutral altar brings reconciliation. MISSING (demoted on the bench: it relabels deaths, the cure is food).
- Never pray in Gehennom (Moloch answers). MISSING.

### Escape and emergency order (each turn, first match wins)
1. Stoning: eat a lizard or acidic corpse, else pray. HAVE.
2. Sickness: unicorn horn (up to 3 applies), else pray. BUILT (1a).
3. HP < 1/3: quaff healing; then Elbereth (not in Gehennom, not vs @ humans and minotaurs); then pray if safe;
   then flee upstairs. HAVE (partly; stairs escape is crude).
4. Confusion, stun, hallucination, blindness: unicorn horn, else wait it out away from monsters. BUILT (1a).

### Items (Part 1a, BUILT on feat/item-skills)
- Wear: armour by AC plus property (MR +10, reflection +8, speed +5); identified harmless rings and amulets by rank.
- Read: known enchant armour (all worn pieces +3 or less), enchant weapon (below +5), remove curse (something worn is
  cursed), identify (rings and amulets first). Unknown scrolls only when every price-group identity is safe.
- Never wear: levitation boots (except by the levitation skill), fumble boots, gauntlets of fumbling, helm of opposite
  alignment, dunce cap; never put on unknown rings or amulets.
- Note (2026-11-02): the bot treats unknown-B/U/C items as uncursed, so it can put on cursed armour. Altar-test at
  Minetown before wearing new armour once that rule exists. MISSING.

### Things never to do (from deaths on the bench)
- Melee floating eyes (HAVE: exp 21), cockatrices bare-handed or chickatrice corpses; eat cockatrice, Medusa, Green-slime.
- Attack peacefuls, kick shop signs, or anger shopkeepers (exp 27). Enter shops below XL 8 while mimics are a risk
  (exp 35, HAVE).
- Chase unicorns (36 baseline deaths).
- Read unknown scrolls in Sokoban (earth) or while confused.

---

## Stage 1. Dlvl 1-4 and the way into the Mines (rungs 1-2)

- Goal: reach the Mines with HP and food; pick up everything light.
- Rules: leave Dlvl 1 once explored (BE_ON_FIRST_LEVEL); Sokoban first for humans (exp 37, plan_for), but take the
  Mines stairs when found on the way (exp 39 mines-detour, HAVE). Pry locked supply chests with the dagger (BUILT 1a).
- Pace yardstick (data): human ascenders enter the Mines at T1173; the bot at about T2900.
- Leave when: Sokoban entrance level (Oracle-1) reached, or the Mines are found.
- Status: HAVE. Known gap: early pace (exp 30/31/33/36 all made the bot faster but weaker; dropped).

## Stage 2. Sokoban (rung 3-4)

- Goal: the prize (amulet of reflection 50%, else bag of holding) and the food on the four levels.
- Start when: the Oracle level is passed and the up branch is known. Human advice: XL 9-10, HP 40+, unburdened.
- Rules: live solver (HAVE); never read scrolls here; fight from the corridor; take all food.
- Leave when: the prize is taken or Sokoban is stuck for 2500 turns (stuck watch, HAVE).
- Status: HAVE. Prize pick-up and wear: HAVE (wear amulet: BUILT 1a).

## Stage 3. Gnomish Mines, Minetown, Mines' End (rungs 2, 5, 6)

- Goal: pick-axe (kill a dwarf: hostile to humans), Minetown shopping (food, protection if gold allows), luckstone.
- Rules: in Minetown buy permafood first; donate 400 x XL gold to the priest for protection only when gold allows
  (data: Minetown gold median 121 at XL 8, protection costs 2400-4000: about 1% can pay); sacrifice fresh corpses at a
  neutral altar if the temple is neutral; altar-test armour. Mines' End: pick up the luckstone at the marked spot (HAVE,
  exact rung). Keep the luckstone forever (Luck 3+ makes prayer and wishes safe).
- Leave when: luckstone held, or Mines' End stuck.
- Status: HAVE except shopping for food, protection, altar-testing (MISSING).

## Stage 4. Main dungeon to Medusa (Dlvl 5-20, rungs 7-8)

- Goal: XL 10-11, AC well below 0, resistances, wands, levitation/reflection sources.
- Yardstick (data, human ascensions): Dlvl 10 at XL 8.5, AC -6, max HP 70; Dlvl 14 at XL 11, AC -9.
  Bot: XL and HP match to Dlvl 12, AC stops at -3 (cause open: see AC-GAP-NH5.md correction).
- Rules:
  - Eat wraith corpses at once (a level each). MISSING.
  - Eat corpses that give resistances when HP allows: killer bees, scorpions (poison), fire ants, red molds (fire),
    floating eyes after a ranged kill (telepathy). MISSING.
  - Engrave-ID wands (HAVE); zap attack wands in fights (HAVE); keep digging (pick-axe, wand of digging).
  - Quaff known gain level only at XL >= 11 (a jump is worth the gap). MISSING.
  - Stuck level: dig down with the pick-axe (exp 23 code, BUILT on feat/medusa).
- Leave when: Dlvl 21 reached (Medusa is Dlvl 21-24).
- Status: partly HAVE; AC growth is the gap.

## Stage 5. Medusa (Dlvl 21-24)

- Going down: do not explore. From Dlvl 21 dig down on arrival (no hardfloor on any of the 4 maps); the Castle floor
  is undiggable, so the dig stops there. BUILT (track-b: 7 of 12 staged games reached the Castle level; now also for
  the pilgrim's GO_DOWN on feat/medusa). If digging is impossible: levitate across (ring/boots) with reflection or a
  blindfold on, kill Medusa only with reflection. Levitation primitives BUILT (1a), crossing route MISSING.
- Coming back up (to reach the Quest, and later with the Amulet): from the Castle take its up stairs to Medusa's down
  stairs, blindfold on unless reflection, quaff a cursed potion of gain level: the hero rises to the level above with no
  water to cross. BUILT (rise_one_level, self-test 4/4). Alternative: confused or cursed scroll of teleportation
  (random, fails with the Amulet).
- Status: staged medusa batch (12 seeds) pending on feat/medusa.

## Stage 6. Castle

- Goal: inside, the wand of wishing and the potion of gain level from the chest, XP from the garrison and eels,
  then the trap doors to the Valley.
- Entry: stand next to the drawbridge, play 5-note tunes on any tonal instrument (flute, horn, harp, bugle) and solve
  the Mastermind from "N tumblers click and M gears turn" (5.3 tries on average, 7 at most). The right tune opens the
  bridge. Solver BUILT (passtune.py), tune playing BUILT (play_tune), walking to the bridge and the loop MISSING.
  Fallbacks: wand of striking/force bolt at the drawbridge, or levitate over the moat to the back.
- Inside: kill soldiers in the corridors one at a time (they carry wands: reflection matters). Eels in the moat: never
  stand next to water without levitation or magical breathing (drowning). Each eel kill is about +1000 XP.
- Wand chest: locked, untrapped; pry it (BUILT 1a: 11/12, two tries; give the Castle more tries).
- Wishes (WISHES-NH5.md): engrave-test is NOT needed (the chest wand is known by position). Zap once: wish; recharge
  with a found scroll of charging BEFORE wresting; then zap the empty wand until it wrests (mean 121 zaps).
  Castle wish order: 1) "2 blessed potions of gain level" if below XL 13, else magic resistance;
  2) "2 cursed potions of gain level" (Medusa return + the Amulet climb). Today's bot list (MR, reflection, levitation,
  gain level) is the general fallback (BUILT 1a); the Castle order is MISSING.
- Leave when: wand used up, chest emptied. Down: the trap doors at the back (row 8) lead to the Valley.
- Status: mostly MISSING.

## Stage 7. XL 14 and the Valkyrie Quest

- Requirement: XL 14 (80,000 XP) and alignment record >= 20 to be let through by the leader (quest.h). Without it the
  home level blocks stairs, holes and digging. Route: Castle before Quest (XL14-NH5.md): garrison + eels + chest potion
  + wished potions; one natural level or a wraith gives the margin.
- Way there: back past Medusa (Stage 5 return), up to the Quest portal level (Dlvl 11-16; "You receive a faint
  telepathic message" on arrival). Portal hunt HAVE (quest_portal.py).
- Quest: home level has fire ants and fire giants; get fire resistance first: eat their corpses (eat.c should_givit:
  chance = monster level / 15, so fire ant 3/15 = 20%, fire giant 9/15 = 60%; giants also give strength), or a ring of
  fire resistance once identified. Lava everywhere: never step on lava; levitate across lava
  levels. Lord Surtur: fight from range or in a corridor; take the Bell of Opening (and the Orb of Fate, a luck item).
- Last resort if XL 14 cannot be reached: kill the leader (new in 5.0: opens the Quest), costs Luck -4 for the rest of
  the game and god anger: do all wishing and praying before.
- Status: MISSING (portal hunt only).

## Stage 8. Valley and Gehennom (Gehennom levels 1 to about 24)

- Hard rules in Gehennom: no prayer (Moloch), no Elbereth (does not work vs minotaurs, @ humans, shopkeepers anyway),
  no sacrifice. Potions on the floor break (Gehennom is "hot").
- Need: magic resistance (wish), reflection, fire resistance, poison resistance, free action helps.
- Travel: dig down through maze and filler levels (diggable except special levels); avoid lava, ice and iron-bar
  mazes (new 5.0 filler styles). Minotaurs in mazes: fight only at full HP, or dig away.
- Vlad's Tower (up stairs from a Gehennom level 9-13): kill Vlad, take the Candelabrum; the 7 candles in the closet
  chests (Vlad's water walking boots are guaranteed there). Vlad's throne: #sit for a wish (1/3 effect per sit, wish
  4/13; acid up to 80 HP: sit only with HP well above 80).
- Wizard's Tower: find the real tower (the portal is in a fake tower: dig into its moat ring with levitation);
  kill the Wizard on the top floor, take the Book of the Dead. Expect him to return and harass from then on.
- Vibrating square: on the bottom level ("You feel a strange vibration under your feet"); confused gold detection
  shows it as a trap.
- Status: MISSING.

## Stage 9. Invocation and Sanctum

- On the vibrating square, in this order: light the Candelabrum with 7 candles attached, ring the Bell, read the Book
  (none of the three cursed: remove curse first). The stairs to the Sanctum appear.
- Sanctum: kill the high priest of Moloch (MR needed), pick up the Amulet (5.0: a wish when picked up: levitation
  if not held, else life saving). Leave at once.
- Status: MISSING.

## Stage 10. The climb

- About 45 levels up. Mysterious force: a neutral hero with the Amulet is sometimes sent down on going up; keep going.
  No level teleport with the Amulet. The Wizard of Yendor harasses: stay healed, fight on stairs.
- Medusa's water again: arrive on her island going up; second cursed potion of gain level, or levitate with
  reflection/blindfold.
- Dlvl 1 up stairs with the Amulet: the Plane of Earth.
- Status: MISSING (rise_one_level BUILT).

## Stage 11. Elemental Planes and Astral

- Earth: dig through (pick-axe/wand of digging). Air: levitate or fly (amulet of flying new in 5.0). Fire: levitate
  over lava, fire resistance. Water: drift with the air bubbles to the portal.
- Portals: confused scroll of gold detection shows them as traps.
- Astral: find the neutral temple (check the priest's alignment by #chat or looking), enter, #offer the Amulet.
  Avoid the Riders.
- Status: MISSING.

---

## Keystone items, in the order they are needed

| Item | First needed | Main source | Status of the skill |
|---|---|---|---|
| Food reserve (2 permafood) | from T3000 | Sokoban, Minetown shops, corpses | partly HAVE |
| Pick-axe | stuck levels, Medusa | hostile dwarves in the Mines | HAVE (keep), dig BUILT |
| Luckstone | prayer and wish safety | Mines' End | HAVE |
| Reflection | Medusa, Castle soldiers | Sokoban amulet 50%, Perseus shield, wish | wear BUILT |
| Unicorn horn | ailments | a pet kills a unicorn | apply BUILT |
| Tonal instrument | Castle drawbridge | Minetown shops, random tools | play BUILT, solve BUILT |
| Blindfold/towel | Medusa without reflection | random tools | rise BUILT |
| Levitation | Medusa crossing, Quest lava, Planes | Perseus boots, ring, wish, Amulet wish | on/off BUILT |
| Cursed potions of gain level (2) | back past Medusa, climb | Castle wish | rise BUILT |
| Magic resistance | Gehennom, Sanctum | Castle wish (gray dragon scale mail) | wish BUILT |
| Bell, Candelabrum + 7 candles, Book | invocation | Quest, Vlad, Wizard | MISSING |

## Order of building (Phase 02.2 Part 1)

1a items: BUILT (bench no-harm check job 73 pending). 1b Medusa: dig down BUILT, return BUILT, crossing by levitation
MISSING, staged batch pending. 1c Castle: solver and tune BUILT, drawbridge loop, chest, wishes, trap doors MISSING.
1d XL 14 and Quest. 1e Gehennom. 1f climb and Planes. 1g one pilgrim plan in autoascend/plans.py.

## For a game played by hand (owner, 2026-11-02: hand-played games planned)

Use this file as the checklist: at each stage write down the stage requirement as found (XL, AC, HP, key items), what
killed or nearly killed the hero, and which rule above was wrong or missing. Those notes become the stage requirements
and the next bot rules.
