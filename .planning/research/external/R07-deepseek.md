# R07 Read-testing scrolls and every scroll prompt (A)

## Summary
- **Do not read-test unidentified scrolls without a plan for genocide, teleportation, punishment, and destroy armor.** The four dangerous scrolls are genocide (cursed = reverse genocide), teleportation (cursed = uncontrolled), punishment (ball and chain), and destroy armor (destroys a worn piece).
- **BUC-test every scroll before read-testing.** A cursed scroll of genocide creates 4–6 of the named monster; a cursed scroll of teleportation can strand the hero. Reading an unknown scroll without BUC knowledge is the main source of read-testing deaths.
- **Remove important armor before read-testing.** A scroll of destroy armor selects a random worn piece; if only a sacrificial cloak and a suit are worn, the cloak is destroyed first. A cheap dwarvish/orcish cloak is the standard sacrifice.
- **Blessed destroy armor in 5.0 asks which armor to destroy** (commit `e23e6ef`). This is a 3.7/5.0 change; in 3.6 it destroyed a random piece. A bot reading a **blessed** destroy armor must answer the prompt with the piece it wants to lose — or avoid reading blessed destroy armor on a piece it needs.
- **Identify is 18% of randomly generated scrolls.** This makes price-identification of the cheapest scroll a reliable way to find identify scrolls without reading unknowns.
- **Punishment is removable with a scroll of remove curse of any BUC status while not confused**, a wand of opening/knock at the chain, prayer (minor problem), a metallivore eating the ball, or a nymph stealing it. Do not read unknown scrolls while confused if punishment is a risk.

---

## Facts

| Claim | Source | Version | Confidence |
|---|---|---|---|
| Reading a **cursed scroll of genocide** creates **4–6** of the specified monster (reverse genocide). | NetHackWiki *Genocide*; Fandom *Genocide* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Reading a **cursed scroll of teleportation** can be “very dangerous” (uncontrolled teleport). | NetHackWiki *Scroll* §Identification | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| **BUC-test all scrolls** before read-testing; do not read-identify a cursed scroll. | NetHackWiki *Scroll* §Identification | 3.6/3.7; 5.0 likely | high |
| **Scroll of identify** = **18%** of randomly generated scrolls (9/50). | NetHackWiki *Scroll of identify*: “18% of all randomly generated scrolls will be a scroll of identify” | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Scroll of identify prompts: **“What do you want to identify <first/next>?”** and opens an inventory menu of unidentified items. | NetHackWiki *Scroll of identify* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Blessed/uncursed identify scroll identifies **1, 2, 3 …** items depending on beatitude. | NetHackWiki *Scroll of identify* | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Scroll of **genocide** prompt: asks **what to genocide**; answer **“none”** to preserve genocideless conduct. | NetHackWiki *Genocide* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Invalid genocide answer **five times** results in nothing genocided; conduct preserved. | NetHackWiki *Genocide* | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Scroll of **stinking cloud** auto-identifies and prompts **“Where do you want to center the cloud?”**; selecting an invalid square uses the scroll with no effect. | NetHackWiki *Scroll of stinking cloud* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Scroll of **charging** prompts the hero to **select an item** from inventory; confused reading instead **increases energy to maximum**. | NetHackWiki *Scroll of charging*; Fandom *Scroll of charging* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Blessed charging restores **more charges**; cursed charging restores **none**. | Fandom *Scroll of charging* | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| **Blessed scroll of destroy armor asks which armor to destroy** (3.7/5.0 change). | GitHub commit `e23e6ef`: “Blessed scroll of destroy armor asks which armor to destroy”; `any_worn_armor_ok` / `count_worn_armor` added | 3.7/5.0 commit; **UNVERIFIED** whether the commit is in 5.0.0 release | medium for 3.7; low for 5.0.0 |
| Unblessed/uncursed destroy armor destroys **one random worn piece**. | NetHackWiki *Scroll of destroy armor*; Fandom | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| If a cloak and suit are worn, destroy armor **destroys the cloak first**. | NetHackWiki *Scroll* §Identification: “If you are wearing only a cloak and a suit, the scroll of destroy armor always destroys the cloak” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| **Punishment** removable by: scroll of remove curse (any BUC, not confused); wand of opening / knock at chain; prayer (minor problem); metallivore eats ball; nymph steals ball; polymorph to nymph and #monster. | NetHackWiki *Punishment* | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |
| Dragging the iron ball takes **at least 2 turns per square** regardless of speed; inhibits travel/run. | NetHackWiki *Punishment* | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Destroy armor **does not risk vaporisation** when read confused (it erodeproofs/repairs but does not raise enchantment). | Fandom *Scroll of enchant armor*: “Reading a cursed scroll of destroy armor while confused will erodeproof but not repair your armor” | 3.6/3.7; 5.0 **UNVERIFIED** | medium |
| Take off **important armor** before read-testing; take off **weapon** if enchanted past +5 (enchant weapon can destroy it). | NetHackWiki *Scroll* §Identification | 3.6/3.7; 5.0 **UNVERIFIED** | high for 3.6/3.7 |

---

## Bot rules

### Rule 0 — Never read-test an unidentified scroll without BUC knowledge and a safe room
**Trigger:** Bot is considering reading an unidentified scroll.
**Action:**
1. **Do not read** if the scroll’s BUC status is unknown and the bot has not BUC-tested it.
2. BUC-test by dropping the scroll for a pet, or by using a known scroll of identify on it, or by price-identifying it.
3. Only after BUC is known, proceed to the scroll-specific rules below.
4. Read-test only in a **safe room** with no adjacent monsters, no lava, and a known upstairs/escape route.

**Done when:** scroll BUC is known and the bot is in a safe room.
**If it fails:** if BUC cannot be determined, do not read; store the scroll.
**Evidence:** cursed genocide and cursed teleportation are the main read-testing dangers; BUC-testing is the standard precaution.

---

### Rule 1 — Identify scroll (`?` of identify)
**Trigger:** Scroll is identified as identify (by price, by previous read, or by type name).
**Action:**
1. Press `r`, select the identify scroll.
2. When prompted **“What do you want to identify <first/next>?”**, select the **highest-value unidentified item** first (artifact, wand, ring, amulet).
3. If the scroll is **blessed**, expect **multiple** prompts; select additional items until the prompt ends.
4. If the menu appears, select items with the menu letter; press `Enter` to confirm.

**Done when:** prompt ends and item(s) are identified.
**If it fails:** if the scroll was cursed, it may identify only one item or none; do not waste additional scrolls on the same unknown batch.
**Evidence:** identify prompt format; blessed/uncursed item counts.

---

### Rule 2 — Genocide scroll
**Trigger:** Scroll is identified as genocide.
**Action:**
- **Uncursed/blessed:** at the **“What do you want to genocide?”** prompt, answer a **strategic monster class** the bot wants removed (e.g., `L` for liches late-game, or `;` for sea monsters). If the bot is preserving genocideless conduct, answer **`none`**.
- **Cursed:** **do not read** unless the bot deliberately wants reverse genocide (e.g., to create a monster for sacrifice or a specific drop). Cursed genocide creates 4–6 of the named monster.
- **If BUC unknown:** do not read. If forced to read, answer **`none`** and accept that the scroll is wasted; do not name a dangerous class.

**Done when:** genocide resolves.
**If it fails:** if a cursed genocide creates a dangerous monster, use teleportation, Elbereth, or a wand to escape; do not melee.
**Evidence:** cursed genocide = 4–6 monsters; `none` preserves conduct; five invalid answers = nothing happens.

---

### Rule 3 — Teleportation scroll
**Trigger:** Scroll is identified as teleportation.
**Action:**
- **Uncursed/blessed:** read only when the bot has **teleport control** or wants a random teleport. If no control, read only in an emergency.
- **Cursed:** **do not read** unless the bot accepts an uncontrolled teleport. Cursed teleportation is “very dangerous”.
- If the bot has **teleport control**, answer the “Where do you want to teleport?” prompt with a known safe square.

**Done when:** teleport resolves.
**If it fails:** if uncontrolled, reorient using the map and stairs.
**Evidence:** cursed teleportation is dangerous; uncursed is controllable only with teleport control.

---

### Rule 4 — Punishment scroll
**Trigger:** Scroll is identified as punishment.
**Action:**
- **Do not read** unless the bot wants to be punished (rare).
- If the bot becomes punished accidentally, immediately apply **Rule 8** to remove the ball and chain.

**Done when:** scroll not read, or punishment removed.
**If it fails:** if the bot is punished and has no removal method, pray (punishment is a minor problem) or find a scroll of remove curse.
**Evidence:** punishment removal methods.

---

### Rule 5 — Destroy armor scroll
**Trigger:** Scroll is identified as destroy armor.
**Action:**
- **Uncursed/blessed (3.6 and earlier):** **do not read** if any worn armor is important; it destroys a random worn piece. If the bot must read it (e.g., to identify it from an unknown stack), first remove all armor except a **sacrificial cloak**.
- **Blessed in 3.7/5.0 (if the commit is in 5.0.0):** reading prompts **which armor to destroy**. Select the **sacrificial cloak** or the least valuable worn piece. **Do not select a piece the bot needs.**
- **Cursed:** do not read on a piece the bot needs.

**Done when:** scroll resolves or is not read.
**If it fails:** if a needed piece is destroyed, replace it from the Mines or a shop.
**Evidence:** unblessed destroys random worn piece; blessed 3.7/5.0 asks which armor; cloak-first rule.

---

### Rule 6 — Stinking cloud scroll
**Trigger:** Scroll is identified as stinking cloud.
**Action:**
1. Press `r`, select the scroll.
2. At **“Where do you want to center the cloud?”**, select a square **adjacent to the bot** if the bot wants to damage nearby monsters, or a **far square** if the bot wants to avoid the cloud.
3. Do **not** select a square out of range or not visible; the scroll is consumed with no effect.

**Done when:** cloud is placed.
**If it fails:** if the bot lacks poison resistance, do not stand in the cloud.
**Evidence:** prompt text; invalid square uses scroll with no effect.

---

### Rule 7 — Charging scroll
**Trigger:** Scroll is identified as charging.
**Action:**
1. Press `r`, select the scroll.
2. At the **item selection prompt**, choose a **wand with 0 charges** or a **tool that needs charging** (e.g., oil lamp, brass lantern).
3. If the bot is **confused**, reading instead **restores energy to maximum**; do not select an item in that case.
4. **Cursed:** do not read; it restores no charges.

**Done when:** item is charged or energy is restored.
**If it fails:** if a wand is already at full charges, do not waste the scroll on it.
**Evidence:** charging prompt; confused = energy; cursed = no charges.

---

### Rule 8 — Remove punishment
**Trigger:** Bot is punished (ball and chain attached).
**Action, in order of preference:**
1. **Scroll of remove curse** (any BUC status), read while **not confused**.
2. **Wand of opening** or **spell of knock**, zapped **down at the chain**.
3. **Pray** (punishment counts as a minor problem; do not pray if prayer timeout is active).
4. **Metallivore** (rock mole, rust monster) eats the ball.
5. **Nymph** steals the ball.
6. **Polymorph into a nymph** and use `#monster` to remove it.

**Done when:** ball and chain are gone.
**If it fails:** if no method works, continue playing with the ball; do not read unknown scrolls while punished if it can be avoided.
**Evidence:** punishment removal methods; 2 turns per square while dragging.

---

### Rule 9 — Do not read unknown scrolls while confused unless the scroll is known safe
**Trigger:** Bot is confused and considering reading an unknown scroll.
**Action:**
- **Do not read** an unidentified scroll while confused. Confusion changes many scroll effects (enchant armour repairs instead of enchants; destroy armour erodeproofs; charging restores energy; teleportation may be uncontrolled).
- If the bot must read a **known** scroll while confused, follow the confused-specific rules above.

**Done when:** confusion ends, or the known scroll is read.
**If it fails:** wait out confusion or use a unicorn horn (if it cures confusion in 5.0 — **UNVERIFIED** whether the horn’s confusion cure survived the 5.0 attribute-restoration removal).
**Evidence:** confused scroll effects differ; cursed scrolls are more dangerous when confused.

---

## Decision table: scroll → read now? → prompt answer

| Scroll | Read now? (BUC known) | Prompt | Bot answer |
|---|---|---|---|
| **Identify** | Yes, always safe | “What do you want to identify?” | Highest-value unidentified item; `Enter` |
| **Genocide** (uncursed/blessed) | Yes, if strategic target chosen | “What do you want to genocide?” | Strategic class, or `none` for genocideless |
| **Genocide** (cursed) | **No**, unless reverse genocide wanted | “What do you want to genocide?” | If forced: `none`; else do not read |
| **Teleportation** (uncursed/blessed) | Yes, if control or emergency | “Where do you want to teleport?” | Safe known square (with control) |
| **Teleportation** (cursed) | **No** | — | Do not read |
| **Punishment** | **No** | — | Do not read |
| **Destroy armor** (uncursed, 3.6) | **No** on important armor | — | Remove armor; sacrificial cloak only |
| **Destroy armor** (blessed, 3.7/5.0) | Only on sacrificial piece | “Which armor?” | Sacrificial cloak |
| **Destroy armor** (cursed) | **No** on needed armor | — | Do not read |
| **Stinking cloud** | Yes, with poison resistance | “Where do you want to center the cloud?” | Adjacent or far square; never invalid |
| **Charging** (uncursed/blessed) | Yes, on empty wand/tool | Item selection | Empty wand or tool |
| **Charging** (cursed) | **No** | — | Do not read |
| **Charging** (confused) | Yes, for energy | — | No item selection; energy restores |
| **Enchant weapon** | Yes, but unwield if > +5 | — | Unwield first |
| **Enchant armor** | Yes, after isolating target | — | Follow R05 Rule 1 |
| **Remove curse** | Yes, if cursed items worn | — | Read while not confused |
| **Create monster** | Yes, if ready for a fight | — | Clear adjacent squares |
| **Earth** | **No** unless digging wanted | — | Do not read in a corridor |
| **Fire** | Yes, if fire resistance or destroy armor wanted | — | Aim at target |
| **Food** / **Taming** / **Magic mapping** / **Light** / **Blank** | Generally safe | Varies | Follow normal use |

---

## Risks and exceptions
- **The blessed destroy armor prompt is 3.7/5.0, not 3.6.** Commit `e23e6ef` is in the 3.7 line; whether it is in the **5.0.0 release** is **UNVERIFIED**. If 5.0.0 does **not** have it, blessed destroy armor still destroys a random worn piece, and Rule 5’s “answer the prompt” step is invalid.
- **Cursed genocide is the deadliest read-testing mistake.** A bot that reads an unknown scroll of genocide and names a dangerous class can create 4–6 monsters that kill it. Rule 2 defaults to `none` when BUC is unknown.
- **Punishment plus low HP is a death spiral.** Dragging the ball costs 2 turns per square; a punished bot cannot flee. Remove punishment immediately if HP is low.
- **Destroy armor can destroy the bot’s best armor.** Rule 5’s sacrificial cloak is not optional; it is the difference between losing a cloak and losing a mithril-coat.
- **Confusion changes scroll identity.** A bot that reads an unknown scroll while confused may misidentify it (e.g., confused enchant armour repairs instead of enchanting). Do not read unknowns while confused.
- **5.0 scroll prompt changes are largely UNVERIFIED.** Only the blessed destroy armor change is confirmed at commit level; the other prompt strings are 3.6/3.7-era.
- **Identify scroll frequency (18%) is 3.6/3.7-era.** 5.0 may have changed scroll generation; price-identify the cheapest scroll rather than assuming 18%.

---

## Open questions
1. **Is commit `e23e6ef` (blessed destroy armor prompt) actually in the 5.0.0 release?** The commit is in the 3.7 line; 5.0.0 inclusion is **UNVERIFIED.**
2. **Exact 5.0 scroll of genocide prompt string** — still “What do you want to genocide?” **UNVERIFIED.**
3. **Exact 5.0 identify scroll prompt** — “What do you want to identify <first/next>?” **UNVERIFIED.**
4. **Exact 5.0 stinking cloud prompt** — still “Where do you want to center the cloud?” **UNVERIFIED.**
5. **Exact 5.0 charging prompt** — does it include oil lamps and lanterns by default (commit `4e1cf071` suggests yes in 3.7)? **UNVERIFIED** for 5.0.0.
6. **Does the 5.0 unicorn horn still cure confusion?** The 5.0 attribute-restoration removal may have affected other horn functions. **UNVERIFIED.**
7. **Exact 5.0 scroll frequency table** — is identify still 18%? **UNVERIFIED.**
8. **Exact 5.0 punishment removal methods** — did 5.0 change prayer, remove curse, or metallivore behaviour? **UNVERIFIED.**
