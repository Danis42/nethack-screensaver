# R08 Avoiding starvation (B)

## Summary

- **Do not wait for the `Weak` status.** In NetHack 5.0, `Hungry` begins at 51–150 nutrition, `Weak` at 1–50, and fainting at zero or below. The Valkyrie receives the specific message `Valkyrie needs food, badly!` when entering Weak. [5.0 `src/eat.c::newuhs()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3175-L3187) [5.0 `src/eat.c::newuhs()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3291-L3304)
- **Carry a predictable food reserve before entering the Gnomish Mines.** Rations, lembas, cram and K-rations have known nutrition values; corpses and tins are contingency food, not the sole plan. [5.0 `include/objects.h`, food objects](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h#L1054-L1076)
- **Lichen and lizard corpses are valuable age-safe food.** The 5.0 nonrotting-corpse list includes both; their species-specific hazards still need to be checked for any other corpse. [5.0 `src/eat.c`, nonrotting corpse definitions](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60)
- **Never blindly eat an unknown corpse.** Poison, acid, petrification, sliming, cannibalism and rot are distinct dangers. A neutral human Valkyrie must never eat a human corpse. [5.0 `src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1825) [5.0 `src/eat.c::maybe_cannibal()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L703-L734)
- **Prayer can remedy hunger, but it is an emergency buffer, not a food supply.** A successful prayer sets a randomized timeout based on `rnz(350)`, and other prayer restrictions still apply. [5.0 `src/pray.c`, hunger trouble and remedy](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L255-L263) [5.0 `src/pray.c`, prayer timeout](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L1295-L1315)
- The supplied 15.7% starvation-loss rate is bot telemetry, not a published human-game statistic. The 5.0 source confirms the hunger-state mechanics below; it does not explain the bot's observed loss rate by itself.

## Facts

| Claim | Source | Version | Confidence |
|---|---|---:|---|
| Hunger states are determined by nutrition: `SATIATED` above 1000; `NOT_HUNGRY` above 150; `HUNGRY` above 50; `WEAK` above 0; `FAINTING` at 0 or less. | [`src/eat.c::newuhs()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3175-L3187) | 5.0.0 | high |
| When a Valkyrie enters the Weak state, the role-specific message is `Valkyrie needs food, badly!`. | [`src/eat.c::newuhs()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3291-L3304) | 5.0.0 | high |
| Starvation death occurs only after nutrition drops below `-(100 + 10 * CON)`; fainting and Weak happen earlier. | [`src/eat.c`, starvation handling](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3215-L3254) | 5.0.0 | high |
| Corpse rot is calculated from `(moves - corpse_age) / (10 + rn2(20))`; cursed corpses get an extra rot adjustment and blessed corpses a freshness adjustment. The divisor is therefore randomized from 10 through 29, so there is no single universal corpse-age expiry. | [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1798) | 5.0.0 | high |
| For an ordinary uncursed corpse, an age under 40 moves keeps the calculated rot at 3 or less even with the smallest possible divisor; this avoids the source's `rotted > 3` illness test on that check. This is a conservative derived guarantee, not a general edible-age limit for cursed corpses or special species. | [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1806) | 5.0.0 | medium |
| A corpse becomes tainted once its rot value exceeds the code's taint threshold; illness can occur at a lower rot threshold. Illness damage is randomized. | [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1806) | 5.0.0 | high |
| Acidic corpses can cause `rnd(15)` damage without acid resistance. | [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1807-L1815) | 5.0.0 | high |
| Poisonous corpses can cause strength loss and HP damage without poison resistance; the poison effect has a 4-in-5 check in this code path. | [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1815-L1825) | 5.0.0 | high |
| A human hero eating a human corpse triggers cannibalism consequences. | [`src/eat.c::maybe_cannibal()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L703-L734) | 5.0.0 | high |
| Lichen and lizard corpses are included in the nonrotting corpse list. This means age does not taint them; it does not make every nonrotting corpse safe to eat. | [`src/eat.c`, nonrotting corpse list](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60) | 5.0.0 | high |
| Riders and acid blobs also occur in special nonrotting handling, but Riders are not safe food and acid blobs retain their acid hazard. | [`src/eat.c`, nonrotting corpse list](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60) [`src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1807-L1815) | 5.0.0 | high |
| The pre-eating check can warn that an item or corpse may be tainted or dangerous. A bot should answer no to a warning it cannot resolve. | [`src/eat.c`, pre-eat warning](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L2491-L2535) | 5.0.0 | high |
| A cursed tin is treated as rotten; tins do not remove the underlying danger of eating the corpse species inside them. | [`src/eat.c`, tin preparation and eating](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1391-L1424) [`src/eat.c`, tin consumption](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1507-L1536) | 5.0.0 | high |
| Food-ration nutrition is 800; lembas is 800; cram is 600; K-ration is 400; C-ration is 300. | [`include/objects.h`, food definitions](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h#L1054-L1076) | 5.0.0 | high |
| Hunger is recognized as a prayer trouble; successful prayer can restore the hero's hunger state with `Your stomach feels content.` | [`src/pray.c`, trouble assessment](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L255-L263) [`src/pray.c`, trouble remedy](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L379-L387) | 5.0.0 | high |
| A successful prayer establishes a randomized timeout using `rnz(350)`; further conditions modify prayer availability. This is not a fixed 350-turn cooldown. | [`src/pray.c`, successful-prayer timeout](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L1295-L1315) | 5.0.0 | high |
| The 5.0 source explicitly says globs do not become tainted; they shrink away instead. | [`src/eat.c`, glob handling/comment](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L2484-L2490) | 5.0.0 | high |
| A complete 3.7-to-5.0 change list for hunger, corpse safety and food generation is **UNVERIFIED** here. Do not import a 3.6 food rule unless confirmed against the 5.0 code. | No complete source diff established | 3.7/5.0 | low |

### Conservative corpse policy for a human Valkyrie

| Category | Bot policy | Reason / evidence | Version | Confidence |
|---|---|---|---:|---|
| Lichen | Eat when hungry if known fresh/identified; age-safe. | Nonrotting list; normal species food. [`eat.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60) | 5.0.0 | high |
| Lizard | Eat when hungry if identified; age-safe, and keep one in reserve where possible. | Nonrotting list. [`eat.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60) | 5.0.0 | high |
| Fresh, identified, nonhuman corpse with no poison/acid/stone/slime flags | Candidate food only after species-specific checks. | Corpse effects are conditional on species traits and corpse age. [`eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1825) | 5.0.0 | high |
| Human corpse | **Never eat.** | Human-on-human cannibalism. [`maybe_cannibal()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L703-L734) | 5.0.0 | high |
| Poisonous corpses (for example, soldier ant, killer bee, poisonous snakes and poisonous kobolds) | Avoid unless poison resistance is confirmed and the nutrition need justifies it. | Poison flag and eating poison effect. [`monsters.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h) [`eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1815-L1825) | 5.0.0 | high for poison hazard; per-species list must be maintained |
| Acidic corpses (for example, acid blob and ochre jelly) | Avoid without acid resistance. | Acid corpse damage. [`eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1807-L1815) | 5.0.0 | high |
| Cockatrice / chickatrice | **Never eat.** | Petrification risk; [NetHackWiki: Cockatrice](https://nethackwiki.com/wiki/Cockatrice) (current Wiki; exact version unspecified). | Wiki, current | high |
| Green slime | **Never eat.** | Sliming risk; [NetHackWiki: Green slime](https://nethackwiki.com/wiki/Green_slime) (current Wiki; exact version unspecified). | Wiki, current | high |
| Riders | **Never eat.** | Their special nonrotting status is not a safety guarantee. [NetHackWiki: Rider](https://nethackwiki.com/wiki/Rider) (current Wiki; exact version unspecified). | Wiki, current | high |
| Corpse that emits `... could be tainted!` or `... could be something very dangerous!` | Cancel; do not override automatically. | 5.0 pre-eat warning path. [`eat.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L2491-L2535) | 5.0.0 | high |

## Bot rules

### Rule 1 — Maintain a food reserve before entering the Mines

- **Trigger =** Status line shows `Hungry`, or bot is about to descend into the Gnomish Mines and its inventory has fewer than the configured food reserve.
- **Action =** Prefer carrying a known ration/packaged food item; do not rely on corpses being generated. When food is needed, press `e`, select the known food inventory letter, and confirm any quantity prompt for one item.
- **Done when =** Hunger status returns to `Not Hungry` or better, and a reserve remains where possible.
- **If it fails =** If there is no known food, search nearby safe corpses/shops; do not spend many exploration turns at Weak while hoping for food.
- **Evidence =** 5.0 nutrition thresholds in `src/eat.c::newuhs()` and food nutrition in `include/objects.h`.

### Rule 2 — Eat before Weak

- **Trigger =** Status line is `Hungry`, or a hunger message indicates the next step may be Weak; use the explicit `Valkyrie needs food, badly!` as an emergency trigger, not the normal trigger.
- **Action =** Press `e`; choose the best known food item by nutrition per weight and strategic reserve policy. Re-check the status line after eating.
- **Done when =** The status is no longer `Hungry` or the hunger budget has been restored above the configured target.
- **If it fails =** If the bot is already Weak or Fainting and has no food, search immediately for a safe lichen/lizard/other verified food source or use an eligible prayer only if prayer conditions permit.
- **Evidence =** 5.0 `src/eat.c::newuhs()` and Valkyrie Weak-entry message.

### Rule 3 — Eat only verified corpses

- **Trigger =** A corpse appears in inventory or on the floor, and the monster species is known.
- **Action =** Check a species denylist for poison, acid, petrification, sliming, human cannibalism, Rider status and other special hazards. Check corpse age/taint warnings. If the bot can track the corpse's creation move, prefer an ordinary uncursed corpse younger than 40 moves for a conservative rot/illness margin; otherwise use only age-safe corpses or cancel. If accepted, press `e`, select the corpse, and answer `y` only when the species and age are verified safe.
- **Done when =** The corpse is eaten without a danger warning and hunger improves.
- **If it fails =** If the warning text says `... could be tainted!` or `... could be something very dangerous!`, answer `n` or Escape. Do not eat an unidentified corpse to identify it.
- **Evidence =** 5.0 `src/eat.c::eatcorpse()`, `maybe_cannibal()`, and pre-eat warning code.

### Rule 4 — Prefer lichen and lizard as emergency corpse food

- **Trigger =** Identified lichen or lizard corpse is available and the hero is Hungry or worse.
- **Action =** Press `e`, select the lichen/lizard corpse, and answer any prompt only after confirming the name.
- **Done when =** The corpse is consumed and hunger status improves.
- **If it fails =** If a warning or unusual status appears, cancel and re-evaluate; nonrotting does not mean every corpse is harmless.
- **Evidence =** 5.0 `src/eat.c` nonrotting corpse list.

### Rule 5 — Use tins as stored food, not as a safety bypass

- **Trigger =** A known tin is in inventory and the bot needs food; BUC is not cursed or the bot has deliberately accepted the risk.
- **Action =** Press `e`, select the tin, and follow the open/eat prompts. If using a tin opener, `a` then select the tin opener and target the tin; exact NLE prompt rendering is UNVERIFIED.
- **Done when =** The tin is consumed and hunger improves.
- **If it fails =** If the tin is cursed or its contents are dangerous/unknown, do not force consumption merely because it is preserved.
- **Evidence =** 5.0 `src/eat.c` tin preparation and consumption.

### Rule 6 — Buy food when a safe shop is available

- **Trigger =** The bot is in a known general store or food shop, is Hungry, and has enough gold without sacrificing essential equipment budget.
- **Action =** Press `p`, select a known ration, lembas, cram or other food item from the shop's floor stock, and confirm the purchase amount/price prompt.
- **Done when =** Food is in inventory and the gold balance reflects the purchase.
- **If it fails =** If the shop is hostile, the item is unpaid/unavailable, or the cost is unaffordable, leave it and use the reserve/other food policy.
- **Evidence =** NetHackWiki: [Shop](https://nethackwiki.com/wiki/Shop) and [Food](https://nethackwiki.com/wiki/Food) (current Wiki; exact version unspecified); 5.0 shop code for purchase handling.

### Rule 7 — Pray only as a hunger emergency

- **Trigger =** Hero is Weak or Fainting, no food is available, and prayer eligibility is known to be plausible (not recently prayed, deity not displeased).
- **Action =** Press `M-p` (`#pray`); do not issue repeated prayers if rejected. On success, recognize `Your stomach feels content.` and re-check status.
- **Done when =** Hunger is restored or food has been obtained.
- **If it fails =** Treat prayer as unavailable; immediately prioritize food acquisition. Do not budget prayer as a repeatable source of nutrition because the timeout is randomized and other conditions apply.
- **Evidence =** 5.0 `src/pray.c`, hunger trouble and `rnz(350)` timeout.

## Risks and exceptions

1. **Weak is already a late trigger.** It is not the point at which the hero first needs food. Use `Hungry` as the routine decision state and Weak as an emergency trigger. [5.0 `src/eat.c::newuhs()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L3175-L3187)
2. **Freshness cannot safely be inferred from the floor glyph alone.** The code uses corpse age and randomized rot; if NLE does not expose corpse age, the bot needs conservative message-based checks. UNVERIFIED whether this NLE build exposes exact corpse age. [5.0 `src/eat.c::eatcorpse()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1772-L1798)
3. **Tinning preserves food, not safety.** The original corpse's poison, acid, stoning, cannibalism and other special effects remain relevant; cursed tins are rotten. [5.0 `src/eat.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L1391-L1424)
4. **Do not eat human corpses.** This is cannibalism for the human Valkyrie. [5.0 `src/eat.c::maybe_cannibal()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L703-L734)
5. **Do not treat all nonrotting corpses as safe.** Riders and acid blobs are special cases in the nonrotting logic but are dangerous. [5.0 `src/eat.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/eat.c#L48-L60) [NetHackWiki: Rider](https://nethackwiki.com/wiki/Rider)
6. **Prayer has a randomized timeout.** `rnz(350)` is not a fixed interval; the bot should not depend on being able to pray again after a fixed exact number of turns. [5.0 `src/pray.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c#L1295-L1315)
7. **3.7 food changes:** a complete exhaustive diff is UNVERIFIED. The bot should treat the 5.0 release source, not older 3.6 summaries, as its executable specification.

## Open questions

- Whether the NLE observation object exposes exact nutrition or only the status string `Hungry`/`Weak`: **UNVERIFIED**.
- Whether the configured NLE build exposes corpse age or only taint/warning messages: **UNVERIFIED**.
- A complete 3.7-to-5.0 list of food-generation, corpse-age, tin and prayer changes: **UNVERIFIED**.
- The 15.7% starvation-loss rate and a breakdown by cause/turn/depth are user-supplied telemetry; a named run sample was not provided.
