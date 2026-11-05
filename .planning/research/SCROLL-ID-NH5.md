# Scroll identification for enchant armour (2026-11-05)

Why: humans read enchant armour successfully in 79% of ascensions before Medusa (median 3 times, first at Dlvl 7)
and reach AC -13 at Dlvl 20; the bot stops at -4 (SURVIVAL-NH5.md, AC-GAP-NH5.md). The bot reads enchant armour
only once it is identified, and it almost never identifies scrolls.

## The bot today (e1d8086, 1152 bench games, first arrival snapshots)
| arrival | unknown scrolls carried (mean) | games with any | enchant armour known |
|---|---|---|---|
| Dlvl 5 | 4.4 | 96% | 0 |
| Dlvl 10 | 8.5 | 88% | 1 of 417 |
| Dlvl 15 | 10.5 | 91% | 1 of 92 |
read_scroll 253, read_unknown_scroll 66 events in 1152 games.
Code: item_manager.py:109 buy-price identification (only for items FOR SALE under the hero, same glyph);
scrolls.py should_read: reads an unknown scroll only if all identities left are in SAFE_UNKNOWN. No sell-price
identification, no read-testing, no frequency identification.

## 5.0 scroll table (objects.h:1187-1265; prob per 1000 scrolls, base price)
20: identify 180 (alone). 50: light 90. 60: enchant weapon 80, blank paper 28. 80: enchant armour 63, remove
curse 65. 100: destroy armour 45, confuse monster 53, scare monster 35, teleportation 55, gold detection 33, food
detection 25, magic mapping 45, fire 30. 200: create monster 45, taming 15, amnesia 35, earth 18. 300: genocide 15,
punishment 15, charging 15, stinking cloud 15.
- 80 zm group = enchant armour or remove curse: both safe and useful to read (not confused).
- Expected per 8.5 unknown scrolls: ~0.5 enchant armour, ~1.5 identify.

## Which piece (do_wear.c:2630 some_armor)
Cloak, else body armour, else shirt; then helm, gloves, boots, shield each take over with 1/4. Enchant armour and
uncursed destroy armour both use it. 5.0: a blessed destroy armour asks which piece (read.c:1366) - a prompt to
answer. Cursed destroy armour disintegrates (or -1 and stun if the piece is cursed too).

## Methods
1. Sell-price identification (risk-free). Drop an unknown scroll in a shop that buys scrolls; the shopkeeper offers
   base/2 (base/3 for a "sucker": dunce cap, bare shirt, Tourist < XL15), and 1/4 of shopkeepers pay a further 3/4
   for unidentified items (consistent per shopkeeper). Answer n. Offers: 20->10/7, 50->25/18, 60->30/22,
   80->40/30, 100->50/37, 200->100/75, 300->150/112. 30 is 60 or 80: both safe to read. Shopkeeper without gold
   offers credit = 90%. Shops that buy scrolls: general store, second-hand bookstore, rare books.
   Minetown: general store in 6 of 7 variants (minetn-2..7; minetn-4 also a book shop); minetn-1 is Orcish Town.
2. Buy-price identification (have it): only scrolls that are for sale; random 1/3 surcharge widens ranges.
3. Frequency: identify is 18% of scrolls; the appearance with the most copies is likely identify.
4. Read-testing: per random unknown read, destroy armour 4.5% (~2 AC lost), amnesia 3.5%, punishment 1.5%
   (ball and chain: known bot crash), create monster 4.5%, fire 3%; gains enchant armour 6.3%, identify 18%,
   remove curse, enchant weapon, magic mapping, teleport. Direct AC is about even (-0.09 vs +0.06 per read); the
   value is knowing the appearance for every later copy. Cursed scrolls make it worse: read-test only uncursed
   (altar-tested) scrolls.

## Human practice (72 NLD 3.6 ascensions, reads before the Medusa kill; scratch scroll_reads.py)
Reads per game: median 29 (p25 18, p75 39); 18.5 on Dlvl <= 10. Outcomes of 2512 reads (first matching message
within 4 lines; about half unmatched): identify 16.2%, enchant weapon 12.3%, enchant armour 9.3% (56 of 72 games),
remove curse 3.7%, magic mapping 2.9%, teleport 1.3%, light 1.1%, genocide 1.0%, amnesia 0.2%, destroy armour 0.1%
(3 reads), punishment 1 read. Blind reading would give destroy armour ~4.5%, amnesia ~3.5%, punishment ~1.5%.
Conclusion: humans identify first (price, then identify scrolls) and then read a lot; they do not read blind.
Bot plan: A (sell-price ID) first; no blind read-testing.

## Proposed order
A. Sell-price identification in shops that buy scrolls (risk-free, Minetown general store on the route).
B. Read any scroll whose candidates are all safe (have it) + make sure enchant armour candidates count as wanted.
C. Then consider read-testing uncursed scrolls of appearances with 2+ copies, if A+B leave most unknown.

## External answers checked against 5.0 source (2026-11-05)
R04/R05/R07 DeepSeek: mostly correct for 3.6/3.7; two 5.0 differences found below. R01 ChatGPT: cites the 5.0
release source directly; every checked number matches (7d4 passive, 2/3 chance, fire vortex speed 22).

Sell price (shk.c:3150-3180, 5.0): offer = base/2 (base/3 with dunce cap, Tourist below XL 15, or a shirt with no
body armour/cloak); unidentified non-gem items: x3/4 when shopkeeper m_id % 4 == 0 (per shopkeeper, as DeepSeek
said). Prompt (shk.c:4137): "<Shk> offers[ only] N gold piece(s) for your <item>.  Sell it?" answered with
nyaq; 'n' keeps the item (marked no_charge). "only" = short funds: do not use that number.

NEW 5.0 OPTION price_quotes (include/optlist.h:598, default Off, settable): the game records every buy and sell
quote per object type (shk.c:439 record_price_quote) and appends it to unidentified item names:
"<name> {buy 106 sell 40}" or ranges "{buy 80-106}" (shk.c:454 append_price_quote, objnam.c:1676). With it on,
the bot reads prices straight from inventory text; every shop visit (buy prices of items on the floor, sell
offers) feeds it. Needs: option in the NLE options string + item parser support for the {...} suffix.

Enchant armour amount (read.c:1178-1220, 5.0 - differs from 3.6 and from R05):
s = (4 - spe) / 2, +1 if elven (or Wizard cornuthaum), +1 if the armour is non-magical, +1 if blessed;
s <= 0 -> 0 (or 1 with chance 1/spe); else rnd(s). So an UNCURSED scroll on +0 plain armour adds 1-3.
Evaporation: spe > 3 (> 5 elven) and rn2(spe) before the read. Every +1 is +1 AC on any piece, so R05's "enchant
the highest base-AC piece first" is wrong; the limit is per piece (+3), which is why spreading over pieces is good.
R04 ChatGPT (external/R04-chatgpt.md): best R04 answer, 5.0 source cited; spot-checked: "seems uninterested"
(shk.c:3995), no-gold credit = offer*9/10 with "cannot pay you at present. Will you accept N in credit for ..."
(shk.c:4049-4055), Bazaar Town general store chance=60 (minetn-7.lua:111) - all correct. Adds: drop on a costly
square (not the door); a deliberate 'd' asks, accidental drops sell without asking; angry keepers take the item;
answer n (q would set later sale prompts to n). Minetown general store: guaranteed in Alley/Grotto/Bustling
(minetn-3/5/6), 90% in Town Square/College (2/4), 60% in Bazaar (7); College Town (4) has a guaranteed bookstore;
Orcish Town (1) none. Scroll quote 30 = base 60 (normal keeper) or 80 (low keeper): both safe to read.
