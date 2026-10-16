# NetHack Terminal Screensaver — Design

Date: 2026-10-16
Status: Approved design, pending spec review

## Goal

A terminal screensaver: after 5 minutes idle at the zsh prompt, the terminal
switches to a live game of NetHack played automatically by the AutoAscend bot.
Any keypress ends it and returns to the untouched prompt.

It is eye candy — success means it starts reliably, looks like real NetHack,
plays at a watchable pace, never breaks the terminal, and never crashes on
screen.

## Decisions

| Topic | Decision |
|---|---|
| Idle detection | zsh `TMOUT=300` + `TRAPALRM`; only fires while idle at the prompt, never during a running program |
| Exit | Any keypress; the key is swallowed (not passed to the shell) |
| Bot | AutoAscend only (NeurIPS 2021 NetHack Challenge winner, rule-based, no ML) |
| Runtime | Port AutoAscend to modern deps; `uv` venv on Python 3.13; no Docker |
| Game engine | NLE 1.3.0 (prebuilt cp313 wheel, NetHack 3.6.6), gymnasium API |
| Pace | ~8–10 moves/sec default, configurable |
| Status line | Optional (`status_line = false` by default) |
| Multiple idle terminals | Each runs its own independent game; no daemon |
| Character | Random role/race/alignment per game; config can pin a role |

## Architecture

```
~/.zshrc ──(TMOUT=300 + TRAPALRM)──► bin/nethack-screensaver   (launcher, shell)
                                          │ alt-screen, raw tty, keypress watch
                                          ▼
                                     nethack_screensaver/player.py   (uv, Python 3.13)
                                       ├── autoascend/   ported & trimmed agent
                                       │     env_wrapper.py  ── step() hook
                                       └── nethack_screensaver/render.py
                                                 │
                                            NLE 1.3.0 (gymnasium)
```

### Units

1. **`autoascend/` — the port.** Vendored from upstream
   `maciej-sypetkowski/autoascend` @ `8527910` (MIT; keep LICENSE and
   attribution). Agent logic stays as upstream. Changes:
   - `env_wrapper.py`: gymnasium API (`reset() -> (obs, info)`,
     `step() -> (obs, reward, terminated, truncated, info)`), no seeding
     patch, no tile visualizer; exposes a per-step callback.
   - Fix private NLE attribute usage (`env._actions`, `env._tempdir`) for
     NLE 1.3.0.
   - NumPy 2 / modern numba / modern OpenCV fixes (removed aliases, stricter
     numba typing in the ~5 jitted kernels). Add `cache=True` to numba jits.
   - Removed: `rl_utils.py` and RL combat scoring (torch), ray simulation,
     `visualization/`, plotting (matplotlib/seaborn/pandas), muzero,
     profiler, `bin/main.py` simulate/profile modes.
   - Target runtime deps: `nle`, `gymnasium`, `numpy`, `numba`,
     `opencv-python-headless`, `toolz`, `nltk`, `scipy` (drop any that turn
     out unused after trimming).
   - If a removed module is referenced from a code path the agent actually
     uses, replace it with the simplest behavior-preserving fallback (e.g.
     RL scoring → upstream's non-RL scoring path).

2. **`nethack_screensaver/render.py` — terminal renderer.** Input: NLE
   observation (`tty_chars`, `tty_colors`, `tty_cursor`) and terminal size.
   Output: ANSI escape sequences drawing the 80×24 screen centered. Diff
   rendering: only cells changed since the last frame are written; full
   redraw on resize. Renders an optional status line below the map. Knows
   nothing about AutoAscend. If the terminal is smaller than 80×24 (81×25
   with status line), draws a centered "terminal too small" message.

3. **`nethack_screensaver/player.py` — game loop.** Forever: show splash
   (first game only) → create env with random character (or configured
   role) → run AutoAscend `main()` → on game end hold the final screen
   (tombstone/DYWYPI) for `end_pause` seconds → append game-log line →
   repeat. The per-step callback renders and then sleeps `delay`; on a
   dungeon-level change it sleeps `level_pause` instead. Handles SIGTERM
   (clean exit) and SIGWINCH (full redraw).

4. **`bin/nethack-screensaver` — launcher.** Saves `stty` state, enters
   alternate screen, hides cursor, sets raw/no-echo, starts the player under
   `nice` as a child with stdout to the terminal, and blocks reading one
   byte from stdin. On a byte (or player exit): SIGTERM the player, SIGKILL
   after 1s, restore stty, show cursor, leave alternate screen. Restoration
   runs from a `trap` on EXIT/INT/TERM so the terminal is never left broken.
   Can be run manually from the prompt.

5. **`zsh/nethack-screensaver.zsh` — shell hook.** Sets `TMOUT` from config
   default (300) and defines `TRAPALRM` to run the launcher, then
   `zle reset-prompt` so the prompt is redrawn intact. Sourced from
   `~/.zshrc`.

6. **Config** — `~/.config/nethack-screensaver/config.toml`, all keys
   optional, read via stdlib `tomllib`:
   ```toml
   idle_timeout = 300     # seconds (applied by the zsh hook)
   delay = 0.1            # seconds per move
   level_pause = 1.0      # extra pause on new dungeon level
   end_pause = 5.0        # hold time on the final screen
   status_line = false
   role = "random"        # or arc|bar|cav|hea|kni|mon|pri|ran|rog|sam|tou|val|wiz
   ```

7. **Game log** — `~/.local/state/nethack-screensaver/games.jsonl`, one
   JSON object per finished game: `timestamp`, `role`, `race`,
   `alignment`, `max_depth`, `turns`, `score`, `end_reason` (death cause,
   or `exception: ...` / `watchdog`). The status line derives "Best: Dlvl N"
   from it.

## Data flow

1. Idle 300s at prompt → `TRAPALRM` → launcher.
2. Launcher prepares the tty and spawns `nice uv run --project <repo> python -m nethack_screensaver.player`.
3. Player shows splash ("a new adventurer enters the dungeon…") while
   imports and numba kernels load (cached after first run).
4. Each agent action → `step()` → callback → render diff → sleep.
5. Game ends → hold final screen → log line → new game (no splash).
6. Keypress → launcher stops player, restores tty → prompt redrawn.

## Error handling

- **Agent exception / panic mid-game:** caught in the player loop, logged
  with `end_reason`, new game starts. Nothing printed to the screen.
- **Stuck agent:** AutoAscend's `no_progress_timeout` plus a player
  watchdog: no screen change for 60s → end game, `end_reason = "watchdog"`.
- **Player crash / startup failure:** launcher shows a one-line error for
  3s, restores the tty, returns to the prompt. Player stderr goes to
  `~/.local/state/nethack-screensaver/player.log`.
- **Resize:** SIGWINCH → re-center with full redraw, or "too small" message.

## Status line (option C)

Single line below the map:
`Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14`.
Game number and best depth come from the game log.

## Testing

- **Unit tests (pytest):** renderer (fixed observation → expected output,
  centering, diff rendering, too-small message, status line), config
  parsing (defaults, overrides, invalid values), game-log writer/reader.
- **Port smoke test (pytest, marked slow):** ~5 headless games, no render,
  no delay. Passes if games complete without unhandled exceptions.
- **Benchmark script (`scripts/benchmark.py`, manual):** ~50 headless games;
  reports median score, median max depth, exception count. Compared against
  upstream AutoAscend's reported results to catch silent behavior
  regressions from the port.
- **Launcher manual checklist:** idle trigger fires, keypress exits, prompt
  intact and key not leaked, resize, too-small terminal, player-crash path
  restores tty.

## Build order

1. Port: vendor AutoAscend, trim, update deps, get headless games running
   (smoke test + benchmark).
2. Renderer + player loop with pacing, splash, random character, game log.
3. Launcher + zsh hook + config.
4. Status line option.

## Out of scope (later)

- **Smart pacing:** fast-forward resting/searching/corridors, slow down for
  combat and new levels.
- **Resuming a game across idle sessions:** NLE lacks clean save/restore;
  fragile.
- Other bots (LLM, simple bot), shared-game daemon, shells other than zsh,
  packaging/distribution.
