# Getting back up past Medusa on NetHack 5 (research, 2026-10-30)

The route digs past Medusa going down, so the hero is below her with the water still uncrossed. The same crossing returns
on the final climb with the Amulet. Sources: dat/medusa-*.lua, dat/castle.lua, do.c goto_level, dungeon.c u_on_rndspot,
potion.c peffect_gain_level, teleport.c, read.c, plus a wizard-mode spike (scratchpad medusa_spike.py, 12 seeds).

## How arrival works (changed from 3.6)

- goto_level: `up = depth(new) < depth(old)`; a non-stair arrival calls u_on_rndspot(up). 3.6 used "carries the Amulet".
- Going upward lands in the level's "up" region: Medusa's island on maps 1, 2, 4; map 3 has none (whole level).
- The Castle has an up staircase on its arrival side (castle.lua stair-up, x 1-10); it leads to Medusa's down stairs,
  where she sleeps with the Perseus statue.

## Ways past

| Method | Works with Amulet | Needs | Notes |
|---|---|---|---|
| Cursed potion of gain level | yes, 4/4 in the spike with the real Amulet | the potion | rises exactly 1 level from wherever the hero landed, no water; 12/12 without the Amulet |
| Level teleport (confused or cursed scroll of teleportation) | no ("disoriented") | scroll, confusion or cursed | skips Medusa outright; random: 1/5 stays, range 1..current+3 |
| Levitation / water walking | yes | ring, boots, potion | also needed on Planes of Air and Fire; must get past an awake Medusa |
| Freeze the water (cold) | yes | wand of cold, frost horn | untested |

## Recommended: stairs plus one cursed potion

1. Walk to the Castle's up stairs (same side as the arrival). 2. Put on a blindfold or wear reflection. 3. Up the stairs
to Medusa's square; she starts asleep. 4. Quaff: one turn, hero is on the level above and never fights her or crosses water.
Blind quaffing works by inventory letter. Then stairs up to the Quest portal level (Dlvl 11-16).

From the Castle itself one potion only reaches her island, so stairs save a potion. If filler levels sit between Medusa
and the Castle (seed 10: Medusa 27, Castle 29) walk those by stairs.

## Sources of the potion

Wish "2 cursed potions of gain level" (67% get 2, else 1; 3: 50% get 3, else 1). The Castle chest potion has random BUC:
if cursed, keep it for this. Two are needed for the whole game: this trip and the climb with the Amulet.

## Not verified

- Walking the real stairs with Medusa on them (the spike used ^V to reach her level).
- That she stays asleep on arrival; the blindfold/reflection covers the gaze if not.
- Random level teleport odds (wizard mode prompts instead of rolling).
