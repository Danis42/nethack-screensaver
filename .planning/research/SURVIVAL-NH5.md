# Survival deep and mid-game: humans vs bot (2026-11-05)

Sources: 72 NLD-NAO NetHack 3.6 ascensions with ttyrecs (scratch scripts medusa_humans.py, ac_sources.py,
crisis_humans.py; aggregates only), 199 hardfought 5.0 ascension dumplogs (bench reference_games, end state only),
1152 bench games of e1d8086 (job 79), NetHack 5.0.0 source, local wiki. Human games are 3.6 and winners: a guide.

## 1. Strength at Medusa (humans, first arrival on her level; 59 games with a Medusa kill)
AC median -14 (p75 -11, p90 -9), XL 13, max HP 110; Castle arrival AC -17, XL 14, HP 119. Medusa depth median 24
(21-29). 752 turns from arrival to her death (median). Staged medusa kit now matches (cloak of protection + gloves).

## 2. Where human AC comes from (before the Medusa kill)
| AC at first arrival | Dlvl 5 | Dlvl 10 | Dlvl 15 | Dlvl 20 |
|---|---|---|---|---|
| humans | 2 | -6 | -10 | -13 |
| bot (job 72, AC-GAP-NH5.md) | 1 | -3 | -4 | -4 |
- Enchant armour read successfully ("glows silver") in 79% of games, median 3 times, first at Dlvl 7 (median).
- A priest donation in 31% of games, first at Dlvl 13.5 (protection message itself is too long for row 0: not
  counted). 5.0 end state: 49% "You were protected", worn-armour enchantment sum +25, 97% dragon scale mail.
- Bot: reads enchant armour only when identified (Part 1a); scrolls are rarely identified. Lever: scroll
  identification (price groups in shops, read-test unknown scrolls when safe) so enchant armour gets read.

## 3. What humans do in a crisis on Dlvl 20+ (HP below 1/3 after being above 2/3)
69 crises in 72 games (median 1 per game): first recognised action
apply 51% | nothing seen 16% | zap 9% | read 6% | quaff 6% | pray 4% | cast 4% | up stairs 3% | Elbereth 1%.
### 3a. What is applied (35 crises, next three message lines)
stethoscope ~14 ("Status of <monster>: Level L HP h(H) AC a": a free action to see whether the monster is nearly
dead; most then keep fighting), bag of holding ~8 (take out healing potions / scrolls), magic whistle 4 (pets),
expensive camera 1, unlock/lock a door 2, blindfold 1, unicorn horn 1, pick-axe 1.
Conclusion: deep down humans rarely escape. Crises are rare (1 per game) and are met by informed fighting plus
healing; survival comes from strength (AC, HP), not escape tricks. For the bot: close the AC gap first
(enchant armour via scroll identification), then healing access; escape rules matter less than expected.

## 4. The bot's low-HP behaviour (autoascend/agent.py emergency_strategy, combat/fight_heur.py)
- quaff a known healing potion below 1/3 HP; pray below about 1/6-1/7 HP if 500+ turns since the last prayer.
- Elbereth in fights: written 3019 times in 1152 games, then ~25,000 turns of waiting on it; never attacks from it
  (0 "hypocrite" messages, mon.c:4267 would erase it). The emergency-path Elbereth is commented out.
- No retreat by stairs, no escape item use, melee-avoid list only floating eye, blue jelly, brown mold, gas spore,
  acid blob (not the energy vortex: passive shock killed staged medusa seed 6).

## 5. Elbereth facts (5.0 source)
- Ignored by: @ humans and elves, minotaurs, shopkeepers, vault guards, blind or peaceful monsters, uniques, lawful
  minions, Angels, Riders, the Wizard; does not work in Gehennom or on the Planes (monmove.c:241-300).
- A scared monster that cannot move away attacks anyway (panicattk, monmove.c:918-968). 33 of 155 bench deaths to
  the six killers below happened with Elbereth under the hero.
- Attacking from it erases it and costs 5 alignment (mon.c:4267).

## 6. Bot's top killers in natural play (job 79, 1152 games)
mumak 40, soldier ant 31, white unicorn 26, owlbear 25, leocrotta 22, black unicorn 11: all at XL 6-9, Dlvl 7-9.
Wiki strategy for each is escape or range: mumak speed 9 (hero 12, Valkyrie intrinsically fast at XL 7), unicorns
avoid melee range on their own (deaths mean the bot engaged), owlbear/leocrotta respect Elbereth, fight from stairs.

## 7. Staged Medusa deaths after the stage fixes (10 seeds, 6696b63)
crowd at T85 (gremlin, water troll, vampire bat), jabberwock T48, minotaur, storm giant (prayer refused),
Aleax + crushing, fire elemental, giant eel drowning. Crossing 4/10.

## Candidate rules (one experiment each; data first)
1. Do not melee monsters with damaging passives. 5.0 monsters.h AT_NONE/AT_BOOM (21): bot avoids 5 (floating eye,
   blue jelly, brown mold, gas spore, acid blob). Missing: energy vortex (ELEC), fire elemental + fire vortex (FIRE),
   gelatinous cube (PLYS), green slime (SLIM), ochre + spotted jelly + green mold (ACID), red mold (FIRE), yellow
   mold (STUN), disenchanter (ENCH), rust monster (RUST), black pudding (CORR); cockatrice/chickatrice only bare-
   handed (handled). Molds never move: avoiding them is free.
   Bench deaths (2620 games, e1d8086 + 7514591): 89 = 3.4% of games: spotted jelly 33 (speed 0: free to avoid),
   energy vortex 26 (speed 20: needs ranged or another answer, not just "no melee"), fire elemental 11,
   gelatinous cube 7, gas spore 5 (already avoided: check why), ochre jelly 5, fire vortex 1, disenchanter 1.
   FIRST EXPERIMENT CANDIDATE: never melee the stationary ones (spotted jelly, molds: speed 0; ochre jelly speed 3,
   engulfs) - walking away costs nothing.
2. Unicorns: check first whether the bot engages them (hypothesis: unicorns keep out of line and away from melee
   on their own, wiki/monmove.c NOTONL), and whether the Sokoban no-teleport levels matter (one death showed
   "A mysterious force prevents the white unicorn from teleporting").
3. Walk away from slow heavy hitters (mumak speed 9) instead of trading blows.
4. Scroll identification so enchant armour gets read (biggest AC lever, 79% of humans).
5. Crisis tools (section 3a) once the apply detail is known.
