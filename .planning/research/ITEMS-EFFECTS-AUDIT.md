# Items and effects audit (2026-10-26)

Method: every object in `src/objects.c` matched against `autoascend/` (outside the data tables), then the bot's
item code read (`item/inventory.py`, `global_logic.py` item split, `agent.py` food/prayer), rules checked in
`src/` (pray.c, eat.c, fountain.c, zap.c), effects counted on the 6a840f2 bench games (2304).

## What the bot does with items today
- Picks up nearly everything light (potions, rings, amulets, wands, scrolls, tools, food, unknown items).
- Uses: best melee weapon, best armour **by AC only**, healing potions in emergencies, fruit juice, food,
  wands (engrave-ID, attack zaps), altar BUC test, sacrifice until the first gift, Excalibur dip, Sokoban prize.
- Never issues: read (scrolls/spellbooks never read), put on (rings/amulets never worn), #sit, #chat, #pay.
  Apply is used for a few tools only. Unknown BUC is often treated as uncursed (item_manager.py 191/234/334).
- Armour choice by AC alone: a cloak of magic resistance, shield of reflection or speed boots is worth no more
  than its AC; nothing values MR, reflection, speed, free action.

## Effects the bot misses, by measured cost (6a840f2, 2304 games)
1. **Poison: 120 deaths (5.2%)**, e.g. "poisoned by a killer bee" 36, "orcish arrow" 26, plus soldier ants and
   killer bees as top killers. Poison resistance removes the instadeath and the Str loss.
   - Source of it the bot refuses: `_is_corpse_editable` rejects every poisonous corpse (agent.py 1355).
     eat.c givit: a killer bee corpse gives poison resistance ~30% (1/4 forced + 1/15), scorpion the same.
     Cost of eating one without resistance: 4/5 chance of -1d4 Str and 1d15 HP (eat.c 1649), never fatal
     above 15 HP.
   - Experiment: eat poisonous corpses when HP > 20 and not yet poison resistant; track the intrinsic from the
     message "You feel healthy" / "(You seem unaffected by the poison)".
2. **Stoning: 82 deaths (3.6%)**; 47 show "You are slowing down"/"limbs are stiffening" before death, 57 had
   1000+ turns since the last prayer. Stoning is the top major trouble prayer fixes (pray.c TROUBLE_STONED).
   The bot prays only for low HP and hunger, and it eats lizard corpses as ordinary food.
   - Experiment: when stoning starts (message, or the NLE status mask), eat a carried lizard/acidic corpse,
     else pray; keep lizard corpses as medicine, not food.
3. **Other prayer-fixable troubles** the bot ignores: strangulation, sliming, food poisoning/illness ("You feel
   deathly sick"), lava, cursed levitation. Few deaths today (slime 1, lava 4), but same fix as 2.
4. **Telepathy**: a floating eye corpse always gives it (eat.c givit, chance 1 for level-2 eye). Useful when
   blind (Medusa, blindfold). The bot avoids melee with floating eyes; it could kill them by throwing/zapping.
5. **Food**: 567 of 576 old starvers carried no food; the bot already picks up all non-corpse food. More
   food = more corpses (poisonous ones above) and tins; no tin opening.

## Items worth using later (Phase 3+), not now
- Rings/amulets: need identification first (price, sink, engrave does not work). Life saving, free action,
  slow digestion (starvation), regeneration, conflict. Risky unknown: teleportitis, hunger, levitation
  (cursed = stuck), strangulation (cursed = death in 6 turns).
- Scrolls: read-ID when safe (enchant armour/weapon, remove curse, teleport as an escape). Never read when
  confused (genocide/fire/teleport change meaning).
- Armour priorities beyond AC: magic resistance, reflection, speed, levitation for Medusa/Castle/Wizard's tower.
- Tools: pick-axe (see ASCENSION-ROUTE-AUDIT.md), blindfold/towel (Medusa, telepathy), unicorn horn
  (cures confusion/stun/blindness/sickness; listed as a skill only), bag of holding, candles, magic marker.
- Wand of digging: escape + descent like the pick-axe.

## Ranked experiment candidates from this audit
1. Pray / eat lizard when stoning starts (82 deaths, cheap, prayer path exists).
2. Eat poisonous corpses for poison resistance when HP allows (120 deaths, cheap: one rule + intrinsic flag).
3. Pick-axe: keep it, dig down when stuck (from the route audit; starvation and stuck levels).
4. Value MR/reflection in armour choice (Phase 3).
