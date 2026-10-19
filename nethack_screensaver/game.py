"""Run one AutoAscend game on NLE, headless-capable."""
from __future__ import annotations

import random
import signal
from dataclasses import dataclass
from typing import Callable

import nle.nethack as nh
from nle.env.tasks import NetHackChallenge

from autoascend.env_wrapper import EnvWrapper
from autoascend.global_logic import Milestone
from autoascend.plans import STRATEGIES, choose_strategy

DEPTH = 12
TURN = 20
FARMING = (Milestone.BE_ON_FIRST_LEVEL,)


class WatchdogTimeout(KeyboardInterrupt):
    """Raised from SIGALRM; KeyboardInterrupt so the agent never swallows it."""


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
    milestone: str = "?"  # last milestone of the plan the bot reached
    elbereth: int = 0  # times the bot wrote Elbereth


def _strategy_and_plan(obs: dict, forced: str | None, rng=random) -> tuple[str, tuple]:
    """Pick the secret strategy once the character is known, tilted by role."""
    name = forced if forced is not None else choose_strategy(role_abbrev(obs).lower(), rng)
    return name, STRATEGIES[name].milestones


def outcome(strategy: str, end_reason: str, max_depth: int, has_loot: bool) -> str:
    if end_reason.startswith("ESCAPED"):
        if strategy == "treasure":
            return "escaped with loot" if has_loot else "escaped empty-handed"
        return "escaped"
    if end_reason.startswith("exception") or end_reason == "watchdog":
        return "crashed"
    if end_reason.startswith("DEATH"):
        return f"died on Dlvl {max_depth}"
    return f"ended on Dlvl {max_depth}"  # ABORTED (no progress), step limit, ...


def _milestone(wrapper) -> str:
    try:
        return wrapper.agent.global_logic.plan.current.name
    except AttributeError:  # agent never started
        return "?"


def _elbereth_count(wrapper) -> int:
    try:
        return wrapper.agent.stats_logger.get_stats_dict()["elbereth_write"]
    except Exception:  # agent never started
        return 0


def _has_loot(wrapper) -> bool:
    try:
        return wrapper.agent.global_logic.has_prize()
    except Exception:  # agent never started, or crashed with its inventory half-parsed
        return False


class _ScreenWatchdog:
    def __init__(self, seconds: float | None):
        self.seconds = seconds
        self._old = None

    def _fire(self, signum, frame):
        raise WatchdogTimeout()

    def __enter__(self):
        if self.seconds:
            self._old = signal.signal(signal.SIGALRM, self._fire)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def screen_changed(self):
        if self.seconds:
            signal.setitimer(signal.ITIMER_REAL, self.seconds)

    def __exit__(self, *exc):
        if self.seconds:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self._old)
        return False


def role_abbrev(obs: dict) -> str:
    bl = obs["blstats"]
    glyph = obs["glyphs"][bl[1], bl[0]]
    if not nh.glyph_is_monster(glyph):
        return "?"
    return nh.permonst(nh.glyph_to_mon(glyph)).mname[:3].capitalize()


def run_game(
    role: str | None = None,
    on_frame: Callable[[dict], None] | None = None,
    max_steps: int | None = None,
    watchdog_seconds: float | None = 60.0,
    strategy: str | None = None,
) -> GameResult:
    env = NetHackChallenge(no_progress_timeout=1000)
    max_depth = 1
    turns = 0
    prev_chars = None
    watchdog = _ScreenWatchdog(watchdog_seconds)

    def on_step(obs):
        nonlocal max_depth, turns, prev_chars
        # The final (game-over) observation has all-zero blstats; keep the last real values.
        max_depth = max(max_depth, int(obs["blstats"][DEPTH]))
        turns = max(turns, int(obs["blstats"][TURN]))
        chars = obs["tty_chars"]
        if prev_chars is None or not (chars == prev_chars).all():
            watchdog.screen_changed()
            prev_chars = chars.copy()
        if on_frame is not None:
            on_frame({**obs, "farming": _farming(wrapper)})

    chosen = {}

    def choose_plan(obs):
        chosen["strategy"], plan = _strategy_and_plan(obs, strategy)
        return plan

    wrapper = EnvWrapper(env, on_step=on_step, step_limit=max_steps, role=role, choose_plan=choose_plan,
                         agent_args=dict(panic_on_errors=False, verbose=False))
    try:
        with watchdog:
            wrapper.main()
        end_reason = wrapper.end_reason or "finished"
    except WatchdogTimeout:
        end_reason = "watchdog"
    except Exception as e:  # never let one bad game kill the screensaver
        end_reason = f"exception: {type(e).__name__}: {e}"
    finally:
        env.close()

    strategy = chosen.get("strategy", strategy or "?")  # "?" if the game never started
    role_s, race, gender, alignment = _character(wrapper)
    return GameResult(role_s, race, alignment, max_depth, turns, int(wrapper.score), end_reason,
                      strategy=strategy, gender=gender, milestone=_milestone(wrapper),
                      elbereth=_elbereth_count(wrapper),
                      outcome=outcome(strategy, end_reason, max_depth, _has_loot(wrapper)))


def _farming(wrapper) -> bool:
    logic = getattr(wrapper.agent, "global_logic", None)
    return logic is not None and logic.milestone in FARMING


def _character(wrapper) -> tuple[str, str, str, str]:
    try:
        parts = str(wrapper.agent.character).split()[0].split("-")
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    except Exception:
        pass
    return "?", "?", "?", "?"
