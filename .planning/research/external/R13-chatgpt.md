# R13 Elemental Planes and Astral (NetHack 5.0)

## Summary

- With the real Amulet, climb the up stair on dungeon level 1 to enter Earth; the order is Earth → Air → Fire → Water → Astral. Each inter-plane transition is a one-way magic portal (`^` once revealed), not a stair. A fake Amulet ends the game instead of entering the Endgame. [Elemental Planes](https://nethackwiki.com/wiki/Elemental_Planes), [Magic portal](https://nethackwiki.com/wiki/Magic_portal).
- Portals can be detected as traps. Confused non-cursed gold detection is the general method; a charged Bell of Opening or wand of secret-door detection also detects portals. On Fire, a cursed gold-detection scroll is poor because of the many fire traps; on Water, remember that the portal moves with its bubble. [Portal detection methods](https://nethackwiki.com/wiki/Portal_detection_methods).
- Earth's portal is in another isolated cavern; Air's portal is stationary on the right side behind moving clouds; Fire's portal is on dry ground and outside the arrival corner; Water's portal is in a moving air bubble. [Plane of Earth](https://nethackwiki.com/wiki/Plane_of_Earth), [Air](https://nethackwiki.com/wiki/Plane_of_Air), [Fire](https://nethackwiki.com/wiki/Plane_of_Fire), [Water](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out).
- The key 3.7 Water change is bubble motion: moving inside a bubble gives it a 50% chance to move in that direction; otherwise it moves randomly. In 5.0, thrown/kicked objects are stopped by Water-plane water. [Water plane](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out), [5.0 fixes](https://github.com/NetHack/NetHack/blob/NetHack-5.0/doc/fixes5-0-0.txt#L3630-L3631).
- Astral has one lawful, one neutral, and one chaotic high altar, plus all three Riders. For a neutral Valkyrie, identify the **neutral** high priest before using `#offer` on the real Amulet. [Astral](https://nethackwiki.com/wiki/Astral), [5.0 `src/pray.c:offer_real_amulet()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/pray.c#L2197-L2202).

## Facts

| claim | source | version | confidence high/medium/low |
|---|---|---:|---|
| Endgame order is Earth, Air, Fire, Water, then Astral. Elemental planes are no-teleport and have undiggable floors. | [NetHackWiki: Elemental Planes](https://nethackwiki.com/wiki/Elemental_Planes) | 3.6-era spoiler; retained 5.0 ordering | high |
| Earth is entered by climbing the up stair on dungeon level 1 while carrying the real Amulet. A fake Amulet instead causes “escape the dungeon” and ends the run. You cannot return to the earlier dungeon branches after entering. | [NetHackWiki: Elemental Planes](https://nethackwiki.com/wiki/Elemental_Planes) | 3.6-era spoiler; 5.0 behavior not independently replayed | high |
| Magic portals are traps represented by `^` when visible; they are hidden until activated or detected. One-way portals connect the four planes in order, and cannot be used to go backward. | [NetHackWiki: Magic portal](https://nethackwiki.com/wiki/Magic_portal) | 3.6/3.7 spoiler lineage; 5.0 UI glyph UNVERIFIED | high for mechanic; medium for screen rendering |
| Portal detection methods include confused gold detection (non-cursed scroll shows traps), a charged Bell of Opening, wand of secret-door detection/detect unseen, or Amulet proximity messages. | [NetHackWiki: Portal detection methods](https://nethackwiki.com/wiki/Portal_detection_methods) | Source references 3.4.3/3.6-era; 5.0 range details UNVERIFIED | medium |
| Earth is mostly solid rock around separated caverns; the hero enters in the bottom-right cavern and the portal to Air is randomly in another cavern. Walls can be dug, but the floor cannot. | [NetHackWiki: Plane of Earth](https://nethackwiki.com/wiki/Plane_of_Earth) | 3.6.7 spoiler source references; 5.0 layout retention UNVERIFIED | medium |
| Earth generation includes an immediate Wizard of Yendor arrival with a digging spellbook, plus many earth elementals/xorns and other monsters; digging with pick/mattock can generate more earth elementals/xorns. | [NetHackWiki: Plane of Earth](https://nethackwiki.com/wiki/Plane_of_Earth), references to `src/makemon.c` and `src/dig.c` | 3.6.7 | medium; exact 5.0 counts UNVERIFIED |
| Air is open air with opaque moving clouds; arrival is on the left and the stationary portal to Fire is somewhere on the right. Only flying/floating/amorphous/noncorporeal/whirly monsters generate there. | [NetHackWiki: Plane of Air](https://nethackwiki.com/wiki/Plane_of_Air) | 3.6.6 spoiler source; 5.0 map retention UNVERIFIED | medium |
| Without levitation or flight, Air movement has a 3/4 chance to fail. A lightning strike has a 1/8 chance each turn; being inside a cloud when it strikes paralyzes for 3 turns and deafens for 30–49 additional turns. Free action does not prevent this paralysis. | [NetHackWiki: Plane of Air](https://nethackwiki.com/wiki/Plane_of_Air), `src/timeout.c` reference | 3.6.6 spoiler source; 5.0 exact odds UNVERIFIED | medium |
| A 3.7 change made mindless monsters such as air elementals and vortices no longer fear musical instruments. Do not depend on instrument-based fear to clear Air. | [NetHackWiki: Plane of Air](https://nethackwiki.com/wiki/Plane_of_Air), commit `6e49372d` history | 3.7; inherited by 5.0 | medium |
| Fire is unlit, has lava, many fire-resistant monsters and fire traps; the portal to Water is on dry land and not in the lower-right arrival area. Lava periodically emits poison clouds (`#`) that can cause poison damage and blindness/coughing. | [NetHackWiki: Plane of Fire](https://nethackwiki.com/wiki/Plane_of_Fire), [Poison cloud](https://nethackwiki.com/wiki/Poison_cloud) | Fire layout spoiler references 3.4.3; poison clouds introduced in 3.6.0; 5.0 map retention UNVERIFIED | medium |
| 3.7 enlarged the Plane of Fire and made its ground hot enough to destroy potions. Treat potions dropped on the floor as at risk. | [NetHackWiki: Plane of Fire](https://nethackwiki.com/wiki/Plane_of_Fire), commits `d3e80bf9`, `6acf5a77` | 3.7; inherited by 5.0 | medium |
| Water is filled with water except for moving air bubbles; the hero arrives in a left-side bubble and the portal is in another bubble (initially right-side) which moves, merges, and divides. The hero cannot leave a bubble without being able to survive underwater; water-walking or freezing the water does not prevent drowning. | [NetHackWiki: Plane of Water](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out) | 3.6-era spoiler; 5.0 map retention UNVERIFIED | medium |
| 3.7 commit `62b78ba0`: when the hero moves within an air bubble, the bubble has a 50% chance to move in the same direction; otherwise it moves randomly as normal. | [NetHackWiki: Plane of Water](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out), history note and commit | 3.7; inherited by 5.0 | medium |
| 5.0 fixes Water-plane water so it stops thrown or kicked items. Do not model thrown-object Newtonian movement as a reliable Water-plane traversal strategy. | [NetHack 5.0.0 `doc/fixes5-0-0.txt`, lines 3630–3631](https://github.com/NetHack/NetHack/blob/NetHack-5.0/doc/fixes5-0-0.txt#L3630-L3631) | 5.0 | high |
| Astral is the last level; it is not mappable, teleportable, or diggable. Three temple rooms contain high altars assigned randomly as lawful, neutral, and chaotic, each with a peaceful high priest of that alignment. | [NetHackWiki: Astral](https://nethackwiki.com/wiki/Astral) | 3.6-era spoiler; 5.0 layout retention UNVERIFIED | medium |
| The three Riders are placed one per round room. They are hostile, can regenerate, and revive from their corpses; do not spend turns manipulating Rider corpses. | [NetHackWiki: Rider](https://nethackwiki.com/wiki/Rider), [Famine](https://nethackwiki.com/wiki/Famines) | 3.6/3.7 spoiler lineage; 5.0 exact timing should be verified | medium |
| Famine has two 8d8 hunger-inducing touch attacks; no resistance blocks the hunger effect. Fainting from hunger on Astral can be fatal. | [NetHackWiki: Famine](https://nethackwiki.com/wiki/Famines) | Current wiki profile; 5.0 monster source not independently checked | medium |
| Pestilence has two 8d8 disease touch attacks; when both hit, the second attack stuns. The Rider is resistant to several elements and regenerates quickly. | [NetHackWiki: Pestilence](https://nethackwiki.com/wiki/Pestilence) | Current wiki profile; 3.6/3.7/5.0 exact source not independently reconciled | medium |
| 3.7 changed Death's deadly touch from a chance of instant death to 8d6 + 50 damage and a maximum-HP reduction equal to half the damage; if the resulting damage reduces HP to zero, death is immediate. | [NetHackWiki: Death](https://nethackwiki.com/wiki/Deaths), 3.7 change note/commit | 3.7; inherited by 5.0 | medium |
| 3.7 made green dragon scales and scale mail confer immunity to sickness, reducing Pestilence's disease threat while worn. This is a 3.7 change, not a 3.6 assumption. | [NetHackWiki: Pestilence](https://nethackwiki.com/wiki/Pestilence), 3.7 change note | 3.7; inherited by 5.0 | medium |
| A high altar that merely looks “aligned” from a distance is not necessarily neutral; far-look only distinguishes aligned from unaligned. Near-look/chat with a high priest is needed to tell the neutral temple from the lawful/chaotic ones. | [NetHackWiki: Altar](https://nethackwiki.com/wiki/An_object_appears_at_your_feet), [Astral](https://nethackwiki.com/wiki/Astral) | 3.6-era spoiler; 5.0 behavior UNVERIFIED | medium |
| Chatting with each high priest while carrying no gold distinguishes the co-aligned priest: cross-aligned priests say they are “not interested”; the co-aligned priest follows the normal donation response. For this neutral Valkyrie, select the neutral priest. | [NetHackWiki: Astral](https://nethackwiki.com/wiki/Astral) | 3.6-era spoiler; 5.0 dialogue wording UNVERIFIED | medium |
| Offering the real Amulet on the hero's co-aligned high altar is the ascension condition. Offering it on another high altar ends the run in disgrace rather than true ascension. | [NetHackWiki: Amulet of Yendor](https://nethackwiki.com/wiki/Amulet_of_Yendor), [5.0 source `src/pray.c:offer_real_amulet()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/pray.c#L2197-L2202) | Wiki 3.6-era; function in 5.0 | high for success condition |
| The Gehennom mysterious force can act when climbing stairs while carrying the real Amulet. The visible message is “A mysterious force momentarily surrounds you...”. 3.7 changed its probability based on accumulated levels of pushback; old 3.6 1-in-4 and neutral max-pushback averages are not valid 5.0 constants. | [NetHackWiki: Mysterious force](https://nethackwiki.com/wiki/Mysterious_force), 3.7 change note | 3.6 baseline + 3.7 change; 5.0 exact probability UNVERIFIED | medium |

## Bot rules

### R13.1 — Enter the Endgame only with the real Amulet

- **Trigger:** Status line shows `Dlvl:1` (or the observed topmost dungeon level); inventory contains the known real `Amulet of Yendor`; an up stair `<` is visible.
- **Action:** Move onto the up stair and press `<`. Do not attempt this with an unidentified or suspected fake Amulet. Confirm a plane transition rather than relying only on the keypress.
- **Done when:** Screen/map changes to the Plane of Earth and the portal/plane state is registered.
- **If it fails:** If the game reports escape from the dungeon or ascension ending immediately, classify the Amulet as fake; do not automate this action until the Amulet is verified. Once on Earth, the earlier dungeon is inaccessible.
- **Evidence:** [Elemental Planes](https://nethackwiki.com/wiki/Elemental_Planes) (3.6-era endgame entry/sequence).

### R13.2 — Detect portals generically

- **Trigger:** Current plane has no ordinary exit stair; a trap/portal detection effect is available; hidden portal candidates are not on the current map.
- **Action:** Preferred: if a non-cursed scroll of gold detection is available and the hero can be confused, apply confusion first, then `r` → select the gold-detection scroll; recognize revealed traps/portals as `^`. Alternatives: `a` → charged Bell of Opening; or `z` → wand of secret-door detection/detect unseen, answering direction only if prompted by the port. If relying on Amulet glow, keep a turn log and react to `The Amulet of Yendor feels warm.`/temperature variants; treat exact glow wording and radius as **UNVERIFIED** for NLE 5.0.
- **Done when:** The portal tile is visible as `^` and its coordinate is stored. Step onto it with a normal movement key to transition.
- **If it fails:** Re-run detection after map/terrain changes; do not assume a missing `^` means no portal. Avoid cursed gold detection on Fire; avoid relying on a stale coordinate on Water.
- **Evidence:** [Portal detection methods](https://nethackwiki.com/wiki/Portal_detection_methods), [Magic portal](https://nethackwiki.com/wiki/Magic_portal) (3.4.3/3.6-era references; 5.0 prompt strings UNVERIFIED).

### R13.3 — Plane of Earth

- **Trigger:** Map is rock with isolated floor caverns; hero starts in the lower-right cavern; no visible stair; screen may immediately identify/depict the Wizard of Yendor.
- **Action:** First survive/disable the Wizard of Yendor using high-threat combat policy; do not dig the floor. Explore every reachable cavern and record all corridor openings. Use confused gold detection, a charged Bell, or secret-door detection to find the portal; if detection fails, search/walk every accessible floor square. Use a pick-axe/wand of digging only to connect an inaccessible rock wall as a fallback; prefer not to dig repeatedly because digging can generate earth elementals/xorns.
- **Done when:** The hidden `^` portal is revealed in a cavern other than the entry cavern; step onto it.
- **If it fails:** If all connected squares have been explored, inspect single-square and separated caverns; do not assume the portal is adjacent or in the entry chamber. If Wizard appears, treat it as a live threat until controlled.
- **Evidence:** [Plane of Earth](https://nethackwiki.com/wiki/Plane_of_Earth) (3.6.7 source references to `src/makemon.c`/`src/dig.c`; exact 5.0 layout/count UNVERIFIED).

### R13.4 — Plane of Air

- **Trigger:** Map consists of open floor/air with opaque moving cloud patches; arrival is on left; portal is not immediately visible and lies in the right-side search area.
- **Action:** Ensure levitation or flight is active before traversing. Move around cloud banks using a shortest safe route; do not make a stationary search loop in clouds. Detect the stationary `^` portal with confused gold detection or the Amulet; secret-door detection is less reliable because clouds move. Keep reflection available for lightning if possible; do not rely on free action to stop cloud-induced paralysis. Avoid relying on a musical instrument to frighten mindless air elementals/vortices (3.7 behavior change).
- **Done when:** Portal `^` is revealed at a fixed coordinate in the right portion; move onto it.
- **If it fails:** If movement attempts fail, re-establish levitation/flight before retrying; move out of cloud patches when lightning/paralysis occurs. Re-detect rather than assuming a moving cloud is the portal.
- **Evidence:** [Plane of Air](https://nethackwiki.com/wiki/Plane_of_Air) (3.6.6 profile, commit `6e49372d` 3.7 behavior change).

### R13.5 — Plane of Fire

- **Trigger:** Map shows lava (`}`), dry floor (`.`), fire traps (`^`), and possibly poison clouds (`#`); arrival is in the lower-right region; many fire-resistant monsters may trigger traps.
- **Action:** Keep fire resistance active; preserve poison resistance and a blindness cure; maintain levitation/flight if available to avoid accidental lava entry. Search/detect the portal on dry land outside the lower-right arrival corner. Prefer confused non-cursed gold detection or Bell/secret-door detection; do **not** use cursed gold detection as the main method because the map contains many fire traps. Do not leave potions on hot floor squares; use inventory containers if available.
- **Done when:** A portal `^` on dry land is visible; step onto it.
- **If it fails:** Use systematic dry-floor scanning and repeat detection; don't walk blindly through lava/fire-trap areas in response to message noise. A poison-cloud `#` should trigger an immediate move out and/or blindness recovery.
- **Evidence:** [Plane of Fire](https://nethackwiki.com/wiki/Plane_of_Fire), [Poison cloud](https://nethackwiki.com/wiki/Poison_cloud); 3.7 commits `d3e80bf9` and `6acf5a77` (map enlargement/hot ground).

### R13.6 — Plane of Water

- **Trigger:** Map is submerged water with moving air bubbles; hero appears in a bubble at the left; portal is a `^` trap carried by another bubble (initially on the right).
- **Action:** If the hero lacks magical breathing/underwater survival, **remain within air bubbles**; do not step into water because water-walking or freezing does not prevent drowning. Detect the portal with confused non-cursed gold detection, a charged Bell, or secret-door detection and store the portal coordinate plus the bubble that contains it. Re-detect/track every turn: under 3.7 motion, moving inside the current bubble may move that bubble with the hero (50% in requested direction, otherwise random). Navigate by waiting/moving safely within bubbles until bubbles merge or the portal bubble comes within reach; step onto the revealed portal only when it is in a bubble the hero can occupy. Do not use throwing/kicking as a movement exploit: 5.0 water stops thrown/kicked items.
- **Done when:** Hero steps onto the visible `^` portal in the portal bubble and transitions to Astral.
- **If it fails:** If the portal's old coordinate changes, discard it and run detection again. If no magical breathing is present and no bubble bridge forms, remain on safe bubble squares rather than entering water. If the 3.7 bubble behavior makes movement drift unexpectedly, update the bubble-tracking state after each action.
- **Evidence:** [Plane of Water](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out), commit `62b78ba0` 3.7; [5.0 fixes, Water-plane thrown/kicked item behavior](https://github.com/NetHack/NetHack/blob/NetHack-5.0/doc/fixes5-0-0.txt#L3630-L3631).

### R13.7 — Identify the neutral high altar on Astral

- **Trigger:** Astral map contains three temple rooms/altars (`_` in standard text glyphs) with high priests; inventory contains the real Amulet. The bot is neutral (status line `Neutral`).
- **Action:** Do not infer neutral alignment from far-look's generic “aligned” label. To identify a priest, first make sure the hero carries no gold (drop all carried gold; gold in a container still counts as carried). Move adjacent and use extended command `#chat` (press `#`, type `chat`, Enter; select the priest/direction as prompted). A cross-aligned priest's `not interested` response marks a wrong temple; the priest who follows the ordinary donation routine is the co-aligned neutral priest. Record that altar's coordinate and do not change alignment.
- **Done when:** A temple's priest is confirmed co-aligned by the no-gold chat test and the high altar tile is known.
- **If it fails:** If the priest is hostile/dead or prompts differ, do not guess. Inspect altar/temple alignment with near-look and seek another priest/temple; far-look alone is insufficient. Preserve the real Amulet.
- **Evidence:** [Astral](https://nethackwiki.com/wiki/Astral), [Altar](https://nethackwiki.com/wiki/An_object_appears_at_your_feet) (3.6-era rules; 5.0 dialogue wording UNVERIFIED).

### R13.8 — Avoid Rider traps and reach the altar

- **Trigger:** A Rider is identified by name/monster detection or the map shows `&`; status shows hunger; sickness/disease messages appear; any Rider corpse is visible.
- **Action:** Keep moving toward the confirmed neutral altar and use ranged damage/avoidance where practical. Enter Astral satiated and carry quick food; restore nutrition immediately if Famine's touch has made the hero hungry. Keep sickness resistance/cure ready for Pestilence; in 3.7 green dragon scales/mail grant sickness immunity. Treat Death as a max-HP threat: avoid melee exchanges and heal before a possible contact. Do not teleport a Rider or a Rider corpse; do not eat, pick up, tin, or otherwise manipulate a Rider corpse, because Riders revive. Killing a Rider is temporary; don't spend turns repeatedly killing one unless it blocks the route.
- **Done when:** The bot reaches the already-identified neutral high altar without being surrounded or critically hungry/sick.
- **If it fails:** If a Rider is adjacent and threatens a lethal contact, prioritize defensive movement/teleportation that does **not** target the Rider/corpse; if hunger/sickness is critical, consume the planned resource before advancing. Recompute path around locked doors using opening/knock/digging only if safe; Astral's floor itself is undiggable.
- **Evidence:** [Rider](https://nethackwiki.com/wiki/Rider), [Famine](https://nethackwiki.com/wiki/Famines), [Pestilence](https://nethackwiki.com/wiki/Pestilence), [Death](https://nethackwiki.com/wiki/Deaths) (3.6/3.7 profile; 5.0 exact probabilities UNVERIFIED).

### R13.9 — Offer the real Amulet for true ascension

- **Trigger:** Hero stands on the high altar in the neutral temple; priest response confirmed co-aligned; inventory contains the real Amulet of Yendor and status alignment is still Neutral.
- **Action:** Use extended command `#offer` (press `#`, type `offer`, Enter); at the object prompt select `Amulet of Yendor`. Do not offer a fake Amulet, quest artifact, or other object. Do not target a lawful/chaotic altar or the unaligned altar in Moloch's Sanctum.
- **Done when:** The game reports true ascension/immortality and terminates with the ascension outcome.
- **If it fails:** Stop. Re-read the current altar identity and inventory; never offer on a different altar as a fallback. An offer to a non-co-aligned high altar produces a different, disgraceful ending, not a true ascension.
- **Evidence:** [Amulet of Yendor — Offering the Amulet](https://nethackwiki.com/wiki/Amulet_of_Yendor#Offering_the_Amulet); 5.0 [`src/pray.c:offer_real_amulet()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/pray.c#L2197-L2202).

### R13.10 — Handle the mysterious force during the Gehennom climb (not on Astral)

- **Trigger:** Before Endgame, inventory contains the real Amulet; hero is climbing Gehennom stairs `<`; message `A mysterious force momentarily surrounds you...` appears.
- **Action:** Parse the post-action `Dlvl`, update the graph with the actual resulting level, and re-plan to the next known up stair. Do not interpret this as the Plane portal effect or as an Astral hazard. Avoid a fixed expected number of stair climbs; keep following recorded stairs.
- **Done when:** Hero leaves Gehennom and reaches the upper dungeon; this rule is inactive after the one-way Elemental Planes entry.
- **If it fails:** If the hero has not changed levels, use the same stair only after checking the current game state; if moved down/sideways, navigate from the actual level. Do not use the old 3.6 `1/4` trigger rate or neutral two-level maximum as a 5.0 constant.
- **Evidence:** [Mysterious force](https://nethackwiki.com/wiki/Mysterious_force), 3.7 change note (exact 5.0 formula UNVERIFIED).

## Risks and exceptions

- **Water is the hard safety gate.** Unless the bot has magical breathing or equivalent ability to survive underwater, it must not step outside an air bubble. Water walking, cold-freezing the surface, or merely having flight/levitation does not make the submerged plane safe. [Plane of Water](https://nethackwiki.com/wiki/You_had_better_wait_for_the_sun_to_come_out) (3.6-era mechanics; 5.0 retention UNVERIFIED).
- **Air can soft-lock a naive movement policy.** Without levitation/flight, many movement commands fail; cloud lightning can paralyze despite free action. Carry levitation or flight and reflection where possible. [Plane of Air](https://nethackwiki.com/wiki/Plane_of_Air) (3.6-era mechanics).
- **Fire's message stream is noisy.** Monsters trigger fire traps and inter-monster combat creates many messages; do not skip message parsing wholesale. Poison clouds (`#`) can blind even when poison damage is resisted. [Plane of Fire](https://nethackwiki.com/wiki/Plane_of_Fire), [Poison cloud](https://nethackwiki.com/wiki/Poison_cloud) (3.6-era layout; 3.6+ poison clouds).
- **Earth is not “one large room.”** The portal may be in a separate cavern; repeated digging can create extra earth elementals/xorns. Track each disconnected cavern explicitly. [Plane of Earth](https://nethackwiki.com/wiki/Plane_of_Earth) (3.6.7 source references).
- **Astral priorities differ from Gehennom.** Keep moving toward the correct temple; don't attempt to clear the level. Rider corpses revive, and teleporting a Rider often relocates it adjacent to the hero rather than removing it. [Astral](https://nethackwiki.com/wiki/Astral), [Rider](https://nethackwiki.com/wiki/Rider) (wiki spoiler lineage).
- **Famine:** have a satiation buffer and fast food. The hunger touch has no resistance; fainting while surrounded on Astral can be fatal. [Famine](https://nethackwiki.com/wiki/Famines) (current wiki profile).
- **Pestilence:** disease plus stun is a controller failure mode. Green dragon scales/mail sickness immunity is a 3.7 change; don't assume a 3.6 character had it. [Pestilence](https://nethackwiki.com/wiki/Pestilence) (3.7 change note).
- **Death:** the 3.7 touch rule is no longer the old probabilistic instadeath: it deals large damage and reduces maximum HP; it still kills immediately if the resulting damage is lethal. [Death](https://nethackwiki.com/wiki/Deaths) (3.7 change note). Treat “high current HP” alone as insufficient if max HP has been repeatedly reduced.
- **Wrong altar ends the game without true ascension.** The co-aligned high altar is required; an “aligned” label from far-look does not prove neutral alignment. [Astral](https://nethackwiki.com/wiki/Astral), [Altar](https://nethackwiki.com/wiki/An_object_appears_at_your_feet), [Amulet of Yendor](https://nethackwiki.com/wiki/Amulet_of_Yendor) (3.6-era altar behavior).
- **Mysterious force is a Gehennom stair-climb issue.** It is not an Astral Plane portal or a final-level Rider ability. The old 3.6 probability table is stale after 3.7; exact 5.0 odds are **UNVERIFIED**. [Mysterious force](https://nethackwiki.com/wiki/Mysterious_force).

## Open questions

- **UNVERIFIED:** Exact 5.0.0 portal coordinates, map dimensions, and monster counts on Earth/Air/Fire/Water/Astral. Wiki pages expose 3.6-era spoilers and some upcoming-3.7 notes; this pass did not reconstruct the final 5.0 Lua maps.
- **UNVERIFIED:** Exact 5.0 NLE glyphs and message variants for hidden/revealed portals and Amulet glow; `^` is the standard magic-portal glyph, but verify against the actual terminal renderer.
- **UNVERIFIED:** Exact 5.0 prompt sequences for `#chat`, `#offer`, scroll detection, and charged Bell detection in the particular NLE build. The action rules specify the NetHack commands and defer menu letters/direction prompts to live text.
- **UNVERIFIED:** Exact timing/turn behavior for Water bubble merging and whether the 3.7 `50% same-direction` step rule is modified by speed, encumbrance, or 5.0 updates.
- **UNVERIFIED:** Exact 5.0 attack formulas/AI targeting for Death, Pestilence, Famine and all named elemental-plane monsters. Confirm from the tagged `dat/monsters.lua` and source before using numeric combat thresholds.
- **UNVERIFIED:** Exact 5.0 mysterious-force probability distribution after repeated pushbacks; the 3.7 source change invalidates the old fixed 3.6 table.
