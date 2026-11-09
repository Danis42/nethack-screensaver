# R12 Gehennom and the invocation (Claude: checks of ChatGPT R12 against local 5.0.0 source)

Late-game topic: I checked ChatGPT's key claims instead of writing a full answer first.

## Verified in source
| claim | source |
|---|---|
| Ritual on the vibrating square, not on stairs: carry Bell AND Candelabrum, else "A chill runs down your spine" (+ "faint chime" / "Vlad's doppelganger is amused") | spell.c:241-262 |
| Candelabrum must have 7 candles and be LIT; the Bell must have been rung LESS THAN 5 TURNS before reading the Book (svm.moves - bell age < 5) | spell.c:264-279 |
| any of the three cursed: "The invocation fails! At least one of your relics is cursed..."; cursed Book: "runes appear scrambled" | spell.c:246-250, 281-285 |
| success also counts as killing the Wizard (udemigod), so he starts harassing within 2d6 turns | spell.c:288-296 |
| Juiblex (unique engulfer) resists digging from inside | fixes5-0-0.txt:107 |
| fix for attaching candles with little fuel left (was unwinnable) | fixes5-0-0.txt:109 |
| silver-hating form may ring the Bell on the vibrating square; Book readable blind | fixes5-0-0.txt:244-251 |
| Book of the Dead weight 20 -> 50 | fixes5-0-0.txt:1326 |
| travel finds/stops at the vibrating square; "gateway to Moloch's Sanctum" annotation | fixes5-0-0.txt:1537-1539, 2626 |
| mysterious force (climbing with the Amulet in Gehennom, not in the last 3 levels): chance 1/(4 + counter), counter += rn2(levels sent down + 2), so it fades with use | do.c:1536-1563 |

## Correction to ChatGPT
- "Candelabrum and Bell may be used in either order": only if the Bell is rung within 4 turns of reading. Safe
  order for the bot: light the Candelabrum, ring the Bell, read the Book at once.

## Not checked (wiki-based in ChatGPT, fine for planning)
- Depth ranges of the Gehennom special levels, fake towers, Orcus' wand of death, Baalzebub, Asmodeus.

## Open questions
- None needed now; this is far beyond where the bot dies today.
