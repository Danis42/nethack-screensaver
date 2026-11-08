# R16 Valkyrie intrinsics and key-item timeline

## Summary

- A neutral human Valkyrie is a valid 5.0.0 character. In the 5.0-linked Valkyrie role data, the intrinsic progression is **cold resistance at XL1, stealth at XL3, speed at XL7**. The 5.0 role change matters: old 3.6/early-3.7 guides that give stealth at game start are stale for this version. [Valkyrie](https://nethackwiki.com/wiki/Valk); [NetHack 5.0.0 `src/attrib.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/attrib.c#L81).
- There is no verified fixed dungeon depth at which a normal run finds poison resistance, telepathy, magic resistance, reflection, free action, speed boots, levitation or a pick-axe. The timeline below gives planning milestones and likely search windows—not guaranteed item drops.
- Before the Valkyrie Quest, the published Norn dialogue explicitly says the hero needs to be immune to fire to face Lord Surtur; the usual access requirements are XL14, original alignment, no helm of opposite alignment and alignment record at least 20. [Valkyrie Quest](https://nethackwiki.com/wiki/Valkyrie_quest); [Quest](https://nethackwiki.com/wiki/Quest).
- Before Medusa, equip a confirmed reflection source or have a reliable blindness/avoidance plan before entering her gaze. Reflection directly blocks Medusa's stoning gaze. Medusa's Island is between DL21 and DL28. [Reflection](https://nethackwiki.com/wiki/Reflection); [Medusa's Island](https://nethackwiki.com/wiki/Medusa's_Island).
- Before the Castle/endgame, prioritize both magic resistance and reflection; free action is a strong additional defensive property. In 5.0.0 dragon mail properties changed: green gives poison resistance, gray magic resistance, silver reflection, orange free action, red fire resistance, and blue very fast speed. [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail); [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance).
- The Valkyrie quest artifact, the Orb of Fate, is a major defensive item, but it is **not** magic resistance: while carried it grants warning, half spell damage, half physical damage and luckstone effects. [Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate).

## Facts

| claim | source | version | confidence high/medium/low |
|---|---|---|---|
| Neutral human Valkyries are a valid role/race/alignment combination; Valkyries are always female. | [NetHackWiki: Valkyrie](https://nethackwiki.com/wiki/Valk) | Current wiki page cites NetHack 5.0 role source; 5.0.0. | high |
| A human Valkyrie begins with a +1 spear (wielded), +0 dagger, +3 small shield, 1–2 uncursed food rations, and a pet that is a little dog or kitten; there is a 1-in-6 oil lamp chance. | [NetHackWiki: Valkyrie](https://nethackwiki.com/wiki/Valk), citing [NetHack 5.0.0 `src/u_init.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/u_init.c#L769) | NetHack 5.0.0. | high |
| Valkyrie intrinsics: XL1 cold resistance; XL3 stealth; XL7 speed. | [NetHackWiki: Valkyrie](https://nethackwiki.com/wiki/Valk), citing [NetHack 5.0.0 `src/attrib.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0/src/attrib.c#L81) | NetHack 5.0.0. | high |
| In earlier versions, Valkyrie stealth was available at the start; the 5.0 role progression moves stealth to XL3. Do not copy the old starting-stealth assumption into a 5.0.0 policy. | [NetHackWiki: Valkyrie history](https://nethackwiki.com/wiki/Valk) | Historical versions before 5.0 versus NetHack 5.0.0. | high |
| The 5.0.0 Guidebook says `#attributes` is the default `^X` command and displays current status information in unabbreviated form; the status line can expose HP, level, dungeon depth, hunger, encumbrance, fatal/nonfatal conditions and movement modifiers such as `Lev`. | [NetHack 5.0.0 Guidebook, status / `#attributes`](https://nethack.org/v500/Guidebook.html) | NetHack 5.0.0. | high |
| The 5.0.0 Guidebook maps `i` to inventory, `P` to put on accessories, `W` to wear armor, `R`/`T` to remove accessories/armor, `a` to apply a tool, `q` to quaff, and `w` to wield. | [NetHack 5.0.0 Guidebook, commands](https://nethack.org/v500/Guidebook.html) | NetHack 5.0.0. | high |
| NetHack 5.0.0 standard poison effects can include additional HP damage, physical-attribute loss, and severe poisoning that inflicts 10–30 HP damage, reduces maximum HP by half that damage and drains 3 Constitution. Poison resistance blocks most ordinary poison attack effects; poison remains dangerous and can still be lethal through damage or special cases. | [NetHackWiki: Poison](https://nethackwiki.com/wiki/Poison), citing NetHack 5.0.0 `src/attrib.c` functions `poison_strdmg()` and `poisoned()` at lines 272–408 | NetHack 5.0.0. | high |
| The old 3.6.7-style “poison can instantly kill the hero” assumption is not a safe general rule for 5.0.0: the 5.0.0 poison overhaul replaces ordinary hero poison instadeath with severe poison effects; special cases and HP depletion can still kill. | [NetHackWiki: Poison resistance](https://nethackwiki.com/wiki/Poison_resistance), 5.0.0 change reference `d0b11fd2`; [NetHackWiki: Poison](https://nethackwiki.com/wiki/Poison) | NetHack 3.6.7 historical behavior versus NetHack 5.0.0. | high |
| Wearing green dragon scale mail grants poison resistance and sickness resistance; wearing gray dragon scale mail grants magic resistance; silver grants reflection; orange grants sleep resistance and free action; red grants fire resistance and infravision; blue grants shock resistance and very fast speed. The wiki explicitly says its revised properties are implemented in stable 5.0.0. | [NetHackWiki: Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail), section “Strategy” and table; [NetHack 5.0.0 change note](https://nethackwiki.com/wiki/Dragon_scale_mail) | NetHack 5.0.0. | high |
| Dragon scale mail is not randomly generated as such; it can be wished for, occur in bones, or be made by reading a non-cursed scroll of enchant armor while wearing the matching dragon scales. | [NetHackWiki: Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail) | Current page explicitly describes stable 5.0.0 properties; 5.0.0. | high |
| Extrinsic telepathy detects non-mindless monsters; intrinsic telepathy detects non-mindless monsters across the current level only while blind. The page's 3.7-specific expanded range rule is labeled “upcoming 3.7.0”; its exact 5.0.0 application should be checked against the pinned build before using distances. | [NetHackWiki: Telepathy](https://nethackwiki.com/wiki/Strange_mental_acuity) | Core behavior described on current page; exact expanded range for 5.0.0 **UNVERIFIED** (page labels it upcoming 3.7.0). | medium |
| Magic resistance protects against many hostile magical effects, including external death magic, polymorph traps, magic missile damage and teleport/level-teleport traps. Listed sources include cloak of magic resistance, gray dragon scale mail, wielded Magicbane and certain role-specific quest artifacts. | [NetHackWiki: Magic resistance](https://nethackwiki.com/wiki/Magic_resistance) | Current NetHack rules; page not explicitly tagged as 5.0.0. Confirm target build if a changed interaction matters. | medium |
| The neutral Valkyrie's Orb of Fate grants warning, half spell damage, half physical damage and luckstone effects while carried; its invocation causes level teleport. It is not listed as a source of magic resistance. | [NetHackWiki: Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate); [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance) | Valkyrie artifact data in current wiki; exact 5.0.0 source verification **UNVERIFIED**. | medium |
| Reflection protects against Medusa's stoning gaze and is granted by an amulet of reflection, shield of reflection, silver dragon scale mail, or certain artifacts. A normal mirror does not itself grant the passive property, though it can be applied. | [NetHackWiki: Reflection](https://nethackwiki.com/wiki/Reflection) | Current NetHack rules; exact 5.0.0 changes **UNVERIFIED**. | high |
| Free action protects against many forms of paralysis. The older page still labels orange dragon scale mail as an upcoming 3.7 change, but the stable 5.0.0 dragon-mail table explicitly includes free action on orange scales/mail. | [NetHackWiki: Free action](https://nethackwiki.com/wiki/Free_action); [NetHackWiki: Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail) | Orange dragon armor property explicitly implemented in NetHack 5.0.0; older Free action page wording is stale. | high |
| Levitation can be acquired from a ring, boots, potion, spell, or other special sources; `Lev` is one of the 5.0.0 Guidebook's movement modifiers. | [NetHackWiki: Levitation](https://nethackwiki.com/wiki/Levitating); [NetHack 5.0.0 Guidebook](https://nethack.org/v500/Guidebook.html) | Guidebook display is 5.0.0; full source list is current wiki, exact 5.0.0 source list **UNVERIFIED**. | medium |
| A pick-axe can be applied to dig rock/walls, doors, floors, boulders and statues; it can also be wielded as a weapon. The Castle's floor is documented as non-diggable, though its maze-part walls may be diggable. | [NetHackWiki: Pick-axe](https://nethackwiki.com/wiki/Pick_Axe); [Castle](https://nethackwiki.com/wiki/Castle) | Pick-axe page is current; Castle page has a stale section explicitly marked “upcoming 3.7.0”; 5.0.0 map details beyond the general diggability summary **UNVERIFIED**. | medium |
| Quest access is normally requested between DL11 and DL16. To receive permission, the hero must be of original alignment, not wear a helm of opposite alignment, have alignment record at least 20, and be XL14 or higher. | [NetHackWiki: Quest](https://nethackwiki.com/wiki/Quest) | Current wiki general rule; exact 5.0.0 source cross-check **UNVERIFIED**. | medium |
| The Valkyrie quest leader Norn says: “To face Lord Surtur, you will need to be immune to fire.” The Quest artifact is the neutral Orb of Fate. | [NetHackWiki: Valkyrie quest](https://nethackwiki.com/wiki/Valkyrie_quest); [Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate) | Current wiki content; exact 5.0.0 dialog/source verification **UNVERIFIED**. | medium |
| Sokoban stairs are listed at Dungeons of Doom DL6–10 inclusive, one level below the Oracle; there are four Sokoban floors. | [NetHackWiki: Sokoban](https://nethackwiki.com/wiki/Soko) | Current wiki general rule; exact 5.0.0 level generation **UNVERIFIED**. | medium |
| Medusa's Island is described at DL21–28, one to four levels above the Castle; the level is non-teleport. | [NetHackWiki: Medusa's Island](https://nethackwiki.com/wiki/Medusa's_Island) | Current wiki general rule; exact 5.0.0 map-generation cross-check **UNVERIFIED**. | medium |
| The Castle is described at DL25–29, just above the Valley, non-teleport and with undiggable floor; the wiki says a wand of wishing is guaranteed. Its detailed map section still contains a stale “upcoming 3.7.0” warning. | [NetHackWiki: Castle](https://nethackwiki.com/wiki/Castle) | General Castle placement/traits on current page; exact 5.0.0 map details **UNVERIFIED**. | medium |

## Bot rules

For all equipment rules, `<letter>` means the inventory letter printed by the current `i` output. The bot must re-read inventory immediately before issuing it because letters can change. The 5.0.0 Guidebook documents `^X` for `#attributes`, `P` for accessories, `W` for armor, `a` for tools, `q` for potions and `i` for inventory. [Guidebook](https://nethack.org/v500/Guidebook.html).

1. **Audit class intrinsics after gaining experience**
   - **Trigger =** Status line `Exp:3` or `Exp:7`, or `Exp:1` at game start; alternatively the experience level value changes.
   - **Action =** Press `^X`; parse the full `#attributes` output. Record cold resistance, stealth and speed only if the actual output confirms them. Do not infer XL3 stealth or XL7 speed from dungeon depth.
   - **Done when =** `#attributes` has been parsed and the bot's intrinsic set matches the observed output.
   - **If it fails =** Keep the intrinsic state unknown and reissue `^X` after the next stable prompt; do not assume the old pre-5.0 starting-stealth rules.
   - **Evidence =** 5.0.0 role intrinsic table; 5.0.0 Guidebook `#attributes`. [Valkyrie](https://nethackwiki.com/wiki/Valk); [Guidebook](https://nethack.org/v500/Guidebook.html).

2. **Equip confirmed poison resistance**
   - **Trigger =** Inventory `i` contains an identified `green dragon scale mail`, `ring of poison resistance`, `amulet versus poison`, or another item whose property has been verified by this build; alternatively `^X` confirms poison resistance intrinsically.
   - **Action =** For body armor: press `W`, then the current `<letter>` for the identified green dragon armor. For ring/amulet: press `P`, then `<letter>`; answer a right/left slot prompt only after parsing the exact prompt and selecting a free/appropriate slot. Press `^X` to verify the property.
   - **Done when =** `#attributes` or authoritative equipment state confirms poison resistance is active.
   - **If it fails =** Re-read `i` and `^X`; if the item is not identified or wearing it would remove more important protection, do not equip blindly. Keep poison-capable monsters at a distance until a safe source is equipped.
   - **Evidence =** 5.0.0 green dragon mail properties; poison resistance effects. [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail); [Poison](https://nethackwiki.com/wiki/Poison); [Guidebook](https://nethack.org/v500/Guidebook.html).

3. **Track and use telepathy conservatively**
   - **Trigger =** `^X` lists telepathy, or inventory `i` lists an identified helm of telepathy / amulet of ESP, or a verified intrinsic is reported.
   - **Action =** If equipping a helm, press `W` then `<letter>`; if an accessory that grants ESP is confirmed, press `P` then `<letter>`. Re-read `^X`. Use blind telepathy only when the bot has a safe plan for acting while blind; do not blind itself near unknown threats just to reveal monsters.
   - **Done when =** The full status says telepathy is active and the map observation is interpreted according to the source (intrinsic only while blind; extrinsic can reveal nearby non-mindless monsters).
   - **If it fails =** Treat unseen map cells as unknown. Do not use the wiki's expanded `8*sqrt(n)` radius until it is verified against the exact 5.0.0 build.
   - **Evidence =** [Telepathy wiki page](https://nethackwiki.com/wiki/Strange_mental_acuity); 5.0.0 Guidebook. Exact expanded radius is **UNVERIFIED** for this policy.

4. **Get magic resistance before deep endgame exposure**
   - **Trigger =** `i` contains an identified `cloak of magic resistance`, gray dragon scale mail, or `Magicbane`; or `^X` already lists magic resistance. The bot is preparing for the Castle, Wizard of Yendor, Gehennom or Astral.
   - **Action =** For cloak/gray DSM: `W`, then `<letter>`. For Magicbane: `w`, then `<letter>` only if the local weapon policy approves replacing the primary weapon. For the Quest artifact, do not mark MR merely because the item is the Orb of Fate; press `^X` and confirm actual properties.
   - **Done when =** `^X` or exact known property state confirms MR active without removing a more important protection.
   - **If it fails =** Treat MR as absent; do not count the Orb of Fate as MR; use deterministic avoidance/escape against death magic and other MR-gated attacks.
   - **Evidence =** [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance); [Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate); [5.0.0 Guidebook](https://nethack.org/v500/Guidebook.html).

5. **Require reflection before entering Medusa's gaze**
   - **Trigger =** Special-level recognizer identifies Medusa's Island, or visible monster identification says `Medusa`; map indicates line-of-sight route may expose the hero to Medusa.
   - **Action =** Before moving into sight, inspect `i` and `^X`. If an identified shield of reflection / silver dragon scale mail is carried, press `W` then `<letter>`; for an amulet, press `P` then `<letter>`. Re-read `^X` and confirm reflection. Prefer passive reflection over relying on a one-shot mirror. Blindness/avoidance is a fallback only if the deterministic controller can maintain it safely.
   - **Done when =** Reflection is confirmed active, or the bot has chosen and validated a route that avoids Medusa's gaze entirely.
   - **If it fails =** Do not step into line of sight; retreat to a safe tile and search for a confirmed source or request a high-level policy decision.
   - **Evidence =** Reflection directly blocks Medusa's stoning gaze; sources are listed on the reflection page. [Reflection](https://nethackwiki.com/wiki/Reflection); [Medusa's Island](https://nethackwiki.com/wiki/Medusa's_Island).

6. **Use free action as a paralysis safeguard**
   - **Trigger =** Inventory `i` lists an identified ring of free action or orange dragon scale mail; or `^X` lists free action. Higher priority before areas with paralysis threats.
   - **Action =** Ring: `P`, then `<letter>`, then answer any hand-selection prompt using only the captured choices. Orange dragon scale mail: `W`, then `<letter>`. Verify with `^X`.
   - **Done when =** The full status/equipment model confirms free action.
   - **If it fails =** Re-read the prompt and inventory; do not repeat `P` blindly or assume the stale wiki “ring only” sentence applies to 5.0.0.
   - **Evidence =** 5.0.0 dragon-mail page includes orange free action; free action mitigates many paralysis sources. [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail); [Free action](https://nethackwiki.com/wiki/Free_action).

7. **Prepare a controlled levitation source for water/air transitions**
   - **Trigger =** Map recognizer identifies a water/moat crossing or a plane/transition that requires levitation/flying; inventory `i` contains identified levitation boots/ring/potion, or `^X` reports levitation.
   - **Action =** Boots: `W`, then `<letter>`. Ring: `P`, then `<letter>`. Potion: `q`, then `<letter>` only when the route is ready and duration risk is acceptable. Re-read status; check for `Lev` in the status line or full `^X` output.
   - **Done when =** `Lev` is active and a safe landing/disable/route plan exists, or the obstacle has been crossed.
   - **If it fails =** Stop movement toward water/void; do not consume a time-limited potion while exploring or fighting unless the local route planner can finish within its verified duration.
   - **Evidence =** [Levitation](https://nethackwiki.com/wiki/Levitating); 5.0.0 Guidebook `Lev` status field.

8. **Acquire and manage a pick-axe as utility, not default weapon**
   - **Trigger =** `i` lists an identified `pick-axe`; alternatively the map has a known rock wall, diggable door or boulder on a route required by the path planner.
   - **Action =** Press `a`, then `<letter>`, then the direction key corresponding to the target tile from the current map. If interrupted or a hostile enters range, stop digging and press `w`, then the normal weapon's current `<letter>` to restore combat readiness.
   - **Done when =** The planned obstacle is opened/removed and the resulting map is re-parsed.
   - **If it fails =** Do not repeat into a non-diggable tile; check the Castle floor flag and special-level rules. Do not dig through a shop/watch-protected wall or door without an explicit cost/hostility policy.
   - **Evidence =** [Pick-axe](https://nethackwiki.com/wiki/Pick_Axe); [Castle](https://nethackwiki.com/wiki/Castle); 5.0.0 Guidebook `a`, `w` commands. Castle page's detailed map section is labeled upcoming 3.7.0, so test 5.0.0 diggability in-engine.

9. **Do not enter the Valkyrie Quest without its fire gate**
   - **Trigger =** Quest portal/branch recognizer found; or the Norn interaction includes the exact published warning text `To face Lord Surtur, you will need to be immune to fire.`; character status is below the Quest's usual XL14/alignment requirements.
   - **Action =** Read `^X` and check fire resistance, XL, alignment and alignment record; check `i` for an identified red dragon scale mail source. If carrying red dragon armor, press `W`, then `<letter>` and verify fire resistance. Enter only when the bot's Quest gate passes: XL at least 14, original neutral alignment, alignment record at least 20, no helm of opposite alignment, and fire resistance active.
   - **Done when =** Norn grants permission and the fire-resistance property is confirmed before descending to Lord Surtur.
   - **If it fails =** Leave via the return portal and resume preparation; do not assume cold resistance or the Orb of Fate substitutes for fire resistance.
   - **Evidence =** [Quest access rules](https://nethackwiki.com/wiki/Quest); [Valkyrie quest dialogue](https://nethackwiki.com/wiki/Valkyrie_quest); [5.0.0 dragon mail](https://nethackwiki.com/wiki/Dragon_scale_mail).

10. **Do not approach Medusa until reflection or safe avoidance is proven**
    - **Trigger =** Current special-level recognizer says Medusa's Island / `DL21–28`, or monster parser positively identifies Medusa; do not use a guessed glyph alone.
    - **Action =** Run rule 5. If no reflection is available, retreat, blind before entering gaze range only if the movement/attack controller is explicitly validated, or avoid the Medusa room. Do not rely on an untested mirror interaction as the only protection.
    - **Done when =** Reflection is active or a validated no-gaze route is selected.
    - **If it fails =** Retreat to last safe tile. Since the island is non-teleport, do not use teleport as an assumed escape.
    - **Evidence =** [Medusa's Island](https://nethackwiki.com/wiki/Medusa's_Island); [Reflection](https://nethackwiki.com/wiki/Reflection).

11. **Castle preflight: defensive properties and no-teleport/no-dig assumptions**
    - **Trigger =** Castle recognizer confirms the level or the bot's branch graph places it immediately above Valley of the Dead.
    - **Action =** Press `^X`; require confirmed magic resistance and reflection for the endgame policy; add free action if available. Verify healing, ranged options and an exit/escape plan; do not schedule floor-digging or level teleport as routine Castle escape. Preserve the pick-axe only for diggable maze walls if the active 5.0.0 map permits.
    - **Done when =** Preflight state is logged and all hard policy gates pass; otherwise remain at a safe approach tile.
    - **If it fails =** Retreat to Valley/previous safe level; mark unavailable protections as missing and revise the strategy rather than assuming the Castle's guaranteed wand of wishing will be accessible without risk.
    - **Evidence =** [Castle](https://nethackwiki.com/wiki/Castle); [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance); [Reflection](https://nethackwiki.com/wiki/Reflection); [Free action](https://nethackwiki.com/wiki/Free_action). Castle map details contain stale 3.7 wording; verify against pinned 5.0.0 data.

### Practical progression timeline (milestones, not guaranteed drops)

| phase | expected milestone / search objective | bot interpretation and evidence |
|---|---|---|
| Start / XL1 | Cold resistance is already intrinsic. Starting gear includes spear, dagger, shield, rations and pet. | Do not spend turns searching for cold resistance before it is needed. [Valkyrie](https://nethackwiki.com/wiki/Valk). |
| Early game / XL3 | Stealth intrinsic becomes active. | Update the intrinsic ledger only after status verification. [Valkyrie](https://nethackwiki.com/wiki/Valk). |
| Early-to-mid / XL7 | Speed intrinsic becomes active. This is the Valkyrie's baseline speed power; speed boots can be a further upgrade, not a prerequisite for the intrinsic. | Track `speed` separately from item source. Exact point when speed boots are found in a typical run: **UNVERIFIED**. [Valkyrie](https://nethackwiki.com/wiki/Valk); [Speed](https://nethackwiki.com/wiki/Speed). |
| Early-to-mid dungeon | Search shops, floor items and suitable monster drops for a pick-axe; Gnomish Mines are a natural place to notice dwarven tunneling gear, but no fixed acquisition floor is established here. | Pick-axe is a tool; apply with `a`, do not keep it wielded as the default weapon. Exact Mines access/dwarf drop timeline in 5.0.0: **UNVERIFIED**. [Pick-axe](https://nethackwiki.com/wiki/Pick_Axe). |
| Around DL6–10 | Sokoban branch entrance is listed one level below Oracle. | This is a branch/loot milestone, not a guarantee of reflection, levitation or any specific armor. 5.0.0 level-generation cross-check: **UNVERIFIED**. [Sokoban](https://nethackwiki.com/wiki/Soko). |
| Before Quest / portal request DL11–16 | Reach XL14 and alignment record 20 while retaining original neutral alignment; obtain fire resistance for Lord Surtur. | Red dragon scale mail is a 5.0.0 fire-resistance source. Exact normal depth of acquiring red dragon scale mail: **UNVERIFIED**. [Quest](https://nethackwiki.com/wiki/Quest); [Valkyrie quest](https://nethackwiki.com/wiki/Valkyrie_quest); [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail). |
| Midgame to Medusa / DL21–28 | Have confirmed reflection before entering Medusa's gaze; have a route/means for any water moat. | Reflection is a real hard safety gate; levitation is useful but not universally mandatory. Exact item acquisition depth: **UNVERIFIED**. [Medusa's Island](https://nethackwiki.com/wiki/Medusa's_Island); [Reflection](https://nethackwiki.com/wiki/Reflection); [Levitation](https://nethackwiki.com/wiki/Levitating). |
| Castle / DL25–29 | Confirm magic resistance, reflection and preferably free action; carry resources for a high-monster-density no-teleport level. | Blue dragon mail gives very fast speed, but the Valkyrie already has intrinsic speed at XL7. Exact typical gear acquisition depths: **UNVERIFIED**. [Castle](https://nethackwiki.com/wiki/Castle); [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance); [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail). |
| Quest reward | Orb of Fate can provide warning, half spell damage, half physical damage and luckstone effects while carried. | Do not mark MR or reflection from Orb of Fate; check each property individually. [Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate). |

## Risks and exceptions

- **Random gear has no reliable dungeon-level acquisition schedule.** A timeline saying “get MR at DLx” or “find speed boots by DLy” would be invented. Treat the table as search phases and readiness gates only.
- **Do not use 3.6 assumptions for poison.** In 5.0.0, ordinary poison exposures can deal extra HP damage, damage attributes and reduce maximum HP in severe cases; it is still dangerous, and resistance remains valuable. Avoid writing “poison can never instakill” as a universal rule: special poison sources and lethal HP damage remain exceptions. [Poison](https://nethackwiki.com/wiki/Poison), citing 5.0.0 `src/attrib.c`.
- **Dragon armor has material 5.0.0 changes.** Old guides may list blue/green/orange/red/white dragon mail without its added secondary effects. The current 5.0.0 page explicitly lists them; pin the actual game build before using any appearance or property inference. [Dragon scale mail](https://nethackwiki.com/wiki/Dragon_scale_mail).
- **Telepathy's exact 3.7-expanded radius is not safe to hard-code from the current page alone.** The page still labels that rule “upcoming 3.7.0”; test with the pinned 5.0.0 executable. The basic intrinsic-while-blind distinction is suitable as a conservative rule, but range values are **UNVERIFIED** here. [Telepathy](https://nethackwiki.com/wiki/Strange_mental_acuity).
- **Quest, Sokoban, Medusa and Castle depth bands come from current NetHackWiki pages, not a line-by-line 5.0.0 level-generation source audit.** The Castle page still marks its detailed map as upcoming 3.7.0. Use those ranges as guidance, not a guaranteed level-number oracle.
- **Reflection and magic resistance are different properties.** Reflection is not granted by a normal mirror as passive equipment; magic resistance does not replace reflection against Medusa. The Orb of Fate is defensive but is not a source of MR. [Reflection](https://nethackwiki.com/wiki/Reflection); [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance); [Orb of Fate](https://nethackwiki.com/wiki/Orb_of_Fate).
- **Armor-slot conflicts matter.** Gray/green/red/silver/orange/blue DSM all occupy body armor; swapping one color for another may remove a previously useful resistance. Accessories may also compete for ring/amulet slots. Re-evaluate the complete active property set after each equipment change.
- **NLE observation text can differ by wrapper and terminal settings.** Do not require a string not actually present in the 5.0.0/NLE screen. Parse current inventory letters and prompt text dynamically; never blindly answer a menu or direction prompt.

## Open questions

- Does the exact NetHack 5.0.0 build used by the bot expose every relevant intrinsic/extrinsic in `^X` with stable machine-parseable labels? Capture fixtures for all target properties.
- What is the exact NetHack 5.0.0 level-generation range for Sokoban entrance, Quest message/portal, Medusa's Island and Castle in the pinned source commit?
- Which monster corpses, tins, prayers or other sources are safest/reliable for gaining poison resistance or telepathy in the target build, and what are their actual 5.0.0 probabilities?
- Can a 5.0.0 neutral human Valkyrie safely complete Medusa without passive reflection using only blindness/cancellation/route avoidance? This should be tested as a policy alternative, not assumed.
- Which defensive kit has the highest empirical ascension rate under the bot's item-generation distribution: gray DSM versus MR cloak, silver DSM versus shield/amulet reflection, orange DSM versus ring of free action, and blue DSM versus separate speed boots?
- Which named human 5.0.0 neutral human Valkyrie dumplogs provide a defensible empirical distribution of dungeon depth at first acquisition of poison resistance, telepathy, MR, reflection, free action, speed boots, levitation and pick-axe? No such matched dump set was verified for this file.
