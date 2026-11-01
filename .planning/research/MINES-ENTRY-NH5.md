# When should a human Valkyrie enter the Mines? (research, 2026-11-01)

Question: 10% of human games die before T3000 (dwarf 4%), 20 of 57 on the first Mines level. I proposed "stay out until about XL 6" with
no evidence. This checks that assumption before any code.

## Evidence

- Real 5.0 ascensions (hardfought dumplogs, 110 non-dwarf, non-gnome with Mines dates): enter at median T1173, quartiles T665-T1773. Rank
  events put XL below 3 in 47, 3-5 in 57, 6+ in only 6. Sokoban first in only 3 of 110; human Valkyries 0 of 7. They are survivors and
  skilled, so this shows what can work, not what is safe for the bot.
- Source: dwarf level 2, d8 weapon attack, to-hit 10 + 2 + AC. AC 6 is hit about 85% of the time, AC 0 about 55%. 1/8 of dwarves carry a
  mattock (d12): up to 20 per hit, average 11. 1/4 have a heavy-weapon kit, 1/4 a pick-axe, 1/2 a dagger.
- Wiki and guides: no XL or AC threshold. Mines arrival is often "substantially harder"; humans lack infravision and 50% of filler levels
  are dark; lawful humans are often ignored by dwarves; weak heroes: fight at the upstairs, retreat, repeat (r/nethack).
- Bot, 198 traced seeds on `3d163d9`, 129 reached the Mines, median T2829, XL 3-5 mostly, max HP 40, AC 3:
  - 10 of 129 died within 800 turns of arrival, 7 of them within 92 turns.
  - By AC at arrival: AC 3 or better 2/72, AC 4+ 8/55 (Fisher p = 0.02). By XL: 6+ 0/24, 5 or less 10/105 (p = 0.21). AC is the stronger
    signal; XL and AC are confounded and the counts are small.
  - Bot's killers include zapped wands and thrown weapons, not only dwarves.
- Bot, 576 stored games of `d5f032c`: 18 of 24 Mines deaths before T3000 have milestone FIND_SOKOBAN: the plan does not want the Mines yet.
  The hero takes the wrong `>` on the branch level. Of 359 games reaching the Mines, 244 never reach Sokoban.

## Assumptions

- "Too low level is the problem, gate on XL 6": not supported. Humans enter earlier and lower; the XL signal is weak.
- "The bot chooses the Mines too early": false for most early deaths. It arrives by accident while seeking Sokoban.
- Untested: human Valkyrie on the Mines-first route. Experiment 38 tested dwarf + Sokoban only; ascenders almost all go Mines first.

## First visit, measured (161 seeds on `3d163d9`, 107 reached the Mines)

- 50 arrived while the plan was FIND_SOKOBAN: arrival T2210, XL 3, first visit median 1212 turns on Mines level 1 (quartiles 801-3938).
  Only 2 left within 30 turns; 17 of 50 died on that visit, 6 within 132 turns. Those 17 are the target.
- 51 arrived on FIND_GNOMISH_MINES (Sokoban gave up or done): T3392, XL 5, 23 died on the first visit, but over a much longer stay.

Conclusion: the evidence backs "do not stay on a Mines level the plan does not want", not an XL gate.
