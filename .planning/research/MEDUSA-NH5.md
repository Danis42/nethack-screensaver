# Medusa's Island in NetHack 5.0: how humans pass it, what our bot needs (2026-11-03)

Sources: local wiki (Medusa's Island, Medusa, Raven pages), NetHack 5.0.0 source (dig.c, monmove.c, dat/medusa-1..4.lua),
199 hardfought 5.0 ascension dumplogs in the bench store (reference_games), two staged hand games
(.planning/hand-games/medusa-seed1/NOTES.md).

## The level
- 4 maps, equal chance, may be flipped. Medusa sleeps on the down stairs with the statue of Perseus (shield of
  reflection 75% on maps 1/3/4, 25% on map 2; levitation boots 25% / 75% on map 2).
- Map 3: 30 ravens (speed 20, bite 1d6 + a claw that blinds up to 6 turns), "shortsighted" level, trees.
  Map 2: titan, electric eels. Map 4: yellow dragon, kraken, 14 snakes, black nagas. Map 1: eels, water trolls.

## How humans pass it (wiki)
1. Cross the water: levitation or water walking boots (most common), freeze a path (wand of cold, frost horn,
   cone of cold), boulders (scroll of earth; 8 for map 1/4, 16 for map 2), jumping, magical breathing.
2. Or dig down, then come back up the stairs into Medusa's room: "be absolutely sure not to dig on a
   water-adjacent square, or you are likely to drown".
3. Medusa herself: reflection kills her with her own gaze (she must see you), or blind yourself (blindfold, towel)
   and melee her (AC 2, weak attacks); telepathy to find her while blind.
4. Ravens: blindfold yourself + telepathy (their claw cannot blind a blinded hero, telepathy shows them), or lenses /
   a visored helmet. Being blinded "can prevent reliably engraving Elbereth".

## Human 5.0 ascensions (199 dumplogs, final state; timing of intrinsics is not logged)
| Item / property at the end | share |
|---|---|
| blindfold or towel carried | 96% |
| telepathic (13% via a helm/amulet, the rest intrinsic: eaten floating eye) | 95% |
| levitation item (ring, boots, potion) | 85% |
| reflection | 83% |
| dig tool (pick-axe, mattock, wand of digging) | 82% |
| wand of cold or frost horn | 78% |
| water walking boots | 42% |
Medusa killed (logged in 130): median T29317, quartiles T22669-T36008.

## Our two staged hand games (medusa seed 1 = map 3, XL14, AC -10, MIDGAME_KIT + amulet of reflection)
- Dig under attack never progresses: dig.c:1355 apply only sets the occupation; each attack stops it first.
- Elbereth vs a crowd fails: monmove.c:918 boxed-in scared monsters "panic attack"; blind engraving is unreliable too.
- Blind melee without telepathy: 2 kills / 18 turns / -51 HP. With telepathy: ~17 kills, 2 extra healings, HP rising.
- Digging next to water fills the hole and drops the hero in (dig.c:606 fillholetyp): dry arrival squares per map
  (arrival = teleport_region dir=down): map 1 32/67, map 2 46/53, map 3 0/16, map 4 6/51.

## What the bot lacks (status 2026-11-03)
1. Telepathy: the bot never melees floating eyes (exp 21) and has no rule to kill them at range and eat the corpse.
   95% of human ascenders are telepathic. Candidate early-game rule: kill a floating eye with thrown daggers or an
   attack wand from >= 2 squares (never melee), eat the corpse at once. MISSING.
2. Blindfold or towel: 96% of humans carry one; the bot picks them up? CHECK. Use: wear before Medusa's map and
   against ravens when telepathic.
3. Crossing: levitation (BUILT primitives, route MISSING), wand of cold path MISSING, dig only on a square with no
   water within 1 (digging.dig_square does not check: MISSING, small fix).
4. Stage requirement for Medusa (candidate, to test on staged runs): telepathy + blindfold + (levitation or cold or
   a dry dig square) + reflection or blindfold for Medusa.
