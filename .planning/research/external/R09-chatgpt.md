# R09 Medusa's Island in 5.0 (B)

## Summary

- **There are four 5.0 map scripts**, and the level is a no-teleport, water-crossing level. The chosen map can be mirrored, so hard-coded screen coordinates must be normalized against the observed map rather than assumed from the script. [5.0 `dat/medusa-1.lua`–`medusa-4.lua`](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat) [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp)
- **Maps 3 and 4 randomize the Medusa/downstairs/Perseus-statue location among candidate rooms.** In 5.0 the statue is placed on the same selected square as Medusa and the downstairs; the script explains that this prevents object detection from trivially revealing the stairs. [5.0 `dat/medusa-3.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-3.lua#L32-L45) [5.0 `dat/medusa-4.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-4.lua#L34-L49)
- **Most reliable crossings:** levitation or water walking. A wand of cold is a useful fallback; boulders/earth are less reliable and can trap the hero; digging down is an emergency bypass, not a normal crossing strategy. [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp)
- **Reflection is the best way to kill Medusa if she sees her own reflected gaze.** A blindfold protects the hero from her gaze but does not itself kill her. Cockatrice corpses are not a valid stoning shortcut because Medusa is stone-resistant. [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [5.0 `include/monsters.h`, Medusa definition](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h)
- The 5.0 map-3 script demonstrably changes the Perseus-statue placement compared with the 3.6.7 `.des` layout. Map 4's exact 3.6.7-to-5.0 coordinate diff is UNVERIFIED; do not use old statue-location heuristics without checking the version. [3.6.7 `dat/medusa.des`](https://github.com/NetHack/NetHack/blob/NetHack-3.6.7_Released/dat/medusa.des) [5.0 `dat/medusa-3.lua` and `medusa-4.lua`](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat)

## Facts

### Level-wide properties

| Claim | Source | Version | Confidence |
|---|---|---:|---|
| Medusa's level is one to four levels above the Castle. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) | Current Wiki; exact tagged version unspecified | medium |
| There are four alternate map scripts: `medusa-1.lua`, `medusa-2.lua`, `medusa-3.lua`, and `medusa-4.lua`. | [5.0 `dat/medusa-1.lua`–`medusa-4.lua`](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat) | 5.0.0 | high |
| The scripts mark Medusa's level as a maze/no-teleport environment; floor digging is possible according to the level's flag setup and Wiki guidance. | [5.0 Medusa map scripts](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat) [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) | 5.0.0 / current Wiki | medium |
| Screen coordinates in the scripts are not safe universal coordinates for a bot because the map can be flipped/mirrored by level-generation handling. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) [5.0 level scripts](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat) | 5.0.0 / current Wiki | medium |
| Medusa is a unique monster with a stoning gaze; reflection can return her own gaze to her. | [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) | Current Wiki; exact tagged version unspecified | high |
| Medusa resists ordinary stoning from a cockatrice corpse; reflected Medusa gaze is the relevant exception. | [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [5.0 `include/monsters.h`, Medusa resistance flags](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h) | Wiki / 5.0.0 | high |
| The Perseus statue may contain a shield of reflection or levitation boots, a blessed +2 scimitar, and a sack according to independent scripted chances. | [5.0 `dat/medusa-1.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-1.lua#L61-L91) [5.0 `dat/medusa-2.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-2.lua#L77-L80) [5.0 `dat/medusa-3.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-3.lua#L64-L97) [5.0 `dat/medusa-4.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-4.lua#L57-L76) | 5.0.0 | high |
| The shield-of-reflection / levitation-boots roll is 75% / 25% on maps 1, 3 and 4; map 2 uses the opposite 25% / 75% weighting. The scimitar and sack each have independent 50% placement chances. | Same four 5.0 map scripts above | 5.0.0 | high |

### Four map variants

Coordinates below are script coordinates `(x,y)`, not guaranteed terminal coordinates after any mirroring. The arrival regions specify where the hero can enter from the adjacent levels; the down stair is the route onward.

| Map | Layout / arrival | Dry route and downstairs | Doors | Perseus statue / scripted items | Special monsters | Source / version / confidence |
|---|---|---|---|---|---|---|
| **1 — palace on an island** | A central palace/building with surrounding water and shoreline/approach areas. Arrival from above is in the west/northwest entry region around x1–5, y1–17; arrival from below is in the palace-side region around x26–50, y4–15. | Up stair `(5,14)`; down stair and Perseus/Medusa area `(36,10)`. The palace interior and shore provide dry squares; use the visible corridor/door geometry rather than assuming a straight line across water. | Closed doors `(46,7)` and `(30,12)`; locked doors `(38,8)` and `(38,11)`. | Perseus statue at `(36,10)`; 75% cursed +0 shield of reflection / 25% levitation boots; 50% blessed +2 scimitar; 50% sack. | Asleep Medusa at the same location; giant eels, jellyfish and water trolls. | [5.0 `medusa-1.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-1.lua#L42-L111); 5.0.0; high |
| **2 — two major islands** | Two large dry islands separated by water; the eastern island has the palace. Arrival from above near x2–5, y3–16; arrival from below near x61–72, y3–16. | Up stair `(4,9)`; down stair and Perseus/Medusa at `(68,10)`. A boulder is scripted at `(4,4)` and another near `(52,9)`; these can help with a bridge but are not a guaranteed complete route. | Locked eastern-island door `(71,7)`; the island walls are nondiggable. | Perseus statue at `(68,10)`; 25% cursed +0 shield of reflection / 75% levitation boots; 50% blessed +2 scimitar; 50% sack. | A titan, gremlin, electric eels, jellyfish, stone golems, cobras and other random monsters. | [5.0 `medusa-2.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-2.lua#L39-L125); 5.0.0; high |
| **3 — wooded/islet map** | Irregular water-separated islands with trees and scattered dry rooms. Entry from above is in the north-central area around x33–38, y2–7. | Up-stair arrival region around x32–39, y1–7. Three candidate room locations are `(8,6)`, `(66,5)`, `(46,15)`; one is selected for Medusa, Perseus and downstairs. | Locked doors at `(8,8)`, `(64,5)`, `(48,15)`; another door near `(50,13)` is variable. | Selected candidate gets Medusa + down stair + Perseus statue. A different candidate receives a decoy/empty statue; another gets a fountain. Statue item rolls: 75% shield / 25% levitation boots, +2 blessed scimitar 50%, sack 50%. | 30 hostile ravens, giant eels, jellyfish, wood nymphs and water nymphs. | [5.0 `medusa-3.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-3.lua#L32-L132); 5.0.0; high |
| **4 — palace / snake map** | A large western palace island with surrounding water and separate approach areas. Arrival from above near x64–74, y1–17; arrival from below near x2–18, y2–13. | Up stair is in the eastern arrival region; one of four candidate rooms `(4,8)`, `(10,4)`, `(10,8)`, `(10,12)` is selected for Medusa, Perseus and downstairs. | Several palace doors are locked, including `(4,6)`, `(4,10)`, `(8,4)`, `(8,12)`, `(10,6)`, `(10,10)`, `(12,8)`; walls are nondiggable. | Perseus statue at the randomly selected Medusa/downstairs location; 75% cursed +0 shield / 25% levitation boots; 50% blessed +2 scimitar; 50% sack. A second statue can act as a decoy. | A kraken, giant eels, jellyfish, yellow dragon / possible baby dragon and eggs, snakes and black nagas/hatchlings. | [5.0 `medusa-4.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-4.lua#L34-L146); 5.0.0; high |

### Ways across water, ranked

| Method | Reliability | Conditions and hazards | Source | Version | Confidence |
|---|---|---|---|---:|---|
| Levitation | **1 — best** | Permanent levitation boots or a known effect with enough duration avoids drowning while crossing. It does not make aquatic monsters harmless; do not hover within reach unnecessarily. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) [NetHackWiki: Levitation](https://nethackwiki.com/wiki/Levitation) | Current Wiki; exact version unspecified | high |
| Water walking | **2 — excellent** | Water-walking boots or a reliable equivalent permits walking over water. Confirm the effect is active before stepping over water. | [NetHackWiki: Water walking](https://nethackwiki.com/wiki/Water_walking) | Current Wiki; exact version unspecified | high |
| Wand of cold / frost horn | **3 — good but resource-dependent** | Freeze water in a continuous usable path. A single zap may not create a connected crossing if the path is too wide or the wand charges are limited. Verify the map changes before stepping onto the ice. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) [5.0 `src/zap.c`, cold rays](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/zap.c) | Wiki / 5.0.0 | medium |
| Boulders / scroll of earth | **4 — situational** | Boulders can create stepping stones or a bridge, but may be scarce and the earth scroll can drop boulders onto the hero. The scripts provide some boulders on map 2; other map layouts differ. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) [5.0 `dat/medusa-2.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-2.lua#L93-L105) | Wiki / 5.0.0 | medium |
| Digging down | **5 — emergency bypass, not normal crossing** | The floor can be dug through in the relevant level setup, but this abandons the ordinary route and can leave the bot on a deeper level without having completed the intended route. The exact best digging square and NLE command sequence are UNVERIFIED. | [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp) | Current Wiki; exact version unspecified | medium |

### Killing Medusa

| Method | Recommendation | Facts | Source | Version | Confidence |
|---|---|---|---|---:|---|
| Reflection | **Best if equipped and Medusa can see the hero.** | Her gaze can reflect back and petrify her. Keep reflection equipped; do not blindfold Medusa or otherwise prevent her gaze. | [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [NetHackWiki: Reflection](https://nethackwiki.com/wiki/Reflection) | Current Wiki; exact version unspecified | high |
| Blindfold | **Best defensive fallback.** | Wearing a blindfold prevents the hero from seeing Medusa and protects against the gaze; it does not kill her. Fight with ranged attacks or melee while keeping the blindfold on, and do not remove it while she can gaze at the hero. | [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [NetHackWiki: Blindfold](https://nethackwiki.com/wiki/Blindfold) | Current Wiki; exact version unspecified | high |
| Cockatrice corpse | **Do not use as a plan.** | Medusa is resistant to ordinary external stoning; the reflected gaze is the relevant stoning route. | [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [5.0 `include/monsters.h`, Medusa resistance](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h) | Wiki / 5.0.0 | high |

## Bot rules

### Rule 1 — Classify the map before crossing

- **Trigger =** Hero arrives on Medusa's level; map has `~` water, `#` corridors/walls, closed/locked doors, and a stair/arrival area. Status or level memory identifies the level as Medusa's Island, or it is the level immediately above the known Castle.
- **Action =** Match the visible geometry against the four map templates. Normalize possible horizontal/vertical flips before using script coordinates. Record all dry squares, stair symbols, doors, and the positions of visible aquatic monsters.
- **Done when =** A candidate map variant and a path from the arrival region to a safe dry area have been identified.
- **If it fails =** Do not assume coordinates from an unmirrored script. Use map topology and discover the stairs/rooms by exploration.
- **Evidence =** 5.0 `dat/medusa-1.lua`–`medusa-4.lua`; current NetHackWiki: Medusa's swamp.

### Rule 2 — Choose the safest available water crossing

- **Trigger =** A planned route requires stepping onto a `~` water tile.
- **Action =** Prefer, in order: active levitation; active water walking; known wand of cold/frost horn to create a connected ice path; a controlled boulder bridge. Do not use an unknown scroll of earth as an exploratory bridge. Confirm each terrain square is now safe before entering it.
- **Done when =** The hero reaches the next dry island or the palace without entering water.
- **If it fails =** Retreat to the previous dry square. Do not test an uncertain levitation duration over water; use stairs/another route or wait for a known source of crossing equipment.
- **Evidence =** NetHackWiki: Medusa's swamp, Levitation and Water walking; 5.0 map scripts show water/island geometry and scripted boulders.

### Rule 3 — Recover the Perseus statue rewards safely

- **Trigger =** The bot sees a statue identified as Perseus or a statue in the likely Medusa/downstairs room; inventory or floor text shows a statue containing objects.
- **Action =** Inspect the statue/object contents. Prefer the shield of reflection or levitation boots if present. Check BUC and curse status before equipping. Do not assume the statue always contains the same items.
- **Done when =** Contents are recovered and any useful item is safely equipped or stored.
- **If it fails =** If the statue is absent from an expected room, consider map 3/4 randomization and search the candidate rooms; do not assume object-detection marks the stair location.
- **Evidence =** 5.0 `dat/medusa-1.lua`–`medusa-4.lua` item rolls and randomized statue placements.

### Rule 4 — Approach and kill Medusa with reflection

- **Trigger =** Monster name `Medusa` is visible or identified, and the hero has a known equipped source of reflection.
- **Action =** Keep reflection equipped. Allow Medusa to see the hero; do not blindfold her. Avoid unnecessary approach while she can gaze. If she does not die to her reflected gaze, attack from a safe position with a ranged weapon or spell.
- **Done when =** Death message confirms Medusa is dead and the map no longer shows her monster.
- **If it fails =** If reflection is not confirmed active, do not expose the hero to her gaze. Put on a blindfold and use ranged attacks or seek a reflection source.
- **Evidence =** NetHackWiki: Medusa and Reflection.

### Rule 5 — Use a blindfold when reflection is unavailable

- **Trigger =** Medusa is alive, and no functioning reflection is available; a blindfold or towel is in inventory.
- **Action =** Press `P`, select the blindfold/towel to wear it, then attack with ranged weapons or safe melee. Keep it worn while Medusa is alive and in gaze range.
- **Done when =** Medusa is dead or the hero has escaped beyond her threat range.
- **If it fails =** If the hero becomes unblinded while Medusa is still able to gaze, immediately retreat behind cover or restore blindness; do not continue normal combat.
- **Evidence =** NetHackWiki: Medusa and Blindfold.

### Rule 6 — Do not use cockatrice stoning against Medusa

- **Trigger =** A cockatrice corpse, chickatrice corpse, or weaponized corpse is available and Medusa is the target.
- **Action =** Do not apply or wield the corpse for this fight. Use reflection or blindfold plus ordinary attacks.
- **Done when =** Medusa is killed by the safe route.
- **If it fails =** If the bot has already equipped the corpse, remove it when safe and do not attempt repeated contact.
- **Evidence =** NetHackWiki: Medusa; 5.0 Medusa resistance flags.

### Rule 7 — Locate the randomized downstairs on maps 3 and 4

- **Trigger =** Map geometry matches Medusa map 3 or 4 and object detection/known statue positions do not reveal the downstairs.
- **Action =** Search the three map-3 candidate rooms `(8,6)`, `(66,5)`, `(46,15)`, or the four map-4 candidate rooms `(4,8)`, `(10,4)`, `(10,8)`, `(10,12)`, after accounting for flips. The selected location is the Medusa/statue/downstairs location. Do not step onto it while Medusa is alive.
- **Done when =** Medusa is dead and the downstairs is located/accessible.
- **If it fails =** Explore each candidate and inspect the tile after eliminating Medusa; coordinates must be transformed for the actual mirrored layout.
- **Evidence =** 5.0 `dat/medusa-3.lua` and `dat/medusa-4.lua`.

## Risks and exceptions

1. **Do not trust the statue as an object-detection beacon on maps 3 and 4.** In 5.0, the scripts deliberately co-locate Perseus, Medusa and the downstairs at the selected random room. [5.0 `medusa-3.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-3.lua#L32-L45) [5.0 `medusa-4.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/medusa-4.lua#L34-L49)
2. **Water is dangerous even with a good route.** Giant eels, electric eels and the map-4 kraken are separate threats; levitation protects against drowning but does not make the aquatic monsters harmless. [5.0 map scripts](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat)
3. **Do not blind Medusa if relying on her gaze to kill herself.** Reflection only returns an attack that actually occurs. If the hero is blindfolded, the reflected-gaze plan may no longer trigger. [NetHackWiki: Medusa](https://nethackwiki.com/wiki/Medusa) [NetHackWiki: Reflection](https://nethackwiki.com/wiki/Reflection)
4. **A statue's rewards are probabilistic.** Do not assume the shield or levitation boots always spawn. The item selection is scripted with separate chances. [5.0 Medusa map scripts](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat)
5. **Digging down skips the intended level route.** It may be a survival escape but can put the bot on a deeper level before the Castle is ready; the exact NLE key sequence and strategic consequences are UNVERIFIED.
6. **The four map layouts are not fixed screen coordinate systems.** Mirroring and random placements mean template matching should use geometry and adjacency, not raw hard-coded coordinates. [NetHackWiki: Medusa's swamp](https://nethackwiki.com/wiki/Medusa%27s_swamp)

## Open questions

- Exact mirroring transforms used by the specific NLE 5.0 observation renderer: **UNVERIFIED**. The bot should infer a transform from the observed map rather than assume one.
- Exact item probabilities for the Perseus statue on every branch are taken from the 5.0 Lua scripts; a full statistical validation against generated NLE episodes has not been run.
- Whether a specific NLE build exposes water, ice, boulders, statues and downstairs in the same glyph set as the stock terminal: **UNVERIFIED**.
- Complete diff of all four Medusa map scripts against the 3.6.7 `medusa.des`: the map-3 statue/downstairs randomization change is established; other differences, including map 4's older statue placement, are **UNVERIFIED**.
