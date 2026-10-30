# Reaching the Quest on NetHack 5: the XL 14 problem (research, 2026-10-30)

Sources: reference/nethack-5.0.0 (quest.c, quest.h, exper.c, mon.c, timeout.c, objnam.c, mkobj.c, mkroom.c, dat/castle.lua,
dat/medusa-*.lua), local wiki (Experience level), bench `6c7bfef` (2304 games). Nothing here has been tried in a game.

## The requirement

- Quest leader's permission: XL >= 14 and alignment record >= 20, original alignment (quest.h, quest.c).
- Without permission the descent from the home level is blocked for stairs, holes and digging (do.c, dokick.c, zap.c).
- XP thresholds: XL 10 5120, XL 11 10,000, XL 12 20,000, XL 13 40,000, XL 14 80,000 (exper.c newuexp).
- Bot today: median XL 7; XL 11+ in 51 of 2304; XL 14+ in 1 (T39165); games at Dlvl 15+ median XL 10.

## Why kills alone are unrealistic

Kill XP is about level^2 + 50 + bonuses: about 225 for a level 12 monster, so XL 11 to 14 by kills is about 300 such kills.
The wiki agrees: most characters reach XL 10-11 by killing, then need other sources.

## Level jumps: the key rule

`pluslvl(FALSE)` (gain level, wraith) sets XP to the new level's threshold. So a jump is worth the whole gap: at XL 13 it
is worth 40,000 XP, at XL 11 10,000. Drink late; do not spend potions below XL 11. Blessed potions give the same one level.

## Sources, cheapest first

| Source | Yield | Notes | Bot today |
|---|---|---|---|
| Castle wishing chest | 1 gain level, guaranteed | same chest as the wand; locked (needs prying) | can't reach |
| Wraith corpse | 1 level | morgues: 20% of inhabitants; graveyard undead leave a corpse only 1/3 of the time | no rule |
| Eel kills | +1000 XP each (giant eel, electric eel, kraken) | exper.c, hero not amphibious. Castle 4 giant eels, Medusa 0-3; drowning risk; needs eels adjacent to shore | no rule |
| Castle garrison | a few thousand XP | soldiers about 45 each, lieutenants about 170 | can't reach |
| Random potion of gain level | 2% of potions | appearance shuffled each game; 300 zm base price | never recognised |
| Wish | 3 blessed potions: 50% get 3, else 1. 2 potions: 67% get 2, else 1 | objnam.c `cnt < rnd(6)` | can't wish |
| Foocubus | small chance of a level per encounter | not a plan | - |

## Wishes

See WISHES-NH5.md: 2 reliable at the Castle, 4-5 in the whole game.

## Bypass: kill the Quest leader (last resort)

`ok_to_quest` is also true with `killed_leader`, new in NetHack 5. Price (mon.c): alignment set to minus half the alignment limit (10 + turns/200, so about -105 at T40000), god anger +7,
Luck -20, guardians hostile, base Luck -4 for the rest of the game (timeout.c). So no prayer ever again and wishes come out
cursed while Luck < 0: do all wishing first. Norn is level 20, speed 15, two 4d10 weapon attacks. Whether the Bell stays reachable in practice is unverified (guardians hostile, no prayer).
Only for a run that is otherwise stuck.

## Proposed route (Castle before Quest)

1. Natural play to XL 10-11 at Dlvl 20+ (Track A: survive, eat wraiths, stop dying to peacefuls).
2. Past Medusa by digging, Castle: eels and garrison toward XL 11-12, chest: wand + gain level.
3. Wish(es): one for levels if still below XL 13 after the potion, rest for the kit.
4. Back past Medusa: see MEDUSA-RETURN-NH5.md (cursed potion of gain level, or level teleport).
5. Quest at XL 14 with alignment 20.

Example budget: XL 10 on arrival + 4 eels + garrison = about 10,000 XP (XL 11); chest potion XL 12; wish for potions: two more
reach XL 14 (needs both). The plan has no margin: one more natural level or one wraith makes it much safer.

## Open questions

- Alignment record: never measured on the bot; killing peacefuls costs -5 each. Log it.
- Whether humans reach XL 14 before the Castle: the NLD game table has no XL field; needs ttyrecs.

## Near-term experiments

1. Eat wraith corpses at once, even when not hungry (natural bench; rare, so measure by XL 11+ rate).
2. Quaff known gain level at XL >= 11 only; hold otherwise.
3. Track B: staged Castle: kill eels from the shore without drowning.
