import signal
import time

import pytest

from nethack_screensaver import game


def test_watchdog_fires_without_screen_change():
    wd = game._ScreenWatchdog(seconds=1)
    with pytest.raises(game.WatchdogTimeout):
        with wd:
            time.sleep(3)


def test_watchdog_rearmed_by_changes_does_not_fire():
    wd = game._ScreenWatchdog(seconds=1)
    with wd:
        for i in range(6):
            time.sleep(0.4)
            wd.screen_changed()
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0


@pytest.mark.slow
def test_headless_games_complete_without_exceptions():
    for _ in range(2):
        frames = []
        result = game.run_game(on_frame=lambda obs: frames.append(1), max_steps=3000)
        assert not result.end_reason.startswith("exception"), result.end_reason
        assert result.max_depth >= 1
        assert result.turns > 0
        assert result.role and result.race and result.alignment
        assert len(frames) > 10


@pytest.mark.slow
def test_pinned_role():
    result = game.run_game(role="val", max_steps=200)
    assert result.role == "val"


@pytest.mark.slow
def test_agent_makes_progress():
    # Full games take ~10-40 s headless; a healthy port gets past Dlvl 2 in at least one of four.
    depths = [game.run_game().max_depth for _ in range(4)]
    assert max(depths) >= 3, depths


@pytest.mark.slow
def test_leave_dungeon_plan_escapes(monkeypatch):
    from autoascend.plans import STRATEGIES, Milestone as M, StrategySpec
    monkeypatch.setitem(STRATEGIES, "test_escape",
                        StrategySpec("test_escape", "Test", "escape the dungeon",
                                     (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)))
    result = game.run_game(strategy="test_escape", max_steps=2000)
    assert result.end_reason == "ESCAPED: escaped the dungeon", result.end_reason


@pytest.mark.parametrize("strategy,reason,loot,expected", [
    ("sightseer", "ESCAPED: escaped the dungeon", False, "escaped"),
    ("treasure", "ESCAPED: escaped the dungeon", True, "escaped with loot"),
    ("treasure", "ESCAPED: escaped the dungeon", False, "escaped empty-handed"),
    ("daredevil", "DEATH: killed by a soldier ant", False, "died on Dlvl 7"),
    ("pilgrim", "exception: AssertionError: x", False, "crashed"),
    ("pilgrim", "watchdog", False, "crashed"),
    ("pilgrim", "ABORTED", False, "ended on Dlvl 7"),
    ("pilgrim", "steplimit", False, "ended on Dlvl 7"),
    ("pilgrim", "finished", False, "ended on Dlvl 7"),
])
def test_outcome(strategy, reason, loot, expected):
    assert game.outcome(strategy, reason, 7, loot) == expected


def _start_obs(role_name, welcome):
    import nle.nethack as nh
    import numpy as np
    mon = next(i for i in range(nh.NUMMONS) if nh.permonst(i).mname == role_name)
    glyphs = np.zeros((21, 79), dtype=np.int16)
    glyphs[5, 7] = nh.GLYPH_MON_OFF + mon
    chars = np.full((24, 80), ord(" "), dtype=np.uint8)
    chars[0, :len(welcome)] = np.frombuffer(welcome.encode(), dtype=np.uint8)
    bl = np.zeros(27, dtype=np.int64)
    bl[0], bl[1] = 7, 5
    return {"glyphs": glyphs, "tty_chars": chars, "blstats": bl}


def test_strategy_follows_the_role_or_the_forced_name():
    from autoascend.plans import STRATEGIES
    obs = _start_obs("valkyrie", "Hello Agent, welcome to NetHack!")
    assert game._strategy_and_plan(obs, "pilgrim") == ("pilgrim", STRATEGIES["pilgrim"].milestones)
    name, plan = game._strategy_and_plan(obs, None)
    assert name in STRATEGIES and plan == STRATEGIES[name].milestones


def test_loot_check_survives_missing_agent():
    class Wrapper:
        agent = None
    assert game._has_loot(Wrapper()) is False


@pytest.mark.slow
@pytest.mark.parametrize("strategy", ["sightseer", "treasure"])
def test_escape_strategies_run(strategy):
    milestones = []
    for _ in range(3):  # a game can die on Dlvl 1 before its plan moves on
        result = game.run_game(strategy=strategy, max_steps=3000)
        assert result.strategy == strategy
        assert not result.end_reason.startswith("exception"), result.end_reason
        assert result.outcome
        milestones.append(result.milestone)
        if result.milestone != "BE_ON_FIRST_LEVEL":
            break
    assert milestones[-1] != "BE_ON_FIRST_LEVEL", milestones


def test_loot_check_survives_broken_inventory():
    class Logic:
        def has_prize(self):
            raise ValueError("inventory parse failed")

    class Agent:
        global_logic = Logic()

    class Wrapper:
        agent = Agent()
    assert game._has_loot(Wrapper()) is False


def test_last_milestone_is_reported():
    from types import SimpleNamespace

    from autoascend.plans import Milestone as M, Plan
    plan = Plan([M.BE_ON_FIRST_LEVEL, M.GO_DOWN])
    plan.advance()
    wrapper = SimpleNamespace(agent=SimpleNamespace(global_logic=SimpleNamespace(plan=plan)))
    assert game._milestone(wrapper) == "GO_DOWN"
    assert game._milestone(SimpleNamespace(agent=None)) == "?"


def test_agent_recovers_from_bot_errors_but_not_from_the_watchdog():
    from types import SimpleNamespace
    from autoascend.agent import Agent
    stub = SimpleNamespace(panic_on_errors=game.AGENT_ARGS["panic_on_errors"], all_panics=[], verbose=False,
                           stats_logger=SimpleNamespace(log_event=lambda name: None))
    Agent.handle_exception(stub, AssertionError("TODO: nested containers"))  # upstream assert: replan
    assert len(stub.all_panics) == 1
    with pytest.raises(game.WatchdogTimeout):
        Agent.handle_exception(stub, game.WatchdogTimeout())
