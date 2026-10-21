# Flee Upstairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In a fight, the bot climbs (or steps toward) a nearby up staircase when a fast insect (soldier ant, fire ant, giant ant, killer bee) is within 6 squares.

**Architecture:** One pure-ish decision function `flee_upstairs_action(agent, monsters)` in `autoascend/combat/fight_heur.py` returns fight actions like the existing `elbereth_action`; `Agent._fight2_perform_action` executes the two new actions; a stat counts climbs.

**Tech Stack:** Python 3.13, NLE 1.3.0, NumPy, pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-10-21-flee-upstairs-design.md`

## Global Constraints

- Values, verbatim: insects `('soldier ant', 'fire ant', 'giant ant', 'killer bee')`; sight 6 (monster distance as given by `get_visible_monsters`); stairs within 8 BFS steps; priorities `flee_up` 50, `flee_to` 40; cooldown 150 turns per level.
- Never on (Dungeons of Doom, 1); only in the Dungeons of Doom and the Gnomish Mines.
- `flee_to` only when the next square has no monster (`agent.monster_tracker.monster_mask`), because `Agent.move` raises AgentPanic on an occupied square.
- Whole suite before and after: `uv run pytest -q -m ""`.
- Branch `flee-upstairs` from `main`; never push; merging waits for the bench experiment.

## Review Focus

- Standing on the Dlvl 1 up staircase with an ant next to us must not climb (it would end the game as an escape) — tested.
- A staircase the BFS cannot reach (dis -1) must be ignored, not chosen — tested.
- The cooldown is per level key, so fleeing from Mines 3 does not block fleeing from Mines 4 — tested.
- `action_str` must not crash on the 1-tuple `('flee_up',)` (its fallback indexes `a[1]`) — tested.
- Numpy integer stair coordinates compared with the player's position tuple — tested by the on-stairs case.

---

### Task 1: Flee decision, execution and stat

**Files:**
- Modify: `autoascend/combat/fight_heur.py` (new constants and `flee_upstairs_action`; call it in `get_available_actions`)
- Modify: `autoascend/agent.py` (`Agent.__init__`: `self.fled_from = {}`; `_fight2_perform_action`: two new branches)
- Modify: `autoascend/combat/utils.py` (`action_str`: two new branches)
- Modify: `autoascend/stats_logger.py` (`_values`: `"flee_upstairs": 0`)
- Modify: `nethack_screensaver/game.py` (`GameResult.flee_upstairs: int = 0`, filled with `_stat(wrapper, "flee_upstairs")`)
- Test: `tests/test_flee_upstairs.py`

**Interfaces:**
- Produces: `fight_heur.FAST_INSECTS`, `FLEE_SIGHT = 6`, `FLEE_STEPS = 8`, `FLEE_COOLDOWN = 150`, `flee_upstairs_action(agent, monsters) -> list[tuple[float, tuple]]` returning `[(50, ('flee_up',))]`, `[(40, ('flee_to', y, x))]` or `[]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_flee_upstairs.py
from types import SimpleNamespace

import numpy as np

from autoascend.combat import fight_heur
from autoascend.combat.utils import action_str
from autoascend.glyph import C, MON, SS
from autoascend.level import Level


def fake_agent(pos=(10, 10), stairs=((10, 12),), key=(Level.DUNGEONS_OF_DOOM, 5), time=1000,
               fled_from=None, occupied=(), unreachable=False):
    objects = np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16)
    for y, x in stairs:
        objects[y, x] = SS.S_upstair
    yy, xx = np.mgrid[0:C.SIZE_Y, 0:C.SIZE_X]
    dis = np.maximum(abs(yy - pos[0]), abs(xx - pos[1]))
    if unreachable:
        for y, x in stairs:
            dis[y, x] = -1
    mask = np.zeros((C.SIZE_Y, C.SIZE_X), bool)
    for y, x in occupied:
        mask[y, x] = True
    level = SimpleNamespace(dungeon_number=key[0], level_number=key[1], key=lambda: key, objects=objects)

    def path(y1, x1, y2, x2):
        out = [(y1, x1)]
        while (y1, x1) != (y2, x2):
            y1 += int(np.sign(y2 - y1))
            x1 += int(np.sign(x2 - x1))
            out.append((y1, x1))
        return out

    return SimpleNamespace(blstats=SimpleNamespace(y=pos[0], x=pos[1], time=time),
                           current_level=lambda: level, bfs=lambda: dis, path=path,
                           monster_tracker=SimpleNamespace(monster_mask=mask),
                           fled_from=fled_from if fled_from is not None else {})


def monster(name, dist=2, y=10, x=8):
    glyph = MON.fn(name)
    return (dist, y, x, MON.permonst(glyph), glyph)


def test_climbs_when_standing_on_the_up_stairs():
    agent = fake_agent(pos=(10, 12))
    assert fight_heur.flee_upstairs_action(agent, [monster("soldier ant")]) == [(50, ('flee_up',))]


def test_steps_toward_near_stairs():
    agent = fake_agent(pos=(10, 10), stairs=((10, 12),))
    assert fight_heur.flee_upstairs_action(agent, [monster("killer bee")]) == [(40, ('flee_to', 10, 11))]


def test_no_flee_without_a_fast_insect_in_sight():
    agent = fake_agent(pos=(10, 12))
    assert fight_heur.flee_upstairs_action(agent, [monster("soldier ant", dist=7)]) == []
    assert fight_heur.flee_upstairs_action(agent, [monster("newt")]) == []
    assert fight_heur.flee_upstairs_action(agent, []) == []


def test_no_flee_where_going_up_is_wrong():
    ant = [monster("fire ant")]
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.DUNGEONS_OF_DOOM, 1)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.SOKOBAN, 2)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.QUEST, 1)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.GNOMISH_MINES, 1)), ant) \
        == [(50, ('flee_up',))]


def test_far_unreachable_or_blocked_stairs_are_ignored():
    ant = [monster("giant ant")]
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), stairs=((10, 19),)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), unreachable=True), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), occupied=((10, 11),)), ant) == []


def test_cooldown_is_per_level():
    ant = [monster("soldier ant")]
    key = (Level.GNOMISH_MINES, 3)
    recent = fake_agent(pos=(10, 12), key=key, time=1000, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(recent, ant) == []
    later = fake_agent(pos=(10, 12), key=key, time=1050, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(later, ant) == [(50, ('flee_up',))]
    other = fake_agent(pos=(10, 12), key=(Level.GNOMISH_MINES, 4), time=1000, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(other, ant) == [(50, ('flee_up',))]


def test_action_str_prints_flee_actions():
    assert action_str(None, (50, ('flee_up',))) == '50<'
    assert action_str(None, (40, ('flee_to', 3, 4))) == '40flee:3,4'
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_flee_upstairs.py -q`
Expected: FAIL with `AttributeError: module 'autoascend.combat.fight_heur' has no attribute 'flee_upstairs_action'`.

- [ ] **Step 3: Implement**

`autoascend/combat/fight_heur.py`: change `from ..utils import adjacent` to `from ..utils import adjacent, isin` (`autoascend/utils.py` defines `isin`) and add `from ..level import Level`. Then, after `elbereth_action`:

```python
# Surviving human players went upstairs five times as often as those these killed
# (NLD-NAO, 3.6 games; docs/superpowers/specs/2026-10-21-flee-upstairs-design.md).
FAST_INSECTS = ('soldier ant', 'fire ant', 'giant ant', 'killer bee')
FLEE_SIGHT = 6
FLEE_STEPS = 8
FLEE_COOLDOWN = 150


def flee_upstairs_action(agent, monsters):
    level = agent.current_level()
    if level.dungeon_number not in (Level.DUNGEONS_OF_DOOM, Level.GNOMISH_MINES) or \
            level.key() == (Level.DUNGEONS_OF_DOOM, 1):
        return []
    if agent.blstats.time - agent.fled_from.get(level.key(), -FLEE_COOLDOWN) < FLEE_COOLDOWN:
        return []
    if not any(mon.mname in FAST_INSECTS and dis <= FLEE_SIGHT for dis, _, _, mon, _ in monsters):
        return []
    here = (agent.blstats.y, agent.blstats.x)
    stairs = [(int(y), int(x)) for y, x in zip(*isin(level.objects, G.STAIR_UP).nonzero())]
    if here in stairs:
        return [(50, ('flee_up',))]
    dis = agent.bfs()
    reachable = [(dis[y, x], y, x) for y, x in stairs if 0 < dis[y, x] <= FLEE_STEPS]
    if not reachable:
        return []
    _, y, x = min(reachable)
    ny, nx = agent.path(agent.blstats.y, agent.blstats.x, y, x)[1]
    if agent.monster_tracker.monster_mask[ny, nx]:
        return []
    return [(40, ('flee_to', ny, nx))]
```

Note the cooldown default: with no entry, `time - (-150) >= 150` for any time ≥ 0, so the first flee is always allowed. In `get_available_actions`, after `actions.extend(wait_action(agent, monsters))`, add `actions.extend(flee_upstairs_action(agent, monsters))`.

`autoascend/agent.py`: in `Agent.__init__` (next to other per-game state such as `self._last_turn`), add `self.fled_from = {}  # level key -> turn the bot fled upstairs from it`. In `_fight2_perform_action`, before `raise NotImplementedError(best_action)`:

```python
        elif best_action[0] == 'flee_up':
            self.fled_from[self.current_level().key()] = self.blstats.time
            self.stats_logger.log_event('flee_upstairs')
            self.move('<')
            return wait_counter
        elif best_action[0] == 'flee_to':
            _, target_y, target_x = best_action
            self.move(target_y, target_x)
            return wait_counter
```

`autoascend/combat/utils.py` `action_str`, before the final `else`:

```python
    elif a[0] == 'flee_up':
        return f'{priority}<'
    elif a[0] == 'flee_to':
        return f'{priority}flee:{a[1]},{a[2]}'
```

`autoascend/stats_logger.py` `_values`: add `"flee_upstairs": 0,` after `"ladder_error": 0,`.

`nethack_screensaver/game.py`: `GameResult` gains `flee_upstairs: int = 0  # times the bot fled upstairs from fast insects` after `ladder_error`; `run_game` passes `flee_upstairs=_stat(wrapper, "flee_upstairs")`.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_flee_upstairs.py tests/test_fight_heur.py tests/test_game.py -q -m ""`
Expected: all pass. Then `uv run pytest -q -m ""` (before: 239 passed, 5 skipped, 5 xfailed, 1 xpassed on `main`).

- [ ] **Step 5: Commit**

```bash
git add autoascend/combat/fight_heur.py autoascend/agent.py autoascend/combat/utils.py autoascend/stats_logger.py nethack_screensaver/game.py tests/test_flee_upstairs.py
git commit -m "feat(fight): flee upstairs from fast insects, as surviving humans do"
```

### Task 2 (controller): experiment `rung2` vs `2653410`, merge only on a gain, record in PORTING.md.
