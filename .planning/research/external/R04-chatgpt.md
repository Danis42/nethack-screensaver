# R04 Sell-price identification in 5.0 shops (A)

## Summary

- Yes: deliberately dropping one item inside a suitable shop is a safe price-quote method, provided the shopkeeper is peaceful and you answer `n`. The deliberate-drop path asks whether to sell; declining leaves the item yours. Use `d`, not an accidental drop.
- For a neutral Valkyrie not wearing a dunce cap or an exposed shirt, the normal offer is rounded `base price ÷ 2`. One quarter of shopkeepers instead offer rounded `3 × base price ÷ 8` for unidentified items. This is a stable property of the shopkeeper, derived from `m_id % 4`, not a fresh random roll for each item. [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998)
- The phrase “a sucker” is not a separate sale-dialog message. It describes the less favorable formula triggered by wearing a dunce cap or a visible shirt without body armor or a cloak. [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2961-L2967)
- General stores and bookstores buy scrolls. Other shop types have narrower acceptance rules; a potion shop buys potions, a ring shop buys rings and amulets, and the shop called a wand shop is actually a quality-apparel shop that accepts wands. [5.0 `shknam.c::shtypes[]` and `saleable()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L194-L331)
- One quote identifies a base-price bucket, not necessarily the exact object. Some different scrolls, potions, rings, and wands share prices. Ordinary amulets all have the same base price, so this method cannot distinguish their types.
- Minetown has seven map variants. College Town is the one with a guaranteed bookstore; Orcish Town has no functioning shopkeepers. The other variants rely on general, tool, food, and candle shops, with some shops optional. [5.0 `dat/minetn-1.lua`–`dat/minetn-7.lua`](https://github.com/NetHack/NetHack/tree/NetHack-5.0.0_Released/dat?utm_source=chatgpt.com)

## Facts

### 1. Exact sale-dialog behavior

The relevant command path in 5.0 is `do.c::dodrop()` followed by `shk.c::sellobj_state()` and `shk.c::sellobj()`. A deliberate drop sets the sale response to unset, so the shopkeeper asks. An accidental drop sets the response to automatic acceptance. [5.0 `do.c::dodrop()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do.c?utm_source=chatgpt.com#L23-L39) [5.0 `shk.c::sellobj_state()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3670-L3682)

| Situation                                   | Message / prompt                                                                             | Meaning and bot interpretation                                                              | Source                                                                                                                             | Version | Confidence |
| ------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| Ordinary offer, one item                    | `<shk> offers N gold piece(s) for your <item>. Sell it?`                                     | `N` is the offer. Answer `n` to decline.                                                    | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3880-L3907)  | 5.0.0   | high       |
| Ordinary offer, stack                       | Same offer structure, with plural wording such as `Sell them?`                               | `N` is for the offered object quantity, not necessarily one unit.                           | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3880-L3898)  | 5.0.0   | high       |
| Shopkeeper has some, but not enough, gold   | `<shk> offers only N gold piece(s) ...`                                                      | The amount is capped by the keeper's available gold. It is not a valid price-ID quote.      | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3831-L3835)  | 5.0.0   | high       |
| Shopkeeper has no gold                      | `<shk> cannot pay you at present.` followed by `Will you accept N ... in credit for <item>?` | This is a credit offer, not a cash offer. Declining with `n` keeps the item yours.          | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3793-L3830)  | 5.0.0   | high       |
| Shopkeeper does not want the item           | `<shk> seems uninterested.`                                                                  | No sale price is offered. This does not mean the item's base price is zero.                 | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3781-L3791)  | 5.0.0   | high       |
| Part of a container's contents are unwanted | `<shk> seems uninterested in the rest.`                                                      | Container-specific case; not a price quote for the unwanted contents.                       | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3781-L3791)  | 5.0.0   | high       |
| Angry shopkeeper                            | `Thank you, scum!` or, if unable to speak, `<shk> smirks with satisfaction.`                 | The keeper takes the item without paying. Do not perform a price test with an angry keeper. | [`shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3721-L3729)  | 5.0.0   | high       |
| “A sucker”                                  | No separate “sucker” message                                                                 | It is a pricing condition caused by worn gear, not an additional dialogue branch.           | [`shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2961-L2967) | 5.0.0   | high       |

The normal offer is built by `safe_qbuf()` and passed to `nyaq()`. The source supports the `y`, `n`, `a`, and `q` responses. The precise display of the choices as `[ynaq]` in the particular NLE terminal build is UNVERIFIED; the game-side response characters are verified. [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3880-L3935)

What the responses do:

| Key | Effect                                                          | Bot policy                                                       |
| --- | --------------------------------------------------------------- | ---------------------------------------------------------------- |
| `y` | Accepts the sale. The item is relinquished and payment is made. | Never use for price identification.                              |
| `n` | Declines; the item remains yours and is marked no-charge.       | Use this.                                                        |
| `a` | Accepts and makes future sale prompts automatically accept.     | Never use.                                                       |
| `q` | Declines and sets the future sell response to `n`.              | Avoid; use `n` so the bot does not change later prompt behavior. |

Source: [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3901-L3935).

### 2. Sell-price formula and the one-quarter shopkeepers

For the requested classes, define `P` as the object's base `oc_cost`, after any special `getprice()` adjustments. For a single eligible item sold by a peaceful shopkeeper:

| Condition                                                            | Offer formula           |
| -------------------------------------------------------------------- | ----------------------- |
| Neutral Valkyrie, ordinary outfit, ordinary shopkeeper               | `round_half_up(P / 2)`  |
| Same outfit, low-quote shopkeeper, unidentified item                 | `round_half_up(3P / 8)` |
| Wearing a dunce cap or a visible shirt without body armor or a cloak | `round_half_up(P / 3)`  |
| Same “sucker” outfit, low-quote shopkeeper, unidentified item        | `round_half_up(P / 4)`  |

`round_half_up` here means the integer rounding performed by the source: multiply by ten, divide, add five, then divide by ten. The formula and outfit conditions are explicit in 5.0 `shk.c::set_cost()`. [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998)

The low-quote condition is:

```
if (!obj->dknown || !objects[obj->otyp].oc_name_known) {
    ...
} else if (tmp > 1L && !(shkp->m_id % 4))
    multiplier *= 3L, divisor *= 4L;
```

In practical terms:

- It applies when either the object's appearance has not been seen (`dknown` false) or the true object type is not known globally (`oc_name_known` false).
- For non-gems, one in four shopkeeper IDs satisfies `m_id % 4 == 0`.
- The selection is per shopkeeper. The same keeper has the same low-quote property for all qualifying unknown items.
- It does not apply when the object is already known, or when its effective price is at most one.

Source: [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2968-L2980).

Version comparison

| Claim                                                                                                                                                                                                    | Source                                                                                                                                   | Version | Confidence |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| The sale calculation, outfit divisor, unidentified-item condition, and `m_id % 4` low-quote branch use the same logic for the requested non-gem categories.                                              | [`shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998)       | 5.0.0   | high       |
| The corresponding 3.7 `set_cost()` logic matches the 5.0 logic for these non-gem classes.                                                                                                                | [`3.7 shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-3.7/src/shk.c?utm_source=chatgpt.com#L2954-L2998)              | 3.7     | high       |
| The same basic non-gem formula and low-quote mechanism are present in 3.6.7. Its gem-specific indexing differs, but that difference does not affect scrolls, potions, rings, wands, or ordinary amulets. | [`3.6.7 shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-3.6.7_Released/src/shk.c?utm_source=chatgpt.com#L2189-L2234) | 3.6.7   | high       |

This comparison is scoped to the sale-price formula for the requested classes; it is not a claim that no other part of `shk.c` changed between 3.6, 3.7, and 5.0.

### 3. Base-price groups and quote tables

The following tables assume a single item, a peaceful shopkeeper, and a neutral Valkyrie who is not wearing a dunce cap or a visible shirt without body armor or a cloak.

`P` is the item's base price. `Normal` is the ordinary keeper's offer. `Low keeper` is the offer for an unidentified item from a keeper satisfying `m_id % 4 == 0`.

| Base price `P` | Normal offer | Low-quote offer |
| -------------- | ------------ | --------------- |
| 20             | 10           | 8               |
| 50             | 25           | 19              |
| 60             | 30           | 23              |
| 80             | 40           | 30              |
| 100            | 50           | 38              |
| 150            | 75           | 56              |
| 175            | 88           | 66              |
| 200            | 100          | 75              |
| 250            | 125          | 94              |
| 300            | 150          | 113             |
| 500            | 250          | 188             |

These values are the integer results of 5.0 `set_cost()`; the underlying class costs are in 5.0 `objects.h`. [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998) [5.0 `include/objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L1078-L1458)

Scrolls

| Base price | Scroll types                                                                                                      |
| ---------- | ----------------------------------------------------------------------------------------------------------------- |
| 20         | Identify                                                                                                          |
| 50         | Light                                                                                                             |
| 60         | Enchant weapon                                                                                                    |
| 80         | Enchant armor; remove curse                                                                                       |
| 100        | Destroy armor; confuse monster; scare monster; teleportation; gold detection; food detection; magic mapping; fire |
| 200        | Create monster; taming; amnesia; earth                                                                            |
| 300        | Genocide; punishment; charging; stinking cloud                                                                    |

Source: 5.0 `include/objects.h`, scroll definitions. [Scroll prices](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L1138-L1200)

Potions

| Base price | Potion types                                                              |
| ---------- | ------------------------------------------------------------------------- |
| 20         | Healing                                                                   |
| 50         | See invisible; booze; sickness; fruit juice                               |
| 100        | Restore ability; confusion; hallucination; extra healing; sleeping        |
| 150        | Blindness; invisibility; monster detection; object detection; gain energy |
| 200        | Speed; levitation; enlightenment; full healing; polymorph                 |
| 250        | Acid; oil                                                                 |
| 300        | Gain ability; paralysis; gain level                                       |

Source: 5.0 `include/objects.h`, potion definitions. [Potion prices](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L1078-L1137)

Rings

| Base price | Ring types                                                                                                                                                                 |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 100        | Adornment; protection; stealth; sustain ability; hunger; warning; protection from shape changers                                                                           |
| 150        | Gain strength; gain constitution; increase accuracy; increase damage; aggravate monster; poison resistance; cold resistance; shock resistance; invisibility; see invisible |
| 200        | Regeneration; searching; levitation; fire resistance; free action; slow digestion; teleportation                                                                           |
| 300        | Conflict; teleport control; polymorph; polymorph control                                                                                                                   |

Source: 5.0 `include/objects.h`, ring definitions. [Ring prices](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L701-L794)

Wands

| Base price | Wand types                                                                                                                                                             |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 100        | Light; nothing                                                                                                                                                         |
| 150        | Secret door detection; enlightenment; stasis; striking; make invisible; slow monster; speed monster; undead turning; opening; locking; probing; digging; magic missile |
| 175        | Fire; cold; sleep; lightning                                                                                                                                           |
| 200        | Create monster; polymorph; cancellation; teleportation                                                                                                                 |
| 500        | Wishing; death                                                                                                                                                         |

The shuffled wand appearances are also defined with their corresponding base costs in the same section. Source: 5.0 `include/objects.h`, wand definitions. [Wand prices](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L1398-L1459)

Amulets

| Type                                            | Base price | Result                                                               |
| ----------------------------------------------- | ---------- | -------------------------------------------------------------------- |
| Every ordinary amulet type                      | 150        | Same quote bucket; cannot distinguish ordinary amulet types by price |
| Cheap plastic imitation of the Amulet of Yendor | 0          | No ordinary positive-price quote                                     |
| Amulet of Yendor                                | 30,000     | Special object; not a normal unidentified-amulet test                |

Source: 5.0 `include/objects.h`, amulet definitions. [Amulet prices](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L795-L840)

Important `getprice()` exceptions

The base table is not always the effective price:

- An uncursed, unblessed potion of water has effective price zero. Cursed or blessed water retains the listed base cost.
- A wand with `spe == -1` has effective price zero. An ordinary wand with zero charges is not the same as a cancelled wand.
- Stack quantity multiplies the price. For price identification, test exactly one item at a time.

Source: 5.0 `shk.c::getprice()` and `get_pricing_units()`. [5.0 `shk.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2671-L2684) [5.0 `shk.c::getprice()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L4053-L4090)

### 4. Which shops accept which objects?

This is the 5.0 sale-acceptance list, not a prediction of what stock happens to be on the floor. `saleable()` checks the shop's accepted classes and exact object types. The general store accepts any class; specialist shops can accept a complete class or particular named objects. [5.0 `shknam.c::shtypes[]`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L194-L331) [5.0 `shknam.c::saleable()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L3441-L3478)

| Shop type                                   | Accepted objects relevant to price identification                                                                              |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| General store                               | Any object class                                                                                                               |
| Used armor dealership                       | Armor; weapons                                                                                                                 |
| Second-hand bookstore                       | Scrolls; spellbooks                                                                                                            |
| Liquor emporium / potion shop               | Potions                                                                                                                        |
| Antique weapons outlet                      | Weapons; armor                                                                                                                 |
| Delicatessen / food shop                    | Food; fruit juice; booze; water; ice box                                                                                       |
| Jewelers                                    | Rings; gems; amulets                                                                                                           |
| Quality apparel and accessories / wand shop | Wands; leather gloves; elven cloak                                                                                             |
| Hardware store / tool shop                  | Tools                                                                                                                          |
| Rare books / bookstore                      | Scrolls; spellbooks                                                                                                            |
| Health food store                           | Vegetarian food; fruit juice; healing potion; full-healing potion; food-detection scroll; lump of royal jelly                  |
| Lighting store                              | Tallow candle; wax candle; brass lantern; oil lamp; magic lamp; oil potion; wand of light; scroll of light; spellbook of light |

For the user’s requested classes:

- Scrolls: general store; second-hand bookstore; rare books. Also the health-food shop accepts the specific food-detection scroll, and the lighting shop accepts the specific light scroll.
- Potions: general store and liquor emporium. The food shop and health-food shop accept only particular potion types; the lighting shop accepts oil.
- Rings: general store and jewelers.
- Wands: general store and quality apparel/accessories (the wand shop); the lighting shop accepts the wand of light.
- Amulets: general store and jewelers.

### 5. Minetown shops in the seven 5.0 variants

The probabilities below are probabilities for generating the corresponding shop room in that variant, not probabilities that an already-existing shop buys an item. The `monkfoodshop()` helper creates a health-food shop for a Monk, but a regular Valkyrie gets a food shop. [5.0 `dat/nhlib.lua::monkfoodshop()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/nhlib.lua?utm_source=chatgpt.com#L39-L48)

| Variant           | Shops generated by the map script                                                                                                                  | Price-ID value for a Valkyrie                                                                       | Source                                                                                                                                                                                                                                                                            |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — Orcish Town   | Overrun/destroyed town; shopkeeper corpses are placed, not functioning shops.                                                                      | No usable merchant for this method.                                                                 | [5.0 `dat/minetn-1.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-1.lua?utm_source=chatgpt.com#L5-L9)                                                                                                                                            |
| 2 — Town Square   | General store 90%; tool shop 90%; food shop 90%; candle shop guaranteed.                                                                           | General store is the broad test option; no scroll/potion/ring specialist is guaranteed.             | [5.0 `dat/minetn-2.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-2.lua?utm_source=chatgpt.com#L84-L105)                                                                                                                                         |
| 3 — Alley Town    | General store guaranteed; tool-shop attempts 30% and 40%; food shop 90%; wand shop 30%; candle shop guaranteed.                                    | General store accepts scrolls, potions, rings, wands, and amulets. Wand shop accepts wands.         | [5.0 `dat/minetn-3.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-3.lua?utm_source=chatgpt.com#L18-L22) [additional placements](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-3.lua?utm_source=chatgpt.com#L50-L105) |
| 4 — College Town  | Book shop guaranteed; candle shop guaranteed; tool shop 90%; food shop 90%; general store 90%.                                                     | Best Minetown variant for scroll price-ID: the guaranteed book shop accepts scrolls and spellbooks. | [5.0 `dat/minetn-4.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-4.lua?utm_source=chatgpt.com#L13-L17) [additional placements](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-4.lua?utm_source=chatgpt.com#L37-L83)  |
| 5 — Grotto Town   | Candle shop, general store, tool shop, and food shop guaranteed.                                                                                   | Guaranteed general store; no guaranteed scroll/potion/ring specialist.                              | [5.0 `dat/minetn-5.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-5.lua?utm_source=chatgpt.com#L90-L98)                                                                                                                                          |
| 6 — Bustling Town | Candle shop, tool shop, general store, and food shop guaranteed.                                                                                   | Guaranteed general store.                                                                           | [5.0 `dat/minetn-6.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-6.lua?utm_source=chatgpt.com#L44-L48)                                                                                                                                          |
| 7 — Bazaar Town   | Food shop 50%; tool shop 50%; candle shop guaranteed; general store 60%; an additional food-shop attempt 50%; an additional tool-shop attempt 30%. | General store is the only broad price-ID option, and it is not guaranteed.                          | [5.0 `dat/minetn-7.lua`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/minetn-7.lua?utm_source=chatgpt.com#L66-L127)                                                                                                                                         |

The food shop created by the helper is a delicatessen for a Valkyrie, not a health-food store. [5.0 `dat/nhlib.lua::monkfoodshop()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/dat/nhlib.lua?utm_source=chatgpt.com#L43-L48)

## Bot rules

### Rule 1 — Select an eligible test shop

- Trigger = The bot is standing on a known shop interior tile; an appropriate shopkeeper is present; the shop type is known from the map/room identification or has previously accepted an item of the relevant class.
- Action = Prefer a general store for any of the requested classes. For scrolls, a second-hand bookstore or rare-books shop is also suitable. For potions, use a potion shop; for rings and ordinary amulets, use a jeweler; for wands, use a wand shop. Do not infer eligibility from the shop's floor stock alone.
- Done when = The bot has selected a shop whose acceptance rules include the target class or exact object type.
- If it fails = If the keeper says `seems uninterested`, classify the test as not accepted here, not as a price of zero. Retrieve the item and try a different eligible shop.
- Evidence = `saleable()` and `shtypes[]`, 5.0. [Source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L194-L331)

### Rule 2 — Verify conditions before testing

- Trigger = The target item is in inventory and is eligible to be sold to the selected shop.
- Action = Check the equipment listing:
  1. Do not wear a dunce cap.
  2. Do not wear a shirt unless body armor or a cloak covers it.
  3. Ensure the item is not marked unpaid and is not shop property.
  4. Use only one item from a stack.
  5. Do not conduct the test if the keeper is angry or the shop is already hostile.
- Done when = The outfit and item satisfy the ordinary price-test assumptions.
- If it fails = Defer the test. A quote under the sucker formula or an angry keeper's no-payment behavior is not a valid normal price sample.
- Evidence = The outfit divisor and unidentified-item modifier are in `set_cost()`; the angry-shopkeeper branch bypasses payment in `sellobj()`, 5.0. [Pricing source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998) [Angry-shopkeeper source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3721-L3729)

### Rule 3 — Offer exactly one item and decline the offer

- Trigger = The bot is on a costly shop tile, inside a suitable shop, with a peaceful keeper and a valid one-item test candidate.
- Action =
  1. Press `d`.
  2. At the drop selection, enter the target's current inventory letter. For a stack, enter quantity `1` before the letter (for example, `d1a` as the standard command sequence).
  3. Read the entire next message.
  4. If the keeper offers gold, press `n`.
  5. If the keeper offers credit, press `n`.
  6. Never press `y`, `a`, or `q`.
- Done when = The offer amount and dialogue variant have been recorded, and the prompt has been declined.
- If it fails = If no prompt appears, do not assume a price. Check for an accidental drop, a non-costly shop tile, a non-buying shop, or an ineligible item. If `offers only` appears, mark the result as cash-capped. If `seems uninterested` appears, mark the test ineligible.
- Evidence = `do.c::dodrop()` invokes deliberate sale handling; `shk.c::sellobj_state()` distinguishes deliberate from accidental drops; `sellobj()` constructs the prompt and processes `n`, 5.0. [Drop command](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do.c?utm_source=chatgpt.com#L23-L39) [Sale state](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3670-L3682) [Offer processing](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3880-L3935)

### Rule 4 — Recover the item after declining

- Trigger = The bot has pressed `n` and the offer has ended.
- Action =
  1. Press `,` to invoke pickup.
  2. Select the declined item if a pickup list appears.
  3. Verify that it is back in inventory.
- Done when = The item appears in the inventory again and has not been sold.
- If it fails = Recheck the floor at the bot's current position and the adjacent shop tiles; do not leave the shop until the item is located. If a pet is present, account for it having moved the item.
- Evidence = On declining a normal offer, `sellobj()` marks the object no-charge rather than selling it; the item therefore remains player-owned, 5.0. [Source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3901-L3912)

### Rule 5 — Convert the quote into candidate base prices

- Trigger = The bot has a cash offer that does not include `only`, and has verified that the keeper was peaceful and the item was sold as a single unit.
- Action =
  1. Let `Q` be the quoted number of gold pieces.
  2. Generate candidates from the normal table (`Q = round_half_up(P/2)`) and low-quote table (`Q = round_half_up(3P/8)`).
  3. Intersect the candidates with the relevant class's `oc_cost` list.
  4. Retain every candidate still consistent with the quote; do not force a single type if more than one remains.
- Done when = The bot has either one possible base-price bucket, multiple unresolved price buckets, or no valid price interpretation.
- If it fails = If the quote matches neither table, classify the test as contaminated (sucker outfit, stack, cash cap, special effective price, wrong store, or other unexpected state) and discard it.
- Evidence = `set_cost()` applies the price calculation and `get_pricing_units()` accounts for object quantity, 5.0. [Pricing formula](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2998) [Quantity function](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2671-L2684)

### Rule 6 — Handle the no-cash credit prompt

- Trigger = Message contains `cannot pay you at present.` and the prompt asks whether to accept credit.
- Action = Press `n`. Store the credit amount only as a separate, lower-quality observation; do not treat it as the normal cash offer. If modelling it, invert the credit rule: for offers greater than one, `credit = floor(0.9 × cash_offer)`.
- Done when = The prompt closes and the item remains yours.
- If it fails = If the screen changes to another sale prompt, continue to answer `n`. Never press `a`, which enables automatic credit acceptance.
- Evidence = `sellobj()` computes `tmpcr = ((offer * 9) / 10) + (offer <= 1)`, asks about credit, and processes the response, 5.0. [Source](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3793-L3830)

## Risks and exceptions

1. A low quote does not identify the shopkeeper's profile by itself. The low-price condition is based on the keeper's internal monster ID, not a visible label. The normal and low quote tables overlap. Examples:
   - Scroll quote `30` could mean base price `60` from a normal keeper or `80` from a low-quote keeper.
   - Potion quote `75` could mean base price `150` from a normal keeper or `200` from a low-quote keeper.
   - Ring or wand quote `75` has the same ambiguity for their applicable price groups.
   The terminal does not ordinarily expose `m_id`; direct profile identification from ordinary NLE observations is UNVERIFIED. Use a set of candidate prices rather than a forced keeper classification. [5.0 `shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2968-L2980)
2. A quote identifies a price bucket, not always an object type. The scroll and potion lists contain repeated base prices; rings and wands also have multiple types sharing costs. All ordinary amulets cost 150. This method cannot distinguish types that have the same `oc_cost`. [5.0 `include/objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L701-L1459)
3. Do not interpret an “only” offer as a price. A keeper with insufficient money caps the offer to the money available. A zero-money keeper substitutes a credit offer. Both are unsuitable as a normal cash-price sample. [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3793-L3835)
4. Angry keepers confiscate instead of paying. The source explicitly labels the angry branch as turning the dropped object into shop property without payment. A test with an angry keeper can lose the item. [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3721-L3729)
5. The drop must be deliberate. The source comment says accidental drops are automatically bought without asking. This includes the pre-query risk from slippery fingers. Use the intentional `d` command path, and avoid testing while exposed to effects that can make the hero drop inventory. [5.0 `shk.c::sellobj_state()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3670-L3682)
6. The item is left on the floor after `n`. Do not walk away and forget it. A pet may move an item before the bot retrieves it; the game has explicit shop bookkeeping for no-charge objects in pets' inventories. Pet-stealing behavior is also described on [NetHackWiki's Shop page](https://nethackwiki.com/wiki/Shop?utm_source=chatgpt.com); its precise behavior under the specific 5.0 NLE build is UNVERIFIED. [5.0 `shk.c::clear_no_charge_pets()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L361-L369)
7. Use a costly shop tile, not the threshold. `sellobj()` checks `costly_spot(x, y)` before processing a sale. A drop on a non-costly entrance square may not invoke the price process. [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3694-L3716)
8. Avoid special zero-price cases. Uncursed, unblessed water; cancelled wands; and the fake Amulet of Yendor have effective price zero. No positive-price identification should be inferred from an uninterested response to one of these objects. [5.0 `shk.c::getprice()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L4053-L4090) [5.0 `objects.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/objects.h?utm_source=chatgpt.com#L830-L840)
9. A shop accepting a class does not mean every item in it gets an offer. The sale code rejects some objects regardless of the shop's accepted class, including zero-price items, certain partially eaten foods, and candles below the required remaining age. [5.0 `shk.c::sellobj()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L3781-L3791)

## Open questions

- NLE exact prompt rendering: The game code passes the sale string to `nyaq()` with `y/n/a/q` responses. Whether the specific NLE 5.0 terminal build prints the choices in exactly the form `[ynaq]` is UNVERIFIED. The bot should parse the preceding message and respond to the active prompt rather than depend on the exact bracket formatting.
- NLE shopkeeper disposition visibility: The source uses the keeper's `mpeaceful` state. Whether the bot's configured terminal observation exposes that state directly (rather than only hostility messages or colors) is UNVERIFIED. Do not test with a keeper that the bot has previously angered.
- NLE pickup interaction: The standard pickup command is `,`, but the exact item-selection display and prompt sequence in the bot's configured NLE wrapper should be validated. The sale logic confirms that `n` does not transfer ownership; it does not guarantee a particular wrapper rendering of the floor item.
