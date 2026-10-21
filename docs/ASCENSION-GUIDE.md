# The standard route to an ascension

A short guide for people (and for us): what a normal human ascension looks like, in 12
steps, and which ladder rung and roadmap sub-project belongs to each step. Rungs are
from `docs/superpowers/specs/2026-10-21-ascension-ladder-design.md`; sub-projects (SP)
are from `docs/ROADMAP.md`. Turn numbers are medians of 687 real ascensions (see
"Yardstick" in `docs/STATUS.md`).

**Where our bot is:** median game about 4900 turns, ends on Dlvl 5. The best games reach
Dlvl 10-22. So today the bot is somewhere in steps 1-3.

## Early game (turn 0 to about 12,000)

| # | Step | What to do | Rung | Sub-project | Where our bot is |
|---|------|------------|------|-------------|------------------|
| 1 | Survive Dlvl 1-4 | Keep the pet close. Use Elbereth when in danger. Pray only in real trouble (HP below 1/7 of max or below 6, or Weak from hunger), and not more than about once per 1000 turns. | (basis) | SP1 | Most games die on Dlvl 4-8. This is the main loss. |
| 2 | Gnomish Mines to Minetown | Temple (priest, co-aligned altar to test items for curses), shops. Mines entered at turn ~1173, Minetown ~3538. | 1 `mines`, 2 `minetown` | SP1 | Mines in about two thirds of games (to be confirmed by the baseline). |
| 3 | Sokoban | Safe experience and items. Prize at the top: bag of holding or amulet of reflection. Entered ~9022, solved ~12412. | 4 `sokoban`, 5 `sokoban_solved` | SP1, SP2 | Rare. Oracle (rung 3) is on the way. |
| 4 | Mines' End luckstone | Go to the bottom of the Mines and take the luckstone (~10853). | 6 `mines_end` | SP2 | Almost never. |
| 5 | Safe corpses and food | Eat corpses for resistances (fire, cold, poison, sleep) and as a sure food supply. Never eat a corpse older than 50 turns (except lichens and lizards). Avoid kobolds (poisonous). | (basis) | SP1, SP3 | Starvation kills about 13% of games. |

## Midgame (about 12,000 to 30,000)

| # | Step | What to do | Rung | Sub-project | Where our bot is |
|---|------|------------|------|-------------|------------------|
| 6 | Magic resistance and reflection | Cloak of magic resistance, gray or silver dragon scale mail, the Sokoban amulet, shops, wishes. At the end of real ascensions: magic resistance 100%, reflection 83%. | 7 `dlvl15` (needs both to go deep) | SP3 | No planned source yet. |
| 7 | Armour class | AC below 0 early, later around -20 (median at the end: -38). Priests sell protection: donate 400 x XL gold for one point. | (basis) | SP3 | Wears found armour only. |
| 8 | Medusa (Dlvl 21-24) | Reflection or a blindfold against her gaze, and a way over the water (levitation). Killed at ~29317. | 9 `medusa` | SP4 | Never reached. |
| 9 | Castle | Get the wand of wishing. Typical wishes: gray dragon scale mail, speed boots, blessed scrolls of charging and genocide. | 10 `castle` | SP5 | Never reached. |
| 10 | Quest (from XL 14) | Bell of Opening and the role artifact. Quest entered ~22426, Bell ~30475. Median XL at the end: 23. | 8 `quest` | SP6 | Never reached. |

## Late game (about 34,000 to 54,000)

| # | Step | What to do | Rung | Sub-project | Where our bot is |
|---|------|------------|------|-------------|------------------|
| 11 | Gehennom | Enter (~34155). Vlad's Tower for the Candelabrum (~44189). Wizard's Tower for the Book of the Dead. Find the vibrating square, perform the invocation (~49741), take the Amulet of Yendor in Moloch's Sanctum. | 11 `gehennom`, 12 `vlad`, 13 `wizard_tower`, 14 `invocation` | SP7 | Never reached. |
| 12 | Back up and Ascend | Go up with the Wizard harassing you, cross the Elemental Planes (~53180) and the Astral Plane (~53518), and offer the Amulet at your god's altar (~53630). | 15 `planes`, 16 `astral`, 17 `ascended` | SP8 | Never reached. |

## Wiki links

- Overview: [Standard strategy](https://nethackwiki.com/wiki/Standard_strategy), [Ascension](https://nethackwiki.com/wiki/Ascension)
- Survival: [Elbereth](https://nethackwiki.com/wiki/Elbereth), [Prayer](https://nethackwiki.com/wiki/Prayer)
- Gear: [Magic resistance](https://nethackwiki.com/wiki/Magic_resistance), [Reflection](https://nethackwiki.com/wiki/Reflection)
- Early branches: [Sokoban](https://nethackwiki.com/wiki/Sokoban), [Mines' End](https://nethackwiki.com/wiki/Mines%27_End)
- Midgame: [Medusa's Island](https://nethackwiki.com/wiki/Medusa%27s_Island), [Castle](https://nethackwiki.com/wiki/Castle), [Quest](https://nethackwiki.com/wiki/Quest)
- Endgame: [Gehennom](https://nethackwiki.com/wiki/Gehennom), [Elemental Planes](https://nethackwiki.com/wiki/Elemental_Planes), [Astral Plane](https://nethackwiki.com/wiki/Astral_Plane)
