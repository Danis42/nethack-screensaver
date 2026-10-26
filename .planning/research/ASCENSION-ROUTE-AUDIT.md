# Ascension route audit: every mandatory level vs. the bot (2026-10-26)

Source: NetHack 3.6.6 `dat/*.des` (level layouts) and `dungeon.def`, checked against `src/` where the rule lives.
Read directly (not summarised by the local model). Bot state: grep of `autoascend/` at main 88f4a54.

## Route (dungeon.def)
Dungeons of Doom 25-29 levels: Mines branch Dlvl 2-4, Oracle 5-9, Sokoban entrance = level above Oracle,
Big Room 10-12 (40%), Quest portal Oracle+6..+7, Ludios portal (vault, optional) 18-21, Medusa = Castle-1..-4,
Castle = bottom. Gehennom 20-24 levels: Valley (1st), Juiblex 4-7, Baalzebub 6-9, Asmodeus 2-7, Orcus 10-15,
Wizard's Tower 11-16 (3 levels), fake towers 3-6 levels above the bottom, Vlad's Tower branch 9-13 (up),
vibrating square = level above the Sanctum, Sanctum = bottom. Then up to Dlvl 1 and the Planes:
Earth, Air, Fire, Water, Astral.

## Dig-down map (dungeon.c Can_dig_down: not hardfloor, not the bottom level, not the invocation level)
| Level | Dig down? | Teleport? | Note |
|---|---|---|---|
| ordinary DoD levels, Oracle, Big Room, Quest filler, Mines | yes | yes | |
| Sokoban | no (hardfloor on 2 of 4, and digging breaks the puzzle rules) | no | |
| Medusa (all 4 variants) | **yes** | no | digging down on the arrival side skips the water AND Medusa |
| Castle | **no** (bottom level) | no | only exits down: 5 trap doors inside, at (40..55, 8) |
| Valley | no (hardfloor) | no | walk to the downstairs in the far top-left corner |
| Gehennom mazes, Juiblex, Orcus, Asmodeus, Baalzebub | **yes** | no in lairs | lair walls undiggable, floor diggable |
| Wizard's Tower levels | no (hardfloor) | no | |
| Vibrating square level | no | | |
| Sanctum, Vlad's Tower, all Planes | no | no | |

**Conclusion 1: a pick-axe / dwarvish mattock is the most valuable single item for this route.** It skips
Medusa, speeds up every DoD and Gehennom maze level, digs out of dead ends (the stuck/starve chain), and is
*mandatory* on the Plane of Earth (solid rock, portal at a random spot outside the arrival corner). A dwarvish
Valkyrie gets one from the Mines dwarves almost for free. The bot only uses a pick-axe for one narrow case
(`global_logic.py` ~443, before Sokoban); it never digs down or through.

## Level by level

### Medusa (`medusa.des`, 4 variants, noteleport)
- Arrive on the west edge; downstairs on Medusa's island, which is walled and partly undiggable around the stairs.
- Water everywhere: giant eels / electric eels (drowning grab = instadeath), krakens (var. 4), jellyfish.
- Medusa's gaze stones you unless blind (blindfold/towel) or reflecting (then she is stoned herself).
- Perseus statue: shield of reflection 75% (var. 1, 3, 4) / 25% (var. 2), levitation boots 25% / 75%.
- Variant 2: titan; variant 3: 30 hostile ravens (blinding), nymphs; variant 4: yellow dragon, nagas.
- **Bot: nothing.** Cheapest crossing for this bot: dig down right after arrival (needs pick-axe), which needs no
  gaze protection and no water handling. Fallbacks: levitation (boots/ring/potion), wand of cold over water.

### Castle (`castle.des`, noteleport, no downstairs, undiggable)
- Moat all round (giant eels, sharks); drawbridge on the west side, closed.
- Ways in: play the passtune (learned by Mastermind with any tonal instrument at the drawbridge, or from a
  prayer boon); **zap a wand of striking / force bolt at the drawbridge = destroyed** (zap.c ~3315), wand of
  opening / knock opens it; or levitate over the moat to the east back door (56,8, locked).
- Inside: barracks (17 soldiers + lieutenant), throne room with ~27 L/N/E/H/M/O/R/T/X/Z monsters, 4 dragons,
  storerooms of armour/weapons/gems/food.
- Wand of wishing in a chest in one of the 4 corner towers, on a burned Elbereth + cursed scare monster scroll.
- Exit down only by the 5 trap doors in the east corridor at row 8.
- **Bot: nothing** (drawbridge only appears in the ladder detector; "wishing strategy" is a TODO in agent.py:467).

### Valkyrie Quest (`Valkyrie.des`; needs XL 14 and lawful standing)
- Home: Norn + 8 warriors; lava pools on the ice; 10 fire ants, 2 fire giants (one ON the downstairs), fire traps.
- Locate: 9 giants. Filler: fire ants, fire giants. Goal: Lord Surtur on an island inside lava, reached by two
  drawbridges (north one open 75%), 12 fire giants, the Orb of Fate.
- Needs: fire resistance (fire giant corpses can grant it), no stepping into lava, cold resistance is innate.
- Lord Surtur carries the Bell of Opening.
- **Bot: quest portal entry exists (exp 14); nothing for the leader talk or the levels.**

### Valley (`gehennom.des`, noteleport, hardfloor)
- Arrive on the east side (falling through a Castle trap door lands in (58..72, 9..18)); downstairs at (1,1),
  behind locked doors at the far west. 3 morgues (wraiths, ghosts, vampire bats), temple of Moloch with a priest.
- **Praying anywhere in Gehennom never helps and usually angers the god** (pray.c 1902). The bot's emergency
  prayer (`agent.py` prayer_trouble) must be switched off in Gehennom.

### Gehennom lairs
- Juiblex: swamp, Juiblex in the middle; up/down stairs at opposite edges. Orcus: town with undead, Orcus on the
  downstairs with a wand of death. Asmodeus/Baalzebub: walled lairs, stairs inside; both dig-down-able.

### Wizard's Tower (`yendor.des`)
- Three levels, hardfloor, noteleport; tower walls undiggable and no-passwall. The **only way in is the magic
  portal in the centre of `fakewiz1`** (a 3x3 room inside a moat ring), which leads into `wizard3`; ladders up
  to `wizard1`, where the Wizard sleeps on the Book of the Dead with a hell hound and a vampire lord, in a ring of
  water with krakens and eels. Needs a way over 2 squares of water (levitation / water walking / freezing).

### Vlad's Tower (`tower.des`, up from a Gehennom level)
- 3 levels, ladders. Vlad holds the Candelabrum. Chests: 4..8 wax + 4..8 tallow candles (enough for 7),
  an amulet of life saving, water walking boots, crystal plate mail, invisibility.

### Invocation (spell.c deadbook, apply.c)
- On the vibrating square, not on stairs: ring the Bell, then read the Book within 5 turns, with the Candelabrum
  holding 7 candles and lit; none of the three cursed (the Book must not be cursed). Then the stairs to the
  Sanctum appear. The bot has rung detection only (`ladder.py` vibration_level).

### Sanctum
- High priest of Moloch holds the Amulet; temple with many minions. Hardfloor, noteleport.

### Planes (`endgame.des`, all noteleport, hardfloor)
- Earth: solid rock, arrive at (69,16); portal at a random spot elsewhere -> must dig (or wand of digging).
- Air: portal on the east side (57..78); clouds, air elementals. Fire: lava, fire traps, portal random.
- Water: air bubbles move; portal on the east side (51..75); eels.
- Astral: arrive bottom centre; three temples, one per alignment, at random; find the lawful altar, enter, #offer
  the Amulet. Angels, Riders, player monsters.

## What is missing in the roadmap (to fold into phases 3-8)
1. **Phase 3 kit**: add pick-axe/mattock (keep from Mines dwarves) + a dig command (down, sideways); wand of
   striking kept for the drawbridge; blindfold/towel; candles from Izchak's shop as a fallback.
2. **Phase 4 Medusa**: primary plan = dig down on arrival (no gaze, no water); crossing is only the fallback.
3. **Phase 5 Castle**: getting in = striking/force bolt at the drawbridge (or opening); exit = trap doors on row 8.
4. **Phase 7 Gehennom**: no prayer in Gehennom; dig down through mazes; fake-tower portal for the Wizard's Tower;
   the exact invocation order above.
5. **Phase 8 Planes**: digging is mandatory on Earth.
6. **Now (Phase 2)**: digging also attacks the current main killer, starvation on stuck levels: a bot that can dig
   down is never stuck. Candidate experiment: keep a pick-axe from the Mines and dig down when stuck.
