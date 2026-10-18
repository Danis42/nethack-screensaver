# Secret Strategies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every game secretly gets one of four bot strategies (pilgrim, daredevil, sightseer, treasure), each a different milestone route toward a different ending; logged per game and optionally revealed on the game-over screen.

**Architecture:** The bot's fixed milestone order becomes a `Plan` (ordered list of `Milestone`s plus an index) in a new `autoascend/plans.py`, which also defines the four named strategies. `GlobalLogic` reads the current milestone from the plan and asks it to advance. `run_game` picks a strategy, passes its plan down through `EnvWrapper` → `Agent` → `GlobalLogic`, and reports `strategy`, `gender`, `outcome` in `GameResult`. The player shows an optional reveal line on the final screen.

**Tech Stack:** Python 3.13, NLE 1.3.0, vendored AutoAscend, pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-10-18-secret-strategies-design.md`

## Global Constraints

- Strategy names, exactly: `pilgrim`, `daredevil`, `sightseer`, `treasure`.
- Target endings, exactly: pilgrim `ascension`, daredevil `escape in celestial disgrace`, sightseer `escape the dungeon`, treasure `escape with loot`.
- Config: `strategy = "random"` (or a name), `reveal_goal = false`; invalid values warn and fall back, like `role`.
- Outcome strings: `escaped`, `escaped with loot`, `escaped empty-handed`, `died on Dlvl N`, `crashed`.
- Reveal format: `Secret goal: <Name> · <target ending> · <outcome>`; a successful escape outcome is upper-cased with `!`.
- No Amulet / Quest / Castle / Gehennom code. Strategy never shown during play.
- Every plan starts with `BE_ON_FIRST_LEVEL`. Pacing's `farming` stays "milestone is BE_ON_FIRST_LEVEL".
- Run all tests before and after: `uv run pytest -q -m ""`. Local git only: never push or add remotes.

## Review Focus

- An escape ending must never be logged as a death: NLE reports it with end_status DEATH and the text "escaped the dungeon [max level N]".
- A plan's last milestone (`GO_DOWN`, `LEAVE_DUNGEON`) must never advance past the end of the list (IndexError would crash every long game).
- Sokoban dropped as unsolvable in `treasure` must skip `LOOT_SOKOBAN_PRIZE`, not loot an unsolved level forever.
- `LEAVE_DUNGEON` when the Dlvl 1 upstairs is not known or not reachable must keep exploring Dlvl 1, not crash.
- Old `games.jsonl` records without the new fields, and an agent that crashed before `GlobalLogic` existed, must still produce a valid result/log line.

---

## File Structure

- Create `autoascend/plans.py`: `Milestone` enum (moved from global_logic), `Plan`, `StrategySpec`, `STRATEGIES`.
- Modify `autoascend/global_logic.py`: import `Milestone`/`Plan`; plan-driven loop; new milestone branches; `leave_dungeon` strategy.
- Modify `autoascend/agent.py:39-67`: `plan` parameter passed to `GlobalLogic`.
- Modify `autoascend/env_wrapper.py:80-93`: escape parsing.
- Modify `nethack_screensaver/game.py`: strategy pick, loot check, outcome, new `GameResult` fields.
- Modify `nethack_screensaver/config.py`, `nethack_screensaver/render.py`, `nethack_screensaver/player.py`: config keys, reveal line.
- Modify `scripts/benchmark.py`, `README.md`, `autoascend/PORTING.md`.
- Tests: `tests/test_plans.py` (new), `tests/test_env_wrapper.py`, `tests/test_game.py`, `tests/test_config.py`, `tests/test_render.py`, `tests/test_gamelog.py`; fixture `tests/data/escaped_tty_chars.npy`.

---

### Task 1: Recognise escape endings

**Files:**
- Modify: `autoascend/env_wrapper.py` (`_parse_end_reason`)
- Test: `tests/test_env_wrapper.py`
- Create: `tests/data/escaped_tty_chars.npy` (copy of the captured final screen)

**Interfaces:**
- Produces: `EnvWrapper._parse_end_reason(obs, info) -> str` returns `"ESCAPED: escaped the dungeon"` for an escape (status prefix `ESCAPED`, `[max level N]` stripped). Deaths unchanged.

- [ ] **Step 1: Add the fixture**

The final screen of a real escape was captured with NLE (reset, `<`, `y`); its text is
`... Agent-Bar-Orc-Mal-Cha escaped the dungeon [max level 1]. 15 [15]`.

```bash
cp /tmp/claude-1000/-home-user-screens/b28844e3-60c4-471e-a119-1d25817be534/scratchpad/escaped_tty_chars.npy tests/data/escaped_tty_chars.npy
```

If that file is gone, regenerate it:

```bash
uv run python - <<'EOF'
import numpy as np
from nle.env.tasks import NetHackChallenge
from nle.nethack import actions as A
e = NetHackChallenge(); e.reset()
o, *_ = e.step(e.actions.index(A.MiscDirection.UP))
o, *_ = e.step(e.actions.index(ord('y')))
np.save("tests/data/escaped_tty_chars.npy", o["tty_chars"])
EOF
```

- [ ] **Step 2: Write the failing test** (append to `tests/test_env_wrapper.py`)

```python
def test_escape_is_not_reported_as_death():
    obs = {"tty_chars": np.load(DATA / "escaped_tty_chars.npy")}
    reason = EnvWrapper(env=None)._parse_end_reason(obs, {"end_status": NLE.StepStatus.DEATH})
    assert reason == "ESCAPED: escaped the dungeon"
```

- [ ] **Step 3: Run it, expect FAIL**

Run: `uv run pytest tests/test_env_wrapper.py -q`
Expected: FAIL, got `'DEATH: escaped the dungeon [max level 1]'`.

- [ ] **Step 4: Implement** (in `_parse_end_reason`, replace the `return f'{status_name}: ...'` line)

```python
            cause = rest.strip().rstrip('.') or first.split(' in ')[0].strip()
            if cause.startswith('escaped'):
                # NLE reports escapes with end_status DEATH; the text says otherwise.
                return 'ESCAPED: ' + cause.split(' [')[0]
            return f'{status_name}: {cause[:1].lower()}{cause[1:]}'
```

- [ ] **Step 5: Run tests, expect PASS**

Run: `uv run pytest tests/test_env_wrapper.py -q` → 3 passed.

- [ ] **Step 6: Commit**

```bash
git add autoascend/env_wrapper.py tests/test_env_wrapper.py tests/data/escaped_tty_chars.npy
git commit -m "fix: report dungeon escapes as ESCAPED, not DEATH"
```

---

### Task 2: Plans and strategies

**Files:**
- Create: `autoascend/plans.py`
- Modify: `autoascend/global_logic.py` (remove the `Milestone` class at ~line 141, import it instead)
- Test: `tests/test_plans.py`

**Interfaces:**
- Produces:
  - `Milestone(IntEnum)`: existing members unchanged (`BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN, FIND_SOKOBAN, SOLVE_SOKOBAN, FIND_MINES_END, GO_DOWN`) plus `EXPLORE_MINETOWN, LOOT_SOKOBAN_PRIZE, RETURN_TO_SURFACE, LEAVE_DUNGEON`.
  - `Plan(milestones: Sequence[Milestone])`: `.current -> Milestone`, `.advance() -> None` (no-op on the last milestone), `.drop_sokoban() -> None` (advance; then also skip `LOOT_SOKOBAN_PRIZE` if it is current).
  - `StrategySpec(name: str, title: str, ending: str, milestones: tuple[Milestone, ...])` (frozen dataclass).
  - `STRATEGIES: dict[str, StrategySpec]` keyed by name; `DEFAULT_PLAN = STRATEGIES["pilgrim"].milestones`.
  - `global_logic.Milestone` keeps working (re-exported by import).

- [ ] **Step 1: Write the failing tests** (`tests/test_plans.py`)

```python
import pytest

from autoascend.plans import DEFAULT_PLAN, STRATEGIES, Milestone as M, Plan


def test_plan_walks_milestones_in_order():
    p = Plan([M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.GO_DOWN])
    seen = [p.current]
    for _ in range(2):
        p.advance()
        seen.append(p.current)
    assert seen == [M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.GO_DOWN]


def test_last_milestone_never_advances():
    p = Plan([M.BE_ON_FIRST_LEVEL, M.LEAVE_DUNGEON])
    for _ in range(5):
        p.advance()
    assert p.current == M.LEAVE_DUNGEON


def test_dropped_sokoban_skips_the_loot():
    p = Plan(STRATEGIES["treasure"].milestones)
    while p.current != M.SOLVE_SOKOBAN:
        p.advance()
    p.drop_sokoban()
    assert p.current == M.RETURN_TO_SURFACE


def test_dropped_sokoban_in_pilgrim_just_advances():
    p = Plan(STRATEGIES["pilgrim"].milestones)
    while p.current != M.SOLVE_SOKOBAN:
        p.advance()
    p.drop_sokoban()
    assert p.current == M.FIND_MINES_END


@pytest.mark.parametrize("name", ["pilgrim", "daredevil", "sightseer", "treasure"])
def test_every_strategy_starts_on_first_level(name):
    s = STRATEGIES[name]
    assert s.name == name and s.title and s.ending
    assert s.milestones[0] == M.BE_ON_FIRST_LEVEL


def test_endings_and_routes_match_spec():
    assert {n: s.ending for n, s in STRATEGIES.items()} == {
        "pilgrim": "ascension",
        "daredevil": "escape in celestial disgrace",
        "sightseer": "escape the dungeon",
        "treasure": "escape with loot",
    }
    assert STRATEGIES["daredevil"].milestones == (M.BE_ON_FIRST_LEVEL, M.GO_DOWN)
    assert STRATEGIES["sightseer"].milestones[-2:] == (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)
    assert DEFAULT_PLAN == STRATEGIES["pilgrim"].milestones


def test_global_logic_still_exports_milestone():
    from autoascend.global_logic import Milestone
    assert Milestone is M
```

- [ ] **Step 2: Run, expect FAIL** — `uv run pytest tests/test_plans.py -q` → `ModuleNotFoundError: autoascend.plans`.

- [ ] **Step 3: Implement `autoascend/plans.py`**

```python
"""Secret strategies: each is an ordered milestone plan aiming at one ending."""
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Sequence


class Milestone(IntEnum):
    BE_ON_FIRST_LEVEL = auto()
    FIND_GNOMISH_MINES = auto()
    FIND_MINETOWN = auto()
    FIND_SOKOBAN = auto()
    SOLVE_SOKOBAN = auto()
    FIND_MINES_END = auto()
    GO_DOWN = auto()
    EXPLORE_MINETOWN = auto()
    LOOT_SOKOBAN_PRIZE = auto()
    RETURN_TO_SURFACE = auto()
    LEAVE_DUNGEON = auto()


class Plan:
    def __init__(self, milestones: Sequence[Milestone]):
        self._milestones = tuple(milestones)
        self._index = 0

    @property
    def current(self) -> Milestone:
        return self._milestones[self._index]

    def advance(self) -> None:
        # The last milestone (GO_DOWN, LEAVE_DUNGEON) ends the game by itself.
        self._index = min(self._index + 1, len(self._milestones) - 1)

    def drop_sokoban(self) -> None:
        self.advance()
        if self.current == Milestone.LOOT_SOKOBAN_PRIZE:
            self.advance()


@dataclass(frozen=True)
class StrategySpec:
    name: str
    title: str
    ending: str
    milestones: tuple[Milestone, ...]


M = Milestone
STRATEGIES = {s.name: s for s in [
    StrategySpec("pilgrim", "Pilgrim", "ascension",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.FIND_MINETOWN, M.FIND_SOKOBAN,
                  M.SOLVE_SOKOBAN, M.FIND_MINES_END, M.GO_DOWN)),
    StrategySpec("daredevil", "Daredevil", "escape in celestial disgrace",
                 (M.BE_ON_FIRST_LEVEL, M.GO_DOWN)),
    StrategySpec("sightseer", "Sightseer", "escape the dungeon",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.FIND_MINETOWN, M.EXPLORE_MINETOWN,
                  M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)),
    StrategySpec("treasure", "Treasure hunter", "escape with loot",
                 (M.BE_ON_FIRST_LEVEL, M.FIND_SOKOBAN, M.SOLVE_SOKOBAN, M.LOOT_SOKOBAN_PRIZE,
                  M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)),
]}
DEFAULT_PLAN = STRATEGIES["pilgrim"].milestones
```

In `autoascend/global_logic.py`: delete the whole `class Milestone(IntEnum): ...` block (including its two commented-out members) and add to the imports:

```python
from .plans import DEFAULT_PLAN, Milestone, Plan
```

(`IntEnum, auto` stay imported if still used elsewhere in the file; remove them only if `grep -n "IntEnum\|auto()" autoascend/global_logic.py` shows no other use.)

- [ ] **Step 4: Run, expect PASS** — `uv run pytest -q` → all pass (existing tests import `Milestone` from `global_logic` via `game.py`).

- [ ] **Step 5: Commit**

```bash
git add autoascend/plans.py autoascend/global_logic.py tests/test_plans.py
git commit -m "feat: milestone plans and the four secret strategies"
```

---

### Task 3: Plan-driven GlobalLogic and the new milestones

**Files:**
- Modify: `autoascend/agent.py:39-40,67` (`plan` param)
- Modify: `autoascend/global_logic.py` (`__init__`, `milestone`, sokoban drop at ~line 314, `current_strategy` loop, `global_strategy`, new `leave_dungeon`)
- Test: `tests/test_game.py` (slow)

**Interfaces:**
- Consumes: `Plan`, `Milestone`, `DEFAULT_PLAN` from Task 2.
- Produces:
  - `Agent(env, ..., plan: Sequence[Milestone] | None = None)`; `None` means `DEFAULT_PLAN`.
  - `GlobalLogic(agent, plan=None)`; `GlobalLogic.milestone` becomes a read-only property returning `self.plan.current` (callers such as `game._farming` and the sokoban preempt keep working).
  - Constants `TOWN_TURNS = 1000`, `LOOT_TURNS = 1500` in `global_logic.py`.

- [ ] **Step 1: Write the failing slow test** (append to `tests/test_game.py`)

```python
@pytest.mark.slow
def test_leave_dungeon_plan_escapes(monkeypatch):
    from autoascend.plans import STRATEGIES, Milestone as M, StrategySpec
    monkeypatch.setitem(STRATEGIES, "test_escape",
                        StrategySpec("test_escape", "Test", "escape the dungeon",
                                     (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)))
    result = game.run_game(strategy="test_escape", max_steps=2000)
    assert result.end_reason == "ESCAPED: escaped the dungeon", result.end_reason
```

(This needs `run_game(strategy=...)` from Task 4; the test is written here and goes green at the end of Task 4. In this task, verify with the manual check in Step 5.)

- [ ] **Step 2: Agent plumbing** (`autoascend/agent.py`)

```python
    def __init__(self, env, seed=0, verbose=False, panic_on_errors=False,
                 rl_model_to_train=None, rl_model_training_comm=(None, None), plan=None):
```

and at line 67:

```python
        self.global_logic = GlobalLogic(self, plan)
```

- [ ] **Step 3: GlobalLogic uses the plan** (`autoascend/global_logic.py`)

Constants near the top (after imports):

```python
TOWN_TURNS = 1000  # sightseer: turns to look around Minetown
LOOT_TURNS = 1500  # treasure: turns on the top Sokoban level to clear the zoo and loot
```

`__init__`:

```python
    def __init__(self, agent, plan=None):
        self.agent = agent
        self.plan = Plan(plan or DEFAULT_PLAN)
        self._arrived = {}  # milestone -> turn it first stood on its target level
```

(keep the remaining existing lines of `__init__`, delete `self.milestone = Milestone(1)`), and add:

```python
    @property
    def milestone(self):
        return self.plan.current

    def _stayed(self, key, turns):
        """True once the bot has been on level `key` for `turns` turns in this milestone."""
        if self.agent.current_level().key() != key:
            return False
        start = self._arrived.setdefault(self.milestone, self.agent.blstats.time)
        return self.agent.blstats.time - start >= turns

    def has_prize(self):
        """Sokoban prize (or an unidentified item that may be it) in the inventory."""
        prizes = {O.from_name('bag of holding'), O.from_name('amulet of reflection')}
        return any(prizes & set(item.objs) for item in flatten_items(self.agent.inventory.items))
```

Sokoban drop (~line 314), replace `self.milestone = Milestone(int(self.milestone) + 1)` with:

```python
            self.plan.drop_sokoban()
```

In `current_strategy`, replace the advancement block

```python
            if condition():
                self.milestone = Milestone(int(self.milestone) + 1)
                continue
```

with

```python
            if condition():
                self.plan.advance()
                continue
```

and add these branches before the final `else:` of the milestone `if/elif` chain:

```python
            elif self.milestone == Milestone.EXPLORE_MINETOWN:
                condition = lambda: self._stayed(self.minetown_level, TOWN_TURNS)
                level = self.minetown_level

            elif self.milestone == Milestone.LOOT_SOKOBAN_PRIZE:
                condition = lambda: self.has_prize() or self._stayed((Level.SOKOBAN, 1), LOOT_TURNS)
                level = (Level.SOKOBAN, 1)

            elif self.milestone in (Milestone.RETURN_TO_SURFACE, Milestone.LEAVE_DUNGEON):
                # LEAVE_DUNGEON never completes here: leave_dungeon() ends the game.
                condition = lambda: self.milestone == Milestone.RETURN_TO_SURFACE and \
                                    self.agent.current_level().key() == (Level.DUNGEONS_OF_DOOM, 1)
                level = (Level.DUNGEONS_OF_DOOM, 1)
```

New strategy method (next to `solve_sokoban_strategy`):

```python
    @Strategy.wrap
    def leave_dungeon(self):
        if self.agent.current_level().key() != (Level.DUNGEONS_OF_DOOM, 1):
            yield False
        stairs = [(y, x) for y, x in zip(*utils.isin(self.agent.current_level().objects, G.STAIR_UP).nonzero())
                  if self.agent.bfs()[y, x] != -1]
        if not stairs:
            yield False  # upstairs not known or not reachable yet: keep exploring Dlvl 1
        yield True
        y, x = stairs[0]
        self.agent.go_to(y, x)
        # "Beware, there will be no return! Still climb?" is answered 'y' by Agent.update.
        self.agent.direction('<')
```

In `global_strategy`, add one preempt right after the sokoban one:

```python
            .preempt(self.agent, [
                self.leave_dungeon().condition(lambda: self.milestone == Milestone.LEAVE_DUNGEON)
            ])
```

- [ ] **Step 4: Run fast tests** — `uv run pytest -q` → all pass.

- [ ] **Step 5: Manual check of the escape path** (run_game has no `strategy` yet)

```bash
uv run python - <<'EOF' 2>&1 | grep -v Warn
from autoascend.plans import Milestone as M
from nethack_screensaver import game
import autoascend.env_wrapper as ew
orig = ew.EnvWrapper.__init__
def init(self, *a, **k):
    orig(self, *a, **k)
    self.agent_args["plan"] = (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)
ew.EnvWrapper.__init__ = init
print(game.run_game(max_steps=2000).end_reason)
EOF
```

Expected: `ESCAPED: escaped the dungeon`.

- [ ] **Step 6: Commit**

```bash
git add autoascend/agent.py autoascend/global_logic.py tests/test_game.py
git commit -m "feat: plan-driven milestones with Minetown, Sokoban loot, return and escape"
```

---

### Task 4: Strategy pick, outcome and result fields

**Files:**
- Modify: `nethack_screensaver/game.py`
- Test: `tests/test_game.py`, `tests/test_gamelog.py`

**Interfaces:**
- Consumes: `STRATEGIES` (Task 2), `Agent(plan=...)` (Task 3), `"ESCAPED: ..."` end reasons (Task 1).
- Produces:
  - `run_game(role=None, on_frame=None, max_steps=None, watchdog_seconds=60.0, strategy: str | None = None) -> GameResult`; `None` → `random.choice(sorted(STRATEGIES))`.
  - `GameResult` gains, after `end_reason`: `strategy: str = "?"`, `gender: str = "?"`, `outcome: str = ""`.
  - `outcome(strategy: str, end_reason: str, max_depth: int, has_loot: bool) -> str`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_game.py`)

```python
@pytest.mark.parametrize("strategy,reason,loot,expected", [
    ("sightseer", "ESCAPED: escaped the dungeon", False, "escaped"),
    ("treasure", "ESCAPED: escaped the dungeon", True, "escaped with loot"),
    ("treasure", "ESCAPED: escaped the dungeon", False, "escaped empty-handed"),
    ("daredevil", "DEATH: killed by a soldier ant", False, "died on Dlvl 7"),
    ("pilgrim", "exception: AssertionError: x", False, "crashed"),
    ("pilgrim", "watchdog", False, "crashed"),
])
def test_outcome(strategy, reason, loot, expected):
    assert game.outcome(strategy, reason, 7, loot) == expected


def test_random_pick_covers_all_strategies():
    from autoascend.plans import STRATEGIES
    picks = {game._pick_strategy(None) for _ in range(200)}
    assert picks == set(STRATEGIES)
    assert game._pick_strategy("sightseer") == "sightseer"


def test_loot_check_survives_missing_agent():
    class Wrapper:
        agent = None
    assert game._has_loot(Wrapper()) is False
```

Append to `tests/test_gamelog.py`:

```python
def test_new_fields_are_logged(tmp_path):
    p = tmp_path / "g.jsonl"
    r = GameResult("val", "hum", "law", 3, 10, 5, "ESCAPED: escaped the dungeon",
                   strategy="sightseer", gender="fem", outcome="escaped")
    append_result(p, r)
    rec = json.loads(p.read_text())
    assert (rec["strategy"], rec["gender"], rec["outcome"]) == ("sightseer", "fem", "escaped")


def test_old_records_without_new_fields_still_count(tmp_path):
    p = tmp_path / "g.jsonl"
    p.write_text('{"role": "val", "max_depth": 4, "end_reason": "DEATH: x"}\n')
    assert read_stats(p).games == 1 and read_stats(p).best_depth == 4
```

(add `import json` and `read_stats` to the imports of `tests/test_gamelog.py` if not present.)

- [ ] **Step 2: Run, expect FAIL** — `uv run pytest tests/test_game.py tests/test_gamelog.py -q` → `AttributeError: outcome` / `TypeError: unexpected keyword 'strategy'`.

- [ ] **Step 3: Implement** (`nethack_screensaver/game.py`)

Imports: `import random`, `from autoascend.plans import STRATEGIES`.

```python
@dataclass
class GameResult:
    role: str
    race: str
    alignment: str
    max_depth: int
    turns: int
    score: int
    end_reason: str
    strategy: str = "?"
    gender: str = "?"
    outcome: str = ""


def _pick_strategy(strategy: str | None) -> str:
    return strategy if strategy is not None else random.choice(sorted(STRATEGIES))


def outcome(strategy: str, end_reason: str, max_depth: int, has_loot: bool) -> str:
    if end_reason.startswith("ESCAPED"):
        if strategy == "treasure":
            return "escaped with loot" if has_loot else "escaped empty-handed"
        return "escaped"
    if end_reason.startswith("exception") or end_reason == "watchdog":
        return "crashed"
    return f"died on Dlvl {max_depth}"


def _has_loot(wrapper) -> bool:
    try:
        return wrapper.agent.global_logic.has_prize()
    except AttributeError:  # agent never started or crashed before its inventory existed
        return False
```

In `run_game`: add parameter `strategy: str | None = None`; before creating the wrapper:

```python
    strategy = _pick_strategy(strategy)
```

and pass the plan:

```python
    wrapper = EnvWrapper(env, on_step=on_step, step_limit=max_steps, role=role,
                         agent_args=dict(panic_on_errors=False, verbose=False,
                                         plan=STRATEGIES[strategy].milestones))
```

Return:

```python
    role_s, race, gender, alignment = _character(wrapper)
    return GameResult(role_s, race, alignment, max_depth, turns, int(wrapper.score), end_reason,
                      strategy=strategy, gender=gender,
                      outcome=outcome(strategy, end_reason, max_depth, _has_loot(wrapper)))
```

- [ ] **Step 4: Run tests** — `uv run pytest -q -m ""` → all pass, including `test_leave_dungeon_plan_escapes` from Task 3.

- [ ] **Step 5: Commit**

```bash
git add nethack_screensaver/game.py tests/test_game.py tests/test_gamelog.py
git commit -m "feat: secretly pick a strategy per game and log strategy, gender, outcome"
```

---

### Task 5: Config and the optional reveal

**Files:**
- Modify: `nethack_screensaver/config.py`, `nethack_screensaver/render.py`, `nethack_screensaver/player.py`, `README.md`
- Test: `tests/test_config.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: `GameResult.strategy/outcome` (Task 4), `STRATEGIES` (Task 2).
- Produces: `Config.strategy: str = "random"`, `Config.reveal_goal: bool = False`; `format_reveal(strategy: str, outcome: str) -> str` in `render.py`.

- [ ] **Step 1: Write the failing tests**

`tests/test_config.py`:

```python
def test_strategy_and_reveal(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text('strategy = "treasure"\nreveal_goal = true\n')
    c = load_config(p)
    assert c.strategy == "treasure" and c.reveal_goal is True
    p.write_text('strategy = "speedrun"\nreveal_goal = "yes"\n')
    assert load_config(p) == Config()
    err = capsys.readouterr().err
    assert "strategy" in err and "reveal_goal" in err
```

`tests/test_render.py` (add `format_reveal` to the import):

```python
def test_format_reveal():
    assert format_reveal("sightseer", "escaped") == "Secret goal: Sightseer · escape the dungeon · ESCAPED!"
    assert format_reveal("treasure", "escaped empty-handed") == \
        "Secret goal: Treasure hunter · escape with loot · ESCAPED EMPTY-HANDED!"
    assert format_reveal("daredevil", "died on Dlvl 11") == \
        "Secret goal: Daredevil · escape in celestial disgrace · died on Dlvl 11"
```

- [ ] **Step 2: Run, expect FAIL** — `uv run pytest tests/test_config.py tests/test_render.py -q`.

- [ ] **Step 3: Implement**

`config.py`: add fields and validation.

```python
    role: str = "random"
    strategy: str = "random"
    reveal_goal: bool = False
```

```python
from autoascend.plans import STRATEGIES  # cheap: autoascend/__init__.py and plans.py import nothing heavy
```

In `_valid`:

```python
    if name in ("status_line", "reveal_goal"):
        return isinstance(value, bool)
    if name == "strategy":
        return value == "random" or value in STRATEGIES
```

(replacing the existing `status_line` branch.)

`render.py`:

```python
from autoascend.plans import STRATEGIES  # at the top of render.py


def format_reveal(strategy: str, outcome: str) -> str:
    s = STRATEGIES[strategy]
    shown = outcome.upper() + "!" if outcome.startswith("escaped") else outcome
    return f"Secret goal: {s.title} · {s.ending} · {shown}"
```

`player.py`: keep the last frame and redraw it with the reveal.

In `main`, `state = {"depth": None, "turn": 0, "role": None, "obs": None}`; at the end of `on_frame` add `state["obs"] = obs`. Replace

```python
        result = run_game(role=role, on_frame=on_frame)
        append_result(log_path, result)
```

with

```python
        strategy = None if cfg.strategy == "random" else cfg.strategy
        result = run_game(role=role, on_frame=on_frame, strategy=strategy)
        append_result(log_path, result)
        if cfg.reveal_goal and state["obs"] is not None and result.strategy in STRATEGIES:
            obs = state["obs"]
            _write(out, renderer.frame(obs["tty_chars"], obs["tty_colors"], *_size(),
                                       status=format_reveal(result.strategy, result.outcome)))
```

with imports `from nethack_screensaver.render import Renderer, format_reveal, format_status` and `from autoascend.plans import STRATEGIES` at the top of `player.py` (cheap).

`git add` in Step 5 must not include `tests/test_plans.py` (unchanged in this task).

`README.md` config block: add

```toml
strategy = "random"  # secret goal per game: pilgrim daredevil sightseer treasure
reveal_goal = false  # true: show the secret goal on the game-over screen
```

and a short paragraph after the pacing one:

```markdown
Secret goals: each game secretly follows one strategy. Pilgrim (aims to ascend)
tours the Mines, Minetown and Sokoban, then dives; Daredevil (aims to escape in
celestial disgrace) dives straight down; Sightseer visits Minetown and climbs
back out of the dungeon; Treasure hunter solves Sokoban, loots its prize and
escapes. Only the two escapes are reachable for this bot. The log records each
game's `strategy` and `outcome`.
```

- [ ] **Step 4: Run tests** — `uv run pytest -q -m ""` → all pass.

- [ ] **Step 5: Commit**

```bash
git add nethack_screensaver/config.py nethack_screensaver/render.py nethack_screensaver/player.py README.md tests/test_config.py tests/test_render.py
git commit -m "feat: strategy and reveal_goal config, secret goal reveal on game over"
```

---

### Task 6: Per-strategy benchmark and acceptance run

**Files:**
- Modify: `scripts/benchmark.py`, `autoascend/PORTING.md`
- Test: `tests/test_game.py` (slow)

**Interfaces:**
- Consumes: `run_game(strategy=...)`, `GameResult.strategy/outcome`.

- [ ] **Step 1: Slow smoke tests** (append to `tests/test_game.py`)

```python
@pytest.mark.slow
@pytest.mark.parametrize("strategy", ["sightseer", "treasure"])
def test_escape_strategies_run(strategy):
    result = game.run_game(strategy=strategy, max_steps=3000)
    assert result.strategy == strategy
    assert not result.end_reason.startswith("exception"), result.end_reason
    assert result.outcome
```

- [ ] **Step 2: Benchmark flags and per-strategy summary** (`scripts/benchmark.py`)

```python
def _one(strategy):
    return run_game(watchdog_seconds=120, strategy=strategy)
```

```python
    ap.add_argument("--strategy", default=None,
                    help="pilgrim/daredevil/sightseer/treasure (default: random per game)")
```

```python
        for i, r in enumerate(pool.imap_unordered(_one, [args.strategy] * args.games), 1):
            results.append(r)
            print(f"[{i}/{args.games}] {r.strategy} {r.role} depth={r.max_depth} score={r.score} "
                  f"turns={r.turns} :: {r.outcome} :: {r.end_reason[:70]}", flush=True)
```

After the existing summary:

```python
    for name in sorted({r.strategy for r in results}):
        rs = [r for r in results if r.strategy == name]
        print(f"\n{name}: {len(rs)} games, median depth {statistics.median(r.max_depth for r in rs)}")
        for o, n in Counter(r.outcome.split(" on Dlvl")[0] for r in rs).most_common():
            print(f"  {n}x {o}")
```

- [ ] **Step 3: Run tests** — `uv run pytest -q -m ""` → all pass.

- [ ] **Step 4: Acceptance runs** (background, ~2 h total; 12 cores)

```bash
for s in pilgrim daredevil sightseer treasure; do
  uv run python scripts/benchmark.py -n 36 -j 12 --strategy $s 2>&1 | grep -v Warning > /tmp/claude-1000/-home-user-screens/b28844e3-60c4-471e-a119-1d25817be534/scratchpad/bench_$s.txt
done
```

Branch reach (Mines / Minetown / Sokoban) is not in `GameResult`. For criterion 2, use the scratch trace script, which records visited branches and Sokoban levels per game: in `/tmp/claude-1000/-home-user-screens/b28844e3-60c4-471e-a119-1d25817be534/scratchpad/scripts/trace_dlvl1.py` change `one(_)` to `one(strategy)`, call `run_game(on_frame=on_frame, watchdog_seconds=120, strategy=strategy)`, and map over `[sys.argv[2]] * n`; then run it per strategy, e.g. `uv run python <that path> 36 sightseer`. (Minetown itself is not visible in blstats; Mines depth ≥ 5-8 in `dungeons`/depth is the proxy.)

Check against spec acceptance:
1. sightseer and treasure have ≥1 `escaped…` outcome.
2. daredevil has the deepest median; sightseer the most Minetown visits; treasure reaches Sokoban far more than 2%.
3. pilgrim ≈ median Dlvl 5, Mines in about two thirds.
4. No new exception types versus the last benchmark.

If (1) fails, investigate with superpowers:systematic-debugging before tuning `TOWN_TURNS` / `LOOT_TURNS`.

- [ ] **Step 5: Record results** — add a "Strategies benchmark (2026-10-18)" section to `autoascend/PORTING.md` with the per-strategy summaries, and a line under Changes for `plans.py` and the escape parsing.

- [ ] **Step 6: Commit**

```bash
git add scripts/benchmark.py autoascend/PORTING.md tests/test_game.py
git commit -m "test: per-strategy benchmark and escape-strategy smoke tests"
```
