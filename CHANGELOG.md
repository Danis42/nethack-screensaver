# Changelog

## 0.2.0 (2026-10-18): secret strategies

Released with the realistic targets below; whether to keep tuning is open.

**Gameplay**
- Every game secretly follows one of four strategies, picked after the character is
  known and tilted by role: Pilgrim (ascension; Mines, Minetown, Sokoban, then dive),
  Daredevil (escape in celestial disgrace; dives), Sightseer (escape; Minetown and back
  out), Treasure hunter (escape with loot; Sokoban prize and back out).
- Optional reveal of the secret goal on the game-over screen (`reveal_goal`).
- The bot leaves Dlvl 1 once Hungry (upstream farmed it to XL 8 and mostly starved).
- Escape plans retreat home directly and bail out when out of food and prayer.
- Smart pacing: fast-forwards quiet stretches and farming (`fast_delay`).

**Bot fixes and knowledge**
- Sokoban: stored solutions line up again (they crashed on the first move); a live-board
  solver takes over when they no longer fit; Sokoban is searched only below the Oracle;
  the prize is picked up.
- Prays when Weak from hunger (Weak is already major trouble).
- Escapes are logged as escapes, not deaths; log gains strategy, gender, outcome, milestone.

**Realistic targets (benchmarks, 36-192 games each)**

| Strategy | Goal | Result |
|---|---|---|
| Sightseer | escape the dungeon | about 20% |
| Treasure hunter | escape with the Sokoban prize | about 1-2% (any escape 15-20%) |
| Daredevil | reach Dlvl 10+ (stand-in for its Amulet goal) | about 12-20% |
| Pilgrim | complete the tour (stand-in for ascension) | rare |

Main remaining obstacle: surviving Dlvl 6-9 at XL 7-9 (most Sokoban visitors die there).

## 0.1.0 (2026-10-17)

First version: zsh idle hook, launcher and AutoAscend ported to Python 3.13 / NLE 1.3.0.
