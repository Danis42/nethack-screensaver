# R10 The Castle in 5.0 (B)

## Summary

- The Castle is a **no-teleport, non-diggable maze level** with a moat, drawbridge, hostile soldiers, four dragons, aquatic monsters and a central court containing additional random monsters. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L5-L20) [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L156-L229)
- The drawbridge can be opened using the **passtone/passtune**, a wand of opening, or the appropriate opening magic. The tune is a five-note Mastermind puzzle: tumblers count correct notes in wrong positions; gears count correct notes in correct positions. [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L742-L849) [NetHackWiki: Passtune](https://nethackwiki.com/wiki/Passtune)
- A wand of striking or force bolt **breaks/destroys** the drawbridge rather than performing the normal raising operation. Treat that as destructive and potentially dangerous to creatures/objects at the bridge. [NetHackWiki: Drawbridge](https://nethackwiki.com/wiki/Drawbridge)
- The wand of wishing is in a **locked, untrapped chest in one randomly selected tower**. In 5.0 the chest also contains a potion of gain level; this is a difference from the 3.6.7 Castle script. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L137-L147) [3.6.7 `dat/castle.des`](https://github.com/NetHack/NetHack/blob/NetHack-3.6.7_Released/dat/castle.des#L134-L140)
- **With reflection and levitation already available at XL14, prefer the moat/back-entry route** if the observation confirms a safe crossing and enough levitation duration. Avoid standing in front of the bridge while opening it, and approach soldiers/dragons through controlled corridors rather than entering the court blindly.
- The five trapdoors on the center row drop to the Valley. Avoid them while routing to the tower chest. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L149-L165)

## Facts

### Level structure, doors and routes

| Claim | Source | Version | Confidence |
|---|---|---:|---|
| The Castle is generated as a maze level with no teleport and non-diggable sections; ordinary teleportation and tunneling are not reliable ways through it. | [5.0 `dat/castle.lua`, level flags and map](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L5-L39) | 5.0.0 | high |
| The front entrance is a drawbridge at approximately `(5,8)` in the script map. The map also permits back entry using levitation or water walking across the moat. | [5.0 `dat/castle.lua`, map and comments](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L5-L39) | 5.0.0 | high |
| The map contains closed doors at `(7,3)`, `(55,3)`, `(15,8)`, `(26,8)`, `(7,13)`, `(55,13)` and locked doors at `(32,4)`, `(26,5)`, `(46,5)`, `(48,5)`, `(47,7)`, `(38,8)`, `(56,8)`, `(47,9)`, `(26,11)`, `(46,11)`, `(48,11)`, `(32,12)`. | [5.0 `dat/castle.lua`, door placement](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L40-L76) | 5.0.0 | high |
| The drawbridge can be opened through the passtune, wand of opening or knock/opening magic. | [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L742-L849) [NetHackWiki: Drawbridge](https://nethackwiki.com/wiki/Drawbridge) | 5.0.0 / current Wiki | high |
| The passtune is five notes chosen from A through G; H is converted to B in the tune parser. | [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L742-L766) | 5.0.0 | high |
| A correct note in the correct position produces a gear clue; a correct note in a wrong position produces a tumbler clue. | [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L768-L849) [NetHackWiki: Passtune](https://nethackwiki.com/wiki/Passtune) | 5.0.0 / current Wiki | high |
| The tune is checked when the hero is within the drawbridge's interaction area; it can be played from either side if in range. | [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L768-L789) | 5.0.0 | medium |
| Wand of striking or force bolt destroys the drawbridge rather than safely opening it as a normal bridge. | [NetHackWiki: Drawbridge](https://nethackwiki.com/wiki/Drawbridge) | Current Wiki; exact tagged version unspecified | medium |

### Monsters and traps

| Claim | Source | Version | Confidence |
|---|---|---:|---|
| The map scripts place eight soldiers, one lieutenant and eight additional soldiers near the towers. | [5.0 `dat/castle.lua`, monster placement](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L156-L176) | 5.0.0 | high |
| Four dragon monsters are placed as storeroom guards. Their species/traits should be identified from the live monster name; do not assume all four are the same dragon type. | [5.0 `dat/castle.lua`, dragon placement](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L177-L190) | 5.0.0 | high |
| Four giant eels and four sharks are placed in the moat. | [5.0 `dat/castle.lua`, aquatic monster placement](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L190-L198) | 5.0.0 | high |
| The central court has 27 additional monster placements drawn from shuffled monster classes. | [5.0 `dat/castle.lua`, court monsters](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L198-L229) | 5.0.0 | high |
| Five trapdoors are placed along the central row at approximately `(40,8)`, `(44,8)`, `(48,8)`, `(52,8)` and `(55,8)`; they lead to the Valley of the Dead. | [5.0 `dat/castle.lua`, trapdoors](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L149-L165) | 5.0.0 | high |

### Wand-of-wishing chest

| Claim | Source | Version | Confidence |
|---|---|---:|---|
| One of four tower locations (script positions `(4,2)`, `(58,2)`, `(4,14)`, `(58,14)`) is selected for the treasure room. | [5.0 `dat/castle.lua`, random tower selection](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L40-L76) | 5.0.0 | high |
| The selected tower contains a locked, untrapped chest with a wand of wishing and a potion of gain level. | [5.0 `dat/castle.lua`, treasure chest](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L137-L147) | 5.0.0 | high |
| The same 3.6.7 Castle treasure chest script contains the wand of wishing but not the potion of gain level. | [3.6.7 `dat/castle.des`, tower chest](https://github.com/NetHack/NetHack/blob/NetHack-3.6.7_Released/dat/castle.des#L134-L140) | 3.6.7 | high |
| The chest is locked but not trapped, according to the 5.0 script. | [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L137-L147) | 5.0.0 | high |
| An Elbereth engraving and a cursed scare-monster scroll are placed as part of the tower treasure setup. | [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L137-L147) | 5.0.0 | high |

## Bot rules

### Rule 1 — Prepare before entering

- **Trigger =** Hero reaches the Castle's up-stair/entry level at XL14; inventory shows reflection and levitation are available.
- **Action =** Confirm reflection is actually equipped/active and levitation is active with sufficient remaining duration (or permanent boots). Keep a known wand of opening or tonal instrument available if possible. Do not start with a short levitation timer unless the bot can refresh it.
- **Done when =** The bot has confirmed reflection, levitation and one drawbridge-opening option.
- **If it fails =** Do not step into the moat. Search for a reliable levitation/water-walking duration or use the front drawbridge route with a safe opening method.
- **Evidence =** 5.0 `dat/castle.lua` comments/map and NetHackWiki: Castle / Drawbridge.

### Rule 2 — Prefer moat/back entry with levitation

- **Trigger =** Castle map is visible; levitation is active; an unobstructed dry or moat-edge route exists on the map.
- **Action =** Navigate from the current entry region to the moat crossing using the visible dry tiles; move over water only while levitation is confirmed active. Keep distance from visible eels/sharks. Do not route onto the drawbridge tile if the goal is to use the back entrance.
- **Done when =** Hero reaches the interior side of the moat on safe floor.
- **If it fails =** Retreat to the last dry tile. If levitation expires or the path is blocked by aquatic monsters, do not continue over water; use the drawbridge-opening method.
- **Evidence =** 5.0 `dat/castle.lua` back-entry comment and aquatic monster placements.

### Rule 3 — Open the drawbridge with a wand of opening

- **Trigger =** The hero is in wand-of-opening range of the drawbridge, and the front entrance is the chosen route.
- **Action =** Press `z`; select the known wand of opening; enter the direction towards the drawbridge. Read the result message and check that the bridge/portcullis state visibly changes before moving through.
- **Done when =** The drawbridge is open and a safe crossing tile exists.
- **If it fails =** Check that the wand is not empty/cancelled and that the direction is correct. Do not substitute a wand of striking or force bolt unless deliberately destroying the bridge is acceptable.
- **Evidence =** 5.0 `src/music.c` alternatives and NetHackWiki: Drawbridge; exact NLE text rendering UNVERIFIED.

### Rule 4 — Solve the passtune as a Mastermind code

- **Trigger =** The hero has a tonal instrument and is in the drawbridge interaction area; the terminal shows `What tune are you playing?` or `Play the passtune?`.
- **Action =**
  1. Apply the instrument with `a`, select its inventory letter and confirm playing if prompted.
  2. Enter exactly five note letters A–G at the tune prompt; treat H as B because the source normalizes H to B.
  3. Parse each clue: `N gear(s) turn.` = N exact-position matches; `N tumbler(s) click.` = N correct notes in wrong positions.
  4. Maintain a candidate set of all five-note strings over A–G. After each guess, retain only candidates whose exact and misplaced counts equal the reported gear/tumbler values.
  5. Choose the next guess to separate the remaining candidates (minimax or maximum partition entropy); repeat until one candidate remains, then enter it.
- **Done when =** Message confirms the drawbridge opens / bridge state changes.
- **If it fails =** If no clues appear, check deafness, instrument suitability and distance. Do not assume that one wrong tune opens the bridge. If the candidate set becomes empty, reset the parser from the complete message log and confirm that singular/plural messages were read correctly.
- **Evidence =** 5.0 `src/music.c::do_play_instrument()`; NetHackWiki: Passtune. The minimax strategy is a bot-side algorithm derived from the Mastermind response semantics, not a game rule.

### Rule 5 — Do not destroy the drawbridge accidentally

- **Trigger =** Bot is considering using force bolt or wand of striking at the drawbridge.
- **Action =** Reject the action as the default. Use wand of opening, knock/opening magic or passtune instead. Only use striking/force bolt when the bot explicitly wants to destroy the bridge and has verified no ally, needed item or safe route will be harmed.
- **Done when =** Bridge remains intact and opens normally, or the bot has deliberately committed to destructive removal.
- **If it fails =** If the bridge is destroyed, recalculate the path; do not assume an intact bridge remains.
- **Evidence =** NetHackWiki: Drawbridge.

### Rule 6 — Fight soldiers and lieutenant in controlled groups

- **Trigger =** Map shows soldier/lieutenant monsters approaching, or the terminal names `soldier` / `lieutenant`.
- **Action =** Pull one or a small number into a corridor; use known sleep/slow/striking wands or ranged attacks before melee. Keep the shield of reflection equipped. Recheck HP and status after each monster action; do not charge through the central court.
- **Done when =** The immediate approach corridor is clear and the bot has a route to the towers.
- **If it fails =** If several soldiers attack together or HP falls rapidly, retreat to a cleared corridor or staircase route. Do not spend turns taking multiple simultaneous melee attacks.
- **Evidence =** 5.0 `dat/castle.lua` soldier and lieutenant placements; `src/zap.c` wand handling.

### Rule 7 — Route around the trapdoors and identify the treasure tower

- **Trigger =** The central Castle row contains suspicious floor traps, trapdoor symbols or a trap message; the map shows tower rooms.
- **Action =** Avoid the five central trapdoor positions; inspect the four tower candidates for the locked chest. Do not assume the treasure is always in the same tower. If a chest is found, inspect its status and use a known wand of opening, lock pick or key as available.
- **Done when =** The chest is open and its contents have been collected.
- **If it fails =** If the chest is locked, use a safe unlocking method; its scripted state is locked but untrapped, so do not spend a turn searching for a nonexistent trap as a prerequisite.
- **Evidence =** 5.0 `dat/castle.lua` random tower selection, chest and trapdoors.

### Rule 8 — Collect the wishing wand safely

- **Trigger =** Inventory/floor message identifies a wand of wishing inside the tower chest.
- **Action =** Pick up the wand, verify its identity and charges, and keep it protected. Collect the potion of gain level if present and safe to carry.
- **Done when =** Wand of wishing is in inventory and the bot records its charge count / blessing state as available.
- **If it fails =** If a chest item is missing, recheck container contents; do not assume the chest was generated with additional items not in the script.
- **Evidence =** 5.0 `dat/castle.lua` treasure chest contents.

## Risks and exceptions

1. **No teleport escape:** the Castle's level flags prohibit teleportation. Preserve a physical retreat route and do not build the plan around teleporting away. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L5-L20)
2. **Levitation is not immunity to monsters.** It avoids the water/drowning problem but does not prove that nearby eels or sharks cannot attack. Maintain distance and do not idle above moat monsters. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L190-L198)
3. **Opening a drawbridge can affect the tiles and creatures around it.** Do not stand directly in the danger area or leave pets/peaceful creatures in the bridge line. [NetHackWiki: Drawbridge](https://nethackwiki.com/wiki/Drawbridge)
4. **Force bolt / striking is destructive.** It is not interchangeable with opening. [NetHackWiki: Drawbridge](https://nethackwiki.com/wiki/Drawbridge)
5. **The center is not empty after the soldiers.** The script places 27 additional shuffled monster-class spawns, plus four dragons, soldiers and aquatic monsters. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L156-L229)
6. **Do not assume all dragons have the same breath or resistance profile.** The Castle script creates dragon-class monsters; identify the live species before selecting a resistance strategy. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L177-L190)
7. **A wrong passtune is not a safe default.** Use a proper candidate parser; do not hard-code a single five-note sequence. [5.0 `src/music.c::do_play_instrument()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/music.c#L742-L849)
8. **The 5.0 chest contents differ from 3.6.7.** Expect the potion of gain level in addition to the wand of wishing, but base the bot's pickup on what the chest actually contains. [5.0 `dat/castle.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/castle.lua#L137-L147) [3.6.7 `dat/castle.des`](https://github.com/NetHack/NetHack/blob/NetHack-3.6.7_Released/dat/castle.des#L134-L140)

## Open questions

- Exact NLE keymap and the instrument-application prompt sequence for the configured build: **UNVERIFIED**. The standard commands are `a` to apply and the instrument's note prompt is source-verified, but wrapper rendering must be tested.
- Exact passtune code-generation distribution (whether repeated notes are always permitted and any constraints on the five notes): **UNVERIFIED** here. The solver should support repeated symbols and use observed feedback rather than assume a permutation.
- Whether aquatic monsters can hit the levitating hero from the water edge in the specific 5.0 ruleset: **UNVERIFIED** for this note; keep distance regardless.
- All other 3.6-to-5.0 Castle differences beyond the additional potion of gain level and Lua map-script representation: **UNVERIFIED**.
