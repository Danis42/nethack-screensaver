# Why the bot's AC stops at -3 (2026-11-02)

Data: snapshots (nethack_screensaver/snapshots.py) at first arrival per depth. First pass: 44 seeds of 56a6fab
(scratchpad ac.py); full pass on job 72 (87e0af5, 2304 games) to follow.

44-game pass:
- Enchantment never grows: summed visible enchantment of worn armour is +3 at every depth (the starting small shield).
  The bot has no code path that reads scrolls (grep: no READ command use in autoascend), so enchant armour is never used.
- Gloves almost never worn (0% to Dlvl 10, 8-40% deeper). Body armour 65-75% from Dlvl 7. Worn slots plateau at 5 from Dlvl 7,
  which is where AC plateaus at -3.
- No priest donation code: protection is never bought.

NetHack 5.0 protection (src/priest.c:637): suggested = peak XL x rn1(101,150) (150-250 per XL);
quan = gold carried / (3 x suggested), min 1. Offer in [2 x s x quan, 3 x s x quan) gives Protection:
first time u.ublessed = 2-4 AC, then +1 per further 2 x suggested (cheaper below 9). Refusing raises later prices
(cheapskate +40 per XL). 3.6 was 400 x XL (600 x XL at higher levels) for 1 point. Any peaceful aligned priest in a temple
works (wiki Protection); Minetown's temple is on the route. Price grows with peak XL, so early is cheaper.

Open: gold carried at Minetown arrival (job 72 snapshots); how often Minetown has a priest in 5.0; human
ascenders' protection purchases (dumplogs: "You feel a feeling of ..." / attributes).

Full pass, job 72 (87e0af5, 2304 games), first arrival per Dlvl (Dlvl 1 snapshot is before the start kit shows):
| Dlvl | n | AC | slots | cloak | helm | gloves | boots | shield | body | ench sum |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 1918 | 1 | 3 | 45% | 83% | 3% | 35% | 99% | 51% | +3 |
| 7 | 1566 | -1 | 5 | 75% | 92% | 6% | 68% | 95% | 64% | +3 |
| 10 | 807 | -3 | 5 | 76% | 97% | 13% | 89% | 96% | 68% | +3 |
| 15 | 183 | -4 | 5 | 64% | 99% | 30% | 94% | 97% | 66% | +3 |
| 20 | 70 | -4 | 5 | 53% | 96% | 41% | 93% | 99% | 79% | +3 |
Confirmed: enchantment never grows (no scroll reading), gloves rare, cloak share falls below Dlvl 10 (lost, not replaced: unchecked),
a third of arrivals have no body armour.
Gold (rung snapshots): Mines median 41 (XL 4), Oracle 92 (XL 6), Sokoban 183 (XL 7), Minetown 121 (XL 8), p90 483.
Protection at XL 8 needs about 2400-4000: about 1% of Minetown arrivals could pay. Protection is not cheap for this bot;
gold supply is the blocker. Bot picks gold up (item priority), drops it only for vault guards (71 of 2304 games).
Levers left: enchant armour (read scrolls: price-id or read-test), body armour and gloves, cloak replacement.
