# Strength per depth: human ascensions vs bot (2026-11-02)

Humans: 72 NLD-NAO 3.6 ascensions, all roles (13 Valkyries), status line at first arrival on each Dlvl.
Bot: 200 games, seeds 4000-4199, main at d5f032c code, same measure. Different game versions (3.6 vs 5.0) and the humans are all
winners, so read this as a guide. Dlvl counts Mines levels too. Scripts were scratch only.

| Dlvl | Human T | Bot T | Human XL | Bot XL | Human max HP | Bot max HP | Human AC | Bot AC | Bot games |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1720 | 3480 | 4 | 5 | 33 | 47 | 3 | 2 | 164 |
| 7 | 3496 | 5054 | 6 | 6 | 50 | 59 | 0 | -2 | 136 |
| 9 | 6940 | 7876 | 8 | 8 | 66 | 74 | -5 | -3 | 84 |
| 10 | 8854 | 8466 | 8.5 | 8 | 70 | 76 | -6 | -3 | 76 |
| 12 | 13824 | 11330 | 10 | 9 | 76 | 82 | -8 | -4 | 32 |
| 14 | 16235 | 13405 | 11 | 9 | 89 | 83 | -9 | -3 | 15 |
| 16 | 17751 | 15024 | 11 | 9 | 95 | 88 | -10 | -3 | 9 |
| 18 | 19932 | 16905 | 11 | 9.5 | 97 | 89 | -12 | -3 | 6 |

Findings:
- XL and max HP match the humans to about Dlvl 10-12. "Too weak, too early" is wrong for XL and HP there.
- AC is the clear gap. Humans keep improving with depth, the bot stops at -3 or -4 from about Dlvl 7. From Dlvl 10 at most 11% of bot
  arrivals match the human median AC.
- Humans also spend longer on Dlvl 10-12 (about 5000 turns against 2900).
- Within the bot, AC at Dlvl 10 predicts little so far: reached Dlvl 15 in 9 of 43 at AC -3 or better, 4 of 33 worse. Small sample, and
  the range is narrow. Unproven until stats recording gives more games.

Open: why armour stops at -3: not found, not picked up, not worn, not enchanted, or no protection bought. Not yet known.
