# R05 Enchant armour and early armour sources (A)

## Summary
- **`some_armor()` picks one random worn piece.** The reliable bot strategy is to **remove every worn armor piece except the one target**, then read the scroll. This eliminates the random selection entirely.
- **Safe enchantment ceiling is +3 for most armor, +5 for elven armor (and Wizard cornuthaum).** Above that ceiling, each scroll has a `1/(current enchantment)` chance of **not** vaporising, i.e. a high chance of destroying the armor. Do not enchant past +3 unless you accept vaporisation risk.
- **Blessed scrolls can add 2 or 3 points; uncursed add 1; cursed subtract 1 and can curse the armor.** Confused non-cursed reading repairs erosion and erodeproofs without changing enchantment — useful, but **does not raise AC**.
- **Valkyries should go to the Gnomish Mines early for dwarvish mithril-coat, dwarvish iron helm, and iron shoes.** These are the cheapest large AC jumps available by Dlvl 10. Shops and monster drops are secondary.
- **The cheapest AC gains for a bot, ranked: (1) dwarvish mithril-coat, (2) dwarvish iron helm, (3) iron shoes, (4) small shield (already starting +3), (5) cloak, (6) rings of protection.** Enchanting the mithril-coat and helm to +3 is the next-cheapest step after acquisition.
- **79% of human ascenders read enchant armour ~3 times before Medusa** — this is a community statistic, not a game rule; treat it as a target, not a hard requirement.

---

## Facts

| Claim | Source | Version | Confidence |
|---|---|---|---|
| `some_armor(&youmonst)` selects one worn armor piece at random. | NetHackWiki *Scroll of enchant armor*; forum code annotation `otmp = some_armor(&youmonst)` | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Removing all other worn armor makes the scroll affect only the remaining piece. | NetHackWiki *Scroll of enchant armor*; Fandom: “most players normally remove all of their armor except for the piece that they want to enchant” | 3.6/3.7; 5.0 likely | high |
| Safe ceiling: **+3** for normal armor; **+5** for **elven armor** and Wizard cornuthaum. | Fandom *Scroll of enchant armor*: “Armor currently at +3 or below is safe … Elven armor … safe to enchant even when it is currently at +5” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Above ceiling: chance the armor **WON’T** be vaporised is **1/(current enchantment)**. | Fandom: “there is a 1 in (current enchantment) chance that it WON’T be vaporized” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Unccursed scroll: **+1** enchantment. | Fandom: “uncursed scroll normally raises enchantment by 1” | 3.6/3.7; 5.0 likely | high |
| Blessed scroll: can raise by **2 or 3**. | Fandom: “blessed scroll can sometimes raise enchantment by 2 or 3” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Cursed scroll: **decreases** enchantment and can **curse** the armor. | Fandom: “cursed scroll … will actually harm your armor … A cursed or blessed scroll will cause the armor it affects to become cursed or blessed” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Unccursed scroll **uncurses** cursed armor. | Fandom: “An uncursed scroll will uncurse cursed armor” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Confused non-cursed scroll **repairs erosion and erodeproofs**; **no vaporisation risk** because enchantment is not raised. | Fandom: “Reading a noncursed scroll while confused will repair erosion … As this does not increase the enchantment … this does not risk vaporization” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Confused cursed scroll **does not heal armor**; removes erodeproofing. | Fandom: “cursed scroll when confused will not heal your armor, and will remove erodeproofing” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Valkyries can wear **all armor without penalty** except weight. | NetHackWiki *Valkyrie*: “Valkyries can wear all armor without penalty (except the weight)” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Gnomish Mines normally yield **dwarvish mithril-coat, iron shoes, and dwarvish iron helm** for Valkyries. | NetHackWiki *Valkyrie*: “Valkyries … should go into the Gnomish Mines as quickly as possible, because this normally yields a dwarvish mithril-coat, iron shoes and a dwarvish iron helm” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Dwarves in the Mines are a source of dwarvish armor; a **pet can BUC-test** by refusing cursed items. | NetHackWiki *Valkyrie*: “using a pet to make sure items are not cursed” | 3.6/3.7 | medium |
| Small shield: Valkyries start with a **+3 small shield**, light for its AC. | NetHackWiki *Valkyrie*; Fandom: “+3 shield … incredibly light for its AC” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| **79%** of human ascenders read enchant armour **~3 times before Medusa**. | User-stated community statistic (not independently verified in this session) | Unknown dataset; **UNVERIFIED** | low |

---

## Bot rules

### Rule 1 — Isolate the target before reading
**Trigger:** Inventory contains a scroll of enchant armour (identified) and a worn piece the bot wants to enchant.
**Action:**
1. Press `T` (take off armor) for every worn armor slot **except** the target piece. Confirm each take-off.
2. Verify inventory shows only the target armor as `(being worn)`.
3. Press `r`, select the enchant armour scroll.
4. Read the result message.

**Done when:** scroll is read and the message names the target piece (or the target’s enchantment changes).
**If it fails:** if another piece was still worn, the scroll may have hit the wrong piece; stop and re-isolate next time.
**Evidence:** `some_armor()` selects randomly; removing all others forces the target.

---

### Rule 2 — Do not read above the safe ceiling without accepting loss
**Trigger:** Target armor’s current enchantment is **≥ +4** (or **≥ +6** for elven armor / cornuthaum).
**Action:**
- **Default: do not read.** Move to another armor piece below its ceiling.
- If the bot has **more scrolls than the piece is worth** and the piece is replaceable, reading is allowed; record that the armor may be destroyed.
- Never read a **cursed** scroll on a piece the bot intends to keep; cursed scrolls lower enchantment and can curse the armor.

**Done when:** decision recorded; scroll not read or read with accepted risk.
**If it fails:** if the armor vaporises, replace it from the Mines or a shop.
**Evidence:** safe ceiling +3 / +5 elven; above ceiling, `1/(enchantment)` chance of survival per read.

---

### Rule 3 — Use blessed scrolls only when the extra points matter
**Trigger:** Bot has both blessed and uncursed enchant armour scrolls.
**Action:**
- Use **uncursed** scrolls first on pieces below +3; they give exactly +1 and do not risk overshooting into the vaporisation zone.
- Save **blessed** scrolls for pieces at +2 or +3 where a +2/+3 jump may reach +4/+5; accept that a blessed scroll can skip past the safe ceiling.
- Never bless a scroll on a piece already at +3 unless the bot is willing to lose the piece.

**Done when:** scroll used or saved.
**If it fails:** if a blessed scroll overshoots to +4 on a non-elven piece, stop enchanting that piece.
**Evidence:** uncursed = +1; blessed = +2/+3.

---

### Rule 4 — Confused reading is for repair, not AC
**Trigger:** Target armor is **eroded** or **not erodeproofed**, and the bot has a non-cursed enchant armour scroll.
**Action:**
1. Confirm the scroll is **not cursed** (BUC-known or pet-tested).
2. Become confused (e.g., wait out a confusion source, or use a known confusion method).
3. Read the scroll.
4. Verify the message indicates erosion repair / erodeproofing.

**Done when:** erosion repaired or armor erodeproofed.
**If it fails:** if the scroll was cursed, erodeproofing may be removed; do not repeat with an unknown scroll.
**Evidence:** confused non-cursed reading repairs erosion and erodeproofs without vaporisation risk.

---

### Rule 5 — Mines-first armor acquisition by Dlvl 10
**Trigger:** Hero reaches Dlvl 5–10 and AC is worse than −4.
**Action, in order:**
1. **Descend to the Gnomish Mines.** Target **dwarvish mithril-coat** first; it is the largest single AC gain.
2. Pick up **dwarvish iron helm** and **iron shoes** when found; wear immediately if not cursed.
3. Use a **pet** to BUC-test: drop the armor; if the pet refuses to pick it up, it is cursed. Do not wear cursed armor.
4. If the Mines do not yield a mithril-coat, check **used armor dealerships** (14% of shops) and **general stores** (42–44%).
5. Keep the starting **+3 small shield** unless a better shield is found and skill allows.

**Done when:** mithril-coat, helm, and shoes are worn, or the bot has exhausted the Mines.
**If it fails:** if the Mines are too dangerous, retreat and shop; do not skip armor acquisition entirely.
**Evidence:** Mines are the documented Valkyrie armor source; Valkyries wear all armor without penalty.

---

### Rule 6 — Enchant the highest-AC pieces first
**Trigger:** Bot has enchant armour scrolls and multiple worn pieces below +3.
**Action:** Enchant in this priority order:
1. **Dwarvish mithril-coat** (body armor; highest base AC).
2. **Dwarvish iron helm** (head).
3. **Iron shoes** (feet).
4. **Small shield** (already +3; enchanting it further is lower priority because it starts high).
5. **Cloak** (low base AC; only if no better target).

Stop enchanting a piece at +3 (or +5 if elven) unless Rule 2 allows risk.
**Done when:** all priority pieces are at +3, or scrolls are exhausted.
**If it fails:** if a piece vaporises, replace it before continuing.
**Evidence:** AC gain per scroll is highest on the highest-base-AC piece; safe ceiling +3.

---

## Risks and exceptions
- **Exact 5.0 `some_armor()` behaviour is UNVERIFIED.** The random-selection rule is 3.6/3.7-era. If 5.0 changed the function to prefer a particular slot, Rule 1’s “remove all others” strategy is still safe but may be unnecessary.
- **5.0 vaporisation formula is UNVERIFIED.** The `1/(enchantment)` survival chance is from 3.6/3.7 sources. Do not treat it as a 5.0 constant; calibrate from observed losses.
- **Blessed scroll overshoot is real.** A blessed scroll on a +3 piece can reach +4 or +5, putting the piece into the vaporisation zone on the next read. Plan scroll use so the last read on a piece is an uncursed +1 that lands at +3, not a blessed jump past it.
- **Elven armor is rare for a human Valkyrie.** The +5 ceiling applies to elven armor, but a human Valkyrie may not find elven mithril early. Do not plan around it.
- **Cursed armor is worse than no armor** if it cannot be removed. Always BUC-test before wearing, or have a scroll of remove curse ready.
- **The 79% statistic is not a rule.** It describes human ascender behaviour, not a game requirement. A bot that reaches −10 AC by Dlvl 15 without three enchant armour reads is not necessarily behind.
- **Minetown shops are not guaranteed to stock armor.** Used armor dealerships are 14% of shops; do not assume one exists.

---

## Open questions
1. **Exact 5.0 `some_armor()` implementation** — random, or slot-prioritised? **UNVERIFIED.**
2. **Exact 5.0 vaporisation formula** — is survival still `1/(enchantment)`, or did 3.7/5.0 change it? **UNVERIFIED.**
3. **Exact 5.0 blessed-scroll distribution** — +2 vs +3 probabilities. **UNVERIFIED.**
4. **Exact 5.0 Valkyrie starting shield enchantment** — still +3? **UNVERIFIED.**
5. **Exact 5.0 Gnomish Mines armor drop rates** for dwarvish mithril-coat, iron helm, iron shoes. **UNVERIFIED.**
6. **Whether 5.0 added new armor sources or changed Mines generation** in a way that affects the Mines-first strategy. **UNVERIFIED.**

---
