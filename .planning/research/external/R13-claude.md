# R13 Elemental Planes and Astral (Claude: checks of ChatGPT R13 against local 5.0.0 source)

## Verified in source
| claim | source |
|---|---|
| Plane of Water: moving inside a bubble turns the bubble your way half the time (!rn2(2)) | mkmaze.c:1927-1938 |
| Water-plane water stops thrown or kicked items | fixes5-0-0.txt:793 |
| Death's touch: 3 in 20 = touch of death unless magic resistance: 50 + 8d6 damage and max-HP loss (no longer plain instadeath); otherwise permanent max-HP drain | uhitm.c:3850-3870, mcastu.c:326-350 |
| Astral priests: with no gold, a cross-aligned priest "is not interested"; a co-aligned one gives "two bits for an ale" or "preaches the virtues of poverty" -> safe way to find the neutral altar | priest.c:610-624 (see R06) |

## Correction / note
- ChatGPT is right that the chat test needs zero gold in open inventory: drop or bag the gold first.

## Not checked (wiki-based, fine for planning)
- Plane layouts, portal positions, lightning on Air, Fire poison clouds, Rider stats.
