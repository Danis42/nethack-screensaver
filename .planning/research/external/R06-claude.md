# R06 Priest protection and gold (Claude, local 5.0.0 source)

## Summary
- 5.0 replaced the 3.6 rule (400 x XL, 600 x XL). Base S = peak XL x (150..250 + 40 x cheapskate count),
  rerolled on every chat (priest.c:637-638). The prompt shows both thresholds: "suggested: A or B".
- Answer B (the second number) and the bot gets protection. B..3A-1 = protection, A..B-1 = clairvoyance only,
  3A and over = alignment only, no protection (priest.c:660-735).
- The first purchase gives 2-4 points (AC -2 to -4) at once; then +1 per 2S up to 9; then 1/points chance, cap 20.
- The priest does not need to share the hero's alignment for protection; it must be peaceful, in its own temple,
  with an intact altar.
- At XL 8 the first purchase costs 2400-4000 gold. The bot's ~120 gold at Minetown buys nothing.
- One vault holds 4 piles of 51..(50 + 100 x depth) gold (sp_lev.c:2763): ~1200 at Dlvl 5, ~2200 at Dlvl 10.
  One or two vaults pay for the first purchase.

## Facts
| claim | source |
|---|---|
| S = peakXL x rn1(101, 150 + 40 x cheapskate); quan = max(1, gold / 3S); prompt shows S x quan and 2S x quan | priest.c:637-646 |
| offer 0: "Thou shalt regret thine action!", -1 alignment if same alignment, cheapskate +1 | priest.c:654-659 |
| offer < S x quan and gold > 2 x offer: "Cheapskate.", cheapskate +1 (raises every later price at this priest) | priest.c:660-664 |
| S x quan <= offer < 2S x quan: "Thou art indeed a pious individual." + clairvoyance | priest.c:671-680 |
| 2S x quan <= offer < 3S x quan: one point step per 2S; first step 2-4 points; "Thou hast been rewarded for thy devotion." | priest.c:681-703 |
| offer >= 3S x quan: "Thy selfless generosity is deeply appreciated.", alignment only | priest.c:704-717 |
| no gold, same alignment: priest gives 1-2 gold "for an ale" or "preaches the virtues of poverty"; otherwise "is not interested." | priest.c:610-624 |
| an offer above the hero's gold gives all of it ("You give ... all your gold") | minion.c:379-381 |
| gold in carried bags does not count (money_cnt(invent)) | priest.c:639 |
| Mines mineral gold: small buried piles, rnd(20) + difficulty x rnd(5) | mklev.c:2371-2380 |
| vault guard: "Croesus" / "Kroisos" / "Creosote" sends it away while Croesus lives (the hero keeps the gold); after Croesus dies the guard turns hostile | vault.c:513-535 |
| a lawful hero who gives a false name loses 1 alignment (the Valkyrie is neutral, so no cost) | vault.c:507-510 |
| fleeing leprechauns bury stolen gold after teleporting | doc/fixes5-0-0.txt:747 |

## Bot rules
1. Chat (#chat) with a temple priest only when gold >= 2 x peakXL x 250 (worst case, no cheapskate). Never chat
   to "check the price": a refused or small offer raises every later price at that priest.
2. Parse "suggested: A or B" and type B. If gold < B (the price came out high), type A (clairvoyance; no penalty).
   Never type 0 or less than A.
3. Gold source worth building: vaults (closed 2x2 rooms, "someone counting money" messages). Getting in needs
   digging or a vault teleporter; the guard is answered with "Croesus" while Croesus lives.
4. Leprechauns: keep gold in a bag on levels with them (the priest counts only gold in open inventory, so take it
   out before chatting).
5. Selling spare items is a small source (R04 covers selling); it will not reach 2400 gold alone.

## Is it worth it
- AC is the bot's known gap (stops at -3, see memory 'Armour is the gap'). The first purchase is AC -2 to -4 in one
  action, as big as the best single armour piece the bot gets, and permanent.
- Nothing else on the pilgrim route needs this much gold early (shop buys are rare for the bot). Gold has no
  better use until the Castle wand and later; protection comes first.
- Price grows with peak XL: buying at XL 8 costs half of buying at XL 16. Buy as early as the gold allows.

## Risks and exceptions
- Peak XL, not current XL, sets the price; level drain does not make it cheaper.
- A gremlin can steal the intrinsic; the points stay stored and come back with the next purchase (priest.c:684-691).
- Minetown temple can be cross-aligned or have no priest (Orcish Town): look for the next temple.

## Open questions
- How often the bot passes a vault and how much gold it carries at Minetown / Dlvl 10 (bench data).
- How many points human players buy: no source found; the wiki's "protection racket" is a low-XL trick.

## Compared with ChatGPT R06 (2026-11-08)
- Agrees on every formula, band and message from priest.c; its cost table by XL is correct.
- Extra in ChatGPT, verified: vault gold 50 + d(100 x depth) per pile (sp_lev.c:2763 rn1(100 x depth, 51));
  Croesus trick (vault.c:513); the guard also counts gold in bags (vault.c hidden_gold); leprechauns bury gold.
- Wrong in ChatGPT: the no-gold message "I will accept a small contribution" does not exist (the priest gives
  "two bits for an ale" or "preaches the virtues of poverty").
- About half of ChatGPT's file repeats R03 (speed, Elbereth, prayer); those parts match R03-chatgpt.md.
- Missed by both before this check: with lots of gold, quan > 1, so one offer of B buys several point steps at once.
