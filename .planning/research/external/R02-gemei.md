# R02 Unicorns: fight or avoid (A)

## Summary

* **Hostile Movement & NOTONL:** Hostile unicorns have the `NOTONL` flag set (`src/monmove.c` in NetHack 3.6/3.7/5.0); they actively try to avoid being lined up with the player and will teleport away (50% chance per turn when pinned with no safe squares) rather than walk voluntarily into melee range unless closed in or forced by geometry.
* **Luck Penalties for Killing:** Killing a co-aligned (neutral gray) unicorn incurs a heavy −5 Luck penalty. Killing cross-aligned (white or black) unicorns incurs 0 Luck penalty.
* **Throwing Gems:** Throwing unidentified valuable gems at a co-aligned neutral unicorn grants +2 Luck; throwing named valuable gems grants +5 Luck. Throwing worthless glass or cross-aligned gems carries risks or no major positive benefit.
* **Experienced Player Strategy:** Early weak heroes should completely ignore or bypass distant unicorns, use pets to eliminate them, or leverage corridors and ranged weapons.
* **Unicorn Horn Value & Acquisition:** The unicorn horn is one of the most powerful utility items in the game, curing sickness, blindness, hallucination, stoning, and confusion. The safest way to acquire one early is letting a pet kill a cross-aligned unicorn or safely sniping it down a corridor.

---

## Facts

| Claim | Source | Version | Confidence |
| --- | --- | --- | --- |
| Unicorns have the `NOTONL` flag set to avoid lining up with the player | NetHackWiki (Unicorn page) / `src/monmove.c` | 3.6 / 3.7 / 5.0 | High |
| Killing a co-aligned unicorn incurs a −5 Luck penalty | NetHackWiki (Luck / Unicorn pages) | 3.6 / 3.7 / 5.0 | High |
| Killing a cross-aligned unicorn incurs 0 Luck penalty | NetHackWiki (Unicorn page) | 3.6 / 3.7 / 5.0 | High |
| Throwing an unidentified valuable gem at a co-aligned unicorn grants +2 Luck | NetHackWiki (Luck / Gems pages) | 3.6 / 3.7 / 5.0 | High |
| Throwing a type-named valuable gem at a co-aligned unicorn grants +5 Luck | NetHackWiki (Luck / Gems pages) | 3.6 / 3.7 / 5.0 | High |
| Unicorn base speed is 24, with multi-attacks (1d12 headbutt + 1d6 kick) | NetHackWiki (Unicorn page) | 3.6 / 3.7 / 5.0 | High |

---

## Bot rules

### Rule 1: Bypass and Ignore Hostile Unicorns

* **Trigger:** Map symbol `u` representing white/black unicorn visible at distance $> 1$, character XL 5–9 without high AC or reflection.
* **Action:**
1. Pathfind around the unicorn using alternative map routes to avoid stepping adjacent to `u`.
2. Do not initiate melee combat or direct movement toward `u`.


* **Done when:** Unicorn is out of vision or hero reaches next dungeon level / target room.
* **If it fails:** If unicorn blocks a single-tile corridor, use a Wand of Digging or allow pet to engage first.
* **Evidence:** NetHackWiki Unicorn page strategy (early game avoidance).

---

### Rule 2: Gem Offering to Co-Aligned Gray Unicorns for Luck

* **Trigger:** Gray unicorn (`u`) visible, character is Neutral (Valkyrie), carrying valuable gems (e.g., ruby, sapphire, emerald) in inventory, and aligned cardinally/diagonally at distance 2–4.
* **Action:**
1. Press `t` (throw).
2. Press inventory letter of the valuable gem.
3. Press direction key (`h`, `j`, `k`, `l`, etc.) toward the gray unicorn.


* **Done when:** Message `"The gray unicorn graciously accepts your gift"` appears, and Luck increases.
* **If it fails:** Message `"The unicorn is not interested in your junk"` (if worthless glass) or unicorn teleports away before throw; resume pathfinding.
* **Evidence:** NetHackWiki Unicorn and Luck pages.

---

### Rule 3: Safe Unicorn Horn Retrieval via Pet

* **Trigger:** Cross-aligned unicorn (`white` or `black`) visible, character XL 5–9, pet adjacent or near the unicorn.
* **Action:**
1. Position character behind pet or out of direct melee reach.
2. Let pet engage and reduce unicorn HP via melee counterattacks.
3. Throw daggers (`t` + dagger letter + direction) if line of sight allows without hitting pet.
4. Once killed, walk onto corpse square and press `,` (pickup) to retrieve `unicorn horn`.


* **Done when:** `unicorn horn` is present in inventory.
* **If it fails:** If pet is near death or unicorn targets hero, retreat via corridor or execute emergency Elbereth (`E` + `-`).
* **Evidence:** NetHackWiki Unicorn horn acquisition strategy.

---

## Risks and exceptions

* **Accidental Co-Aligned Attack:** Striking a gray unicorn directly incurs a severe −5 Luck penalty, ruining character RNG modifications.
* **Sokoban Traps:** Unicorns trapped in Sokoban rooms cannot teleport away easily, leading to erratic defensive strikes if cornered close up.
* **Pet Mortality:** Letting a weak pet solo a speed-24 unicorn can result in pet death if the pet is under-leveled.

---

## Open questions

* **UNVERIFIED:** Exact line numbers for `src/monmove.c` behavior changes specific to NetHack 5.0.0 release.
* **UNVERIFIED:** Potential modifications to gem-throwing Luck formulas in the NetHack 5.0 development branch.
