import os
import json
from dataclasses import asdict
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
        from autoascend.ladder import BY_KEY
        assert set(result.ladder) <= set(BY_KEY)
        json.dumps(asdict(result))  # the worker and the game log serialise results
        assert result.rung == max((BY_KEY[k].number for k in result.ladder), default=0)


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
    name, plan = game._strategy_and_plan(obs, "random")
    assert name in STRATEGIES and plan == STRATEGIES[name].milestones


def test_every_game_plays_the_ascension_route_by_default():
    from autoascend.plans import STRATEGIES
    obs = _start_obs("valkyrie", "Hello Agent, welcome to NetHack!")
    assert game._strategy_and_plan(obs, None) == ("pilgrim", STRATEGIES["pilgrim"].milestones)


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


def test_ladder_is_reported_and_survives_a_missing_agent():
    from types import SimpleNamespace

    from autoascend.ladder import Facts, Ladder
    ladder = Ladder()
    ladder.observe(Facts(turn=40, dungeon=2, level=1))
    wrapper = SimpleNamespace(agent=SimpleNamespace(global_logic=SimpleNamespace(ladder=ladder)))
    assert game._ladder(wrapper, "DEATH: killed by a newt", 900) == ({"mines": 40}, 1)
    assert game._ladder(wrapper, "DEATH: ascended to demigod-hood", 999) == ({"mines": 40, "ascended": 999}, 17)
    assert game._ladder(SimpleNamespace(agent=None), "exception: x", 3) == ({}, 0)


def test_a_seed_replays_the_same_game_start():
    def first_screen(seed):
        frames = []
        result = game.run_game(seed=seed, max_steps=50, on_frame=lambda obs: frames.append(obs["tty_chars"].copy()))
        return result, frames[0]
    r1, s1 = first_screen(17)
    r2, s2 = first_screen(17)
    r3, s3 = first_screen(18)
    assert (s1 == s2).all() and not (s1 == s3).all()
    assert r1.seed == 17 and (r1.role, r1.race) == (r2.role, r2.race)
    assert game.run_game.__defaults__ is not None  # stays callable without a seed


def test_a_seed_with_a_pinned_role_is_refused():
    with pytest.raises(ValueError):
        game.run_game(seed=3, role="val", max_steps=5)


# --- seed decides the moon; death-context observer ---------------------------------------------

def _fake_env_and_wrapper(monkeypatch):
    from types import SimpleNamespace
    calls = {"env_kwargs": None, "seeds": None}

    class FakeNethack:
        def set_initial_seeds(self, core, disp, reseed=False, lgen=None):
            calls["seeds"] = (core, disp, reseed)

    class FakeEnv:
        nethack = FakeNethack()

        def __init__(self, **kwargs):
            calls["env_kwargs"] = kwargs

        def close(self):
            pass

    class FakeWrapper:
        def __init__(self, env, **kwargs):
            self.end_reason = "fake"
            self.score = 0
            self.agent = None

        def main(self):
            return None

    monkeypatch.setattr(game, "NetHackChallenge", FakeEnv)
    monkeypatch.setattr(game, "EnvWrapper", FakeWrapper)
    return calls


def test_seeded_game_takes_the_moon_from_the_seed(monkeypatch):
    calls = _fake_env_and_wrapper(monkeypatch)
    game.run_game(seed=5)
    assert calls["env_kwargs"]["fix_moon_phase"] is True
    assert calls["seeds"] == (5, 5, False)


def test_seeded_game_pins_the_start_time(monkeypatch):
    from nethack_screensaver import fixed_clock
    _fake_env_and_wrapper(monkeypatch)
    monkeypatch.delenv(fixed_clock.ENV_VAR, raising=False)
    game.run_game(seed=5)
    assert os.environ[fixed_clock.ENV_VAR] == str(fixed_clock.seed_time(5))
    game.run_game()
    assert fixed_clock.ENV_VAR not in os.environ


def test_unseeded_game_keeps_the_real_moon(monkeypatch):
    calls = _fake_env_and_wrapper(monkeypatch)
    game.run_game()
    assert calls["env_kwargs"]["fix_moon_phase"] is False
    assert calls["seeds"] is None


def _fake_obs(text, turn=1, hp=10, max_hp=10, hunger=1, depth=1):
    import numpy as np
    tty = np.zeros((24, 80), dtype=np.uint8)
    tty[:] = ord(" ")
    raw = text.encode()
    tty[0, :len(raw)] = np.frombuffer(raw, dtype=np.uint8)
    bl = np.zeros(27, dtype=np.int64)
    bl[game.HP], bl[game.MAX_HP], bl[game.HUNGER], bl[game.DEPTH], bl[game.TURN] = hp, max_hp, hunger, depth, turn
    return {"tty_chars": tty, "blstats": bl}


def test_messages_keep_the_last_eight_distinct_lines():
    ctx = game._DeathContext()
    texts = ["a", "a", "", "b", "c", "c", "d", "", "e", "f", "g", "h", "i", "i", "j", "k"]
    for i, text in enumerate(texts):
        ctx.observe(_fake_obs(text, turn=i + 1))
    assert ctx.last_messages == ["d", "e", "f", "g", "h", "i", "j", "k"]


def test_prayer_is_recorded_with_the_messages_that_follow_it():
    ctx = game._DeathContext()
    ctx.observe(_fake_obs("You walk.", turn=3))
    ctx.observe(_fake_obs("You begin praying to Tyr.", turn=41))
    for i, text in enumerate(["l1", "l1", "", "l2", "l3", "l4", "l5"]):
        ctx.observe(_fake_obs(text, turn=42 + i))
    assert ctx.prayers == [[41, "l1 | l2 | l3 | l4"]]


def test_unfinished_prayer_is_kept_when_the_game_ends():
    ctx = game._DeathContext()
    ctx.observe(_fake_obs("You begin praying to Tyr.", turn=9))
    ctx.observe(_fake_obs("You are surrounded by a shimmering light.", turn=9))
    assert ctx.prayers == [[9, "You are surrounded by a shimmering light."]]


def test_monster_zaps_are_counted_but_own_zaps_are_not():
    ctx = game._DeathContext()
    for text in ["The gnome lord zaps a wand!", "The gnome lord zaps a wand!", "You zap a wand of striking.",
                 "The newt bites!"]:
        ctx.observe(_fake_obs(text))
    assert ctx.zaps_seen == 1


def test_end_state_ignores_the_all_zero_final_observation():
    import numpy as np
    ctx = game._DeathContext()
    ctx.observe(_fake_obs("hi", hp=7, max_hp=30, hunger=3, depth=6))
    final = _fake_obs("DYWYPI?")
    final["blstats"] = np.zeros(27, dtype=np.int64)
    ctx.observe(final)
    assert (ctx.hp_at_end, ctx.max_hp_at_end, ctx.hunger_at_end, ctx.depth_at_end) == (7, 30, 3, 6)


def _food_item(name="food ration", corpse=False):
    import nle.nethack as nh
    from types import SimpleNamespace
    return SimpleNamespace(category=nh.FOOD_CLASS, objs=[SimpleNamespace(name=name)],
                           is_corpse=lambda: corpse, is_container=lambda: False, monster_id=-1)


def test_food_at_end_counts_edible_items_and_survives_a_missing_agent():
    from types import SimpleNamespace
    import nle.nethack as nh
    items = [_food_item(), _food_item("apple"), _food_item("sprig of wolfsbane"), _food_item("newt corpse", True),
             SimpleNamespace(category=nh.WEAPON_CLASS, objs=[SimpleNamespace(name="dagger")],
                             is_corpse=lambda: False, is_container=lambda: False, monster_id=-1)]
    wrapper = SimpleNamespace(agent=SimpleNamespace(inventory=SimpleNamespace(items=items)))
    assert game._food_at_end(wrapper) == 2
    assert game._food_at_end(SimpleNamespace(agent=None)) == -1


def test_events_are_the_non_zero_counters():
    from types import SimpleNamespace
    from autoascend.stats_logger import StatsLogger
    logger = StatsLogger()
    logger.add("elbereth_write", 2)
    wrapper = SimpleNamespace(agent=SimpleNamespace(stats_logger=logger))
    assert game._events(wrapper) == {"elbereth_write": 2}
    assert game._events(SimpleNamespace(agent=None)) == {}
