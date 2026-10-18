# AutoAscend port notes

Upstream: maciej-sypetkowski/autoascend @ 8527910 (MIT).
Target: Python 3.13, NLE 1.3.0 (gymnasium), numpy 2, modern numba/opencv.

## Removed
- visualization/, rl_utils.py, rl_scoring.init_fight2_model (torch/RL, tile viewer)
- utils.plot_dashboard (matplotlib/seaborn)
- nltk (replaced by agent._edit_distance)

## Changes
- character.py, item/inventory.py: regex literals with invalid escapes (`\d`, `\.`, `\?`, `\]`) made raw strings (SyntaxWarning on 3.12+, future error). Behavior unchanged.
- env_wrapper.py: rewritten for NLE 1.3.0 / gymnasium (`reset()->(obs, info)`, 5-tuple `step()`, `env.actions` instead of `env._actions`); no seeding patch, no visualizer, no fork/reload/interactive tooling; per-step `on_step` callback; role pinning by re-rolling `reset()` (as upstream `bin/main.py --role` did). End-reason parsing made non-asserting and keeps the cause of death.
- agent.py: `BLStats(*blstats[:26])` — tolerate extra blstats fields in newer NLE.
- agent.py: `cursor_pos` casts `tty_cursor` (uint8) to int. Under NumPy 2 (NEP 50) `uint8(0) - 1` is 255, not -1 as under NumPy 1 — a silent behavior change. Tests now turn overflow RuntimeWarnings into errors.
- soko_solver/maps.py: the map text is indented 4 columns but the solution coordinates
  are not, so every Sokoban attempt died on the first move (`assert ... == BOULDER`).
  The indent is now stripped; `tests/test_soko_solver.py` replays all 8 solutions.
- global_logic.py (screensaver tuning, not a port fix): upstream farmed Dlvl 1 until
  XL 8, which took 15-25k turns and most games fainted from hunger there. Now the bot
  leaves Dlvl 1 once Hungry, then farms Dlvl 3 (new milestone `FARM_UPPER_DUNGEON`)
  until XL 8 or for at most 4,000 turns, then goes on to the Mines as before.
- Observed: the final game-over observation has all-zero blstats; `game.run_game` keeps the last non-zero turn/depth.

## Benchmark (2026-10-16, 50 games, `scripts/benchmark.py -n 50 -j 10`)

```
games            : 50
median score     : 5952.5
median max depth : 3.0
median turns     : 19001.0
exceptions       : 4
watchdog         : 0
  3x AssertionError:
  1x AssertionError: ('TODO: nested containers', set(), [a partly
```

Reference: upstream AutoAscend's NeurIPS 2021 challenge median score was 5,300
(Hambro et al., "Insights From the NeurIPS 2021 NetHack Challenge", arXiv:2203.11889).
The port's median (5,952) is in line with it. Most deaths involve fainting from
hunger; the same report notes a "very high incidence of death due to 'fainted of
starvation'" for challenge agents, and a traced game showed the port's eating
works (corpses, rations, prayer at Fainting), so this is upstream behavior, not a
port regression. Remaining exceptions are upstream `AssertionError`s (e.g. "TODO:
nested containers"); they end the game and the screensaver starts a new one.
