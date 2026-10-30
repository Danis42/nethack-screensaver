# The wish budget on NetHack 5 (research, 2026-10-30)

Sources: src/zap.c, read.c, sit.c, allmain.c, objnam.c, mkobj.c, shknam.c, potion.c, dat/castle.lua; wizard-mode spike
(scratchpad wand_spike.py, 6 seeds). Companion to XL14-NH5.md and MEDUSA-RETURN-NH5.md.

## Supply

| Source | When | Wishes | Status |
|---|---|---|---|
| Castle wand, charge | Castle | 1 | wand is (0:1): source and spike |
| Wrest the empty wand | Castle | 1 | 1/121 per zap, 1 turn each: 6/6 in the spike, 87-348 zaps; mean 121, 99% by about 555; then dust |
| Recharge with a FOUND scroll of charging | Castle | +1 | spike: (1:1); once only, a second recharge destroys the wand. Recharge BEFORE wresting: a wrest ends the wand |
| Vlad's Tower throne | Gehennom | 1 | NH5 special throne: effect 1/3 per sit, wish 4/13 of effects, about 10 sits; throne leaves only by granting it. Source only |
| Picking up the Amulet | Sanctum | 1 | allmain.c, once. Source only |
| Castle throne | Castle | about 0.08 | wish 1/13 of effects, throne vanishes 1/3 per effect, Luck must not be bad; not worth it |
| Magic lamp | any | rare | lighting shop stock 3%; not a plan. A blessed lamp djinni grants 80% |
| Smoky potion djinni | any | rare | not a plan |

Result: 2 reliable wishes at the Castle (3 with a found charging scroll), 2 more later: 4-5 in the game.
ASCENSION-PLAN-NH5.md said 2-3 and counted neither the wrest nor the Vlad throne.

Wishing for a scroll of charging gains nothing: it spends the wish it returns (spike: 3 wishes, 1 spent, 2 useful).

Vlad throne costs before the wish (per effect, about 2 bad effects expected): acid up to 80 HP (sit only with HP well above
80), permanent level drain, lose an intrinsic, curses, summons, level teleport to the Vibrating Square level (useful).

## Demand

| Need | Latest moment | Item | Alternatives |
|---|---|---|---|
| Levels to XL 14 | before the Quest | blessed potions of gain level | chest potion gives 1; each natural level or wraith saves one |
| Pass Medusa upward | before the Quest | 1 cursed potion of gain level | scroll of teleportation, confused or cursed, random; or kill her and levitate |
| Climb with the Amulet | end | 1 cursed potion of gain level | levitation |
| Magic resistance | before Gehennom | gray dragon scale mail | random cloak of MR |
| Levitation | Planes of Air and Fire | ring | Perseus boots, random |
| Reflection | Medusa, rays | amulet | Sokoban prize 50%, Perseus shield |

Quantities (objnam.c `cnt < rnd(6)`): ask 2: 67% get 2, else 1; ask 3: 50% get 3, else 1.

## Recommended allocation

- Castle charge: "2 blessed potions of gain level".
- Castle wrest: "2 cursed potions of gain level".
- Found charging scroll, if any: magic resistance, before Gehennom.
- Vlad throne: magic resistance if still missing, else what is missing.
- Amulet: levitation for the Planes unless already held.

## Weak points

- No MR on the Quest and in Gehennom down to Vlad's Tower unless a charging scroll or cloak turns up. Unmeasured risk.
- Failed quantity rolls: 1 in 3 for each wish gives one potion. A short level then needs a natural level or wraith; a short
  cursed potion means the Amulet climb needs levitation.
- XL 11 on arrival is assumed; XL 12 frees half a wish, XL 10 breaks the plan.
- Wresting takes about 120 turns on a level with soldiers: do it somewhere cleared.

## Bot work

Zap until wrested (handle "You wrest"), answer the wish prompt with a fixed list, read a scroll (the bot never reads),
quaff blind by letter, #sit with an HP floor, recognise charging by price or by reading unknown scrolls at the wand.
