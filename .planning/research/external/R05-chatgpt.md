# R05 Enchant armour and early armour sources (A)

## Summary

- Enchant armour does not automatically target the best piece. `some_armor()` chooses a starting candidate from cloak, body armour, then shirt; worn helmet, gloves, boots, and shield can each replace that candidate with a 1-in-4 roll. Remove competing pieces if the bot needs to enchant a particular item. [5.0 `do_wear.c::some_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2493-L2515)
- The +3 ordinary / +5 elven limits are evaporation thresholds, not hard enchantment caps. An ordinary item at `+4` has a 3-in-4 evaporation chance on the next relevant read; an elven item at `+6` has a 5-in-6 chance. The corresponding safe stopping points are `+3` and `+5`. [5.0 `read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1127)
- Blessed scrolls give a larger enchantment roll. Uncursed scrolls also improve armour, while cursed scrolls decrease enchantment and curse the item. Reading while confused does not enchant the armour at all; it changes erosion-proofing instead. [5.0 `read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1072-L1100) [5.0 `read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1128-L1216)
- The Mines provide unusually good armour opportunities. Conditional on an ordinary dwarf being generated with inventory, it has a 1-in-12 chance of carrying a dwarvish mithril-coat, a 1-in-4 chance of a dwarvish iron helm, and a 1-in-8 chance of a dwarvish roundshield. [5.0 `makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L365-L384)
- Elven mithril-coats are especially good enchantment targets: base AC contribution `+5`, and the elven evaporation threshold. Elves have a 1-in-4 chance of carrying one; hobbits have a separate 1-in-10 chance. [5.0 `makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L215-L222) [5.0 `makemon.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L347-L364)
- The human-ascender AC benchmarks and the 79% / approximately three scrolls statistic are UNVERIFIED here. They are useful as targets for bot evaluation, but I have not found a named game sample or dumplog supporting those figures.

## Facts

### 1. Enchant armour mechanics

| Claim                                                                                                                                                                                                                                                     | Source                                                                                                                                                                                                                                                                            | Version | Confidence |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| The game calls `some_armor()` to select the item affected by a scroll of enchant armour. If no eligible armour is worn, the scroll is consumed with a strange-feeling message rather than enchanting anything.                                            | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1051-L1070)                                                                                                                                 | 5.0.0   | high       |
| The selection starts with cloak; if no cloak is worn, it uses body armour; if neither is worn, it uses a shirt.                                                                                                                                           | [`do_wear.c::some_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2493-L2502)                                                                                                                                      | 5.0.0   | high       |
| A worn helmet, gloves, boots, and shield are then considered in that order. Each replaces the current candidate if there is no candidate yet, or with a 1-in-4 chance otherwise.                                                                          | [`do_wear.c::some_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2503-L2515)                                                                                                                                      | 5.0.0   | high       |
| Rings and amulets are not candidates in `some_armor()`. They are not enchanted by a scroll of enchant armour.                                                                                                                                             | [`do_wear.c::some_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2493-L2515)                                                                                                                                      | 5.0.0   | high       |
| Elven armour for the special enchantment calculation comprises elven leather helm, elven mithril-coat, elven cloak, elven shield, and elven boots. A Valkyrie does not receive the Wizard's cornuthaum exception.                                         | [`obj.h::is_elven_armor`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L285) [`read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1102)                 | 5.0.0   | high       |
| For a non-cursed scroll, enchantment strength begins with `s = (4 - current_spe) / 2`, then receives a `+1` modifier for special (elven) armour, `+1` for nonmagical armour, and `+1` for a blessed scroll.                                               | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1128-L1153)                                                                                                                                 | 5.0.0   | high       |
| When the resulting strength is positive, the scroll gives a random increase from 1 through that strength. When the computed strength is nonpositive, there is normally no increase, with a rare one-point increase possible for already-enchanted armour. | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1145-L1153)                                                                                                                                 | 5.0.0   | high       |
| A blessed scroll adds one to the enchantment-strength calculation. The target armour is also blessed if it is not already blessed.                                                                                                                        | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1137-L1145) [`read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1185-L1216)        | 5.0.0   | high       |
| An uncursed scroll can increase enchantment and uncurse the target if it was cursed.                                                                                                                                                                      | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1128-L1157) [`read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1185-L1216)        | 5.0.0   | high       |
| A cursed scroll reverses the calculated enchantment change, decreasing the item's enchantment, and curses the target.                                                                                                                                     | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1112-L1157) [`read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1185-L1216)        | 5.0.0   | high       |
| Before the normal enchantment calculation, the code checks for evaporation. For ordinary armour it checks when the effective current enchantment is above `+3`; for special armour it checks above `+5`.                                                  | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1127)                                                                                                                                 | 5.0.0   | high       |
| When the evaporation check is active, the item evaporates if `rn2(s)` is nonzero. Thus ordinary armour at effective `+4` has a 3-in-4 evaporation risk; special armour at effective `+6` has a 5-in-6 risk.                                               | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1112-L1127)                                                                                                                                 | 5.0.0   | high       |
| For a cursed scroll, the effective enchantment used by the evaporation test is sign-reversed. Therefore, heavily negative-enchanted armour can also be at risk when a cursed scroll is read.                                                              | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1112-L1117)                                                                                                                                 | 5.0.0   | high       |
| If the hero is confused when reading the scroll, the normal enchantment and evaporation code is bypassed. A non-cursed scroll makes the selected armour erosion-proof and repairs erosion; a cursed scroll removes erosion-proofing.                      | [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1072-L1100)                                                                                                                                 | 5.0.0   | high       |
| The practical ordinary/elven thresholds are not the engine's absolute `spe` cap. The general item enchantment cap is much higher; it does not make it safe to enchant ordinary armour repeatedly beyond the evaporation threshold.                        | [`read.c::cap_spe()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L73-L81) [`read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1112-L1127) | 5.0.0   | high       |

Practical reading of the formula

The engine uses the current enchantment, armour category, whether the armour is elven/special, whether it is nonmagical, and the scroll's blessing. Therefore there is no single fixed “blessed scroll gives +N” rule that applies to all armour and all starting enchantments.

Examples for an item at `+0`:

| Target                     | Uncursed scroll | Blessed scroll | Explanation                                                           |
| -------------------------- | --------------- | -------------- | --------------------------------------------------------------------- |
| Ordinary nonmagical armour | +1 to +3        | +1 to +4       | Base strength 2, plus 1 for nonmagical armour; blessed adds another 1 |
| Elven nonmagical armour    | +1 to +4        | +1 to +5       | Adds the special/elven bonus too                                      |
| Ordinary magical armour    | +1 to +2        | +1 to +3       | No nonmagical bonus                                                   |

These ranges follow the formula in 5.0 `read.c::seffect_enchant_armor()`, including its `rnd(s)` result. They are not guarantees for an item at a different current `spe`. [5.0 source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1128-L1157)

### 2. Armour value and total AC

The human's base AC is 10 before equipment; lower AC is better. Worn armour contributes its protection rating, with enchantment added to that contribution. [5.0 Guidebook, Armour](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Armor)

`find_ac()` computes the hero's AC by subtracting the protection of the worn suit, cloak, helmet, boots, shield, gloves, and shirt. It also subtracts protection-ring enchantments, a fixed 2 for an amulet of guarding, and intrinsic/spell protection. [5.0 `do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2344-L2379)

\| Piece | Base AC contribution | Details and source | Version | Confidence |\
\|---|---:|---|---:|---|\
\| Dwarvish mithril-coat | +6 | Suit AC value 4; armour macro converts this to `10 - 4`. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L543-L545) [`objects.h::ARMOR`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L396-L401) | 5.0.0 | high |\
\| Elven mithril-coat | +5 | Suit AC value 5; also special/elven for the enchantment threshold. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L546-L548) [`obj.h::is_elven_armor`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L285) | 5.0.0 | high |\
\| Plate mail | +7 | AC 3; heavy at 450 weight. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L528-L530) | 5.0.0 | high |\
\| Splint mail / banded mail | +6 | Both AC 4. Splint mail weighs 400; banded mail weighs 350. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L537-L542) | 5.0.0 | high |\
\| Chain mail | +5 | AC 5; weighs 300. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L549-L551) | 5.0.0 | high |\
\| Orcish chain mail | +4 | AC 6. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L552-L554) | 5.0.0 | high |\
\| Dwarvish iron helm | +2 | AC 8. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L424-L426) | 5.0.0 | high |\
\| Iron shoes | +2 | AC 8. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L669-L670) | 5.0.0 | high |\
\| Large shield / dwarvish roundshield / elven shield | +2 | All have AC 8. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L631-L645) | 5.0.0 | high |\
\| Elven leather helm | +1 | AC 9; special/elven for enchantment. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L418-L420) [`obj.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L285) | 5.0.0 | high |\
\| Elven cloak | +1 | AC 9; special/elven for enchantment. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L585-L586) [`obj.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L285) | 5.0.0 | high |\
\| Leather gloves | +1 | AC 9. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L654-L656) | 5.0.0 | high |\
\| Low boots | +1 | AC 9. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L666-L669) | 5.0.0 | high |\
\| Cloak of protection | +3 | AC 7; not an elven item, so the ordinary evaporation threshold applies. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L607-L610) [`read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1114) | 5.0.0 | high |\
\| Dwarvish cloak | +0 | AC 10; useful for other properties, but not a direct AC improvement. | [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L590-L592) | 5.0.0 | high |

Other AC sources

| Source                                | AC effect       | Bot consideration                                              | Source                                                                                                                                                                                                                                                                     | Version | Confidence |
| ------------------------------------- | --------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| Ring of protection in left ring slot  | `-spe`          | Only helps when its enchantment is positive.                   | [`do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2364-L2367)                                                                                                                                  | 5.0.0   | high       |
| Ring of protection in right ring slot | `-spe`          | Stacks with the left ring if both slots hold protection rings. | [`do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2364-L2367)                                                                                                                                  | 5.0.0   | high       |
| Amulet of guarding                    | `-2`            | Fixed AC benefit; also provides MC benefit.                    | [`do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2368-L2369) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L819-L821) | 5.0.0   | high       |
| Intrinsic protection                  | `-u.ublessed`   | Included in the AC calculation.                                | [`do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2370-L2373)                                                                                                                                  | 5.0.0   | high       |
| Spell protection                      | `-u.uspellprot` | Included in the AC calculation while active.                   | [`do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2370-L2373)                                                                                                                                  | 5.0.0   | high       |

A protection ring's separate magic-cancellation benefit is not multiplied by a second protection ring or by wearing a cloak of protection as well. That is distinct from the AC contribution, which `find_ac()` calculates for each ring slot. [5.0 `objects.h`, ring of protection comment](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L721-L727)

### 3. Early sources of armour

#### Mines dwarves and other monsters

The probabilities below are per generated monster with its ordinary inventory initialization, not the chance of finding the item by a particular dungeon depth. The `makemon()` path calls `m_initweap()` and `m_initinv()` when the monster is allowed to have inventory. [5.0 `makemon.c::makemon()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L1375-L1380)

| Monster    | Armour roll per generated monster | AC value | Source                                                                                                                                                                                                                                                                                                                                                                  | Version | Confidence |
| ---------- | --------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| Dwarf      | Dwarvish cloak: 6/7               | +0       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L365-L369) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L590-L592)                                                                                             | 5.0.0   | high       |
| Dwarf      | Iron shoes: 6/7                   | +2       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L366-L369) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L669-L670)                                                                                             | 5.0.0   | high       |
| Dwarf      | Dwarvish iron helm: 1/4           | +2       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L370-L381) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L424-L426)                                                                                             | 5.0.0   | high       |
| Dwarf      | Dwarvish roundshield: 1/8         | +2       | It requires entering the 1/4 gear branch and taking its shield branch with probability 1/2. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L370-L381) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L643-L645) | 5.0.0   | high       |
| Dwarf      | Dwarvish mithril-coat: 1/12       | +6       | It requires the 1/4 gear branch and the subsequent 1/3 coat roll. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L370-L381) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L543-L545)                           | 5.0.0   | high       |
| Elf        | Elven mithril-coat: 1/4           | +5       | The elf has a 1/2 gear roll and then a 1/2 coat choice. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L215-L222) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L546-L548)                                     | 5.0.0   | high       |
| Elf        | Elven cloak: 1/4                  | +1       | The other half of the same gear roll. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L215-L218) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L585-L586)                                                       | 5.0.0   | high       |
| Elf        | Elven leather helm: 1/2           | +1       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L219-L222) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L418-L420)                                                                                             | 5.0.0   | high       |
| Elf        | Elven boots: 1/8                  | +1       | The boots roll is made only when the 1/2 helm roll fails, followed by a 1/4 chance. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L219-L222) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L682-L683)         | 5.0.0   | high       |
| Elf        | Elven shield: 1/12                | +2       | It requires one of the three weapon/gear branches and then a 1/4 shield roll. [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L225-L232) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L631-L633)               | 5.0.0   | high       |
| Hobbit     | Elven mithril-coat: 1/10          | +5       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L347-L364) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L546-L548)                                                                                             | 5.0.0   | high       |
| Mordor orc | Orcish chain mail: 1/3            | +4       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L395-L408) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L552-L554)                                                                                             | 5.0.0   | high       |
| Mordor orc | Orcish shield: 1/3                | +1       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L400-L408) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L637-L639)                                                                                             | 5.0.0   | high       |
| Uruk-hai   | Iron shoes: 1/3                   | +2       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L410-L422) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L669-L670)                                                                                             | 5.0.0   | high       |
| Uruk-hai   | Uruk-hai shield: 1/3              | +1       | [`makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L417-L422) [`objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L634-L636)                                                                                             | 5.0.0   | high       |

When a normal monster dies, its carried inventory is released onto the map by the monster-death handling path. A carried item can still be lost to floor effects or fail to remain where the bot expects, so confirm it is actually present before approaching or picking it up. [5.0 `mon.c`, `m_detach()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mon.c?utm_source=chatgpt.com#L2613-L2616)

Mercenary equipment is another possible source. Soldiers, guards, sergeants, lieutenants, and captains receive armour generated in rounds (body armour, helmet, shield, boots, then gloves or cloak); the code tries to make each mercenary's resulting AC approximate its assigned target. Exact item probabilities depend on which mercenary it is and the armour already generated, so I would not collapse this into one generic drop percentage. [5.0 `makemon.c::m_initinv()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L583-L654)

Limit on “by Dlvl 10” probabilities: the figures above are conditional on meeting a monster whose inventory initialization takes the corresponding branch. A reliable probability that the Valkyrie has acquired a particular item by Dlvl 10 would require the actual monster-spawn distribution, number of monsters encountered, and survival/loot recovery rates along the bot's route. That cumulative probability is UNVERIFIED.

### 4. Shops as early armour sources

The ordinary generated-shop weights in 5.0 include:

| Shop type                                     | Relative generation weight among ordinary shop types | Armour relevance                                                           |
| --------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------- |
| General store                                 | 42                                                   | Can stock any object class, including armour.                              |
| Used armour dealership                        | 14                                                   | 90% of its stock-generation selections are armour class; 10% weapon class. |
| Second-hand bookstore                         | 10                                                   | Scrolls and spellbooks, not a general armour source.                       |
| Liquor emporium                               | 10                                                   | Potions.                                                                   |
| Antique weapons outlet                        | 5                                                    | Weapons and some armour.                                                   |
| Delicatessen                                  | 5                                                    | Food and listed special items.                                             |
| Jewelers                                      | 3                                                    | Rings, gems, amulets.                                                      |
| Quality apparel and accessories (“wand shop”) | 3                                                    | 90% wands; 5% leather gloves; 5% elven cloak.                              |
| Hardware store                                | 3                                                    | Tools.                                                                     |
| Rare books                                    | 3                                                    | Spellbooks and some scrolls.                                               |
| Health food store                             | 2                                                    | Special food/potion/scroll items.                                          |

Source: 5.0 `shknam.c::shtypes[]`. These weights describe the selection of an ordinary random shop type, not the probability that a shop exists by Dlvl 10; special-level shops can be specified separately. [5.0 `shknam.c::shtypes[]`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L194-L313) [5.0 `mkroom.c::mkshop()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mkroom.c?utm_source=chatgpt.com#L137-L203)

A useful implication for this Valkyrie: an ordinary wand shop is also a possible early source of leather gloves or an elven cloak, although each is only 5% of its stock-selection entries. [5.0 `shknam.c::shtypes[]`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L272-L280)

## Bot rules

### Rule 1 — Equip a worthwhile armour upgrade

- Trigger = Inventory contains a known armour item with a better AC contribution than the currently worn item in that slot; the item's BUC state is known and it is not cursed. The status line exposes current AC.
- Action =
  1. Press `W` (wear armour).
  2. At the item-selection prompt, enter the inventory letter of the candidate.
  3. Re-read the inventory and status line.
  4. Record the item's revealed `+N` if the game reveals it on wearing.
- Done when = The item is worn and the status-line AC has improved or remained equal; the equipment state reflects the new item.
- If it fails = If the item is cursed, do not keep trying to remove it. If AC worsens, restore the prior known-safe equipment if possible; retain the item as an unidentified/cursed candidate rather than treating it as an upgrade.
- Evidence = `W` is the 5.0 wear-armour command. The Guidebook says putting on armour reveals its AC and any plusses; `find_ac()` calculates worn armour's effect. [5.0 Guidebook](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Commands) [5.0 `do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2344-L2379)

### Rule 2 — Prepare the intended target before reading

- Trigger = Inventory contains a known scroll of enchant armour and the bot has selected the particular worn armour item it wants to improve.
- Action =
  1. Move to a safe location with no adjacent hostile monster.
  2. Press `T` to take off competing armour pieces.
  3. If prompted which piece to remove, enter the inventory letter for the cloak, helmet, gloves, boots, or shield that is not the target.
  4. Repeat until only the desired candidate remains among cloak, suit, shirt, helmet, gloves, boots, and shield.
  5. If necessary, press `W` and select the intended target item to wear it.
- Done when = The intended item is the only worn candidate that `some_armor()` can select.
- If it fails = If `T` cannot remove an item, treat it as potentially cursed or otherwise non-removable; do not assume the target is controlled. Defer the scroll until the intended candidate can be isolated.
- Evidence = The complete candidate-selection procedure is 5.0 `do_wear.c::some_armor()`. The Guidebook documents `T` and how it selects worn armour; cursed armour can be unremovable. [5.0 source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2493-L2515) [5.0 Guidebook](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Commands)

Targeting a body suit: leave the suit worn, remove the cloak and the four possible random replacers (helmet, gloves, boots, shield). The shirt under the suit is not the initial target while the suit is worn.

Targeting a cloak: leave the cloak worn, remove the body suit and the four possible random replacers. A shirt underneath does not replace a worn cloak as the starting candidate.

Targeting a shield, helmet, or other accessory slot: remove the other armour categories too. With no other candidate present, the selected item becomes the target when `some_armor()` reaches it.

### Rule 3 — Read only when the enchantment is safe

- Trigger = A known enchant-armour scroll is in inventory, its BUC state is known to be blessed or uncursed, and the status condition does not show confusion.
- Action =
  1. Confirm the target item is worn and is at or below its safe threshold: ordinary `spe <= +3`, elven `spe <= +5`.
  2. Press `r`.
  3. At the read-object prompt, enter the inventory letter of the scroll of enchant armour.
  4. Wait for the reading result, then inspect the status AC and the target's inventory entry.
- Done when = The scroll has been consumed and the status-line AC or target's revealed enchantment shows the result.
- If it fails = If the hero is confused, do not read; wait until confusion is gone. If the scroll is cursed or its BUC state is unknown, do not use it on valuable armour. If the item evaporates, mark the loss and select the next known armour target.
- Evidence = `r` reads a scroll; the confusion, BUC and evaporation conditions are implemented in `read.c::seffect_enchant_armor()`. [5.0 Guidebook](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Objects) [5.0 source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1051-L1216)

For a Valkyrie, use the following stop condition:

| Target                                                                            | Stop at | Policy                                                            |
| --------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------- |
| Ordinary armour, including dwarvish mithril-coat                                  | +3      | Safe enchantment threshold; another read at +4 risks evaporation. |
| Elven mithril-coat, elven cloak, elven leather helm, elven shield, or elven boots | +5      | Safe enchantment threshold; another read at +6 risks evaporation. |
| Cloak of protection                                                               | +3      | It is not one of the items in `is_elven_armor()`.                 |

These thresholds follow the actual 5.0 evaporation test, not an assumption that the game disallows higher enchantments. [5.0 `read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1127) [5.0 `obj.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L285)

### Rule 4 — Check AC sources beyond the body suit

- Trigger = The inventory contains a known positive ring of protection, an amulet of guarding, or additional known armour pieces; the relevant slot is free or its current item is known to be worse.
- Action =
  - For a ring: press `P`, then select the ring's inventory letter.
  - For an amulet: press `P`, then select the amulet's inventory letter.
  - For armour: press `W`, then select the armour item.
  - Read the AC status line after each change.
- Done when = The bot has recorded the resulting AC and the worn inventory state.
- If it fails = Do not wear an unidentified ring merely because its appearance resembles a protection ring. If the status-line AC worsens or the item is cursed, mark the item as unsafe and do not attempt to remove it repeatedly.
- Evidence = 5.0 Guidebook documents `P` for accessories and `W` for armour. `find_ac()` separately subtracts the enchantment of both protection-ring slots and a fixed 2 for an amulet of guarding. [5.0 Guidebook](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Commands) [5.0 `do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2364-L2373)

### Rule 5 — Recover useful monster armour safely

- Trigger = A visible monster carrying armour has died, and the floor/map observation shows armour at its death location.
- Action =
  1. Read the floor item description.
  2. If it is an eligible upgrade, move onto the item or press `,` to pick it up.
  3. At a pickup prompt, select the armour item.
  4. Check the inventory entry and identify BUC status before wearing it.
- Done when = The armour appears in inventory and has been evaluated for weight, AC, slot, and BUC state.
- If it fails = If no item is present, do not infer it was generated simply because that species can carry it. The monster may not have received the relevant inventory roll, or the item may have been removed or destroyed.
- Evidence = `makemon.c::m_initweap()` generates the conditional dwarf/elf/hobbit/orc equipment; `mon.c` releases a dead monster's carried objects onto the map. [5.0 `makemon.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L215-L384) [5.0 `mon.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mon.c?utm_source=chatgpt.com#L2613-L2616)

## Risks and exceptions

1\. Do not treat +3/+5 as hard caps. They are the points before the next enchantment attempt enters the evaporation check. The check is probabilistic: ordinary armour at +4 has a 3-in-4 chance to evaporate; elven armour at +6 has a 5-in-6 chance. The bot should normally stop before that risk rather than deliberately test it. [5.0 `read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1112-L1127)

2\. Do not enchant while confused. The confused branch changes erosion-proofing rather than `spe`, so the scroll will not deliver the AC increase the bot expects. [5.0 `read.c::seffect_enchant_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1072-L1100)

3\. The most protective piece is not necessarily the selected piece. A worn cloak does not guarantee that the cloak gets the enchantment. A helmet, gloves, boots, or shield can displace it in `some_armor()`. The same issue applies when the desired target is body armour. [5.0 `do_wear.c::some_armor()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2493-L2515)

4\. Elven gear has a special advantage beyond its raw AC. All five pieces listed in `is_elven_armor()` receive the special threshold and enchantment modifier. Dwarvish armour does not receive this special treatment. [5.0 `obj.h::is_elven_armor`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/obj.h?utm_source=chatgpt.com#L282-L295) [5.0 `read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1101-L1145)

5\. Some cheap-looking armour upgrades are heavy. Plate mail provides +7 base AC but weighs 450; splint mail provides +6 and weighs 400; banded mail provides +6 and weighs 350. A Valkyrie bot should evaluate encumbrance, not just AC. Dwarvish and elven mithril-coats are +6/+5 and weigh 240. [5.0 `objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L528-L551)

6\. Do not mistake a dwarvish cloak for an AC upgrade. Its base AC value is 10, equivalent to zero direct protection. Elven cloaks contribute +1 and cloaks of protection contribute +3. [5.0 `objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L585-L609)

7\. Protection rings can be negative. `find_ac()` subtracts their `spe`, so a negative-enchanted ring makes AC worse. Wearing unknown rings also risks getting stuck with cursed equipment. Only regard an identified, positively enchanted protection ring as an AC upgrade. [5.0 `do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2364-L2367)

8\. AC is not the only equipment consideration. The cloak of protection and protection rings also affect magic cancellation, but their MC contribution does not simply stack for each additional such item. [5.0 `objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L721-L727) [5.0 `objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L607-L610)

9\. Monster-specific percentages are not depth probabilities. The dwarf and elf percentages describe their initial inventory rolls, not the probability of encountering those monsters by Dlvl 10 or collecting their items. [5.0 `makemon.c::m_initweap()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/makemon.c?utm_source=chatgpt.com#L215-L384)

## Open questions

- Human ascender statistics: UNVERIFIED. A named sample of games or dumplogs is needed to validate the AC benchmarks and the 79% / approximately three enchant-armour scrolls statistic.
- Cumulative gear odds by Dlvl 10: UNVERIFIED. This needs a defined route and monster-population sample; per-monster inventory chances are available, but a cumulative probability is not established here.
- Exact NLE text rendering: UNVERIFIED. The underlying 5.0 commands are `W`, `T`, `P`, and `r`; exact prompt strings and any NLE-specific status-line abbreviations should be calibrated against the bot's actual environment. The bot should use its observed inventory letters and parse the current AC/condition fields rather than assume fixed letters or formatting.
- Best empirical target: I would measure the bot's median AC at Dlvl 10, Dlvl 15, and Medusa across completed runs, then compare those results with the supplied human benchmarks. The source mechanics support a policy of prioritizing high-base-AC gear and targeting known elven armour for scroll investment, but they do not independently establish what human ascenders typically achieve.
