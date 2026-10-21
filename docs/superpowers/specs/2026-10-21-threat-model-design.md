# Threat model (sub-project 1, step 1) — design

Date: 2026-10-21. Part of sub-project 1 "midgame survival" in `docs/ROADMAP.md`.
The user delegated the design details ("do what you think is right"); the bench decides.

## Goal

Raise **Minetown+** (`rung2`, games reaching rung 2 or higher) from the baseline 29%
(576 games of `2653410`) by letting the bot judge monsters by NetHack's real numbers
instead of name lists and fixed HP limits.

## Why

AutoAscend decides fight, flee, Elbereth and wand use with three crude predicates in
`autoascend/combat/monster_utils.py`:

- `is_dangerous_monster`: pets and six insects, nothing else;
- `is_monster_faster`: name contains bat, dog, cat, kitten, pony, horse, bee or fox;
- `imminent_death_on_melee`: HP ≤ 16 against "dangerous" monsters, else HP ≤ 8,
  whatever the monster, our level or our max HP.

Top killers of the baseline: wands and rays 36, ants 39, giant bat 19, dwarf 17, small
mimic 15, werejackal 14, killer bee 13, unicorns 21. Most of them are "not dangerous"
for the bot, and a unicorn is engaged freely at HP 15+.

## Design

**Monster attack table (`autoascend/combat/monster_data.py`, generated).** NLE's
`permonst` gives level, speed and AC but no attacks. A script `scripts/gen_monster_data.py`
reads NetHack 3.6.6 `src/monst.c` (the version NLE plays) and writes a tuple indexed by
NLE monster index: for each monster its name and up to six attacks `(aatyp, adtyp, n, d)`.
The script checks that every name matches `nle.nethack.permonst(i).mname` in order and
fails otherwise. The generated file says where it comes from (NetHack General Public
License data) and is committed.

**`autoascend/combat/threat.py`** (pure functions over plain numbers, testable alone):

- `hit_chance(mlevel, our_ac)`: NetHack's monster to-hit for melee, `tmp = 10 + our_ac +
  mlevel` (negative AC counts as in `mattacku`: `AC_VALUE(ac) = -rnd(-ac)`, on average
  `(ac - 1) / 2`); the attack hits when `tmp > rnd(20)`, so the chance is
  `clamp((tmp - 1) / 20, 0, 1)`.
- `attack_damage(n, d)`: average `n * (d + 1) / 2`.
- `damage_per_turn(mon_index, mlevel, mspeed, our_ac, our_speed)`: sum over damaging
  attacks (melee kinds: claw, bite, kick, butt, touch, sting, hug, tentacle, weapon,
  engulf) of hit chance × average damage, times `mspeed / our_speed`.
  Passive and gaze attacks are ignored here (the bot handles floating eyes and passive
  monsters already).
- `has_special_attack(mon_index)`: any attack whose damage type is a run-ender beyond HP:
  poison/Str drain (AD_DRST, AD_DRDX, AD_DRCO), lycanthropy (AD_WERE), level drain
  (AD_DRLI), stoning (AD_STON), sliming (AD_SLIM), digestion (AD_DGST), disease (AD_DISE),
  paralysis (AD_PLYS), brain eating (AD_DRIN). Stealing items (AD_SITM, AD_SEDU) is not
  counted.
- `our_speed(role)`: 12, or 16 for roles that start intrinsically Fast (Archeologist,
  Monk, Samurai).

**Predicates rewired (`monster_utils.py`)**, same names and signatures, so the callers in
`fight_heur.py` and `movement_priority.py` stay as they are:

- `is_monster_faster(agent, monster)`: monster speed > our speed.
- `is_dangerous_monster(monster)` keeps its one-argument signature: pets (as now) or
  `has_special_attack`, or its `damage_per_turn` against AC 10 and speed 12 is at least
  4 HP (a fixed yardstick, because the callers have no agent).
- `imminent_death_on_melee(agent, monster)`: our HP ≤ 2 × `damage_per_turn` of this
  monster against our real AC and speed, but never below the old floor of HP ≤ 8.

**Bug fixed on the way:** `elbereth_action` compares a permonst object with a list of
names (`if mon in WEAK_MONSTERS`), so weak monsters were never discounted; compare
`mon.mname`.

Unknown monsters (index out of range, invisible "I" glyphs that never reach these
functions) fall back to the old behaviour: damage 0, not special, speed from `mmove`.

## Measurement

One experiment: candidate commit vs `main` (`2653410` code), metric `rung2`, bench
checkpoints 192/384/576/1152. Keep only on a measured gain; otherwise revert and record
the result in `autoascend/PORTING.md`. Follow-ups, each its own experiment after this one:
Elbereth decided by threat (skipping @ humans and minotaurs, which ignore it), retreat
upstairs when `turns_to_live` is short, and stepping out of line with wand users.

## Testing

- Generator: names match `permonst` for all monsters; soldier ant = bite 2d4 + sting 3d4
  AD_DRST; werejackal (dog form) has AD_WERE.
- `threat.py`: hit chance at AC 10 / level 3 and AC -5; damage of soldier ant vs newt;
  speed scaling; special attacks for soldier ant, werejackal, cockatrice; not for newt.
- Predicates: soldier ant and white unicorn are dangerous, newt and lichen are not; giant
  bat and soldier ant are faster at speed 12; imminent death fires earlier for a soldier
  ant than for a newt at the same HP.
- Elbereth weak-monster fix: a lichen counts 0.1, not 1.
- Whole suite before and after.
