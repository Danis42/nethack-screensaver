# Staged hand game: medusa, seed 1 (wizard-mode start, XL14 HP127 AC-10, MIDGAME_KIT + amulet of reflection)

Level: Medusa variant with trees and ~20 ravens (+ wood nymph), Dlvl 26. Arrival at (43,4) on a strip of land.

## Findings
- M1 DIG DOWN UNDER ATTACK DOES NOT PROGRESS (T6-T34). Playbook rule "dig down on arrival" failed: 28 turns of
  re-applying the pick-axe, never through, HP 127 -> 47, blinded by ravens most of the time.
  SOURCE dig.c:1355: apply only sets the occupation and costs the turn (ECMD_TIME); dig() runs on the NEXT
  turns as an occupation, and every monster attack calls stop_occupation first ("You stop digging."). Effort
  +~13 per dig() call (dig.c:366), 250 needed (dig.c:372). With attackers every turn dig() almost never runs.
  Rule: before digging down, no hostile may be adjacent or able to reach the hero within ~20 turns: kill the
  swarm first, or dig where nothing can reach (or Elbereth until the pit at effort 50 wipes it).
  Check the bot: its dig-on-arrival loop must detect "You stop digging." with an attacker and switch to fighting.
- M2 ravens blind on hit ("The raven blinds you!") again and again; extra healing cures blindness once, the next
  bite blinds again. Unicorn horn needed between fights; blind = attackers show as "It".
- M3 ELBERETH FAILS AGAINST A CROWD (T36-42): wrote Elbereth in the dust while blind, ravens kept biting:
  HP 38 -> 0 in 6 turns. SOURCE monmove.c:918-920 + 968: a monster scared by Elbereth that cannot move away
  (MMOVE_NOMOVES: boxed in by the other ravens) makes a "panic attack" anyway. Rule: Elbereth only protects
  against a few attackers with room to flee; against a swarm on a narrow strip it does nothing.
- M4 unicorn horn against raven blindness is useless mid-fight: cured 4 times, re-blinded the same turn each time.
- DEATH T42 (my error): my scripted loop (apply unicorn horn x8) had no HP stop; I still had 3 blessed potions
  of extra healing. The tool's checked commands have HP stops; raw-key loops must too.

## What the Medusa stage needs (rules for the bot, from M1-M4)
- Arrival: the raven variant puts ~20 fast blinding fliers on the hero at once. Dig-on-arrival cannot work
  under attack (M1). Options to test next: fight on a square with few open neighbours (corridor or tree
  cover) so only 1-3 ravens reach; quaff extra healing at 50%; blindfold does not help (they still bite);
  telepathy makes blind fighting possible (floating eye corpse or helm of telepathy - not in the kit).
- Staged kit gap: MIDGAME_KIT has no telepathy and no ranged/area attack; the real hero would have Excalibur
  at most. The stage requirement for Medusa probably includes telepathy (intrinsic) - check human
  ascension data (NLD-NAO) for telepathy before Medusa.

## Replay with the fight-first plan (same seed, 2026-11-03)
- M5 blind melee (no telepathy): 2 ravens killed in 18 turns for -51 HP: swings go at "it" squares the fast
  ravens already left. Not sustainable against 20+ ravens.
- M6 with telepathy (wizard wish: helm of telepathy, swapped for the +2 dwarvish helm, AC -10 -> -7): blind but
  every raven visible. T26-T127: about 17 ravens + a baby gray dragon + a jellyfish killed, 2 extra healings
  used, HP ended 85/127 and rising: the swarm thins and fewer reach the hero. Fight-first WORKS with
  telepathy. Stage requirement candidate: telepathy (intrinsic or helm) before Medusa. CHECK with human data.
- M7 DIG DOWN NEXT TO WATER FILLS THE HOLE: "As you dig, the hole fills with water! You fall into the shallow
  sea!" (twice; armour rusted AC -7 -> -5; sinking can drown a heavy hero). SOURCE dig.c:606 fillholetyp: any
  moat among the 8 neighbours fills the pit/hole with chance moat/(moat+1); pools count /3.
  STATIC CHECK of the 4 maps (arrival region = teleport_region dir=down): floor squares with no water within 1:
  medusa-1 32 of 67, medusa-2 46 of 53, medusa-3 0 of 16 (dig impossible), medusa-4 6 of 51 (one corner,
  (67-69,2-3) in map coordinates). Dry land elsewhere on medusa-3 ((58,16)) is not reachable on foot.
  => Playbook rule "dig down on arrival" is wrong for medusa-3 and needs a dry-square search on medusa-4.
     Bot: digging.dig_square must require no water within 1 square; on medusa-3 crossing needs levitation
     (or water walking / freezing the water with a wand of cold).
