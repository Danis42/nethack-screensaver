# R01 Energy vortex and other fast passive monsters (A)

## Summary

* **Vortices and Elbereth:** In NetHack 3.7 / 5.0 (and 3.6), all vortices are mindless (`M2_MINDLESS`). They **do respect** Elbereth, provided they can move away (mindless monsters respect Elbereth as long as they can perceive the hero / ground or follow scared monster AI).
* **Dagger Throwing:** A basic thrown dagger without thrown skill bonus deals 1d4 (small) / 1d3 (large) physical damage plus Strength/Skill modifiers. An energy vortex (level 6, 6d8 HP = ~27 HP) takes ~5–9 dagger hits to kill.
* **Engulf Behavior:** Melee attacks on an engulfing monster **always hit**. While engulfed, passive attacks still trigger if hit in melee. Engulfing can be ended via teleportation (scroll/wand/teleport control), polymorphing, wand of opening, scaring tools (tooled horn/drum), or killing the vortex.
* **Passive Damage Formula (Fire/Electricity):** Function `passive()` in `mhitu.c` / `uhitm.c` triggers a 2/3 (66.7%) chance of passive retaliation upon a non-killing melee blow. Damage is 2d6 for fire vortex / red mold, 2d6 for energy vortex, and 0d4 (monst.c base 0d4 modified by level/dice in code) for fire elemental.
* **Melee Threshold:** Without resistance, melee is **unacceptable** unless hit points are $\ge 40$ HP and the monster can be killed in a single strike, due to passive damage (avg 7 damage per non-lethal hit) and rapid speed.

---

## Facts

| Claim | Source | Version | Confidence |
| --- | --- | --- | --- |
| Vortices are mindless (`M2_MINDLESS`) and respect Elbereth | NetHackWiki (Vortex, Elbereth pages) / `monst.c` | 3.6 / 3.7 / 5.0 | High |
| Energy vortex speed is 20 (base level 6, 6d8 HP) | NetHackWiki (Energy vortex) / `monst.c` | 3.6 / 3.7 / 5.0 | High |
| Fire elemental speed is 12, flyable, base level 8 | NetHackWiki (Fire elemental) / `monst.c` | 3.6 / 3.7 / 5.0 | High |
| Fire vortex speed is 15 (base level 8, 8d8 HP) | NetHackWiki (Fire vortex) / `monst.c` | 3.6 / 3.7 / 5.0 | High |
| Passive fire/shock attack has a 2/3 (66.7%) chance of retaliatory damage if monster is not canceled or killed on hit | NetHackWiki (Passive attack page) / `uhitm.c` function `passive()` | 3.6 / 3.7 / 5.0 | High |
| Attacks inside an engulfing monster always hit | NetHackWiki (Engulfing page) / `mhitu.c` | 3.6 / 3.7 / 5.0 | High |
| Wand of opening, drum, tooled horn, or teleportation break engulfing immediately | NetHackWiki (Engulfing page) | 3.6 / 3.7 / 5.0 | High |

---

## Bot rules

### Rule 1: Emergency Elbereth / Ranged Retreat Against Fast Passive Monsters

* **Trigger:** Map symbol `v` (energy vortex / fire vortex) or `E` (fire elemental) visible, distance $\le 3$, character lacks matching resistance (Shock or Fire).
* **Action:**
1. Check inventory for Wand of Teleportation or Wand of Digging (if un-engulfed).
2. If on non-engraved square and carrying a Wand of Digging / Fire / Lightning, press `E` then answer prompt with direction `-` (underfoot) to engrave `Elbereth`.
3. If standing on `Elbereth`, switch weapon to daggers (`w` daggers) and throw at monster (`t` + dagger letter + direction).


* **Done when:** Monster is killed, fled out of vision, or character is safely teleported away.
* **If it fails:** If monster enters hero square (engulfs), switch to internal engulfing procedures.
* **Evidence:** NetHackWiki Elbereth page; NetHackWiki Passive attack strategy.

---

### Rule 2: Handling Engulfment inside Energy / Fire Vortex

* **Trigger:** Status/Message contains `"You are engulfed"` or screen shows engulfed state by a vortex.
* **Action:**
1. If carrying a **Wand of Opening**, zap it (`z` + wand letter).
2. Else if carrying a **Wand of Teleportation** / **Scroll of Teleportation**, use it (`z` / `r`).
3. Else if carrying a **Tooled Horn** or **Drum of Panic**, apply it (`a`).
4. Else, wield best melee weapon and attack repeatedly (`F` + direction toward monster center or standard movement attack key) until freed, provided HP > 20.


* **Done when:** Message `"expels you"` or `"slain"` appears, restoring normal grid view.
* **If it fails:** If HP drops below 15 and no escape item exists, quaff Potion of Extra Healing / Healing (`q`) if available.
* **Evidence:** NetHackWiki Engulfing page.

---

## Risks and exceptions

* **Erosion & Flammable Equipment:** Attacking or being engulfed by a fire elemental or fire vortex without fire resistance burns inventory items (scrolls, potions, wooden weapons).
* **Blindness:** If the character is blinded, Elbereth status checks require care since blind monsters or a blind player interact differently, though mindless vortices still follow scaring mechanics unless impaired.
* **Wand Destruction:** Energy vortex shock damage inside/outside can explode wands in inventory.

---

## Open questions

* **UNVERIFIED:** Specific line numbers for `mhitu.c` / `uhitm.c` in NetHack 5.0 source tree specifically for 5.0 release modifications.
* **UNVERIFIED:** Exact damage adjustments to thrown daggers against specific non-solid/unsolid body types in NetHack 5.0.
