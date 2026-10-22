# Phase 1: Midgame Survival - Pattern Map

**Mapped:** 2026-10-22
**Files analyzed:** 14 (new or modified)
**Analogs found:** 13 / 14

All analog paths below are git-tracked (checked with `git ls-files` for PORTING.md, STATUS.md, handoff.txt, benchmark.py; the rest are normal source/tests). Line numbers refer to current `main`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `nethack_screensaver/game.py` (modify: `fix_moon_phase`, new `GameResult` fields, optional `lgen`, optional agent seed for divergence control) | config / service | request-response (one game -> result JSON) | itself: `run_game` lines 140-206, `GameResult` 31-52, `_stat` 85-90 | exact |
| `autoascend/soko_solver/search.py` (modify: drop wall-clock deadline in bench mode) | utility | transform | itself: `solve` lines 97-125, `_fill_one` line 76 | exact |
| `autoascend/agent.py` (modify: death-context stats, prayer failure detection, hunger-prayer gap, food, wand step-off) | service | event-driven | itself: `prayer_trouble` 54-65, `is_safe_to_pray`/`pray` 790-802, emergency block ~1500-1530 | exact |
| `autoascend/global_logic.py` (modify: rest trigger, `_should_bail`, corpse eating) | service | event-driven | itself: preempt list 843-851, `_should_bail` 230-237 | exact |
| `autoascend/combat/fight_heur.py` / `monster_utils.py` (modify: wand and ant/bee tactics) | utility | transform | `drop_floating_eye_melee` (tested in `tests/test_fight_heur.py`) | role-match |
| `scripts/replay_check.py` (new) | utility | batch | `scripts/benchmark.py` | role-match |
| `tests/test_replay.py` (new, slow) | test | request-response | `tests/test_game.py` `test_headless_games_complete_without_exceptions` (`@pytest.mark.slow`) | role-match |
| `tests/test_game.py` (extend: moon-phase wiring) | test | request-response | `tests/test_game.py` lines 57-60 (monkeypatch pattern) | exact |
| `tests/test_soko_search.py` (extend) | test | transform | itself | exact |
| `tests/test_rest.py`, `tests/test_prayer.py` (new) | test | transform | `tests/test_fight_heur.py` (SimpleNamespace fakes) | exact |
| `tests/test_fight_heur.py` (extend) | test | transform | itself | exact |
| `bench/runner.py` (optional: `PYTHONHASHSEED=0`) | config | request-response | itself line 15 | exact |
| `bench/stats.py` (optional: 2304 checkpoint) | config | batch | itself (`CHECKPOINTS`, `_verdict`) | exact |
| `autoascend/PORTING.md`, `.planning/STATE.md`, `docs/STATUS.md`, `handoff.txt` (docs) | doc | n/a | existing PORTING.md verdict entries | role-match |
| `rejudge/<name>` branches (git, no file) | n/a | n/a | RESEARCH Pattern 7 | no analog needed |

## Pattern Assignments

### `nethack_screensaver/game.py` (determinism + instrumentation)

**Analog:** itself.

**Seeding site to edit** (lines 151-156):
```python
    env = NetHackChallenge(no_progress_timeout=1000)
    if seed is not None:
        # NetHackChallenge blocks the instance method; the class's own one still works
        type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False)
```
Change to `NetHackChallenge(no_progress_timeout=1000, fix_moon_phase=seed is not None)`. Unseeded screensaver games stay on the real clock.

**Agent seed for the divergence control** (line 24): `AGENT_ARGS = dict(panic_on_errors=True, verbose=False)`; the divergence control commit adds `seed=1` here and nothing else.

**New GameResult field pattern** (lines 31-52, all additions default so old stored JSON still loads):
```python
    ladder_error: int = 0  # 1 when the ladder broke mid-game (values incomplete)
```
**Reading a stat into the result** (lines 85-90 and 197-202):
```python
def _stat(wrapper, name: str) -> int:
    try:
        return wrapper.agent.stats_logger.get_stats_dict()[name]
    except Exception:  # agent never started
        return 0
...
ladder_error=_stat(wrapper, "ladder_error"), seed=seed,
```
Add new counters (e.g. `rest_turns`, `prayers`, `prayer_failed`, `zaps_seen`) the same way. Death context (last messages, monsters in view) needs a string/list field: build it in a `try/except` helper like `_milestone` (lines 77-82) so it never ends a game.

**Counter side** (agent code): `self.stats_logger.log_event('untrap_success')` (agent.py:757) and `log_cumulative_value(name, key, value)` (agent.py:502; `stats_logger.py:46,49`).

**Test:** `tests/test_game.py:57-60` uses `monkeypatch.setitem(STRATEGIES, ...)`; copy that style to `monkeypatch.setattr(game, "NetHackChallenge", fake)` and assert `fix_moon_phase` kwarg is True for a seeded call, False for unseeded.

### `autoascend/soko_solver/search.py` (remove wall-clock dependence)

**Analog:** itself (lines 76, 97-103):
```python
        if budget[0] < 0 or time.monotonic() > deadline:
            raise _OutOfBudget()
...
def solve(floor, boulders, traps, player, max_states=300_000, max_seconds=10.0, alternatives=3,
          crossable=frozenset()):
    deadline = time.monotonic() + max_seconds
    budget = [max_states]
```
Keep the signature; allow `max_seconds=None` (deadline = infinity) and pass that from the caller `global_logic.py:492-501` (`_solve_live_sokoban`). Extend `tests/test_soko_search.py` with a test that `max_seconds=None` still honours `max_states`.

### `autoascend/agent.py` (SURV-02 prayer/food, instrumentation)

**Prayer decision** (lines 54-65 and 1511-1516):
```python
def prayer_trouble(blstats, safe_hp, safe_hunger, has_food=False):
    low_hp = blstats.hitpoints < 1 / (5 if blstats.experience_level < 6 else 6) * blstats.max_hitpoints \
        or blstats.hitpoints < 6
    return (safe_hp and low_hp) or (safe_hunger and not has_food and blstats.hunger_state >= Hunger.WEAK)
...
        food = self.edible_inventory_food()
        if prayer_trouble(self.blstats, self.is_safe_to_pray(500), self.is_safe_to_pray(400),
                          has_food=food is not None):
            yield True
            self.pray()
            return
```
**Prayer timing/state** (lines 790-802):
```python
    def is_safe_to_pray(self, limit=500):
        return ((self.last_prayer_turn is None and self.blstats.time > 300) or
                (self.last_prayer_turn is not None and self.blstats.time - self.last_prayer_turn > limit))

    def pray(self):
        self.step(A.Command.PRAY)
        self.last_prayer_turn = self.blstats.time
        return True
```
Experiments (one per commit, D-08): change the 400 limit (pure function `prayer_trouble` stays unit-testable); or in `pray()` inspect `self.message` after the step and set a `prayer_failed` flag plus `log_event('prayer_failed')` (failure strings must be taken from the NLD ttyrecs per RESEARCH Open Question 5). Keep `prayer_trouble` a pure function of `blstats` and booleans so `tests/test_prayer.py` can use `SimpleNamespace`/`BLStats` fakes.

**Rest primitive** (lines 877-885): `Agent.search(max_count=1)` wraps `panic_if_position_changes()` and `atom_operation()`, types the count before `Command.SEARCH`. Rest trigger reuses this.

### `autoascend/global_logic.py` (SURV-01 rest, SURV-02 bail/corpses)

**Existing rest hook that only fires when nothing is left to explore** (lines 843-851):
```python
                .preempt(self.agent, [
                    exploration_strategy(0).condition(lambda: not going_home),
                    exploration_strategy(None).until(
                        self.agent, lambda: self.agent.blstats.hitpoints >= 0.8 * self.agent.blstats.max_hitpoints)
                ])
```
The rest-to-full change adds a `.condition(...)`-gated strategy ahead of `exploration_strategy(0)` in this preempt list (gate: no visible hostile, HP below threshold, `hunger_state` not Hungry or food carried, per-level turn cap, log `rest_turns`).

**Food bail-out** (lines 225-237):
```python
        if self.agent.blstats.hunger_state >= Hunger.WEAK and not self.agent.is_safe_to_pray() and \
                not any(item.is_food() for item in flatten_items(self.agent.inventory.items)):
            return True
```
Corpse-eating conditions: lines 873-884 (and `agent.py:1391` `eat_corpses_from_ground`, `agent.py:1538` `eat_from_inventory`).

### `autoascend/combat/fight_heur.py` / `monster_utils.py` (SURV-03, SURV-04)

**Analog:** `drop_floating_eye_melee` in `fight_heur.py`, a pure filter over `(score, action)` lists, tested with fakes (`tests/test_fight_heur.py:1-26`):
```python
def _mon(name, y, x):
    return (1, y, x, SimpleNamespace(mname=name), 0)

def test_drops_melee_on_floating_eye():
    monsters = [_mon("floating eye", 5, 6), _mon("jackal", 4, 5)]
    actions = [(-94, ("melee", 0, 1)), (16, ("melee", -1, 0)), (3, ("move", 1, 0))]
    assert drop_floating_eye_melee(actions, monsters, (5, 5), blind=False) == actions[1:]
```
New wand off-line step and ant/bee tactics should be written as the same kind of pure function over (actions, monsters, position, flags) plus tests extending this file. `INSECTS` list in `monster_utils.py` is the monster-class source for ants/bees.

### `scripts/replay_check.py` (new, batch)

**Analog:** `scripts/benchmark.py` (docstring usage line, argparse `main`, `run_game` import):
```python
"""Headless AutoAscend benchmark: catches silent regressions from the port.

Usage: uv run python scripts/benchmark.py -n 50 -j 8
"""
import argparse
...
from nethack_screensaver.game import run_game
```
Use the same skeleton; read stored games with `Store.games_by_seed(sha, range(n))` (`bench/store.py`) and compare `turns`, `end_reason`, `rung`, `role` per seed. Per-frame hashing probe: RESEARCH Code Example 5 (`on_frame` callback, `obs["tty_chars"].tobytes()`).

### `tests/test_replay.py` (new, slow)

**Analog:** `tests/test_game.py` `@pytest.mark.slow` test at ~line 24 (`test_headless_games_complete_without_exceptions`, plays real games, collects frames via `on_frame`). Run fresh-process cases with `subprocess` and differing `PYTHONHASHSEED`. Slow marker is excluded by default (`addopts = "-m 'not slow'"`).

### `bench/runner.py` / `bench/stats.py` (optional)

`runner.py:15`: `env = {**os.environ, "PYTHONPATH": str(worktree)}` -> add `"PYTHONHASHSEED": "0"`; needs server restart when idle. `bench/stats.py` `CHECKPOINTS` drives `z_for` and the "no measurable difference" rule keyed on `CHECKPOINTS[-1]`; tests in `tests/test_bench_stats.py`, `tests/test_bench_server.py`. `bench/worker.py` must import nothing from `bench`.

### Docs: `autoascend/PORTING.md`, `.planning/STATE.md`, `docs/STATUS.md`, `handoff.txt`

Follow the existing PORTING.md entry style (verdict, interval, SHA, numbers; baselines named by code SHA; add the 17-rung table with n and SHA; mark older numbers "not comparable"). `docs/STATUS.md` and `handoff.txt` become a short pointer to `.planning/STATE.md` (D-02); that docs-only commit is the A/A twin. Log branch SHAs in PORTING.md before `git branch -D` (D-13).

## Shared Patterns

### Behaviour-neutral change proof
**Source:** RESEARCH Pitfall 11 / Wave 0. Instrumentation and determinism commits must replay exact per-seed results (turns, end_reason, rung, role) against current `main` on 192 seeds before becoming the baseline.

### Never end a game from diagnostics
**Source:** `game.py:85-90` (`_stat`) and `_milestone` (77-82): wrap agent reads in try/except returning defaults. Ladder rule: a ladder error never ends a game; `autoascend/ladder.py` stays stdlib-only.

### Unit tests with fakes, not NLE
**Source:** `tests/test_fight_heur.py:1-10` (`SimpleNamespace(mname=...)` tuples); `tests/test_game.py:157` `SimpleNamespace(stats_logger=SimpleNamespace(log_event=lambda name: None))` for agent fakes. Gate: `uv run pytest -q -m ""` green before and after.

### Stats counters
**Source:** `agent.py:757` `self.stats_logger.log_event('...')`; read back with `_stat(wrapper, name)` into `GameResult`.

### Bench naming and merging
**Source:** RESEARCH Pattern 2. Baseline by explicit code SHA, never `main`; merge `better` branches with `git merge --ff-only`; docs edits in separate later commits.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Human food/prayer study script (`nld.db` + `nle.dataset.TtyrecDataset`) | utility | batch | Nothing in the repo reads NLD; use RESEARCH Code Example 7 (offline read-only, no committed file required) |
| Rest-to-full strategy | strategy | event-driven | Only partial analog (global_logic.py:843-851 rest hook, dropped `rest-on-elbereth` stash); design from RESEARCH Pattern 4 |
| Zapper handling (lined-up check, step off line) | utility | transform | `fight_heur.py` has own wand path simulation (`simulate_wand_path`) but only for the hero's wands; reuse its geometry helpers, not its logic |

## Metadata

**Analog search scope:** `nethack_screensaver/`, `autoascend/` (agent, global_logic, combat, soko_solver), `bench/`, `scripts/`, `tests/`
**Files scanned:** ~25 read or grepped
**Pattern extraction date:** 2026-10-22
