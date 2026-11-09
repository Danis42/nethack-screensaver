# R08 Avoiding starvation (Claude, local 5.0.0 source + bot code)

## Summary
- Hunger states (eat.c newuhs): Satiated > 1000, Not hungry > 150, Hungry 51-150, Weak 1-50, Fainting <= 0.
  Death below -(100 + 10 x Con) (eat.c:3437). 5.0 halved this from -(200 + 20 x Con), but nutrition now drops
  more slowly while fainted.
- Prayer: Weak or worse is MAJOR trouble (pray.c:216, fixed when prayer timeout < 200); Hungry is only MINOR
  trouble (pray.c:276, fixed only when timeout < 100 and luck/alignment are good). Start timeout 300
  (u_init.c:1005); after a good prayer rnz(350) (pray.c:1356): median ~350, long tail.
- The bot already prays for hunger (agent.py prayer_trouble, gap 1000 -> 400 turns after 200 Weak turns).
- Food values (objects.h:1106-1113): food ration 800 (weight 20), lembas 800 (5), cram 600 (15), K-ration 400
  (10), C-ration 300 (10).

## Facts
| claim | source |
|---|---|
| corpse rot = age / (10 + rn2(20)); cursed +2, blessed -2 | eat.c:1885-1891 |
| rot > 5: tainted (deadly food poisoning without sick resistance); rot > 3: "rotten" (blind, confused, faint) | eat.c:1895, 2672-2687 |
| so uncursed corpse: age < 40 is always safe; 40-59 may be rotten; >= 60 may be tainted | derived from above |
| lichen and lizard corpses never rot (nonrotting_corpse) | eat.c |
| poisonous corpse (M1_POIS): 4 in 5 chance of Str loss + damage without poison resistance | eat.c, mondata.h:89 |
| acidic corpse (M1_ACID): damage without acid resistance (also cures stoning) | eat.c, mondata.h:88 |
| cockatrice / chickatrice / Medusa flesh petrifies (flesh_petrifies) | mondata.h:203 |
| eating your own race is cannibalism (Luck -2..-5, aggravate) unless Caveman or orc: for a human Valkyrie every human corpse (incl. human were-forms) | eat.c:51, 758-775 |
| 5.0: globs no longer go tainted, they shrink away | eat.c:1894 |
| Valkyrie entering Weak: "Valkyrie needs food, badly!" (not "You feel weak") | eat.c:3486-3490 |

## Bot rules
1. Eat at Hungry, not Weak. Weak is the prayer trigger, not the eating trigger.
2. Corpses: eat only when age < 40 turns (bot can count turns since the kill), never cursed-unknown, never
   M1_POIS / M1_ACID / flesh_petrifies / human / were-; lichen and lizard any age.
3. Carry food before the Mines: at least 1 food ration or 2 smaller rations; pick up every lichen corpse,
   ration, lembas, cram, K/C-ration and tin found.
4. Pray at Weak when timeout is likely < 200 (current rule already does this).
5. Measure first: of the 15.7 % starvation deaths, how many die with food in inventory (not eating) vs no food
   (not finding / not carrying). The fix differs.

## Risks and exceptions
- Tins: the tin's monster keeps its dangers (poison, cannibalism); cursed tins are rotten; opening takes many
  turns without a tin opener.
- Eating while Satiated can choke (eat.c:3138) unless the hero is very hungry.

## Open questions
- Starvation deaths split by food-in-inventory vs none, and by Mines vs main dungeon (bench data).

## Compared with ChatGPT R08 (2026-11-08)
- Agrees on all numbers checked: hunger thresholds, Valkyrie Weak message, rot formula, 40-turn safe corpse age,
  4/5 poison chance, food values, rnz(350) timeout, globs.
- Missed by ChatGPT: 5.0 lowered the starvation-death point (-(100 + 10 x Con)); Hungry is only minor trouble
  for prayer (prayer at Hungry is not a reliable fix); the start timeout of 300.
- ChatGPT says "never eat human corpse" (right); its per-species danger list is short but correct.
- Neither answer can say why the bot starves without bench data: open question above.
