# R16 Valkyrie intrinsics and key-item timeline (Claude: checks of ChatGPT R16 against local 5.0.0 source)

## Verified in source
| claim | source |
|---|---|
| Valkyrie intrinsics: cold resistance XL 1, stealth XL 3 (3.6: XL 1), Fast XL 7 | attrib.c:81-84 |
| start kit: +1 spear (3.6: long sword), +0 dagger, +3 small shield, food ration | u_init.c:160-166 |
| quest needs fire immunity per the Norn's text | quest.lua:2706 |
| 5.0 dragon armour extras (on top of the colour's resistance): black drain res, blue Fast, green sickness res, red infravision, orange free action, yellow stoning res, white slow digestion; gray = magic res, silver = reflection | do_wear.c:809-878 |
| Orb of Fate: no magic resistance (warning, half damage both kinds, luck) | artilist.h:297 |

## Must-haves (from R09-R11 checks)
- Quest: XL 14, alignment 20, fire resistance.
- Medusa: reflection or blindfold, plus levitation or a pick-axe (dig down); amphibious or a greased/oilskin item
  near eels.
- Castle: levitation (moat, east door, trap doors), reflection (soldiers' wands), a spare blade or unlocking tool
  for the wand chest.

## Not checked
- ChatGPT's "typical timeline by dungeon level" is planning advice, not data; the bot's own bench logs are the
  better source (when does it get each property?).

## Compared with ChatGPT R16 (2026-11-08)
- Agrees on everything checked, including the XL 3 stealth change and the dragon armour extras.
