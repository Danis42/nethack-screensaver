# Roadmap: a bot that really ascends

Decided 2026-10-20: the main objective of the project is a real ascension. Pilgrim
(ascension) and daredevil (ascension in disgrace) pursue it for real; sightseer and
treasure keep their reachable escape goals.

**Success is a ladder.** Every game is scored by the highest of 17 rungs it reached
(Mines, Minetown, Oracle, Sokoban, Sokoban solved, Mines' End, Dlvl 15+, Quest, Medusa,
Castle, Gehennom, Vlad's Tower, Wizard's Tower, invocation, Planes, Astral, ascended).
Climbing a rung is progress; a real ascension is the last rung. Yardstick: 687 real
ascensions from hardfought.org in the bench database.

**How we work.** Each sub-project gets its own spec, plan and build (superpowers). Every
change is measured on the bench server, one change per experiment.

| # | Sub-project | Rungs it targets | Status |
|---|-------------|------------------|--------|
| 0 | Ascension ladder: record rungs, bench metrics, yardstick table | (measurement) | done 2026-10-21 (baseline in PORTING.md) |
| 1 | Midgame survival, Dlvl 4-12 (most games die on Dlvl 4-8) | 2-6 | |
| 2 | Real descent past Mines' End and the Big Room; reliably finding downstairs | 6-8 | |
| 3 | Gearing up: wands, rings, armour, protection, reflection, magic resistance | 7-9 | |
| 4 | Medusa's level | 9 | |
| 5 | Castle and wishes | 10 | |
| 6 | Quest (XL 14, Bell) | 8 | |
| 7 | Gehennom: Vlad's, Wizard's Tower, invocation | 11-14 | |
| 8 | Elemental and Astral Planes | 15-17 | |

Specs live in `docs/superpowers/specs/`, plans in `docs/superpowers/plans/`, benchmark
numbers in `autoascend/PORTING.md`.
