"""Screensaver player: forever plays AutoAscend games, paced and rendered."""
import shutil
import signal
import sys
import time

from autoascend.plans import STRATEGIES
from nethack_screensaver.config import Config, load_config
from nethack_screensaver.pacing import Pacer
from nethack_screensaver.paths import config_path, state_dir
from nethack_screensaver.render import Renderer, format_reveal, format_status

SPLASH = "a new adventurer enters the dungeon..."


def frame_delay(prev_depth, depth, cfg: Config, fast: bool = False) -> float:
    if prev_depth is not None and depth != prev_depth:
        return cfg.level_pause
    return cfg.fast_delay if fast else cfg.delay


def _size():
    s = shutil.get_terminal_size((80, 24))
    return s.columns, s.lines


def _write(out, text):
    if text:
        out.write(text)
        out.flush()


def _on_term(signum, frame):
    raise SystemExit(0)


def _install_signals(renderer: Renderer) -> None:
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGHUP, _on_term)  # terminal closed: still run env.close()
    signal.signal(signal.SIGWINCH, lambda *_: renderer.request_redraw())


def main() -> None:
    cfg = load_config(config_path())
    log_path = state_dir() / "games.jsonl"
    out = sys.stdout
    renderer = Renderer()
    _install_signals(renderer)

    _write(out, renderer.message(SPLASH, *_size()))

    # Heavy imports after the splash so the user sees something immediately.
    from nethack_screensaver.game import DEPTH, TURN, role_abbrev, run_game
    from nethack_screensaver.gamelog import append_result, read_stats

    role = None if cfg.role == "random" else cfg.role
    while True:
        stats = read_stats(log_path)
        game_no = stats.games + 1
        state = {"depth": None, "turn": 0, "role": None, "obs": None}
        pacer = Pacer()

        def on_frame(obs):
            depth = int(obs["blstats"][DEPTH])
            turn = int(obs["blstats"][TURN])
            if depth == 0:  # game-over screen: blstats are all zero
                depth, turn = state["depth"] or 1, state["turn"]
            if state["role"] is None:
                state["role"] = role_abbrev(obs)
            fast = pacer.update(obs)
            status = None
            if cfg.status_line:
                status = format_status(game_no, state["role"], depth, turn,
                                       max(stats.best_depth, depth), fast)
            _write(out, renderer.frame(obs["tty_chars"], obs["tty_colors"], *_size(), status=status))
            time.sleep(frame_delay(state["depth"], depth, cfg, fast))
            state["depth"], state["turn"] = depth, turn
            state["obs"] = obs

        strategy = None if cfg.strategy == "random" else cfg.strategy
        result = run_game(role=role, on_frame=on_frame, strategy=strategy)
        append_result(log_path, result)
        if cfg.reveal_goal and state["obs"] is not None and result.strategy in STRATEGIES:
            obs = state["obs"]
            _write(out, renderer.frame(obs["tty_chars"], obs["tty_colors"], *_size(),
                                       overlay=format_reveal(result.strategy, result.outcome)))
        time.sleep(cfg.end_pause)
        renderer.invalidate()


if __name__ == "__main__":
    main()
