# R03 Mumak, leocrotta, owlbear, soldier ants (Claude, local 5.0.0 source + bench data + bot code)

## Summary
- Bench (e1d8086, 1152 games): mumak 40, soldier ant 31, owlbear 25, leocrotta 22 deaths; median XL 7-9,
  Dlvl 8-9, max HP 67-86.
- The bot's retreat test is one fixed number: imminent_death_on_melee = HP <= 8 (HP <= 16 for "dangerous"
  monsters = pets' kinds and insects) (combat/monster_utils.py:15-30). Mumak and leocrotta are commented out of
  the dangerous list. A mumak averages ~33 damage per round (max 60): the bot keeps trading blows long after one
  round can kill it.
- Speed (allmain.c:114-132): hero 12; intrinsic Fast (Valkyrie from XL 7) adds 12 on 1 turn in 3 (avg 16); Very
  fast adds 12 on 2 turns in 3 (avg 20). So the hero outwalks a mumak (9) and, slowly, an owlbear (12); not a
  leocrotta or soldier ants (18).
- All four respect Elbereth (none are @, minotaur, unique); a scared monster that cannot move away still attacks
  (monmove.c:918-968).

## Facts
| monster | level | speed | AC | attacks (avg/round) | source |
|---|---|---|---|---|---|
| mumak | 5 | 9 | 0 | butt 4d12 + bite 2d6 (26+7 = 33; max 60) | include/monsters.h |
| leocrotta | 6 | 18 | 4 | claw 2d6, bite 2d6, claw 2d6 (21; max 36) | include/monsters.h |
| owlbear | 5 | 12 | 5 | claw 1d6, claw 1d6, hug 2d8 (7+9 = 16; hug holds the hero) | include/monsters.h |
| soldier ant | 3 | 18 | 3 | bite 2d4 + poison sting 3d4 (5+7.5 = 12.5 each; small groups) | include/monsters.h |
| hero speed: base 12, Fast +12 with 1/3, Very_fast +12 with 2/3 | src/allmain.c:114-132 | | | | |

## Bot rules
1. Replace the fixed retreat test by expected damage: a monster's expected damage per hero turn =
   (sum of its attack dice averages) x (monster speed / hero average speed). Retreat (or Elbereth / quaff / pray)
   when HP <= 2 x that, not at HP 8. Data source in the bot: MON.permonst(...).mattk and .mmove (already used).
2. Slow heavy hitter (mumak, speed 9 < hero 16 when Fast): never melee at XL <= 10; walk away (it cannot follow
   fast enough) or use ranged attacks while backing off.
3. Owlbear: do not let it get adjacent at low HP (the hug holds the hero); speed 12 vs 16: back off early.
4. Leocrotta / soldier ants (speed 18): no outrunning. Fight in a corridor or doorway (one at a time), Elbereth
   when HP is below the rule-1 threshold, leave by stairs if standing on them.
5. Measure first: how many of these deaths start at full HP (bad engagement) vs during retreat (bad escape).

## Risks and exceptions
- Monster level grows with depth and hero level (makemon.c adj_lev), so damage can exceed the base table.
- Rule 1 is a common-path change (every fight): needs a no-harm bench plus the killer counts.

## Open questions
- Share of these deaths where the bot was already below the rule-1 threshold when it started the fight.

## Compared with ChatGPT R03 (2026-11-08)
- Agrees: all four stat lines, speeds (hero 12 / fast avg 16), Elbereth works on all four, 5.0 panic attack.
- Extra in ChatGPT, verified: none of the four follows the hero on stairs (no M2_STALK, mondata.c:1211-1226), so
  stairs are a clean escape; prayer "low HP" at XL 6-13 is HP <= 5 or HP <= max/6, max capped at 15 x XL
  (pray.c:116-140), i.e. 10-14 HP for max 60-85; burdened removes the speed edge (fast 16 -> 12).
- Missed by both, from source: soldier ant sting poisons 1 hit in 8 (uhitm.c:3154); then 1/30 "deadly" =
  6 + 4d6 (10-34) HP, death only if HP <= that, else lose half of it from max HP and Con/Str (attrib.c:361-382);
  otherwise mostly 6-15 extra HP or Str loss. Valkyries have no poison resistance.
- ChatGPT uses maximum damage (60/36/28) as HP floors; Claude uses average x speed. Max is safer but would make
  the bot flee every mumak at HP < 61, i.e. almost always: use average x speed with a margin, plus "never
  melee a mumak at XL <= 10".
- Owlbear is M2_NASTY (monsters.h:2392); not used by either answer yet.
