# R01 Energy vortex and other fast passive monsters

## Summary
- **Energy vortex is a no-melee monster for a shock-resistant-less Valkyrie.** It has speed 20, a 2⁄3-chance passive shock retaliation on melee, and a 3⁄4-chance energy drain while engulfing. Ranged attacks do **not** trigger the passive, even while engulfed.
- **Thrown daggers are the default ranged answer, but bring many.** An energy vortex has 6d8 HP (average 27), and a dagger does only 1d3 base damage against large monsters. Expect roughly 7–14+ hits depending on Strength and skill; do not engage with 2–3 daggers.
- **Elbereth probably works on vortices, but it is not a perfect panic button.** Vortices are not in the 3.7 non-respecting categories (@, Angelic beings, minotaurs, Riders, uniques), and eyeless monsters such as gelatinous cubes respect Elbereth. However, attacking from Elbereth erases it and abuses alignment in 3.7+.
- **Fire vortex (speed 22) and fire elemental (speed 12) are the other relevant fast/active damaging-passive threats.** Fire resistance trivialises them; without it, use ranged attacks and avoid melee.
- **Most other damaging-passive monsters are sessile or slow** — acid blobs, jellies, molds, and puddings are speed 0–6. They are dangerous only if you insist on meleeing them.
- **Exact 5.0 passive dice are UNVERIFIED.** The 3.6-era dataset lists energy vortex passive as `(level + 1)d4` shock, but I could not confirm this survived into 5.0. Use conservative HP thresholds and calibrate from observed damage.

---

## Facts

| Claim | Source | Version | Confidence |
|---|---|---|---|
| Energy vortex: level 6, speed 20, AC 2, MR 30; engulf 1d6 shock, energy-drain engulf, passive shock 2⁄3 chance. | NetHackWiki, *Energy vortex* (rev. 2024); cim.mcgill.ca monster page | 3.6/3.7 page; 5.0 likely unchanged | medium |
| Energy vortex HP = 6d8 (average 27, range 6–48). | NetHackWiki, *Hit points*: most monsters have `(monster level)d8` HP; level 6 ⇒ 6d8 | 3.6/3.7 formula; 5.0 UNVERIFIED but likely | medium |
| Energy vortex passive shock damage is listed as `(level + 1)d4`. | HuggingFace dataset citing `monst.c#line870` | 3.6-era dataset; **5.0 UNVERIFIED** | low |
| Ranged attacks do not trigger a vortex’s passive; melee does. This includes throwing and picking up weapons while engulfed. | NetHackWiki, *Vortex* / *Energy vortex* | 3.6/3.7; 5.0 likely | high |
| A hero engulfed by an energy vortex has a 3⁄4 chance of energy drain each vortex turn. | NetHackWiki, *Energy vortex* | 3.6/3.7; 5.0 UNVERIFIED | medium |
| Fire vortex: level 8, speed 22, passive fire 2⁄3 chance; fire resistance nullifies. | NetHackWiki, *Fire vortex*; cim.mcgill.ca fire vortex page | 3.6/3.7; 5.0 likely | medium |
| Fire elemental: speed 12 (same as unhasted unburdened hero), passive fire. | NetHackWiki, *Fire elemental* | 3.6/3.7; 5.0 likely | medium |
| Elbereth is respected by most monsters. 3.7 exceptions: uniques, all `@`, Angelic beings, minotaurs, Riders. | NetHackWiki, *Elbereth*; 3.7 change summary | 3.7; 5.0 likely | high for 3.7, medium for 5.0 |
| Eyeless monsters respect Elbereth; blinded sighted monsters do not. Vortices are eyeless. | NetHackWiki, *Elbereth* | 3.6/3.7 | medium |
| Attacking from Elbereth erases the engraving and abuses alignment in 3.7+. | NetHackWiki / NerfHack 3.7 change summary | 3.7+ | high |
| Wand of slow monster can force an engulfing vortex to release the hero; cancellation prevents energy drain. | NetHackWiki, *Energy vortex* strategy | 3.6/3.7 | medium |
| Dagger damage: 1d4 vs small, **1d3 vs large**; +2 to-hit. | NetHackWiki, *Dagger* | 3.6/3.7; 5.0 likely | high |
| Acid blob: passive acid, speed 3 (slow). | NetHackWiki, *Acid blob* | 3.6/3.7; 5.0 likely | medium |
| Spotted jelly: passive acid `(level + 1)d6`, speed 0 (sessile). | NetHackWiki, *Spotted jelly* | 3.6/3.7; 5.0 likely | medium |
| Ochre jelly: passive acid 3d6, speed 3 (slow). | NetHackWiki, *Ochre jelly* | 3.6/3.7; 5.0 likely | medium |
| Blue jelly: passive cold `(level + 1)d6`, speed 0 (sessile). | NetHackWiki, *Blue jelly* | 3.6/3.7; 5.0 likely | medium |
| Brown mold: passive cold `(level + 1)d6`, speed 0. | NetHackWiki, *Mold* dataset | 3.6-era; 5.0 likely | medium |
| Red mold: passive fire dependent on attacker level, speed 0 (sessile). | NetHackWiki, *Red mold* | 3.6/3.7; 5.0 likely | medium |
| Green mold: passive acid, speed 0. | NetHackWiki, *Passive attack* | 3.6/3.7 | medium |
| Black pudding: passive corrosion (acidic), speed 6; not direct HP damage. | NetHackWiki, *Black pudding* | 3.6/3.7; 5.0 likely | medium |
| Floating eye: passive paralysis, speed 1; not HP damage. | NetHackWiki, *Floating eye* | 3.6/3.7 | medium |
| Yellow mold: passive stun, speed 0; not HP damage. | NetHackWiki, *Passive attack* | 3.6/3.7 | medium |

---

## Bot rules

### Rule 1 — Energy vortex adjacent: do not melee
**Trigger:**  
- Map shows adjacent `v` whose monster description is “energy vortex”; or  
- Message: `The air around you crackles with electricity.`; or  
- Status/engulf message indicates an energy vortex.

**Action (in order):**  
1. **If a dagger is in inventory:** press `t`, select the dagger, then target the vortex direction.  
2. **Else if an attack wand is available** (wand of cold, fire, or magic missile): press `z`, select the wand, target the vortex.  
3. **Else if no ranged option:** press `E`, write `Elbereth`, confirm; stay on the square and do not melee.  
4. **Do not press `F`** (melee/fight) against an energy vortex unless Rule 4 is satisfied.

**Done when:** vortex dies, or is no longer adjacent.  
**If it fails:** if engulfed, go to Rule 3.  
**Evidence:** Ranged attacks do not trigger passive; energy vortex speed 20 and passive shock; Elbereth exceptions do not include vortices.

---

### Rule 2 — Energy vortex at range: kill before it closes
**Trigger:** `v` identified as energy vortex at distance > 1 and visible.

**Action:**  
- Throw daggers: `t` → dagger letter → direction.  
- Or zap an attack wand: `z` → wand letter → direction.  
- Do not walk toward it. If it closes to adjacent, immediately switch to Rule 1.

**Done when:** vortex dies or moves out of line of sight.  
**If it fails:** if it closes to adjacency, Rule 1; if it engulfs you, Rule 3.  
**Evidence:** Energy vortex speed 20 means it will close quickly; ranged attack is “all but required”.

---

### Rule 3 — Engulfed by energy vortex
**Trigger:** Message `You were engulfed by an energy vortex.` or status indicates swallowed/engulfed.

**Action:**  
1. **Throw daggers from inside:** `t` → dagger letter → target the engulfer (use `.` or `>`; verify the NLE direction prompt).  
2. **Or zap an attack wand** at the engulfer: `z` → wand letter → target.  
3. **Do not melee** (`F`) while engulfed unless Rule 4 is satisfied.  
4. If no ranged attack: zap a **wand of slow monster** at the vortex to force release; if unavailable, read a **scroll of teleportation** if carried; otherwise melee only as a last resort under Rule 4.

**Done when:** released or vortex dies.  
**If it fails:** if HP is low, quaff a healing potion or pray only if alignment and prayer timeout allow (UNVERIFIED for 5.0 prayer details).  
**Evidence:** Ranged attacks are fine even while engulfed; passive only triggers on melee; slow monster can force release; energy drain is 3⁄4 per turn.

---

### Rule 4 — When is melee acceptable against an energy vortex?
**Trigger:** Energy vortex adjacent and no ranged option, or melee is being considered.

**Action:** Melee **only if at least one** of the following is true:  
- You have **shock resistance** (intrinsic or extrinsic); or  
- Current HP is greater than the conservative maximum passive shock damage **and** the vortex is likely to die in one hit.

Use a conservative threshold: **do not melee if current HP ≤ 4 × (XL + 1)**. This is derived from the unverified `(level + 1)d4` formula; at XL 6 that is 28 HP, at XL 14 it is 60 HP. If you lack shock resistance and your HP is below that threshold, **do not melee**.

**Done when:** vortex dies or you escape.  
**If it fails:** retreat is usually impossible because the vortex is speed 20 vs your speed 12; use Elbereth, teleportation, or a wand of slow monster.  
**Evidence:** Passive shock formula is UNVERIFIED for 5.0, so this is deliberately conservative; energy vortex speed 20.

---

### Rule 5 — Fire vortex / fire elemental
**Trigger:** Adjacent `v` fire vortex or `E` fire elemental.

**Action:**  
- If you have **fire resistance**: melee is acceptable; fire vortex/fire elemental passives are nullified.  
- If you lack fire resistance: use ranged attacks (daggers, wand of cold). Do **not** melee.  
- Fire vortex speed 22 cannot be outrun; if adjacent without fire resistance, engrave Elbereth or use an escape item immediately.

**Done when:** monster dies or you escape.  
**If it fails:** if engulfed by fire vortex, throw daggers from inside; do not melee.  
**Evidence:** Fire vortex speed 22 and passive fire; fire elemental speed 12 and passive fire; fire resistance nullifies both.

---

### Rule 6 — Other damaging-passive monsters (acid/cold)
**Trigger:** Adjacent `b` acid blob, `j` blue/spotted/ochre jelly, `F` brown/green/red mold, or `P` black pudding.

**Action:**  
- Prefer ranged attacks or simply walk away. These monsters are speed 0–6; they cannot chase you.  
- Melee only if you can kill in one hit, or have the relevant resistance (acid/cold/fire), or have enough HP to absorb several retaliations.  
- For blue jelly and brown mold, remember their passive cold **heals them** by half the damage dealt; low-damage melee can make them stronger.

**Done when:** monster avoided or killed.  
**If it fails:** disengage and use ranged attacks.  
**Evidence:** Speed data in Facts table; passive triggers only on melee.

---

## Risks and exceptions
- **Elbereth is not absolute.** It fails in Gehennom and the endgame. It does not stop missile/spell attacks, only melee and directed spells. In 3.7+, attacking from Elbereth erases it and abuses alignment.
- **Blinded monsters ignore Elbereth.** Vortices are eyeless, so they are not “blinded” in this sense and should still respect it; a sighted monster blinded by a camera would not.
- **Energy vortex MR 30** makes scaring tools such as a bugle unreliable.
- **Shock resistance is not a Valkyrie intrinsic** in the XL 6–14 window; the Valkyrie intrinsics are cold resistance (XL 1), stealth (XL 3), and speed (XL 7). Do not assume shock resistance.
- **Fire resistance is not a Valkyrie intrinsic**; do not melee fire vortices/elementals without a source.
- **Dagger count.** Energy vortex HP 6d8 averages 27; each dagger does 1d3 large plus Strength. If your average damage is ~3, you need ~9 successful hits; if ~4, ~7. Misses and pickup turns increase this. Carry at least 10 daggers before voluntarily engaging.
- **Exact 5.0 passive dice are UNVERIFIED.** The 3.6-era dataset’s `(level+1)d4` may have changed. If you observe higher damage, raise the melee HP threshold immediately.
- **List completeness.** The table covers the commonly cited damaging-passive monsters, but an exhaustive source-code audit of 5.0 `monst.c` for every passive was not possible here. Treat “every” as **UNVERIFIED for completeness**.

---

## Open questions
1. **Exact 5.0 passive shock/fire dice** for energy vortex, fire vortex, and fire elemental. The 3.6-era dataset says energy vortex is `(level+1)d4`; 5.0 source confirmation was not obtained.
2. **Does Elbereth specifically block the engulf attack in 5.0**, or only ordinary melee? The wiki says it blocks melee; engulf is melee-range but the exact code path is UNVERIFIED.
3. **Exact NLE key sequence for throwing while engulfed** — whether the direction prompt accepts `.`, `>`, or the engulfer’s map direction.
4. **Energy drain probability** — still 3⁄4 in 5.0? The wiki page is 3.6/3.7-era.
5. **Complete 5.0 list of every monster with a damaging passive and its speed**, including less common monsters such as steam vortex, ice vortex, and any new 5.0 monsters.
