# Constraints (SPEC intel)

Source set: 5 design specs and 4 implementation plans, all classified SPEC (manifest override).
Dates run 2026-10-16 to 2026-10-21; later dated specs evolve earlier ones. Where a later
source supersedes earlier text, the entry says so (see INGEST-CONFLICTS.md, INFO bucket).
Short paths are relative to ``.

Source key:
- S-SAVER  = docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md
- P-SAVER  = docs/superpowers/plans/2026-10-16-nethack-screensaver.md (low confidence)
- S-STRAT  = docs/superpowers/specs/2026-10-18-secret-strategies-design.md
- P-STRAT  = docs/superpowers/plans/2026-10-18-secret-strategies.md
- S-BENCH  = docs/superpowers/specs/2026-10-20-bench-server-design.md
- P-BENCH  = docs/superpowers/plans/2026-10-20-bench-server.md (low confidence)
- S-LADDER = docs/superpowers/specs/2026-10-21-ascension-ladder-design.md
- P-LADDER = docs/superpowers/plans/2026-10-21-ascension-ladder.md
- S-SEED   = docs/superpowers/specs/2026-10-21-seeded-bench-design.md

---

## Screensaver: idle trigger and launcher protocol
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md
- type: protocol
- content:
  Goal: after 5 minutes idle at the zsh prompt the terminal switches to a live NetHack game
  played by the AutoAscend bot; any keypress ends it and returns to the untouched prompt.
  Eye candy: success = starts reliably, looks like real NetHack, watchable pace, never breaks
  the terminal, never crashes on screen.
  - Idle detection: zsh `TMOUT` + `TRAPALRM`; fires only while idle at the prompt, never during
    a running program. Timeout from env var `NETHACK_SCREENSAVER_IDLE` (default 300), read by
    the zsh hook so shell startup never runs Python.
  - Exit: any keypress; the key is swallowed (not passed to the shell).
  - Multiple idle terminals: each runs its own independent game; no daemon.
  - Launcher `bin/nethack-screensaver`: saves `stty` state, enters alternate screen, hides
    cursor, sets raw/no-echo, starts the player under `nice` as a child with stdout to the
    terminal, blocks reading one byte from stdin. On a byte (or player exit): SIGTERM the
    player, SIGKILL after 1 s, restore stty, show cursor, leave alternate screen. Restoration
    runs from a `trap` on EXIT/INT/TERM so the terminal is never left broken. Can be run
    manually from the prompt.
  - Hook `zsh/nethack-screensaver.zsh`: sets `TMOUT` from `NETHACK_SCREENSAVER_IDLE` (default
    300), defines `TRAPALRM` to run the launcher, then `zle reset-prompt`. Sourced from `~/.zshrc`.
  - Data flow: idle 300 s -> TRAPALRM -> launcher -> `nice uv run --project <repo> python -m
    nethack_screensaver.player` -> splash (first game only) while imports/numba kernels load ->
    each agent action: step() -> callback -> render diff -> sleep -> game ends: hold final
    screen -> log line -> new game (no splash) -> keypress: launcher stops player, restores tty.
  - Pace ~8-10 moves/sec default, configurable. Status line optional (`status_line = false`
    default), format `Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14`, game number and best
    depth from the game log.
  - Character: random role/race/alignment per game; config can pin a role.
  - Plan addendum (P-SAVER): launcher drains input so multi-byte escape sequences (arrows,
    function keys) are fully swallowed; env override `NETHACK_SCREENSAVER_PLAYER` = command to
    run instead of the player (for tests).

## Screensaver: runtime, port and dependency constraints
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: nfr
- content:
  - Bot: AutoAscend only (NeurIPS 2021 NetHack Challenge winner, rule-based, no ML).
  - Runtime: port AutoAscend to modern deps; `uv` venv on Python 3.13; no Docker. Plan:
    Python `>=3.13,<3.14`, venv at `<repo>/.venv`.
  - Engine: NLE 1.3.0 (prebuilt cp313 wheel, NetHack 3.6.6), gymnasium API.
  - Vendoring: upstream `maciej-sypetkowski/autoascend` @ `8527910bd85c4d851c18ad912aae606c92cd516a`
    (MIT; keep LICENSE as `autoascend/LICENSE` and attribution). Agent logic stays as upstream.
  - Port changes: `env_wrapper.py` rewritten for gymnasium API (`reset() -> (obs, info)`,
    `step() -> (obs, reward, terminated, truncated, info)`), "no seeding patch" (superseded
    for seeded bench runs by S-SEED), no tile visualizer, per-step callback; fix private NLE
    attributes (`env._actions`, `env._tempdir`); NumPy 2 / numba / OpenCV fixes; `cache=True`
    on numba jits. Removed: `rl_utils.py` and RL combat scoring (torch), ray simulation,
    `visualization/`, plotting, muzero, profiler, `bin/main.py` simulate/profile modes. A removed
    module referenced by a used code path gets the simplest behavior-preserving fallback (RL
    scoring -> upstream non-RL path).
  - Dependencies: spec target list is `nle, gymnasium, numpy, numba, opencv-python-headless,
    toolz, nltk, scipy` (drop any unused after trimming). Plan Global Constraints (more
    specific) list `nle==1.3.0, numpy, numba, opencv-python-headless, scipy, toolz` and
    explicitly exclude torch, ray, matplotlib, seaborn, pandas, nltk, PIL, gym.
  - Paths: config `${XDG_CONFIG_HOME:-~/.config}/nethack-screensaver/config.toml`; state dir
    `${XDG_STATE_HOME:-~/.local/state}/nethack-screensaver/` with `games.jsonl` and `player.log`.
  - Screen is 80x24 (NLE tty); 80x25 with status line.

## Screensaver: config file schema
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: schema
- content:
  `~/.config/nethack-screensaver/config.toml`, all keys optional, read via stdlib `tomllib`:
  ```toml
  delay = 0.1            # seconds per move
  level_pause = 1.0      # extra pause on new dungeon level
  end_pause = 5.0        # hold time on the final screen
  status_line = false
  role = "random"        # or arc|bar|cav|hea|kni|mon|pri|ran|rog|sam|tou|val|wiz
  ```
  Invalid values (`delay = "fast"`, unknown role) fall back to defaults with a warning on
  stderr, never crash. Idle timeout is deliberately not in TOML (env var, see launcher entry).
  Later additions: `strategy`, `reveal_goal` (see secret-strategies entries).

## Screensaver: game log record schema
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: schema
- content:
  `~/.local/state/nethack-screensaver/games.jsonl`, one JSON object per finished game with keys
  `timestamp, role, race, alignment, max_depth, turns, score, end_reason` (death cause, or
  `exception: ...` / `watchdog`). A corrupt or partial line (killed mid-write) must be skipped
  on read without crashing (`test_read_stats_skips_malformed_lines`). Extended later by
  `strategy, gender, outcome` (secret strategies), `unsticks`, `seed`, `ladder`, `rung`.

## Screensaver: module interfaces
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: api-contract
- content:
  - Renderer (`nethack_screensaver/render.py`, knows nothing about AutoAscend): input NLE
    observation (`tty_chars`, `tty_colors`, `tty_cursor`) and terminal size; output ANSI
    drawing the 80x24 screen centered; diff rendering (only changed cells), full redraw on
    resize; optional status line; "terminal too small" centered message if smaller than 80x24
    (81x25 with status line). `Renderer()` with `frame(tty_chars, tty_colors, cols, rows,
    status=None) -> str`, `message(text, cols, rows) -> str`, `invalidate() -> None`;
    `format_status(game_no, role, depth, turn, best_depth) -> str`.
  - Player (`nethack_screensaver/player.py`): forever: splash (first game) -> env with random or
    configured role -> run AutoAscend `main()` -> hold final screen `end_pause` s -> append
    game-log line -> repeat. Callback renders then sleeps `delay`; on dungeon-level change
    sleeps `level_pause`. Handles SIGTERM (clean exit) and SIGWINCH (full redraw).
    `player.frame_delay(prev_depth, depth, cfg) -> float`; `player.main()`, runnable as
    `python -m nethack_screensaver.player`.
  - Game: `autoascend.env_wrapper.EnvWrapper(env, on_step=None, step_limit=None, role=None)` with
    `.main()`, `.score`, `.end_reason`, `.agent`; `nethack_screensaver.game.GameResult(role, race,
    alignment, max_depth, turns, score, end_reason)`; `run_game(role=None, on_frame=None,
    max_steps=None, watchdog_seconds=60.0) -> GameResult`; `role_abbrev(obs) -> str`.
  - Paths/config/log: `paths.config_path()`, `paths.state_dir()` (creates dir);
    `config.Config` frozen dataclass (`delay=0.1, level_pause=1.0, end_pause=5.0,
    status_line=False, role="random"`), `config.ROLES`, `config.load_config(path)` never raises;
    `gamelog.append_result(path, result, now=None)`, `gamelog.LogStats(games, best_depth)`,
    `gamelog.read_stats(path)`.
  - Package layout: `pyproject.toml`, `.python-version`, `autoascend/` (vendored, `PORTING.md`
    logs every port change), `nethack_screensaver/`, `bin/nethack-screensaver`,
    `zsh/nethack-screensaver.zsh`, `scripts/benchmark.py`, `tests/`, `README.md`.

## Screensaver: error handling, watchdog and resize
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: nfr
- content:
  - Agent exception/panic mid-game: caught in the player loop, logged with `end_reason`, new
    game starts, nothing printed to screen.
  - Stuck agent: AutoAscend `no_progress_timeout` plus player watchdog: no screen change for
    60 s -> end game, `end_reason = "watchdog"`.
  - Player crash/startup failure (missing `.venv`, import error): launcher shows a one-line
    error for 3 s, restores the tty, returns to the prompt; player stderr -> `player.log`.
    The terminal must always be restored.
  - Resize: SIGWINCH -> re-center with full redraw, or "too small" message; never garbage.

## Screensaver: testing and acceptance
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md
- type: nfr
- content:
  - Unit tests (pytest): renderer (fixed observation -> expected output, centering, diff
    rendering, too-small message, status line), config parsing (defaults, overrides, invalid),
    game-log writer/reader.
  - Port smoke test (pytest, marked slow): ~5 headless games, no render, no delay; passes if
    games complete without unhandled exceptions.
  - Benchmark script `scripts/benchmark.py` (manual): ~50 headless games; median score, median
    max depth, exception count; compared against upstream AutoAscend's reported results to catch
    silent behavior regressions from the port.
  - Launcher manual checklist: idle trigger fires, keypress exits, prompt intact and key not
    leaked, resize, too-small terminal, player-crash path restores tty.
  - Build order: 1 port (vendor, trim, deps, headless games); 2 renderer + player loop;
    3 launcher + zsh hook + config; 4 status line option.

## Screensaver plan: review focus
- source: docs/superpowers/plans/2026-10-16-nethack-screensaver.md
- type: nfr
- content:
  1. Keypress leaking into the shell (multi-byte escape sequences all swallowed; Task 8).
  2. Player crash at startup must restore terminal and show a one-line error (Task 8, tested with a fake player).
  3. Terminal resized mid-game or smaller than 80x24 (Task 5 tests `test_too_small`, `test_invalidate_forces_full_redraw`).
  4. Corrupt/partial `games.jsonl` line (Task 4 test).
  5. Invalid config values fall back with a warning (Task 3 tests).
  Plan environment note: if `uv` is missing, ask the user to run `! sudo pacman -S uv`; do not run sudo.

---

## Secret strategies: strategy definitions and milestone plans
- source: docs/superpowers/specs/2026-10-18-secret-strategies-design.md ; docs/superpowers/plans/2026-10-18-secret-strategies.md
- type: protocol
- content:
  Every screensaver game starts with NLE's random character and is secretly assigned one of
  four strategies; each aims at a different ending. Secrecy: never shown during play; recorded
  in `games.jsonl`; optional reveal. A strategy is an ordered list of milestones. Every plan
  starts with `BE_ON_FIRST_LEVEL` (explore Dlvl 1, leave when Hungry).
  - `pilgrim` -> ascension: BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN, FIND_SOKOBAN,
    SOLVE_SOKOBAN, FIND_MINES_END, GO_DOWN. Equals upstream order (the baseline).
  - `daredevil` -> escape in celestial disgrace: BE_ON_FIRST_LEVEL, GO_DOWN.
  - `sightseer` -> escape: BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN,
    EXPLORE_MINETOWN, RETURN_TO_SURFACE, LEAVE_DUNGEON.
  - `treasure` -> escape with loot: BE_ON_FIRST_LEVEL, FIND_SOKOBAN, SOLVE_SOKOBAN,
    LOOT_SOKOBAN_PRIZE, RETURN_TO_SURFACE, LEAVE_DUNGEON.
  Exact target-ending strings: `ascension`, `escape in celestial disgrace`, `escape the
  dungeon`, `escape with loot`.
  Original scope limits (S-STRAT "Reality check" and "Out of scope"; SUPERSEDED in direction by
  docs/ROADMAP.md sub-projects 2-8, see INFO): no Amulet/Quest/Castle/Gehennom logic; pilgrim
  and daredevil end in "descend forever"; strategy pick uniformly random per game in `run_game`
  (`strategy` config can force one), no uneven weighting. Current default per docs/STATUS.md:
  pilgrim for every game, other plans behind `strategy = "random"` (code default confirmed:
  `Config.strategy = "pilgrim"`).

## Secret strategies: new milestone behavior and advancing rules
- source: docs/superpowers/specs/2026-10-18-secret-strategies-design.md ; docs/superpowers/plans/2026-10-18-secret-strategies.md
- type: protocol
- content:
  - `EXPLORE_MINETOWN`: explore Minetown (existing exploration on `minetown_level`) for 1,000
    turns (`TOWN_TURNS = 1000`), then advance (turn budget because the explorer never reports done).
  - `LOOT_SOKOBAN_PRIZE`: explore top Sokoban level `(SOKOBAN, 1)`; advance once a possible prize
    (bag of holding / amulet of reflection) is in inventory or after 1,500 turns (`LOOT_TURNS = 1500`).
  - `RETURN_TO_SURFACE`: travel by known stairs to `(DUNGEONS_OF_DOOM, 1)` via existing
    `go_to_level_strategy`, then advance.
  - `LEAVE_DUNGEON`: walk to Dlvl 1 upstairs and go up; the agent answers `[yn]` prompts with `y`
    ("Beware, there will be no return! Still climb?"), ending the game as an escape. If the
    upstairs is unknown or unreachable, keep exploring Dlvl 1, do not crash.
  - Advancing: `GlobalLogic` holds plan + index; advance moves to the next milestone in the plan.
    When Sokoban is dropped as unsolvable (`sokoban_dropped`), the plan skips `LOOT_SOKOBAN_PRIZE`
    if it is next. The last milestone (`GO_DOWN`, `LEAVE_DUNGEON`) never advances (no IndexError).
  - Pacing: `farming` stays "current milestone is BE_ON_FIRST_LEVEL"; return trip over known
    levels fast-forwards by itself.
  - Escape recognition: an escape must never be logged as a death. NLE reports it with
    end_status DEATH and text "escaped the dungeon [max level N]"; `_parse_end_reason` returns
    `"ESCAPED: escaped the dungeon"` (status prefix `ESCAPED`, `[max level N]` stripped). Fixture
    `tests/data/escaped_tty_chars.npy`.

## Secret strategies: result, log, reveal and config schema
- source: docs/superpowers/specs/2026-10-18-secret-strategies-design.md ; docs/superpowers/plans/2026-10-18-secret-strategies.md
- type: schema
- content:
  - `GameResult` and each `games.jsonl` record gain `strategy` (`pilgrim|daredevil|sightseer|treasure`;
    default `"?"`), `gender` (parsed from existing character string; default `"?"`), `outcome`
    (default `""`), placed after `end_reason`.
  - Outcome strings: `escaped` (sightseer); `escaped with loot` / `escaped empty-handed`
    (treasure; loot = possible bag of holding or amulet of reflection picked up on the top
    Sokoban level, items carried in from elsewhere do not count); any death `died on Dlvl N`
    (N = max depth); exception or watchdog `crashed`.
  - Old records without the new fields still load (`read_stats` ignores missing keys); an agent
    that crashed before `GlobalLogic` existed must still yield a valid result/log line.
  - Reveal (off by default; `reveal_goal = true`): during `end_pause`, bottom row of the final
    screen shows `Secret goal: <Name> · <target ending> · <outcome>`; a successful escape
    outcome is upper-cased with `!`. Examples: `Secret goal: Sightseer · escape the dungeon ·
    ESCAPED!`; `Secret goal: Daredevil · escape in celestial disgrace · died on Dlvl 11`.
  - Config: `strategy = "random"` (or pilgrim/daredevil/sightseer/treasure), `reveal_goal = false`;
    unknown values warn and fall back to the default (validated like `role`). Spec/plan default
    is `"random"`; current code default is `"pilgrim"` (see INFO).

## Secret strategies: Python interfaces
- source: docs/superpowers/plans/2026-10-18-secret-strategies.md
- type: api-contract
- content:
  - New `autoascend/plans.py`: `Milestone(IntEnum)` (existing members unchanged plus
    `EXPLORE_MINETOWN, LOOT_SOKOBAN_PRIZE, RETURN_TO_SURFACE, LEAVE_DUNGEON`), `Plan(milestones)` with
    `.current`, `.advance()` (no-op on last), `.drop_sokoban()` (advance; then also skip
    `LOOT_SOKOBAN_PRIZE` if current); frozen `StrategySpec(name, title, ending, milestones)`;
    `STRATEGIES: dict[str, StrategySpec]`; `DEFAULT_PLAN = STRATEGIES["pilgrim"].milestones`;
    `global_logic.Milestone` keeps working (re-export).
  - `Agent(env, ..., plan: Sequence[Milestone] | None = None)` (None -> DEFAULT_PLAN);
    `GlobalLogic(agent, plan=None)`; `GlobalLogic.milestone` read-only property = `self.plan.current`.
  - `run_game(role=None, on_frame=None, max_steps=None, watchdog_seconds=60.0, strategy=None)`;
    None -> `random.choice(sorted(STRATEGIES))` (as written in the plan; current code defaults differently, see INFO).
    `outcome(strategy, end_reason, max_depth, has_loot) -> str`.
  - `Config.strategy: str = "random"`, `Config.reveal_goal: bool = False`; `format_reveal(strategy, outcome)` in `render.py`.
  - Files touched: `autoascend/{plans,global_logic,agent,env_wrapper}.py`, `nethack_screensaver/{game,config,render,player}.py`, `scripts/benchmark.py`, `README.md`, `autoascend/PORTING.md`, tests incl. new `tests/test_plans.py`.

## Secret strategies: acceptance criteria and testing
- source: docs/superpowers/specs/2026-10-18-secret-strategies-design.md ; docs/superpowers/plans/2026-10-18-secret-strategies.md
- type: nfr
- content:
  Success: the four strategies play visibly differently, the two escape strategies actually win
  some runs, nothing gets less stable.
  Acceptance (verbatim):
  1. `sightseer` and `treasure` escape in at least some runs (rate measured, not promised).
  2. Strategies differ: `daredevil` has the deepest median, `sightseer` reaches Minetown most often,
     `treasure` reaches Sokoban far more often than today's 2%.
  3. `pilgrim` matches the current baseline (median Dlvl 5, Mines in about two thirds of games).
  4. No new exception types; all existing tests pass.
  Unit tests: each plan advances in order; dropped Sokoban skips `LOOT_SOKOBAN_PRIZE`; last
  milestone does not advance; random pick covers all four over many draws, forced name used;
  config valid/invalid; outcome text per strategy and end kind; reveal formatting;
  `_parse_end_reason` on recorded "escaped" screen. Slow: one real game each for `sightseer` and
  `treasure` with a step limit (no crash; plan moves past `BE_ON_FIRST_LEVEL`).
  Benchmark: `scripts/benchmark.py --strategy NAME` (default random) prints per strategy median
  max depth, share reaching Mines/Minetown/Sokoban, outcome counts; 24-48 games per strategy.
  Plan constraints: run `uv run pytest -q -m ""` before and after; local git only, never push or add remotes.

---

## Bench server: architecture, storage and lifecycle constraints
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: nfr
- content:
  Goal: replace 2 x ~15 min 576-game shell runs with a local server that plays bot games on
  demand, stores every game, compares a candidate commit with a baseline with honest error
  margins, shows a live status page, is driven by Claude via MCP, and imports real ascensions.
  - Modes: baseline (play a commit up to N games) and experiment (candidate vs baseline, A/B).
  - Load: on demand only (plays while a job is active); workers default 11 (`--workers`),
    started `nice -n 10`.
  - Stack: Python stdlib (`http.server`, `sqlite3`, `subprocess`, `urllib`); only new dependency
    `mcp` (FastMCP) in dependency group `bench` (also in `dev`). Package `bench/`, separate from
    `nethack_screensaver/`; entry point `screens-bench` (`[project.scripts]` -> `bench.cli:main`).
  - Code under test is always a commit, run from a git worktree per commit
    (`~/.cache/screens-bench/worktrees/<sha>`, `git worktree add --detach`, reused); workers run with
    `PYTHONPATH=<worktree>` and the repo's `.venv/bin/python`. Uncommitted changes cannot be benchmarked.
  - Network/paths: server on `127.0.0.1:8765` only (never other interfaces); DB
    `~/.local/share/screens-bench/results.db` (override `SCREENS_BENCH_DATA`); cache under
    `~/.cache/screens-bench/` (override `SCREENS_BENCH_CACHE`); client URL override `SCREENS_BENCH_URL`.
  - `bench/worker.py` must not import anything from `bench` (old commits' worktrees lack it).
  - Lifecycle/errors: `serve` refuses a second instance (port taken) with a clear message, no
    traceback; a game ending in a bot exception is a normal `crashed` result; a dead worker is
    restarted, three deaths in a row stop the job with the error shown; watchdog 120 s per bench
    game (`run_game(watchdog_seconds=120)`; the screensaver's own watchdog is 60 s, different context);
    stopped/interrupted jobs keep stored games; restart while a job ran -> job shows `interrupted`;
    unknown ref fails before anything starts with git's message; a branch gaining commits mid-job
    keeps the SHA resolved at start; `screens-bench prune` removes worktrees unused for 14 days.
  - Old tool `scripts/benchmark.py` stays as fallback. Out of scope: ttyrec recordings, remote
    access, a web framework. Local git only: never push, no remotes.
  - Plan work order: 1 storage/metrics/stats; 2 worker/scheduler/CLI (`serve`, `wait`, `prune`);
    3 JSON API + status page; 4 MCP + `.mcp.json`; 5 importers + Ascenders page; 6 check:
    `choke-points` vs `main` must end `no measurable difference`.
  - Plan commit messages end with a Co-Authored-By line; suite `uv run pytest -q -m ""` stays green; new tests flat in `tests/` named `test_bench_*.py`.

## Bench server: worker and scheduler protocol
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: protocol
- content:
  - Worker (`bench/worker.py`): one process per commit; reads one `play` line per game from
    stdin, runs `run_game(watchdog_seconds=120)`, prints `dataclasses.asdict(GameResult)` as one
    JSON line to the original stdout (everything the game prints goes to stderr). Server stores
    each game immediately. A slot switching commit closes its worker and starts another.
    SUPERSEDED in part by S-SEED: protocol becomes `play <seed>` (bare `play` still accepted).
  - Scheduler: at most one active job plus FIFO queue. `baseline(ref, games)`: play ref until it
    has `games` stored games. `experiment(candidate, baseline, metric)`: per checkpoint, top up
    the baseline commit to the checkpoint size (reusing stored games), then play the candidate to
    the same size; judge; stop when decided or at the last checkpoint. Hands out one game at a
    time to free workers. SUPERSEDED in part by S-SEED (seed-aware assignment).
  - Notification: `screens-bench wait <job-id>` blocks until the job ends and prints its verdict.
  - Plan class interface: `Scheduler(store, spawn, slots=11)` with `submit(kind, spec) -> int`,
    `stop(job_id=None) -> bool`, `tick()`, `status() -> dict`, `shutdown()`, attributes `job`,
    `error`. Baseline spec `{ref, sha, subject, games}`; experiment spec `{candidate, candidate_ref,
    candidate_subject, baseline, baseline_ref, baseline_subject, metric}`; experiment result
    `{checkpoints: [verdict dicts], verdict: verdict dict}`. `ProcessWorker(python, worktree,
    log_path, nice=10)` with `play()`, `results()`, `alive()`, `close()`; `WORKER_SCRIPT` constant.

## Bench server: metrics and statistical verdict rules
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: protocol
- content:
  - Metrics registry (`bench/metrics.py`): name, description, `game -> bool` (rates) or `game -> number`
    (medians). Defaults: reached Dlvl 6+, Dlvl 10+, escaped, crashed, died, starved, died to ants
    (soldier/giant/fire ant), killed by a wand or ray, unstuck at least once; medians of depth,
    turns, score. Metrics run on stored JSON; games lacking a needed field are left out of that
    metric and the skipped count is shown.
  - Rate comparison: difference of two proportions with Newcombe (Wilson score) interval in
    `bench/stats.py`, no statistics library. Plan API: `CHECKPOINTS = (192, 384, 576, 1152)`,
    `Z95`, `Z99`, `wilson(k, n, z)`, `newcombe(k1, n1, k2, n2, z) -> (diff, lo, hi)`,
    `z_for(checkpoint)`, `judge(k_cand, n_cand, k_base, n_base, checkpoint) -> Verdict(state,
    checkpoint, diff, lo, hi)` with `.detectable` and `.as_dict()`.
    SUPERSEDED for experiments by S-SEED's paired interval (same checkpoints and z).
  - Primary metric: each experiment names one (default `dlvl6`); only it decides.
  - Checkpoints 192/384/576/1152 games per side; confidence 99% at 192/384/576, 95% at 1152.
  - Verdict states: `better` / `worse` (interval excludes 0 at a checkpoint), `no measurable
    difference` (at 1152 otherwise, with the smallest detectable difference = half-width), `open`
    before that. Medians shown side by side without a verdict.
  - Filter language `where`: `field=value`, `field>value`, `field<value`, `field~substring`, joined
    by `,`; no free-form code (`parse_where` raises ValueError on a bad clause).
  - Known-number test: the choke-point run 286/576 vs 262/576 must give `open` at 576 and end as
    "no measurable difference". Games from older commits lacking newer fields (e.g. `unsticks`) are skipped by metrics, with count.

## Bench server: JSON API and status page
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: api-contract
- content:
  Under `/api/`: `status`, `jobs` (POST queues), `jobs/<id>` (DELETE stops), `results?ref=&metric=`,
  `games?ref=&where=&limit=`, `experiments`, `reference/summary`, `reference/games?where=`, `import`
  (POST). Plan adds `dashboard`, `metrics`, `DELETE /api/jobs` (active job); errors: 400
  `{"error"}` for bad input, 404 for unknown jobs/routes. `GET /` serves `bench/static/index.html`.
  Plan classes: `App(store, scheduler, repo, cache_dir)` with `status()`, `start_baseline(ref="main",
  games=576)`, `start_experiment(candidate, baseline="main", metric="dlvl6")`, `stop(job_id=None)`,
  `job(job_id)`, `results(ref, metric)`, `games(ref, where, limit)`, `experiments()`,
  `dashboard(ref)`, `reference_summary()`, `reference_games(where, limit)`, `start_import(kind,
  url, limit)`, `loop(stop_event, interval=0.2)`; `serve(app, port=8765, host="127.0.0.1")`
  (SystemExit with message when port taken); `cli.build_app(workers=11, ...)`, `cli.main(argv)`.
  Status page (plain JS, polls `/api/status` every 2 s while a job runs, 30 s idle): job panel
  (kind, refs with short SHA and subject, progress, games/min, ETA, Start baseline / Start
  experiment / Stop); experiment panel (verdict, primary metric with interval, all-metrics table);
  dashboard for newest `main` commit with stored games (top killers, depth histogram, outcomes per
  strategy, crashes with call chains, games with most unsticks); history of experiments; Ascenders.

## Bench server: MCP tool surface
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: api-contract
- content:
  MCP stdio server `bench/mcp_server.py`, registered in repo `.mcp.json`, a thin client of the
  HTTP API; starts `screens-bench serve` in the background if the port does not answer.
  Spec tools: `bench_status()`, `bench_baseline(ref="main", games=576)`, `bench_experiment(candidate,
  baseline="main", metric="dlvl6")`, `bench_results(ref, metric=None)`, `bench_games(ref, where=None,
  limit=50)`, `bench_stop()`, `bench_import(source, url, limit=500)`, `bench_reference(where=None)`.
  Plan/code tools (refinement; the shipped module matches the plan): `bench_results(ref="main", ...)`,
  `bench_games(ref="main", ...)`, extra `bench_experiments()`, `bench_stop(job_id=None)`,
  `bench_import(kind, url=None, limit=500)`, `bench_reference(where=None, limit=50)`; each returns
  the API's JSON, errors as `{"error": ...}`. Module globals `URL`, `mcp`; `main()` runs stdio.

## Bench server: database schema
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: schema
- content:
  SQLite with a schema version number. Tables: `games(id, sha, job_id, finished_at, json)` (whole
  `GameResult` JSON per game), `jobs(id, kind, spec, state, created_at, ended_at, result)` (an
  experiment is a job of kind `experiment`, verdicts in `result`), `reference_games(id, source,
  name, starttime, role, turns, json, dumplog)` (raw dumplog text; unique per source, name and
  start time, so re-importing the same xlogfile adds no duplicates).
  Plan `Store(path)` API: `add_game(sha, job_id, result, finished_at=None)`, `count(sha)`,
  `games(sha, limit=None)` (oldest first), `add_job(kind, spec)`, `set_job(job_id, state,
  result=None)`, `job(job_id)`, `jobs(kind=None, limit=50)` (newest first), `next_queued()`,
  `interrupt_unfinished()`, `shas()`, `add_reference(source, record) -> bool`, `references()`,
  `set_dumplog(ref_id, text)`; `END_STATES = ("done", "stopped", "failed", "interrupted")`.
  `screens-bench import results <file.jsonl> --ref <ref>` stores games from old `scripts/benchmark.py --out` files under a commit.

## Bench server: real-ascension importers
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: protocol
- content:
  - `screens-bench import xlog <url>` (e.g. `https://www.hardfought.org/xlogfiles/nethack50/xlogfile`):
    parse each line (`key=value` separated by tabs, or `:` in old files; achievements from
    `achieveX` names, or decoded from the 3.6 `achieve` bit field); store ascended games in `reference_games`.
  - `screens-bench import dumplogs [--limit 500]`: download dumplogs of stored ascensions lacking
    one; one request per second; cached under `~/.cache/screens-bench/dumplogs/` (each file fetched
    once). Hardfought pattern `https://www.hardfought.org/userdata/<initial>/<name>/nethack/dumplog/<starttime>.nh.txt`
    (older files redirect to an S3 archive); sources without a known pattern are skipped.
  - Dumplog parser splits by section heading; extracts final inventory, attributes, intrinsics,
    conducts, killed-monster count, and the "Major events" timeline with turn numbers where present
    (NetHack 5.0 dumplogs have it; 3.6 do not). Raw text kept so later parsers need no new download.
  - Ascenders page / `bench_reference`: number of ascensions, turns to ascend (median, quartiles),
    role mix, achievement order and milestone turns, share with reflection / magic resistance / bag
    of holding, common wands, final XL and AC.
  - Plan API: `parse_xlog_line`, `achievements`, `fetch(url, cache_dir=None, min_interval=1.0)`,
    `import_xlog(store, url, source=None, fetcher=fetch)`, `dumplog_url`, `import_dumplogs`,
    `sections`, `parse_dumplog`; `reference.summary(refs, min_share=0.5)` keys `ascensions,
    with_dumplog, with_timeline, turns, roles, achievements, milestones, reflection,
    magic_resistance, bag_of_holding, xl, ac, wands`. Tests use saved fixtures in `tests/data/`, no network.

## Bench server: success criteria, testing and error handling
- source: docs/superpowers/specs/2026-10-20-bench-server-design.md ; docs/superpowers/plans/2026-10-20-bench-server.md
- type: nfr
- content:
  Success (verbatim): an experiment needs one command and no shell waiting, Claude notified when
  decided; baseline games stored per commit and reused so an experiment usually plays only the
  candidate; verdicts do not call noise a win (286 vs 262 choke-point run must come out "no
  difference measurable"); real ascensions importable and summarisable.
  Testing: stats against worked examples and verdicts at each checkpoint; scheduler with a fake
  worker (top-up reuses stored games, stop, restart after worker death, three-deaths stop,
  checkpoint verdicts); storage/metrics (new metric applies to old games, skips games missing a
  field); API tests in-process with fake worker; parsers on saved fixtures; one slow test (`-m slow`)
  playing two real games through a real worktree.
  Plan review focus: interrupted-on-restart job and reusable stored games (Tasks 1, 7); port 8765
  taken (Task 7); same xlogfile twice -> no duplicates (Task 10); SHA fixed at job start (Task 7);
  older games lacking fields skipped with count (Task 3).

---

## Ascension ladder: rung list and detection rules
- source: docs/superpowers/specs/2026-10-21-ascension-ladder-design.md ; docs/superpowers/plans/2026-10-21-ascension-ladder.md
- type: schema
- content:
  Success is a ladder of 17 rungs in the median order of the 687 real ascensions. A game's
  result is the highest rung reached (lower rungs need not all be reached). Rungs recorded live
  by the bot (not from the end screen or recordings). Rungs 1-8 must be accurate now; 9-17 are
  simple proxies with a unit test each, refined later. Sub-project 0 only measures: the bot plays
  exactly as before.
  Dungeon numbers (dungeon.def order): 0 Doom, 1 Gehennom, 2 Mines, 3 Quest, 4 Sokoban, 5 Ludios,
  6 Vlad, 7 Elemental Planes (Astral is level 1 there). `blstats` gives (dungeon, level); level
  numbers are inside each dungeon (Sokoban 1 is its top level; in Doom level == depth).
  Rungs (number key: reached when [kind]; yardstick median turn):
  1 mines: in dungeon 2 [exact]; 1173
  2 minetown: `global_logic.minetown_level` set [bot]; 3538
  3 oracle: `global_logic.oracle_level` set [bot]; none
  4 sokoban: in dungeon 4 [exact]; 9022
  5 sokoban_solved: on (4,1), no trap left, at least 100 squares seen (`SOKOBAN_DRAWN = 100`) [bot]; 12412
  6 mines_end: Mines level 9, or Mines level 8 after 1000 turns (`MINES_END_WAIT`) without a seen down staircase; leaving and returning restarts the wait [proxy]; luckstone 10853
  7 dlvl15: level 15+ in dungeon 0 [exact]; none
  8 quest: in dungeon 3 [exact]; 22426
  9 medusa: dungeon 0, level 21+, and Medusa seen or more than a third of seen map is water [proxy]; 29317
  10 castle: dungeon 0 and a drawbridge glyph seen [proxy]; none
  11 gehennom: in dungeon 1 [exact]; 34155
  12 vlad: in dungeon 6 [exact]; 44189
  13 wizard_tower: "Book of the Dead" in inventory [proxy]; 49072
  14 invocation: in dungeon 1, deeper than the level where "You feel a strange vibration" appeared [proxy]; 49741
  15 planes: in dungeon 7 [exact]; 53180
  16 astral: at (7,1) [exact]; 53518
  17 ascended: end reason says "ascended" [exact]; 53630
  Titles: Gnomish Mines, Minetown, Oracle, Sokoban, Sokoban solved, Mines' End, Dlvl 15+, Quest,
  Medusa, Castle, Gehennom, Vlad's Tower, Wizard's Tower, Invocation, Elemental Planes, Astral
  Plane, Ascended. Yardstick events differ from some rungs (they record killing Medusa/the
  luckstone; we record arriving): good enough for a turn comparison.
  Mines' End: the Mines have 8 or 9 levels (`(8, 2)` in dungeon.def); the bot's own check
  `(MINES, 9)` (TODO in `global_logic.py`) misses the 8-level Mines and stays untouched here.
  Sokoban solved: arriving with holes out of sight (0 squares seen) must not count.
  Sightseer and treasure keep their escape goals; their games get a ladder value too.

## Ascension ladder: components and interfaces
- source: docs/superpowers/specs/2026-10-21-ascension-ladder-design.md ; docs/superpowers/plans/2026-10-21-ascension-ladder.md
- type: api-contract
- content:
  - `autoascend/ladder.py` (new; standard library only so the bench can import it): `Rung(number,
    key, title, yardstick_event)` frozen dataclass; `RUNGS` tuple, `BY_KEY`; constants `DOOM, GEHENNOM,
    MINES, QUEST, SOKOBAN, LUDIOS, VLAD, PLANES = range(8)`, `MINES_END_WAIT = 1000`,
    `SOKOBAN_DRAWN = 100`, `VIBRATION = "You feel a strange vibration"`.
    `Facts` frozen dataclass: `turn, dungeon, level, oracle_seen=False, minetown_seen=False,
    sokoban_seen=0, sokoban_traps=True, medusa_seen=False, water_share=0.0, drawbridge_seen=False,
    down_stairs_seen=False, inventory=(), message=""` (built by the caller; no glyph/agent code in the module).
    One detection function per rung `(facts, memory) -> bool`; `memory` holds cross-step state
    (current level and arrival turn, level of the vibrating square). `Ladder()` with
    `.observe(facts)` (records `{key: turn}` for newly reached rungs, skips recorded ones),
    `.finish(end_reason, turn)` (adds `ascended`), `.highest()` (0 for none), `.reached`.
  - `autoascend/global_logic.py`: builds `Facts` in `update()` next to the Oracle/Minetown checks
    (using `G` glyph sets and parsed inventory) and calls `self.ladder.observe(...)`; exposes
    `GlobalLogic.ladder`, `GlobalLogic.ladder_facts()`.
  - `nethack_screensaver/game.py`: `GameResult` gains `ladder: dict[str, int]` (key -> first turn)
    and `rung: int`; `game._ladder(wrapper, end_reason, turns) -> tuple[dict, int]`; goes to the
    game log and bench DB via `asdict`. Nothing new on screen.
  - `bench/metrics.py`: `rung` (median of highest rung) and `rung1`..`rung17` ("reached rung k+
    (<title>)") generated from `RUNGS`; old games lacking `rung` skipped via the existing KeyError rule;
    `dlvl6` stays the default verdict metric (switching default is a later one-line change).
  - `bench/report.py` / dashboard: `summary(games, yardstick=None)` gains `ladder` rows from
    `ladder_rows(games, yardstick=None)` with keys `rung, key, title, hits, n, median_turn,
    yardstick_turn` (our median turn vs yardstick median from reference timelines by
    `yardstick_event`); dashboard shows one table; `bench_results` returns it unchanged via MCP;
    `App.yardstick() -> dict[str, float]`.

## Ascension ladder: error handling, testing and validation
- source: docs/superpowers/specs/2026-10-21-ascension-ladder-design.md ; docs/superpowers/plans/2026-10-21-ascension-ladder.md
- type: nfr
- content:
  - Error handling: facts building is guarded; an exception is logged once (`ladder_error` stat), the
    ladder stops updating, a ladder error never crashes or ends a game; a crashed/watchdog game still
    reports rungs reached so far. While hallucinating, Oracle/Minetown facts ignore it and water share,
    Medusa and drawbridge facts stay false (a rung reached while hallucinating must not be recorded).
  - Testing: per-rung unit tests with hand-made `Facts` (including Mines' End level 8 vs 9 and
    "already recorded rungs are not re-checked"); `Ladder.finish` with ascension and non-ascension
    reasons; metrics `rung`/`rungN` on dict games with old games skipped; report rows from fake games
    and fake reference timelines (old games and empty reference set must not break summary or dashboard);
    real-game test: `GameResult.ladder` holds only known keys and `rung` is the highest among them (0 when empty);
    whole suite before and after (`uv run pytest -q -m ""`).
  - Validation: after merging, a 576-game baseline of new `main` on the bench server. Plausibility:
    Mines in about two thirds of games, Sokoban rarely, nothing above rung 7 except the odd deep dive;
    result written into `autoascend/PORTING.md` (recorded in docs/STATUS.md: Mines 57%, Minetown 29%,
    Oracle 22%, Sokoban 9%, Sokoban solved 5%, Mines' End 4%, Dlvl 15+ 2%, Quest 1 game).
  - Plan constraints: bot behaviour unchanged (no strategy/milestone/check edited); old stored games
    lacking `ladder`/`rung` skipped, not counted; work on branch `ladder`, merge to local `main`, never push.
  - Not in scope: changing any strategy; fixing the bot's Mines' End check; showing rungs on the screensaver; making a rung metric the default verdict.

---

## Seeded bench: game, worker protocol and seed rules
- source: docs/superpowers/specs/2026-10-21-seeded-bench-design.md
- type: protocol
- content:
  Why: unseeded games make each side of an experiment an independent random sample; a control
  test (same code on both sides, 1152 games each) gave -2.3 points and the smallest detectable
  difference is about 3.5 points, so real gains of 1-3 points cannot be seen. NetHack can start from
  fixed seeds (`set_initial_seeds`; the bot's own RNG already fixed at seed 0).
  - Game: `run_game(seed=None)`; with a seed, NetHack's core and display RNGs start from
    `(seed, seed)` via `type(env.nethack).set_initial_seeds` (because `NetHackChallenge` blocks the
    instance method). `GameResult.seed` records it. A seed with a pinned role is refused
    (`ValueError`): the role loop resets until the role matches, which never happens when every reset
    replays the same seed.
  - Worker protocol: `play <seed>` (and still `play`). Worker passes the seed when the commit's
    `run_game` accepts one; a result without `seed` means the commit predates seeding.
  - This supersedes S-SAVER's "no seeding patch" for bench use and S-BENCH's unseeded `play` protocol.

## Seeded bench: scheduler and paired verdict
- source: docs/superpowers/specs/2026-10-21-seeded-bench-design.md
- type: protocol
- content:
  - Scheduler: a job needs seeds `0 .. N-1` for each commit (baseline: `N = games`; experiment: `N` =
    current checkpoint, both sides). Hands out the lowest seed neither stored nor in flight for that
    commit; a dead worker's seed is handed out again. A result without a seed fails the job ("commit
    cannot play seeded games").
  - Verdict: paired. For each seed both sides have, the metric's two values; difference of rates
    `d = (n10 - n01) / n` with paired (Wald) interval `d ± z * sqrt(n10 + n01 - n * d²) / n`
    (n10: candidate yes / baseline no). Same checkpoints and z as before (99% early, 95% at 1152).
    The rest of the experiment table stays but uses the same paired games.
  - After: a seeded A/A control (same code twice) should come out near 0 with a much narrower
    interval; then the pilgrim-only baseline.

## Seeded bench: store queries and testing
- source: docs/superpowers/specs/2026-10-21-seeded-bench-design.md
- type: api-contract
- content:
  - Store: `seeds(sha)` and `games_by_seed(sha, seeds)` read `$.seed` from the stored JSON. Unseeded
    old games stay for statistics and history; jobs ignore them.
  - Testing: paired interval against a hand-computed example and the "no discordant pairs" edge;
    scheduler (seeds 0..N-1 handed out once per commit, stored seeds reused, dead worker's seed
    replayed, old-commit result fails the job, both sides play the same seeds); store seed queries;
    worker protocol (`play 7` reaches `run_game(seed=7)`; an old `run_game` without the parameter runs
    unseeded); a real game (same seed twice gives the same first screen); seed plus pinned role is refused.
