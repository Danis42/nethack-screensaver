# R05 Enchant armour and early armour sources (Claude, local 5.0.0 source + bench and NLD data)

## Summary
- The AC gap is about 3 points at Dlvl 10 (humans -6, bot -3) and 9-10 points at Dlvl 15-20 (humans -10/-13,
  bot -4). The bot wears 5 slots from Dlvl 7 on; its summed enchantment never grows (+3, the starting shield).
- 5.0 enchant armour adds more than 3.6: on +0 plain armour an uncursed scroll adds rnd(3) (avg +2), blessed
  rnd(4); evaporation risk only once a piece is above +3 (elven +5) (read.c:1178-1220).
- The scroll picks the piece itself (cloak first). Spreading reads over pieces is automatic; taking pieces off
  first is only needed to protect a piece already at +3 or more.
- Missing slots are the second lever: gloves worn 3-13% of games to Dlvl 10; body armour missing in 1/3; the cloak
  is lost below Dlvl 10 (worn 76% -> 53%).
- Mines dwarves: iron shoes and dwarvish cloak 6/7 each, iron helm 1/4, mithril coat 1/12 per dwarf
  (makemon.c:380-400). They cover boots/helm/cloak, not gloves or (mostly) body armour.

## Facts
| claim | source | confidence |
|---|---|---|
| Enchant amount s=(4-spe)/2 +1 elven/cornuthaum +1 non-magical +1 blessed; s<=0 -> 0 (1 if !rn2(spe)); else rnd(s) | read.c:1201-1218 | high |
| Evaporates when spe > 3 (> 5 special) and rn2(spe); vibration warning "vibrates warningly" for elven past limit | read.c:1164-1190 | high |
| Target = some_armor(): cloak, else body armour, else shirt; then helm, gloves, boots, shield each replace it with 1/4 | do_wear.c:2630-2653 | high |
| Dwarf gear: cloak 6/7, iron shoes 6/7; 1/4 armed: short sword, mattock 1/2 or axe/spear + roundshield, iron helm, mithril 1/3 (1/12 overall); else pick-axe 1/3 or dagger | makemon.c:384-402 | high |
| Hobbit: elven mithril coat 1/10 | makemon.c:375-378 | high |
| Humans (72 NLD 3.6 ascensions) AC at first arrival: Dlvl 5: 2, 10: -6, 15: -10, 20: -13; enchant armour read in 79% of games before Medusa, median 3 | NLD scan (ac_sources.py) | medium (3.6 games) |
| Bot (job 72, 2304 games) AC: Dlvl 5: 1, 10: -3, 15: -4, 20: -4; worn: gloves 3/13/30/41%, body 51/68/66/79%, cloak 45/76/64/53% at Dlvl 5/10/15/20 | AC-GAP-NH5.md | high |
| Bot carries 4.4 / 8.5 / 10.5 unknown scrolls at Dlvl 5/10/15 and knows enchant armour in 1 game of 417 at Dlvl 10 | bench e1d8086 snapshots | high |

## Bot rules (ranked by expected AC per effort)
1. Identify scrolls by price (price_quotes option + sell offers) and read every scroll whose candidates are all
   safe; enchant armour is in the 80 zm group with remove curse. Expected: ~0.5 enchant armour by Dlvl 10, ~0.7
   by Dlvl 15 from carried scrolls alone, avg +2 each on plain +0 armour.
2. Before reading enchant armour, take off nothing unless a worn piece is already at +3 or more (elven +5): then
   take that piece off first (the scroll may pick it and evaporate it on the next read).
3. Wear gloves when found (the bot rarely wears any): find out why first (not found, not picked up, or not worn).
4. Replace a lost cloak (find out first why the cloak share falls below Dlvl 10: destroyed, taken off, swapped).
5. Body armour: a third of games have none by Dlvl 10. Dwarves give mithril 1/12 each; check whether the bot
   strips dwarvish mithril from kills (pickup priority) before building anything.

## Risks and exceptions
- Cursed enchant armour lowers the piece by 1 and curses it; read only known non-cursed scrolls (altar or price
  plus "uncursed" in the name).
- The data on gloves and cloaks says "missing", not why; each lever needs a cause check first (no guessed fixes).

## Open questions
- Why the bot's cloak share falls from 76% to 53% after Dlvl 10.
- Why gloves stay rare: supply (few drops) or pickup/wear rules.

## Compared with ChatGPT R05 (2026-11-05)
Agreement on: some_armor order, 5.0 enchant formula (ChatGPT has it right; DeepSeek had 3.6), evaporation at
spe > 3 / > 5 elven (ChatGPT adds: 3/4 chance at +4, 5/6 at elven +6), dwarf odds.
Missed by me: elves carry an elven mithril coat with 1/4 (rn2(2) then rn2(2), makemon.c:226-229); hobbits 1/10.
Elves are frequent in bot games (Woodland/Green/Grey-elf killed 50 of 1152 heroes in job 79), so killing them
is also the most common chance at elven mithril (AC 5, safe to +5): check whether the bot picks it up and wears it.
