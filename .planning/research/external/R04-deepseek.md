# R04 Sell-price identification in 5.0 shops (A)

## Summary
- **The sell prompt is stable across 3.6–5.0:** `"<shopkeeper> offers <N> gold pieces for your <item>. Sell it? [ynaq]"`. Answer `n` to decline; the item remains yours. **`a`** may appear as an option in some builds, but the canonical prompt is `[ynaq]` in 3.6/3.7; 5.0 is **UNVERIFIED** for the exact option letters.
- **Sell price is normally half base price**, but **25% of shopkeepers pay 25% less** for **unidentified** objects. This modifier is **per-shopkeeper**, not per-item. Re-dropping an item until you see two different offers is the standard workaround.
- **Sell price is charisma-independent.** Buy price is charisma-dependent; sell price is not. This makes sell-price identification more reliable for a bot.
- **Shop types gate which items can be sold.** General stores buy almost anything. Bookstores buy scrolls and spellbooks. Liquor emporiums buy potions. Jewelers buy rings, gems, and amulets. **Selling a class the shop does not buy produces “not interested”**; exact message text is **UNVERIFIED** for 5.0.
- **Minetown in 5.0 still guarantees Izchak’s lighting shop**; general store, food shop, and tool shop have **~90%** chance each in the standard variant. Other variants differ; a full 5.0 variant table was not obtained.
- **The 25% “unidentified” discount is the key identification signal.** A bot that records the offer for the same base-price item under both modifier states can narrow the item’s identity without reading it.

---

## Facts

| Claim | Source | Version | Confidence |
|---|---|---|---|
| Sell prompt: `"<shopkeeper> offers <N> gold pieces for your <item>. Sell it? [ynaq]"`. | NetHackWiki *Price identification*; NetHack::PriceID example `"Wonotobo offers 75 gold pieces for your clay ring. Sell it?"` | 3.6/3.7; 5.0 **UNVERIFIED** for exact prompt string | high for 3.6/3.7 |
| Declining with `n` returns the item to the hero; the item is **not** sold. | NetHackWiki *Price identification* (declining restores ownership) | 3.6/3.7; 5.0 likely | high |
| Sell price normally = **½ base price**. | NetHackWiki *Price identification*: “The sell price will normally be half the ‘base price’” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| **¼ of shopkeepers pay ¼ less** for **unidentified** objects; modifier is **consistent for a given shopkeeper**. | NetHackWiki *Shop* §Selling: “¼ of shopkeepers will pay ¼ less for unidentified objects; this modifier is consistent for a given shopkeeper” | 3.6.7 `shk.c:3396`; 5.0 **UNVERIFIED** | high for 3.6.7 |
| Sell price is **not affected by charisma**. | NetHackWiki *Price identification*: “The sell price is easier to use because it is not affected by your charisma” | 3.6/3.7; 5.0 likely | high |
| If the shopkeeper has **no gold**, offer is **90% of normal sell price as store credit**. | NetHackWiki *Price identification*; alt.org shopping spoiler | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| If the shopkeeper has **some but not enough gold**, message is `"<shopkeeper> offers only <N> for your <item>"`. | NetHackWiki *Shop* §Selling | 3.6.7; 5.0 **UNVERIFIED** | medium |
| Dunce cap / Tourist ≤ level 14 / uncovered shirt → sell price is **⅓ base** instead of ½. | NetHackWiki *Price identification* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| General store: **42–44%** probability, stock 100% random; buys almost anything except worthless glass. | NetHackWiki *Shop* table; Fandom *Shop* | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Bookstore: **10%** probability, stock **90% scrolls / 10% spellbooks**. | NetHackWiki *Shop* table | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Liquor emporium: **10%**, stock **100% potions**. | NetHackWiki *Shop* table | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Jeweler: **3%**, stock **85% rings / 10% gems / 5% amulets**. | NetHackWiki *Shop* table | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Minetown: **Izchak’s lighting shop is guaranteed**; general store, food shop, and tool shop each have **~90%** chance in the standard variant. | NetHackWiki *Minetown*; alt.org Gazetteer | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Minetown has **seven map variants**; shop composition differs per variant. | NetHackWiki *Minetown*: “There are seven different minetowns” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| 5.0 added **in-game tutorial**; does **not** document exact 5.0 shop prompt changes. | 5.0 release summary | 5.0 | low (not a rule source) |

---

## Bot rules

### Rule 1 — Drop one candidate item and read the offer
**Trigger:** Hero is inside a shop; inventory contains an unknown item of a class the shop buys; bot wants to price-identify it.
**Action:**
1. Press `d`, select the item, confirm drop.
2. Read the prompt. Expected format: `"<Shopkeeper> offers <N> gold pieces for your <item>. Sell it? [ynaq]"`
3. Press **`n`** to decline.
4. Press `g` (or `,`) to pick the item back up.

**Done when:** offer number `N` is recorded for that item.
**If it fails:** if the item is not bought by this shop type, the shopkeeper may say “not interested”; move to a shop that buys the class (see Rule 3). Exact 5.0 refusal message is **UNVERIFIED**.
**Evidence:** sell prompt format; declining returns the item.

---

### Rule 2 — Re-drop to detect the 25% unidentified discount
**Trigger:** Offer `N` recorded; item is still unidentified; bot wants to know whether this shopkeeper is in the “25% less” group.
**Action:**
1. Pick up the item, drop it again, decline with `n`, pick up.
2. If the **same item** yields a **different offer** on a later drop, the shopkeeper’s modifier has been observed. Record both `N` values.
3. If the offer is **always the same**, the shopkeeper is either consistently in the discount group or consistently not. Do not assume the item is identified.

**Done when:** two distinct offer values have been recorded for the same item, or the bot decides the shopkeeper is consistent.
**If it fails:** if the offer never changes, treat the single value as the shopkeeper’s price and use base-price tables (Rule 4) rather than relying on the discount signal.
**Evidence:** “25% chance that you will only be offered 3/4 of the normal sell price”; “modifier is consistent for a given shopkeeper”; workaround is to re-drop until two prices are seen.

---

### Rule 3 — Route to the correct shop class
**Trigger:** Bot needs to price-identify a scroll, potion, ring, wand, amulet, or armor.
**Action:**

| Item class | Shop to use | Notes |
|---|---|---|
| Scrolls | Bookstore (10% of shops) | 90% scrolls / 10% spellbooks |
| Potions | Liquor emporium (10%) | 100% potions |
| Rings | Jeweler (3%) | 85% rings / 10% gems / 5% amulets |
| Amulets | Jeweler (3%) | 5% amulets |
| Wands | General store (42–44%) | General store is the fallback for wands |
| Armor | Used armor dealership (14%) | 90% armor |
| Weapons | Antique weapons outlet (5%) | 90% weapons |

If the current shop does not buy the class, **do not drop the item for sale**; the shopkeeper will refuse. Leave and find the right shop.
**Done when:** item is dropped in a shop that buys its class.
**If it fails:** if no suitable shop exists on the level, defer identification.
**Evidence:** shop-type stock table.

---

### Rule 4 — Compare offer `N` to base-price table (do not invent numbers)
**Trigger:** Offer `N` recorded for an unidentified item in a shop that buys its class.
**Action:**
1. Compute the **normal sell price** candidates: `floor(base_price / 2)` and, if the shopkeeper is in the discount group, `floor(base_price / 4)` (because “¼ less” of ½ base = ⅜ base; the wiki states “3/8 of the base price overall”).
2. For each candidate base price in the item class’s table, check whether `N` matches either the normal or discounted value.
3. If exactly one base price fits, the item’s base price is narrowed. Use the class’s base-price table to narrow the subtype.
4. **Do not hard-code base-price numbers from memory.** The bot should carry a table sourced from 5.0 `objects.c` / wiki; any number not in that table is **UNVERIFIED**.

**Done when:** candidate set is reduced, or no candidate fits.
**If it fails:** if no candidate fits, the item may be unidentified with an unidentified surcharge on the **buy** side (not sell), or the shopkeeper has no gold; record as **UNVERIFIED** and move on.
**Evidence:** sell price = ½ base, 25% chance of 3/8 base overall; buy-side surcharge is separate.

---

### Rule 5 — Handle “no gold” and “partial gold”
**Trigger:** Prompt includes **`only`** (`"offers only <N>"`) or offer is exactly 90% of the computed sell price.
**Action:**
- `"offers only <N>"` → shopkeeper has some but not enough gold; `N` is capped at available gold. **Do not use `N` for identification** until the shopkeeper has more gold.
- If offer is 90% of the computed price, the shopkeeper has **no gold**; `N` is store credit. **Do not use credit offers for price identification.**
- Sell a cheap item first to give the shopkeeper gold, then re-drop the candidate.

**Done when:** shopkeeper has enough gold for a normal offer.
**If it fails:** if the shopkeeper never has enough gold, defer.
**Evidence:** “offers only” message; 90% store credit rule.

---

### Rule 6 — Minetown routing
**Trigger:** Bot reaches Minetown.
**Action:**
- **Always** visit Izchak’s lighting shop (guaranteed) — it buys tools/lighting, not scrolls.
- If a **general store** exists (~90% in standard variant), use it for wands and miscellaneous items.
- If a **bookstore** exists in the variant, use it for scrolls; if not, scroll price-identification must wait for a non-Minetown bookstore or be done via general store buy-price (charisma-dependent).
- Consult the variant’s shop table (Rule 3) before routing.

**Done when:** bot has recorded which shop types exist.
**If it fails:** if no shop buys the class, do not force a sale.
**Evidence:** Minetown guaranteed lighting shop; ~90% general/food/tool in standard variant; seven variants.

---

## Risks and exceptions
- **Exact 5.0 prompt option letters are UNVERIFIED.** The `[ynaq]` set is 3.6/3.7-era. If 5.0 changed the prompt, the bot’s `n` answer may need to be remapped. Verify from a live 5.0 ttyrec before deploying.
- **Selling transfers ownership.** If the bot accidentally answers `y`, the item becomes the shopkeeper’s and must be bought back or stolen. Rule 1 always presses `n`.
- **Pets can steal dropped items** while the bot is re-dropping. Do not perform Rule 2 with a pet adjacent to the drop square.
- **Angering the shopkeeper.** Declining a sale is safe. Leaving the shop with unpaid items, teleporting out, or attacking the shopkeeper causes anger. The bot should never sell-then-steal.
- **The 25% discount is per-shopkeeper, not per-shop-type.** A general store in one game may discount and another may not; do not carry a “this shop discounts” assumption across games.
- **5.0 shop `shk.c` changes are UNVERIFIED.** No 5.0 source diff for the sell-price formula was obtained. Treat the 3.6.7 formula as a hypothesis to be tested in 5.0, not a confirmed constant.
- **Minetown variant completeness is UNVERIFIED for 5.0.** The seven-variant statement and the ~90% probabilities are 3.6/3.7-era; 5.0 may have adjusted them.

---

## Open questions
1. **Exact 5.0 sell prompt string** — is it still `"offers N gold pieces for your <item>. Sell it? [ynaq]"`, or did 3.7/5.0 change the options? **UNVERIFIED.**
2. **Exact 5.0 “not interested” message** when selling a class the shop does not buy. **UNVERIFIED.**
3. **Exact 5.0 sell-price formula in `shk.c`** — line numbers and whether the 25%/¼-less modifier survived. **UNVERIFIED.**
4. **Complete 5.0 Minetown variant shop table** — all seven variants and their guaranteed/probabilistic shops. **UNVERIFIED.**
5. **Whether 5.0 changed the 90% store-credit rule or the “offers only” message.** **UNVERIFIED.**
6. **Base-price tables for 5.0 scrolls/potions/rings/wands/amulets** — needed to operationalize Rule 4; not obtained here.

---
