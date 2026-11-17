"""Run one AutoAscend game on NLE, headless-capable."""
from __future__ import annotations

import random
import re
import signal
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import nle.nethack as nh
from nle.env.tasks import NetHackChallenge

from autoascend.env_wrapper import EnvWrapper
from autoascend.global_logic import Milestone
from autoascend.glyph import MON
from autoascend.item import flatten_items
from autoascend.plans import DEFAULT_STRATEGY, STRATEGIES, choose_strategy, plan_for, race_from_welcome
from nethack_screensaver import dungeon_truth, fixed_clock, snapshots, staging

HP = 10
MAX_HP = 11
DEPTH = 12
TURN = 20
HUNGER = 21
DUNGEON_NUMBER = 23
LEVEL_NUMBER = 24
WATCHDOG_FRAMES = 12  # innermost frames kept from a watchdog-ended game's stack
XP_LEVEL = 18
FARMING = (Milestone.BE_ON_FIRST_LEVEL,)


# panic_on_errors=True turns upstream assertions into AgentPanic: the bot replans instead of
# crashing; its cyclic-panic guard and NLE's no-progress timeout still end a stuck game.
AGENT_ARGS = dict(panic_on_errors=True, verbose=False)
# Until the first ascension every game is a human Monk: neutral, so Mines natives are hostile, which makes them
# food and experience. Chosen by the character A/B (02-CHARACTER-PREREG.md, job 21). "@" brings random ones back.
CHARACTER = "mon-hum-mal-neu"


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
    xp_level: int = 0  # highest experience level
    panics: int = 0  # times the bot replanned after a panic (incl. recovered errors)
    stuck_diving: int = 0  # 2500-turn spells of diving in the main dungeon without finding a way down
    unsticks: int = 0  # turns the bot let pass because NetHack kept refusing an action
    seed: int | None = None  # NetHack core/display seed of a seeded (bench) game
    lgen: int | None = None  # NLE level-generation seed of a bench lgen game; None = off
    ladder: dict = field(default_factory=dict)  # ascension-ladder rung key -> first turn (autoascend/ladder.py)
    rung: int = 0  # highest ladder rung reached
    ladder_error: int = 0  # 1 when the ladder broke mid-game (values incomplete)
    last_messages: list = field(default_factory=list)  # last 8 distinct message lines, oldest first
    prayers: list = field(default_factory=list)  # [turn, the next 4 message lines joined with " | "] per prayer
    zaps_seen: int = 0  # distinct message lines where a monster zapped something
    hp_at_end: int = 0  # from the last observation whose blstats are not all zero
    max_hp_at_end: int = 0
    hunger_at_end: int = 0
    depth_at_end: int = 0
    dungeon_at_end: int = 0  # NetHack dungeon number (0 Dungeons of Doom, 2 Gnomish Mines, ...)
    level_at_end: int = 0  # level number inside that dungeon
    food_at_end: int = -1  # edible food items in the inventory after the game, -1 if unreadable
    events: dict = field(default_factory=dict)  # the bot's non-zero event counters
    stuck_reports: list = field(default_factory=list)  # one row per stuck-watch firing (autoascend/stuck.py)
    watchdog_stack: list = field(default_factory=list)  # "dir/file.py:line function", innermost last
    stage: str | None = None  # staged (wizard-mode) game: never mixed into natural-play rates
    snapshots: dict = field(default_factory=dict)  # hero stats per depth/rung/end (nethack_screensaver/snapshots.py)


def _strategy_and_plan(obs: dict, forced: str | None, rng=random) -> tuple[str, tuple]:
    """Pick the strategy once the character is known: the ascension route unless forced;
    "random" tilts the mix of all plans by role. The route still depends on the race."""
    screen = "\n".join(bytes(row).decode(errors="replace").rstrip() for row in obs["tty_chars"])
    if forced == "random":
        name = choose_strategy(role_abbrev(obs).lower(), rng)
    else:
        name = forced or DEFAULT_STRATEGY
    return name, plan_for(name, race_from_welcome(screen))


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


def _stat(wrapper, name: str) -> int:
    try:
        return wrapper.agent.stats_logger.get_stats_dict()[name]
    except Exception:  # agent never started
        return 0


def _ladder(wrapper, end_reason: str, turns: int) -> tuple[dict, int]:
    try:
        ladder = wrapper.agent.global_logic.ladder
    except AttributeError:  # agent never started
        return {}, 0
    ladder.finish(end_reason, turns)
    return dict(ladder.reached), ladder.highest()


def _reached(wrapper) -> tuple:
    """Rung keys the ladder has seen so far (read only; empty before the agent exists)."""
    try:
        return tuple(wrapper.agent.global_logic.ladder.reached)
    except Exception:
        return ()


def _has_loot(wrapper) -> bool:
    try:
        return wrapper.agent.global_logic.has_prize()
    except Exception:  # agent never started, or crashed with its inventory half-parsed
        return False


_ZAPS = re.compile(r"\bzaps\b")
_PRAYING = "You begin praying to"
_PRAYER_LINES = 4


def _edible_food(item) -> bool:
    # same rule as autoascend.agent.Agent.edible_inventory_food (kept in step by hand: touching the
    # agent here would risk changing its behaviour)
    return (item.category == nh.FOOD_CLASS and item.objs[0].name != "sprig of wolfsbane" and
            (not item.is_corpse() or
             item.monster_id in [MON.from_name(n) - nh.GLYPH_MON_OFF for n in ("lizard", "lichen")]))


class _DeathContext:
    """Records how a game ended. It sees observations only (never the wrapper or the agent), so it
    cannot act on the game; the bench judges games it runs inside."""

    def __init__(self, keep: int = 8):
        self.keep = keep
        self.last_messages: list[str] = []
        self.zaps_seen = 0
        self.hp_at_end = self.max_hp_at_end = self.hunger_at_end = self.depth_at_end = 0
        self.dungeon_at_end = self.level_at_end = 0
        self._prayers: list[list] = []  # [turn, lines]
        self._row0 = None

    @property
    def prayers(self) -> list:
        return [[turn, " | ".join(lines)] for turn, lines in self._prayers]

    def observe(self, obs):
        bl = obs["blstats"]
        if bl.any():  # the final (game-over) observation is all zero
            self.hp_at_end, self.max_hp_at_end = int(bl[HP]), int(bl[MAX_HP])
            self.hunger_at_end, self.depth_at_end = int(bl[HUNGER]), int(bl[DEPTH])
            self.dungeon_at_end, self.level_at_end = int(bl[DUNGEON_NUMBER]), int(bl[LEVEL_NUMBER])
        row = obs["tty_chars"][0]
        if self._row0 is not None and (row == self._row0).all():
            return
        self._row0 = row.copy()
        line = bytes(row).decode(errors="replace").strip()
        if not line or (self.last_messages and self.last_messages[-1] == line):
            return
        for turn, lines in self._prayers:
            if len(lines) < _PRAYER_LINES:
                lines.append(line)
        if _PRAYING in line:
            self._prayers.append([int(bl[TURN]), []])
        if _ZAPS.search(line) and not line.startswith("You"):
            self.zaps_seen += 1
        self.last_messages.append(line)
        del self.last_messages[:-self.keep]


def _give_ladder_truth(wrapper, env) -> bool:
    """Hand the real Mines' End level to the ladder (measuring only, never to the bot's decisions).

    False until the agent exists; True once handed over or found unreadable (counted, game goes on)."""
    agent = getattr(wrapper, "agent", None)
    if agent is None:
        return False
    try:
        seeds = type(env.nethack).get_current_seeds(env.nethack)[:2]
        agent.global_logic.truth_mines_end_level = dungeon_truth.read(seeds).mines_end[1]
    except Exception:  # the ladder falls back to its proxy
        agent.stats_logger.log_event("ladder_truth_error")
    return True


def _food_at_end(wrapper) -> int:
    try:
        return sum(1 for item in flatten_items(wrapper.agent.inventory.items) if _edible_food(item))
    except Exception:  # agent never started, or crashed with its inventory half-parsed
        return -1


def _stack(exc: BaseException) -> list:
    """Where the game was when the watchdog fired: the innermost frames of the interrupted stack."""
    frames = traceback.extract_tb(exc.__traceback__)[-WATCHDOG_FRAMES:]
    return [f"{Path(f.filename).parent.name}/{Path(f.filename).name}:{f.lineno} {f.name}" for f in frames]


def _stuck_reports(wrapper) -> list:
    try:
        return list(wrapper.agent.global_logic.stuck_reports)
    except Exception:  # agent never started
        return []


def _events(wrapper) -> dict:
    try:
        return wrapper.agent.stats_logger.counters()
    except Exception:  # agent never started
        return {}


class _ScreenWatchdog:
    def __init__(self, seconds: float | None):
        self.seconds = seconds
        self._old = None
        self._turn = None
        self._turn_since = 0.0

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

    def check_turn(self, turn: int, now: float | None = None):
        """A hang can keep the screen changing (a panic loop on a menu); game turns cannot. Raises
        WatchdogTimeout when the turn has not moved for `seconds` of wall time."""
        if not self.seconds:
            return
        now = time.monotonic() if now is None else now
        if turn != self._turn:
            self._turn, self._turn_since = turn, now
        elif now - self._turn_since > self.seconds:
            raise WatchdogTimeout()

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
    seed: int | None = None,
    stage: str | None = None,
    lgen: int | None = None,
) -> GameResult:
    if lgen is not None and seed is None:
        raise ValueError("lgen needs a seed")
    if lgen == 0:
        raise ValueError("lgen 0 means off in the NLE fork (screens-nh5 cb9d6572f); pass a nonzero value")
    if seed is not None and role is not None:
        # the wrapper resets until the role matches; with a fixed seed every reset is the same game
        raise ValueError("a seeded game cannot pin the role")
    # fix_moon_phase: a seeded game takes moon phase, Friday the 13th and night from the seed, not from
    # today's date; an unseeded screensaver game keeps the real clock (NLE 1.3.0 reads it otherwise)
    # fixed_clock.pin: a seeded game also sees a start time derived from the seed (NetHack picks shopkeeper
    # names from it, which fix_moon_phase does not cover); takes effect where the fixed_clock shim is preloaded
    fixed_clock.pin(seed)
    # a pinned role (screensaver config) is found by resetting random characters until it matches
    # a staged game (staging.py) plays in wizard mode from a chosen late-game situation; never natural play
    env_class = NetHackChallenge if stage is None else staging.StagedChallenge
    if stage is not None and strategy is None:
        strategy = staging.STAGES[stage].strategy
    if stage is not None and max_steps is None:
        max_steps = staging.STAGES[stage].max_steps
    env = env_class(no_progress_timeout=1000, fix_moon_phase=seed is not None,
                    character=CHARACTER if role is None else "@")
    if seed is not None:
        # NetHackChallenge blocks the instance method; the class's own one still works
        type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False, lgen)
    max_depth = 1
    turns = 0
    xp_level = 0
    prev_chars = None
    watchdog = _ScreenWatchdog(watchdog_seconds)
    ctx = _DeathContext()
    recorder = snapshots.Recorder()
    truth_for = set()  # agents that got the layout (a pinned role resets the env and makes a new agent)

    def on_step(obs):
        nonlocal max_depth, turns, xp_level, prev_chars
        ctx.observe(obs)
        recorder.observe(obs, _reached(wrapper))
        agent = getattr(wrapper, "agent", None)
        if agent is not None and id(agent) not in truth_for and _give_ladder_truth(wrapper, env):
            truth_for.add(id(agent))
        # The final (game-over) observation has all-zero blstats; keep the last real values.
        max_depth = max(max_depth, int(obs["blstats"][DEPTH]))
        turns = max(turns, int(obs["blstats"][TURN]))
        xp_level = max(xp_level, int(obs["blstats"][XP_LEVEL]))
        if int(obs["blstats"][TURN]):  # the game-over observation has all-zero blstats
            watchdog.check_turn(int(obs["blstats"][TURN]))
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
                         agent_args=dict(AGENT_ARGS),
                         prepare=None if stage is None else lambda e, obs: staging.apply_stage(e, staging.STAGES[stage]))
    watchdog_stack = []
    try:
        with watchdog:
            wrapper.main()
        end_reason = wrapper.end_reason or "finished"
    except WatchdogTimeout as e:
        end_reason = "watchdog"
        watchdog_stack = _stack(e)
    except Exception as e:  # never let one bad game kill the screensaver
        end_reason = f"exception: {type(e).__name__}: {e}"
    finally:
        env.close()

    strategy = chosen.get("strategy", strategy or "?")  # "?" if the game never started
    role_s, race, gender, alignment = _character(wrapper)
    ladder, rung = _ladder(wrapper, end_reason, turns)
    return GameResult(role_s, race, alignment, max_depth, turns, int(wrapper.score), end_reason,
                      strategy=strategy, gender=gender, milestone=_milestone(wrapper),
                      elbereth=_stat(wrapper, "elbereth_write"), xp_level=xp_level,
                      panics=_stat(wrapper, "agent_panic"), stuck_diving=_stat(wrapper, "stuck_diving"),
                      unsticks=_stat(wrapper, "unstick"), ladder=ladder, rung=rung,
                      ladder_error=_stat(wrapper, "ladder_error"), seed=seed, lgen=lgen,
                      last_messages=list(ctx.last_messages), prayers=ctx.prayers, zaps_seen=ctx.zaps_seen,
                      hp_at_end=ctx.hp_at_end, max_hp_at_end=ctx.max_hp_at_end,
                      hunger_at_end=ctx.hunger_at_end, depth_at_end=ctx.depth_at_end,
                      food_at_end=_food_at_end(wrapper), events=_events(wrapper),
                      stuck_reports=_stuck_reports(wrapper), dungeon_at_end=ctx.dungeon_at_end,
                      level_at_end=ctx.level_at_end, watchdog_stack=watchdog_stack,
                      outcome=outcome(strategy, end_reason, max_depth, _has_loot(wrapper)), stage=stage,
                      snapshots=recorder.result())


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
