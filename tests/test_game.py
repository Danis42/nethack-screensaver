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


@pytest.mark.slow
@pytest.mark.parametrize("strategy", ["sightseer", "treasure"])
def test_escape_strategies_run(strategy):
    result = game.run_game(strategy=strategy, max_steps=3000)
    assert result.strategy == strategy
    assert not result.end_reason.startswith("exception"), result.end_reason
    assert result.outcome
