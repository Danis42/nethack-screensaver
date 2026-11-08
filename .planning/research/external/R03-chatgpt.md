# R03 Dangerous monsters at XL 6–9 (A)

## Summary

- Mumak: speed 9, AC 0, attacks with a 4d12 butt and 2d6 bite. It is the best candidate of these four for walking away from, provided the Valkyrie is not encumbered. Its potential melee damage is enormous.
- Soldier ant: speed 18, AC 3, with a 2d4 bite and 3d4 poisonous sting. It can outrun an intrinsically fast Valkyrie (average speed 16). Treat it as an escape-or-ranged-combat threat.
- Owlbear: speed 12, AC 5, with two 1d6 claws and a 2d8 grabbing attack. The grabbing attack makes it dangerous even though it is no faster than a normal hero.
- Leocrotta: speed 18, AC 4, with three 2d6 physical attacks. It is both faster than the intrinsically fast Valkyrie and capable of substantial consecutive damage.
- Elbereth works against all four species on eligible levels, because none is among the written-Elbereth-resistant species. However, 5.0 introduced a dangerous exception: a scared hostile monster that cannot move away can attack anyway. A narrow corridor can therefore make a scare strategy dangerous.
- With 60–85 maximum HP and AC around -3, none of these monsters should be given a universal safe melee threshold. Use HP-based damage bounds as emergency estimates, not guarantees.

## Facts

### Monster statistics

All four monster definitions below are verified against `NetHack-5.0.0_Released/include/monsters.h`. In `LVL(level, speed, AC, MR, alignment)`, the third field is the monster's base AC.

| Monster     | Base level | Speed | Base AC | Attacks per attack sequence  | Maximum raw damage if all attacks hit                  | Source                                                                                                                                         | Version | Confidence |
| ----------- | ---------- | ----- | ------- | ---------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| Mumak       | 5          | 9     | 0       | Butt 4d12; bite 2d6          | 60 physical                                            | [`monsters.h`, mumak](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L833-L840)      | 5.0.0   | high       |
| Soldier ant | 3          | 18    | 3       | Bite 2d4; sting 3d4 poison   | 20 dice damage, excluding additional poisoning effects | [`monsters.h`, soldier ant](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L98-L105) | 5.0.0   | high       |
| Owlbear     | 5          | 12    | 5       | Claw 1d6; claw 1d6; hug 2d8  | 28 physical                                            | [`monsters.h`, owlbear](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L2380-L2387)  | 5.0.0   | high       |
| Leocrotta   | 6          | 18    | 4       | Claw 2d6; bite 2d6; claw 2d6 | 36 physical                                            | [`monsters.h`, leocrotta](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L841-L848)  | 5.0.0   | high       |

The maximums in this table are theoretical dice maximums, assuming every attack hits and before any damage-reducing effects. They are not estimates of the damage the hero will necessarily take in a single turn.

### Speed and the fast Valkyrie

| Claim                                                                                                                                            | Source                                                                                                                                              | Version                     | Confidence |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ---------- |
| Valkyries gain intrinsic fast speed at experience level 7.                                                                                       | [`src/attrib.c`, role intrinsic initialization](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/attrib.c?utm_source=chatgpt.com) | 5.0.0                       | high       |
| Normal hero movement rate is 12; intrinsic fast increases the average rate to 16.                                                                | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                     | Current Wiki; 5.0 mechanics | high       |
| Burdened fast hero movement falls to 12; stressed fast movement falls to 8.                                                                      | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                     | Current Wiki; 5.0 mechanics | high       |
| A monster with speed 18 averages 1.5 movement actions per hero turn; speed 12 gives one movement action per turn.                                | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                     | Current Wiki; 5.0 mechanics | high       |
| Soldier ants and leocrottas are faster than a fast Valkyrie even when unburdened.                                                                | Monster definitions above and [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                       | 5.0.0                       | high       |
| A mumak is slower than an unencumbered fast Valkyrie. An owlbear is slower than an unencumbered fast Valkyrie, but equal to a normal-speed hero. | Monster definitions above and [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                       | 5.0.0                       | high       |

The relevant speed comparison is:

| Monster     | Base speed | Hero speed at XL 6 | Hero speed at XL 7+, unencumbered | Can the hero reliably walk away?          |
| ----------- | ---------- | ------------------ | --------------------------------- | ----------------------------------------- |
| Mumak       | 9          | 12                 | 16                                | Yes, provided movement and terrain permit |
| Soldier ant | 18         | 12                 | 16                                | No                                        |
| Owlbear     | 12         | 12                 | 16                                | Only with intrinsic fast                  |
| Leocrotta   | 18         | 12                 | 16                                | No                                        |

Important: movement speed is not the same as the number of melee attacks a monster can make when adjacent. A monster can attack without moving. Do not infer that a slow mumak is harmless once it reaches melee range.

### Elbereth, stairs, wands and melee decisions

| Monster     | Walk away?                                                                     | Elbereth                                             | Stairs                                                          | Melee recommendation                                                                                   |
| ----------- | ------------------------------------------------------------------------------ | ---------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Mumak       | Yes, even at XL6, unless encumbered. At XL7, fast makes the separation easier. | Useful on eligible levels, in an open room.          | Excellent fallback; it does not follow the hero between levels. | Avoid if possible. The 60-damage theoretical attack-set maximum makes a low-HP fight dangerous.        |
| Soldier ant | No. Speed 18 exceeds the unburdened fast hero's average 16.                    | Good if there is room for it to flee.                | Excellent fallback; it does not follow.                         | Avoid without poison resistance or a strong immediate kill opportunity.                                |
| Owlbear     | At XL6, not reliably; at XL7+, yes if unburdened.                              | Useful in an open area.                              | Excellent fallback; it does not follow.                         | More manageable than the other three, but the grabbing attack and 28 maximum attack-set damage matter. |
| Leocrotta   | No. Speed 18 exceeds the unburdened fast hero's average 16.                    | Useful if it can actually escape from the engraving. | Excellent fallback; it does not follow.                         | Avoid unless it is nearly dead or the hero has a substantial HP margin.                                |

Elbereth and the panic attack

In 5.0, `onscary()` checks whether the monster is affected by a scare engraving. These four species have no species-specific written-Elbereth immunity. Written Elbereth does not work in Gehennom or the Endgame, however. [5.0 `src/monmove.c::onscary()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/monmove.c?utm_source=chatgpt.com#L2617-L2687)

The important 5.0 exception is the panic-attack path: when a scared monster cannot find a legal move, `dochug()` can set `panicattk`, allowing it to attack despite being scared. Therefore:

- Prefer an open room with several escape directions.
- Do not use a one-tile dead-end as an Elbereth refuge.
- Do not stand in a doorway that prevents the monster from moving away.
- Check whether the monster actually retreats; the existence of an engraving is not proof that it will remain harmless.

Source: [5.0 `src/monmove.c::dochug()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/monmove.c?utm_source=chatgpt.com#L847-L900).

Stair escape

The four species do not have the stalking flag that makes certain monsters follow the hero to another level. Ordinary hostile mumaks, soldier ants, owlbears and leocrottas therefore do not follow through the stairs. Tame monsters and the Wizard are separate exceptions. [5.0 `src/mondata.c::levl_follower()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mondata.c?utm_source=chatgpt.com#L1136-L1152) [5.0 `include/monsters.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L98-L105)

Wands

A known wand of sleep, slow monster or striking can be preferable to another sword exchange.

| Wand          | Suggested use                                | Limitation                                                                                                 |
| ------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Sleep         | Disable the threat, then retreat or attack.  | The monster may resist; do not assume the wand worked until the message/state confirms it.                 |
| Slow monster  | Create a chance to establish distance.       | Verify that the monster is actually slowed; do not assume one zap makes a speed-18 monster safe to outrun. |
| Striking      | Damage the target from range.                | It is damage, not guaranteed incapacitation.                                                               |
| Teleportation | Remove the monster from the immediate fight. | Can be blocked by level restrictions and is not necessarily a permanent solution.                          |

The monster definitions specify magic resistance of zero for mumak, soldier ant and owlbear, and 10 for leocrotta. This does not mean every wand is guaranteed to work on the first three: individual wand effects have their own resistance checks. Exact success probabilities for each wand/monster pair are UNVERIFIED here. [5.0 `include/monsters.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L98-L105) [5.0 `src/zap.c`](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/src?utm_source=chatgpt.com)

Melee HP limits

The maximum raw damage from one complete monster attack sequence is useful as a conservative warning, not a safe-fight guarantee:

| Monster     | Maximum raw attack-set damage             | Minimum current HP to survive that theoretical set, assuming every attack hits and no other damage |
| ----------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Mumak       | 60                                        | 61                                                                                                 |
| Soldier ant | 8 from bite, plus the poison-sting effect | No reliable HP-only threshold without accounting for poison resistance and poison consequences     |
| Owlbear     | 28                                        | 29                                                                                                 |
| Leocrotta   | 36                                        | 37                                                                                                 |

The maximums are dice maxima. They do not include other monsters, traps, or multiple monster actions made possible by speed. A leocrotta or soldier ant can get extra movement/action opportunities relative to the hero because its speed is 18. An owlbear may also grab the hero. Sources: 5.0 `monsters.h` attack definitions and `src/monmove.c::dochug()`.

Prayer as an emergency resource

For a hero at XL6–9, the 5.0 low-HP test used by the trouble assessment is approximately one-sixth of maximum HP, with a separate absolute threshold of 5 HP. For a maximum HP of 60–85, that corresponds to approximately 10–14 HP. This is a game-defined emergency threshold, not a tactical target to wait for. [5.0 `src/pray.c::critically_low_hp()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c?utm_source=chatgpt.com#L102-L143)

Prayer has a cooldown and can fail if the deity is displeased or the prayer is too soon. An accepted emergency prayer takes time; it is not a normal combat action to spam. The `#pray` command is `M-p` under the standard keymap. [5.0 `src/pray.c::can_pray()` and `dopray()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c?utm_source=chatgpt.com#L2041-L2154) [5.0 Guidebook, Commands](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Commands)

## Bot rules

### Rule 1 — Identify and classify the dangerous monster

- Trigger = The screen or monster-identification output names `mumak`, `soldier ant`, `owlbear`, or `leocrotta`. A glyph by itself may be ambiguous; for example, quadrupeds share the `q` glyph.
- Action =
  1. Record monster identity, position and distance.
  2. Read the hero's experience level and encumbrance status.
  3. If the monster is mumak or owlbear and the hero is unburdened with fast intrinsic, consider retreating.
  4. If the monster is soldier ant or leocrotta, do not use ordinary walking as the only escape plan.
- Done when = The bot has selected a monster-specific policy.
- If it fails = If species identification is unavailable, classify an ambiguous dangerous quadruped or ant as an unknown threat and retreat towards stairs or another escape resource.
- Evidence = 5.0 `include/monsters.h` species definitions; `NetHackWiki: Speed`.

### Rule 2 — Retreat from mumaks and owlbears when faster

- Trigger = The monster is named mumak or owlbear; status shows intrinsic fast and no burdened/stressed encumbrance.
- Action =
  1. Determine the direction from the monster to the hero.
  2. Press the opposite direction key (`h`, `j`, `k`, `l`, `y`, `u`, `b` or `n`, assuming vi movement).
  3. Re-read the map and status.
  4. Repeat only while distance increases and the retreat route remains safe.
- Done when = The monster is no longer visible or threatening, or the hero reaches stairs or another safe area.
- If it fails = If encumbrance changes or the distance stops increasing, use an escape item or stairs rather than continuing to assume a speed advantage.
- Evidence = 5.0 monster speeds in `monsters.h`; `NetHackWiki: Speed`; `NetHackWiki: Valkyrie`.

### Rule 3 — Use stairs to abandon a dangerous fight

- Trigger = Monster is one of the four targets, and a known up/down stair is accessible.
- Action =
  1. Move towards the known stair without moving adjacent to another threat.
  2. Stand on the stair tile.
  3. Press `<` for upstairs or `>` for downstairs.
  4. Confirm the new level and the monster's absence.
- Done when = The hero is on another level.
- If it fails = If blocked or the stair is occupied, use Elbereth or a known escape wand to create room. Do not spend repeated turns moving towards a stair while the faster monster is landing attacks.
- Evidence = 5.0 `src/mondata.c::levl_follower()`; 5.0 monster definitions.

### Rule 4 — Use Elbereth in an open escape area

- Trigger = An eligible level, no swallowing, a clear floor tile, and an approaching hostile target.
- Action =
  1. Press `E`.
  2. Select `-` for engraving with fingers, if the engraving-method prompt appears.
  3. Type `Elbereth`.
  4. Press Enter.
  5. Remain on the engraving tile while checking whether the monster flees.
  6. If it does not flee, or cannot find a legal escape, do not assume it is harmless.
- Done when = The monster has retreated sufficiently for the bot to escape or reach the stairs.
- If it fails = Move to an open area, use a wand, or leave via stairs. Do not wait for a monster that is blocked from fleeing.
- Evidence = 5.0 `src/monmove.c::onscary()` and `dochug()`.

### Rule 5 — Use known wands rather than repeated melee

- Trigger = A dangerous monster is visible, a known sleep/slow/striking/teleportation wand is available, and a clear direction to the target exists.
- Action =
  1. Press `z`.
  2. Select the known wand's inventory letter.
  3. Enter the direction towards the monster.
  4. Parse the result message.
  5. If sleep or slowing succeeded, retreat or reassess before using another attack.
- Done when = The threat is disabled, killed, removed, or no longer adjacent.
- If it fails = If the monster resists or continues moving normally, stop wasting turns on repeated ineffective zaps and use stairs or prayer if the emergency threshold is reached.
- Evidence = 5.0 `src/zap.c`; monster magic-resistance values in `include/monsters.h`.

### Rule 6 — Melee only when the risk is acceptable

- Trigger = The bot proposes a long-sword attack against one of the four monsters.
- Action = Compare current HP with the theoretical maximum attack-set warning above. For a soldier ant, also check poison resistance. Prefer melee only if the monster is already near death, the hero has sufficient HP margin, no second dangerous monster is present, and escape remains possible.
- Done when = The monster dies or the hero breaks contact.
- If it fails = If HP drops sharply, poison is applied, or the hero is grabbed, stop treating the fight as routine. Move to stairs or use the emergency resource policy.
- Evidence = 5.0 `include/monsters.h` attack definitions; `src/monmove.c::dochug()`.

### Rule 7 — Prayer only at genuine critical HP

- Trigger = Current HP is at or below the 5.0 critically-low-HP threshold (for these XLs, approximately one-sixth of max HP, or 5 HP).
- Action =
  1. Check that prayer cooldown permits a prayer.
  2. Press `M-p` (`#pray`).
  3. Observe the message and subsequent state.
  4. If prayer is rejected, do not repeat immediately.
- Done when = The hero is restored or otherwise no longer in critical danger.
- If it fails = Use an available escape item or staircase. Do not budget prayer as a guaranteed combat cooldown.
- Evidence = 5.0 `src/pray.c::critically_low_hp()`, `can_pray()` and `dopray()`.

## Risks and exceptions

1\. A damage maximum is not a full-turn survival guarantee. Speed-18 monsters can act more frequently than the hero, and the dice maxima are not average damage. Multiple attack opportunities can occur before the bot successfully retreats.

2\. Soldier-ant poison is not just extra damage. The sting is a poison attack. Poison can cause attribute loss or death, so a hero with 60–85 HP is not automatically safe merely because the nominal HP damage is survivable.

3\. AC -3 is helpful but not immunity. It does not make high-damage monsters safe to melee. A successful attack can still cause severe damage, especially when several attacks are packed into one monster action.

4\. Elbereth requires a real escape route. The 5.0 panic-attack behavior means a scared monster can attack if movement is impossible. Do not implement “engraving present = monster cannot attack” as a deterministic rule.

5\. The monster speed comparison assumes the hero is not encumbered. The status line should be read every turn. Fast intrinsic speed does not make a stressed hero faster than a speed-18 ant or leocrotta.

6\. Do not rely on a weapon-only solution. The hero's long sword may be strong enough to dispatch a target, but a missed attack does not stop the monster from taking its next action. A retreat route should be available before starting melee.

## Open questions

- Exact per-wand hit and resistance probabilities against these four monsters: UNVERIFIED for the particular NLE wrapper and wand configurations.
- Exact monster HP at spawn: UNVERIFIED from the ordinary terminal map. Monster HP is randomized and level-adjusted.
- Whether the bot's NLE observation exposes monster names or only glyphs: UNVERIFIED. If only glyphs are available, the `q` quadruped glyph cannot safely distinguish mumak from leocrotta.
- The observed 1152-game killer counts are the user's supplied data; their species frequencies and confidence intervals have not been independently verified.

