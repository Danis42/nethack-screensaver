# Ascension Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every game records which of the 17 ascension-ladder rungs it reached (and when), and the bench server compares and shows those rungs next to the 687 real ascensions.

**Architecture:** A standard-library module `autoascend/ladder.py` holds the rung list and the detection rules over plain `Facts`. `GlobalLogic.update()` builds those facts each step and feeds a `Ladder`; `run_game` copies the result into `GameResult`. The bench imports the rung list for metrics, the summary table and the dashboard.

**Tech Stack:** Python 3.13, NumPy, NLE 1.3.0, pytest, `uv`; bench: stdlib HTTP server + plain JS page.

**Spec:** `docs/superpowers/specs/2026-10-21-ascension-ladder-design.md`

## Global Constraints

- `autoascend/ladder.py` imports only the standard library (the bench imports it).
- The bot's behaviour does not change; no strategy, milestone or check of the bot is edited.
- A ladder error never ends a game: it is counted once (`ladder_error` stat) and the ladder stops updating.
- Level numbers are `blstats` level numbers inside each dungeon; dungeon numbers 0 Doom, 1 Gehennom, 2 Mines, 3 Quest, 4 Sokoban, 5 Ludios, 6 Vlad, 7 Planes.
- Old stored games lack `ladder`/`rung` and must be skipped, not counted, by every new metric.
- Run the whole suite before and after: `uv run pytest -q -m ""`.
- Work on branch `ladder`; merge to local `main` when done and tested. Never push.

## Review Focus

- A rung reached while hallucinating (Medusa, water, drawbridge facts) must not be recorded — tested in Task 2.
- Arriving on Sokoban level 1 before the map is drawn (0 squares seen, no traps visible) must not count as solved — tested in Task 1 (`seen` threshold) and Task 2.
- Leaving Mines level 8 and coming back restarts the 1000-turn wait instead of summing visits — tested in Task 1.
- A game that crashes or hits the watchdog still reports the rungs it reached — tested in Task 2 (`_ladder` on a half-built wrapper).
- Old games without the fields and an empty reference set must not break the summary or the dashboard — tested in Task 3.

---

### Task 1: Ladder module

**Files:**
- Create: `autoascend/ladder.py`
- Test: `tests/test_ladder.py`

**Interfaces:**
- Produces: `RUNGS: tuple[Rung, ...]` with `Rung(number: int, key: str, title: str, yardstick_event: str | None)`; `BY_KEY: dict[str, Rung]`; `Facts` dataclass (fields below); `Ladder()` with `.observe(facts: Facts) -> None`, `.finish(end_reason: str, turn: int) -> None`, `.highest() -> int`, `.reached: dict[str, int]`; constants `MINES_END_WAIT = 1000`, `VIBRATION = "You feel a strange vibration"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ladder.py
import pytest

from autoascend.ladder import BY_KEY, RUNGS, Facts, Ladder, MINES_END_WAIT

DOOM, GEHENNOM, MINES, QUEST, SOKOBAN, LUDIOS, VLAD, PLANES = range(8)


def reached(*steps):
    ladder = Ladder()
    for facts in steps:
        ladder.observe(facts)
    return ladder


def test_rungs_are_numbered_in_order_with_unique_keys():
    assert [r.number for r in RUNGS] == list(range(1, 18))
    assert len(BY_KEY) == 17
    assert RUNGS[0].key == "mines" and RUNGS[-1].key == "ascended"


@pytest.mark.parametrize("dungeon, level, key", [
    (MINES, 1, "mines"), (SOKOBAN, 4, "sokoban"), (QUEST, 1, "quest"), (GEHENNOM, 1, "gehennom"),
    (VLAD, 1, "vlad"), (PLANES, 5, "planes"), (DOOM, 15, "dlvl15"),
])
def test_rungs_from_the_dungeon_number(dungeon, level, key):
    assert key in reached(Facts(turn=7, dungeon=dungeon, level=level)).reached


def test_astral_is_planes_level_one_and_dlvl15_only_counts_in_the_main_dungeon():
    ladder = reached(Facts(turn=1, dungeon=PLANES, level=1), Facts(turn=2, dungeon=GEHENNOM, level=20))
    assert {"planes", "astral"} <= set(ladder.reached)
    assert "dlvl15" not in ladder.reached
    assert "dlvl15" not in reached(Facts(turn=1, dungeon=DOOM, level=14)).reached


def test_rungs_the_bot_notices():
    ladder = reached(Facts(turn=5, dungeon=MINES, level=3, minetown_seen=True),
                     Facts(turn=9, dungeon=DOOM, level=6, oracle_seen=True))
    assert ladder.reached["minetown"] == 5 and ladder.reached["oracle"] == 9


def test_sokoban_solved_needs_the_top_level_drawn_and_no_trap_left():
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=40, sokoban_traps=False)).reached
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=300, sokoban_traps=True)).reached
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=2, sokoban_seen=300, sokoban_traps=False)).reached
    assert "sokoban_solved" in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=300, sokoban_traps=False)).reached


def test_mines_end_is_level_nine_or_a_level_eight_without_down_stairs():
    assert "mines_end" in reached(Facts(turn=1, dungeon=MINES, level=9)).reached
    stay = [Facts(turn=t, dungeon=MINES, level=8) for t in (100, 100 + MINES_END_WAIT)]
    assert reached(*stay).reached["mines_end"] == 100 + MINES_END_WAIT
    early = [Facts(turn=t, dungeon=MINES, level=8) for t in (100, 99 + MINES_END_WAIT)]
    assert "mines_end" not in reached(*early).reached
    stairs = [Facts(turn=t, dungeon=MINES, level=8, down_stairs_seen=True) for t in (100, 5000)]
    assert "mines_end" not in reached(*stairs).reached


def test_leaving_mines_level_eight_restarts_the_wait():
    visits = [Facts(turn=100, dungeon=MINES, level=8), Facts(turn=900, dungeon=MINES, level=7),
              Facts(turn=1000, dungeon=MINES, level=8), Facts(turn=1500, dungeon=MINES, level=8)]
    assert "mines_end" not in reached(*visits).reached


def test_medusa_and_castle_proxies():
    assert "medusa" in reached(Facts(turn=1, dungeon=DOOM, level=22, medusa_seen=True)).reached
    assert "medusa" in reached(Facts(turn=1, dungeon=DOOM, level=23, water_share=0.5)).reached
    assert "medusa" not in reached(Facts(turn=1, dungeon=DOOM, level=12, water_share=0.5)).reached
    assert "medusa" not in reached(Facts(turn=1, dungeon=DOOM, level=23, water_share=0.2)).reached
    assert "castle" in reached(Facts(turn=1, dungeon=DOOM, level=27, drawbridge_seen=True)).reached
    assert "castle" not in reached(Facts(turn=1, dungeon=GEHENNOM, level=3, drawbridge_seen=True)).reached


def test_wizard_tower_and_invocation_proxies():
    book = Facts(turn=1, dungeon=GEHENNOM, level=12, inventory=("a papyrus spellbook", "the Book of the Dead"))
    assert "wizard_tower" in reached(book).reached
    vibration = Facts(turn=2, dungeon=GEHENNOM, level=20, message="You feel a strange vibration under your feet.")
    assert "invocation" not in reached(vibration).reached
    assert "invocation" in reached(vibration, Facts(turn=3, dungeon=GEHENNOM, level=21)).reached
    assert "invocation" not in reached(Facts(turn=3, dungeon=GEHENNOM, level=21)).reached


def test_first_turn_is_kept_and_highest_rung_is_reported():
    ladder = reached(Facts(turn=10, dungeon=MINES, level=1), Facts(turn=20, dungeon=MINES, level=2),
                     Facts(turn=30, dungeon=SOKOBAN, level=4))
    assert ladder.reached == {"mines": 10, "sokoban": 30}
    assert ladder.highest() == 4
    assert Ladder().highest() == 0


def test_finish_adds_ascended_only_for_an_ascension():
    ladder = Ladder()
    ladder.finish("DEATH: killed by a newt", 500)
    assert ladder.reached == {}
    ladder.finish("ASCENDED: ascended to demigod-hood", 53000)
    assert ladder.reached == {"ascended": 53000} and ladder.highest() == 17
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ladder.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'autoascend.ladder'`

- [ ] **Step 3: Write the module**

```python
# autoascend/ladder.py
"""The ascension ladder: 17 rungs from the Gnomish Mines to an ascension (docs/ROADMAP.md).

Standard library only, so the bench server can import the rung list. The bot hands over
plain Facts once per step; no glyph or agent code lives here. Level numbers are NetHack's
level numbers inside each dungeon (Sokoban 1 is its top level, Astral is Planes level 1)."""
from dataclasses import dataclass

DOOM, GEHENNOM, MINES, QUEST, SOKOBAN, LUDIOS, VLAD, PLANES = range(8)  # dungeon.def order
MINES_END_WAIT = 1000  # turns on Mines level 8 without a down staircase before it counts as the bottom
SOKOBAN_DRAWN = 100  # squares seen before "no trap left" means anything (Sokoban levels are lit)
VIBRATION = "You feel a strange vibration"


@dataclass(frozen=True)
class Rung:
    number: int
    key: str
    title: str
    yardstick_event: str | None  # first-time event in real ascensions' dumplogs, if there is one


RUNGS = tuple(Rung(i + 1, *r) for i, r in enumerate([
    ("mines", "Gnomish Mines", "entered the Gnomish Mines"),
    ("minetown", "Minetown", "reached Mine Town"),
    ("oracle", "Oracle", None),
    ("sokoban", "Sokoban", "entered Sokoban"),
    ("sokoban_solved", "Sokoban solved", "completed 4th Sokoban level"),
    ("mines_end", "Mines' End", "acquired the Mines' End luckstone"),
    ("dlvl15", "Dlvl 15+", None),
    ("quest", "Quest", "entered Home 1, the Quest"),
    ("medusa", "Medusa", "killed Medusa"),
    ("castle", "Castle", None),
    ("gehennom", "Gehennom", "entered Gehennom"),
    ("vlad", "Vlad's Tower", "destroyed Vlad the Impaler"),
    ("wizard_tower", "Wizard's Tower", "acquired the Book of the Dead"),
    ("invocation", "Invocation", "performed the invocation"),
    ("planes", "Elemental Planes", "entered the Elemental Planes"),
    ("astral", "Astral Plane", "entered the Astral Plane"),
    ("ascended", "Ascended", "ascended"),
]))
BY_KEY = {r.key: r for r in RUNGS}


@dataclass(frozen=True)
class Facts:
    turn: int
    dungeon: int
    level: int
    oracle_seen: bool = False
    minetown_seen: bool = False
    sokoban_seen: int = 0  # squares seen on the current level
    sokoban_traps: bool = True  # a trap glyph is left on the current level
    medusa_seen: bool = False
    water_share: float = 0.0  # share of the seen squares that are water
    drawbridge_seen: bool = False
    down_stairs_seen: bool = False
    inventory: tuple[str, ...] = ()
    message: str = ""


@dataclass
class _Memory:
    here: tuple[int, int] | None = None
    arrived: int = 0  # turn the bot arrived on `here`
    vibration_level: int | None = None  # Gehennom level of the vibrating square


def _mines_end(f, m):
    if f.dungeon != MINES:
        return False
    return f.level >= 9 or (f.level == 8 and not f.down_stairs_seen and f.turn - m.arrived >= MINES_END_WAIT)


DETECTORS = {
    "mines": lambda f, m: f.dungeon == MINES,
    "minetown": lambda f, m: f.minetown_seen,
    "oracle": lambda f, m: f.oracle_seen,
    "sokoban": lambda f, m: f.dungeon == SOKOBAN,
    "sokoban_solved": lambda f, m: (f.dungeon, f.level) == (SOKOBAN, 1) and f.sokoban_seen >= SOKOBAN_DRAWN
                                   and not f.sokoban_traps,
    "mines_end": _mines_end,
    "dlvl15": lambda f, m: f.dungeon == DOOM and f.level >= 15,
    "quest": lambda f, m: f.dungeon == QUEST,
    "medusa": lambda f, m: f.dungeon == DOOM and f.level >= 21 and (f.medusa_seen or f.water_share > 1 / 3),
    "castle": lambda f, m: f.dungeon == DOOM and f.drawbridge_seen,
    "gehennom": lambda f, m: f.dungeon == GEHENNOM,
    "vlad": lambda f, m: f.dungeon == VLAD,
    "wizard_tower": lambda f, m: any("Book of the Dead" in name for name in f.inventory),
    "invocation": lambda f, m: f.dungeon == GEHENNOM and m.vibration_level is not None
                               and f.level > m.vibration_level,
    "planes": lambda f, m: f.dungeon == PLANES,
    "astral": lambda f, m: (f.dungeon, f.level) == (PLANES, 1),
    "ascended": lambda f, m: False,  # only the end of the game tells, see Ladder.finish
}


class Ladder:
    def __init__(self):
        self.reached = {}  # rung key -> turn first reached
        self._memory = _Memory()

    def observe(self, facts: Facts) -> None:
        m = self._memory
        here = (facts.dungeon, facts.level)
        if here != m.here:
            m.here, m.arrived = here, facts.turn
        if facts.dungeon == GEHENNOM and VIBRATION in facts.message:
            m.vibration_level = facts.level
        for rung in RUNGS:
            if rung.key not in self.reached and DETECTORS[rung.key](facts, m):
                self.reached[rung.key] = facts.turn

    def finish(self, end_reason: str, turn: int) -> None:
        if "ascended" in end_reason.lower():
            self.reached.setdefault("ascended", turn)

    def highest(self) -> int:
        return max((BY_KEY[k].number for k in self.reached), default=0)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_ladder.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add autoascend/ladder.py tests/test_ladder.py
git commit -m "feat(ladder): rungs of the ascension ladder and their detection rules"
```

---

### Task 2: Record the ladder in every game

**Files:**
- Modify: `autoascend/global_logic.py` (imports; `GlobalLogic.__init__` near line 200; `update()` near line 267)
- Modify: `autoascend/stats_logger.py` (`_values`: add `"ladder_error": 0`)
- Modify: `nethack_screensaver/game.py` (`GameResult`; `run_game` return; new `_ladder` helper next to `_stat`)
- Test: `tests/test_game.py`, `tests/test_ladder.py`

**Interfaces:**
- Consumes: `Facts`, `Ladder` from Task 1.
- Produces: `GlobalLogic.ladder: Ladder`; `GlobalLogic.ladder_facts() -> Facts`; `GameResult.ladder: dict[str, int]` and `GameResult.rung: int`; `game._ladder(wrapper, end_reason: str, turns: int) -> tuple[dict[str, int], int]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_game.py`:

```python
def test_ladder_is_reported_and_survives_a_missing_agent():
    from types import SimpleNamespace

    from autoascend.ladder import Facts, Ladder
    ladder = Ladder()
    ladder.observe(Facts(turn=40, dungeon=2, level=1))
    wrapper = SimpleNamespace(agent=SimpleNamespace(global_logic=SimpleNamespace(ladder=ladder)))
    assert game._ladder(wrapper, "DEATH: killed by a newt", 900) == ({"mines": 40}, 1)
    assert game._ladder(wrapper, "ASCENDED: ascended", 999) == ({"mines": 40, "ascended": 999}, 17)
    assert game._ladder(SimpleNamespace(agent=None), "exception: x", 3) == ({}, 0)
```

In `test_headless_games_complete_without_exceptions`, after `assert len(frames) > 10`, add:

```python
        from autoascend.ladder import BY_KEY
        assert set(result.ladder) <= set(BY_KEY)
        assert result.rung == max((BY_KEY[k].number for k in result.ladder), default=0)
```

Append to `tests/test_ladder.py` (facts from a real `GlobalLogic` on a fake agent, including hallucination):

```python
import numpy as np


def _fake_logic(hallu=False, objects=None, seen=None, glyphs=None, key=(0, 22)):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    from autoascend.glyph import C
    logic = GlobalLogic.__new__(GlobalLogic)
    level = SimpleNamespace(dungeon_number=key[0], level_number=key[1], key=lambda: key,
                            objects=objects if objects is not None else np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16),
                            seen=seen if seen is not None else np.ones((C.SIZE_Y, C.SIZE_X), bool))
    logic.agent = SimpleNamespace(
        current_level=lambda: level, blstats=SimpleNamespace(time=123),
        character=SimpleNamespace(prop=SimpleNamespace(hallu=hallu)),
        glyphs=glyphs if glyphs is not None else np.zeros((C.SIZE_Y, C.SIZE_X), np.int16),
        inventory=SimpleNamespace(items=[]), message="")
    logic.oracle_level = logic.minetown_level = None
    return logic


def test_facts_see_water_and_medusa_but_not_while_hallucinating():
    from autoascend.glyph import C, MON, SS
    objects = np.full((C.SIZE_Y, C.SIZE_X), SS.S_pool, np.int16)
    glyphs = np.zeros((C.SIZE_Y, C.SIZE_X), np.int16)
    glyphs[3, 3] = MON.fn('Medusa')
    facts = _fake_logic(objects=objects, glyphs=glyphs).ladder_facts()
    assert facts.turn == 123 and (facts.dungeon, facts.level) == (0, 22)
    assert facts.water_share == 1.0 and facts.medusa_seen
    tripping = _fake_logic(hallu=True, objects=objects, glyphs=glyphs).ladder_facts()
    assert tripping.water_share == 0.0 and not tripping.medusa_seen and not tripping.drawbridge_seen


def test_facts_on_an_undrawn_sokoban_top_level_are_not_solved():
    from autoascend.glyph import C
    facts = _fake_logic(key=(4, 1), seen=np.zeros((C.SIZE_Y, C.SIZE_X), bool)).ladder_facts()
    assert facts.sokoban_seen == 0
    assert "sokoban_solved" not in reached(facts).reached
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ladder.py tests/test_game.py -q -m ""`
Expected: FAIL — `AttributeError: ... has no attribute 'ladder_facts'` and `module 'nethack_screensaver.game' has no attribute '_ladder'`.

- [ ] **Step 3: Implement**

`autoascend/stats_logger.py`, in `_values` after `"drop_gold": 0,`:

```python
            "ladder_error": 0,
```

`autoascend/global_logic.py`, imports (after `from .item.item_priority_base import ItemPriorityBase`):

```python
from .ladder import Facts, Ladder
```

Below the imports, next to the other module constants:

```python
WATER = frozenset({SS.S_pool, SS.S_water})
DRAWBRIDGE = frozenset({SS.S_vodbridge, SS.S_hodbridge, SS.S_vcdbridge, SS.S_hcdbridge})
MEDUSA = frozenset({MON.fn('Medusa')})
```

In `GlobalLogic.__init__`, after `self.minetown_level = None`:

```python
        self.ladder = Ladder()
        self._ladder_broken = False
```

At the end of `update()` (after the Minetown block, outside the `if not hallu` block):

```python
        if not self._ladder_broken:
            try:
                self.ladder.observe(self.ladder_facts())
            except Exception:  # measuring must never end a game
                self._ladder_broken = True
                self.agent.stats_logger.log_event('ladder_error')
```

New method after `update()`:

```python
    def ladder_facts(self):
        """What the ascension ladder needs to know about this step (see ladder.py)."""
        level = self.agent.current_level()
        hallu = self.agent.character.prop.hallu
        seen = int(level.seen.sum())
        water = int((utils.isin(level.objects, WATER) & level.seen).sum())
        return Facts(
            turn=self.agent.blstats.time, dungeon=level.dungeon_number, level=level.level_number,
            oracle_seen=self.oracle_level is not None, minetown_seen=self.minetown_level is not None,
            sokoban_seen=seen, sokoban_traps=bool(utils.isin(level.objects, G.TRAPS).any()),
            medusa_seen=not hallu and bool(utils.isin(self.agent.glyphs, MEDUSA).any()),
            water_share=0.0 if hallu or not seen else water / seen,
            drawbridge_seen=not hallu and bool(utils.isin(level.objects, DRAWBRIDGE).any()),
            down_stairs_seen=bool(utils.isin(level.objects, G.STAIR_DOWN).any()),
            inventory=tuple(item.text for item in flatten_items(self.agent.inventory.items)),
            message=self.agent.message)
```

`nethack_screensaver/game.py`: change `from dataclasses import dataclass` to `from dataclasses import dataclass, field` (check the existing import line), and add to `GameResult` after `unsticks`:

```python
    ladder: dict = field(default_factory=dict)  # ascension-ladder rung key -> first turn (autoascend/ladder.py)
    rung: int = 0  # highest ladder rung reached
```

New helper after `_stat`:

```python
def _ladder(wrapper, end_reason: str, turns: int) -> tuple[dict, int]:
    try:
        ladder = wrapper.agent.global_logic.ladder
    except AttributeError:  # agent never started
        return {}, 0
    ladder.finish(end_reason, turns)
    return dict(ladder.reached), ladder.highest()
```

In `run_game`, before `return GameResult(...)`:

```python
    ladder, rung = _ladder(wrapper, end_reason, turns)
```

and add `ladder=ladder, rung=rung,` to the `GameResult(...)` keyword arguments (after `unsticks=...`).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_ladder.py tests/test_game.py tests/test_gamelog.py tests/test_stats_logger.py -q -m ""`
Expected: all pass (the real games take a minute or two).

- [ ] **Step 5: Commit**

```bash
git add autoascend/global_logic.py autoascend/stats_logger.py nethack_screensaver/game.py tests/test_game.py tests/test_ladder.py
git commit -m "feat(ladder): record the rungs each game reaches in GameResult"
```

---

### Task 3: Bench metrics, ladder table and dashboard

**Files:**
- Modify: `bench/metrics.py` (`METRICS`)
- Modify: `bench/report.py` (`summary`, new `ladder_rows`)
- Modify: `bench/server.py` (`App.__init__`, new `App.yardstick`, `results`, `dashboard`)
- Modify: `bench/static/index.html` (`renderDashboard`)
- Test: `tests/test_bench_metrics.py`, `tests/test_bench_server.py`

**Interfaces:**
- Consumes: `RUNGS` from Task 1; stored games with `ladder: dict[str, int]` and `rung: int` from Task 2.
- Produces: metrics `rung` (median) and `rung1`…`rung17` (rates); `report.ladder_rows(games, yardstick=None) -> list[dict]` with keys `rung, key, title, hits, n, median_turn, yardstick_turn`; `report.summary(games, yardstick=None)` adds `"ladder"`; `App.yardstick() -> dict[str, float]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bench_metrics.py`:

```python
from bench.report import ladder_rows


def test_rung_metrics_skip_games_without_a_ladder():
    games = [_g(rung=2, ladder={"mines": 900, "minetown": 3000}), _g(rung=0, ladder={}), _g()]
    assert evaluate(METRICS["rung1"], games) == {"n": 2, "skipped": 1, "hits": 1, "rate": 0.5}
    assert evaluate(METRICS["rung3"], games)["hits"] == 0
    assert evaluate(METRICS["rung"], games)["median"] == 1
    assert METRICS["rung2"].description == "reached rung 2+ (Minetown)"
    assert "rung17" in METRICS


def test_ladder_rows_compare_with_the_yardstick():
    games = [_g(rung=4, ladder={"mines": 1000, "sokoban": 8000}), _g(rung=1, ladder={"mines": 2000}), _g()]
    rows = {r["key"]: r for r in ladder_rows(games, {"entered the Gnomish Mines": 1173})}
    assert len(rows) == 17
    assert rows["mines"] == {"rung": 1, "key": "mines", "title": "Gnomish Mines", "hits": 2, "n": 2,
                             "median_turn": 1500, "yardstick_turn": 1173}
    assert rows["oracle"]["hits"] == 1 and rows["oracle"]["median_turn"] is None  # rung 4 counts as 3+
    assert rows["ascended"]["hits"] == 0 and rows["ascended"]["yardstick_turn"] is None
    assert summary(games)["ladder"][0]["n"] == 2
    assert summary([])["ladder"][0]["n"] == 0
```

Append to `tests/test_bench_server.py`:

```python
def test_results_carry_the_ladder_even_without_reference_ascensions(bench_app):
    assert bench_app.yardstick() == {}
    rows = bench_app.results("main")["ladder"]
    assert [r["rung"] for r in rows] == list(range(1, 18))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_bench_metrics.py tests/test_bench_server.py -q`
Expected: FAIL — `ImportError: cannot import name 'ladder_rows'` (collection error).

- [ ] **Step 3: Implement**

`bench/metrics.py`: add `from autoascend.ladder import RUNGS` after the `typing` import, and change the end of the `METRICS` list from

```python
    Metric("score", "score", "median", lambda g: g["score"]),
]}
```

to

```python
    Metric("score", "score", "median", lambda g: g["score"]),
    Metric("rung", "highest ascension-ladder rung", "median", lambda g: g["rung"]),
] + [Metric(f"rung{r.number}", f"reached rung {r.number}+ ({r.title})", "rate",
            lambda g, n=r.number: g["rung"] >= n) for r in RUNGS]}
```

`bench/report.py`: add `import statistics` and `from autoascend.ladder import RUNGS` to the imports, add the function before `summary`:

```python
def ladder_rows(games, yardstick=None):
    """Per rung: games reaching it or higher, our median first turn, the real ascenders' median turn."""
    yardstick = yardstick or {}
    laddered = [g for g in games if "ladder" in g]  # older commits did not record it
    rows = []
    for r in RUNGS:
        turns = [g["ladder"][r.key] for g in laddered if r.key in g["ladder"]]
        rows.append({"rung": r.number, "key": r.key, "title": r.title,
                     "hits": sum(g["rung"] >= r.number for g in laddered), "n": len(laddered),
                     "median_turn": statistics.median(turns) if turns else None,
                     "yardstick_turn": yardstick.get(r.yardstick_event)})
    return rows
```

and change `def summary(games):` to `def summary(games, yardstick=None):`, adding to its returned dict (after `"metrics": ...`):

```python
        "ladder": ladder_rows(games, yardstick),
```

`bench/server.py`: in `App.__init__` add `self._yardstick = (None, {})`. New method after `reference_summary`:

```python
    def yardstick(self):
        """Median first turn of each timeline event in the real ascensions (cached per import state)."""
        refs = self.store.references()
        state = (len(refs), sum(1 for r in refs if r["dumplog"]))
        if self._yardstick[0] != state:
            from . import reference
            milestones = reference.summary(refs).get("milestones", [])
            self._yardstick = (state, {m["event"]: m["median_turn"] for m in milestones})
        return self._yardstick[1]
```

In `results`, change `**report.summary(games)` to `**report.summary(games, self.yardstick())`; in `dashboard`, change `**report.summary(self.store.games(sha))` to `**report.summary(self.store.games(sha), self.yardstick())`.

`bench/static/index.html`, in `renderDashboard`: after the `const outcomes = ...;` line add

```js
  const ladder = (d.ladder || []).map(r => [r.rung, esc(r.title), r.n ? pct(r.hits / r.n) : '–', `${r.hits}/${r.n}`,
    r.median_turn ?? '–', r.yardstick_turn ?? '–']);
```

and after the `'<h3>Rates</h3>' + ...` line insert

```js
    + '<h3>Ascension ladder</h3>' + table(['#', 'rung', 'reached (or higher)', 'games', 'our median turn', 'ascenders median turn'], ladder)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_bench_metrics.py tests/test_bench_server.py tests/test_bench_e2e.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add bench/metrics.py bench/report.py bench/server.py bench/static/index.html tests/test_bench_metrics.py tests/test_bench_server.py
git commit -m "feat(bench): ascension-ladder metrics, table and yardstick turns"
```

---

### Task 4: Docs, full suite, merge, baseline

**Files:**
- Create: `docs/ASCENSION-GUIDE.md`
- Modify: `docs/ROADMAP.md` (sub-project 0 status), `autoascend/PORTING.md` (ladder baseline), `docs/STATUS.md` and `handoff.txt` (copy)

- [ ] **Step 1: Write `docs/ASCENSION-GUIDE.md`** — the standard route in 12 steps as agreed in chat (early game: survive Dlvl 1-4, Mines to Minetown, Sokoban, Mines' End luckstone, safe corpses and food; midgame: magic resistance and reflection, AC, Medusa, Castle wand of wishing, Quest from XL 14; late game: Vlad's, Wizard's Tower, invocation, Amulet, Planes, Astral), each step naming its ladder rung and roadmap sub-project, with the yardstick numbers from `docs/STATUS.md` and links to the NetHack wiki pages (Standard strategy, Ascension, Magic resistance, Reflection, Sokoban, Mines' End, Medusa's Island, Castle, Quest, Gehennom, Elemental Planes, Astral Plane).

- [ ] **Step 2: Full suite**

Run: `uv run pytest -q -m ""`
Expected: all pass (previous count 215 plus the new tests).

- [ ] **Step 3: Commit and merge**

```bash
git add docs/ASCENSION-GUIDE.md
git commit -m "docs: ascension guide mapped to the ladder"
git checkout main && git merge --no-ff ladder -m "Merge branch 'ladder': ascension ladder (sub-project 0)"
```

- [ ] **Step 4: Baseline on the bench server**

Start the server if it is not running (`uv run screens-bench serve`, background), then start a 576-game baseline of `main` (MCP `bench_baseline` or `uv run screens-bench baseline main`), and run `uv run screens-bench wait <job>` in the background. Research NetHack tactics for sub-project 1 while it runs.

- [ ] **Step 5: Check and record**

Check with `bench_results main`: Mines reached in roughly two thirds of games, Sokoban rarely, almost nothing above rung 7, `ladder_error` never logged (`bench_games main where="end_reason LIKE 'exception%'"` shows no ladder-related crash). Write the ladder table into `autoascend/PORTING.md`, mark sub-project 0 done in `docs/ROADMAP.md`, update `docs/STATUS.md` and copy it to `handoff.txt` (`\cp -f docs/STATUS.md handoff.txt`), commit.
