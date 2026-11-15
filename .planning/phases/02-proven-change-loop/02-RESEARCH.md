# Phase 2: Proven Change Loop - Research

**Researched:** 2026-11-15 (inline, code reading only; no web sources needed for this phase's build work)
**Inputs:** 02-CONTEXT.md (D-01..D-16), ROADMAP Phase 2, REQUIREMENTS CODE-01/02/04, SURV-01/04/06

## 1. Refactor gate (CODE-01, D-12, D-13)

- No frame trace exists today (`grep -rn 'frame_hash\|trace' bench nethack_screensaver` finds none).
- `run_game(on_frame=...)` (`nethack_screensaver/game.py:290`, call at :350) is called once per env step with the
  full observation (`tty_chars`, `blstats`, `glyphs`, ...). It has existed long before the Phase 1 baseline commit,
  so **the worker can build the trace in `on_frame` without any change to bot code**, and old commits can be
  traced too (the worker script runs from the bench tree, `bench/runner.py:11 WORKER_SCRIPT`; game code comes
  from the commit's worktree on `PYTHONPATH`).
- Trace design (Claude's discretion): per step, `blake2b(tty_chars.tobytes() + blstats.tobytes(), digest_size=8)`;
  the file holds `(step:uint32, turn:uint32, digest:8 bytes)` records, 16 bytes per step; a 30k-step game is about
  480 KB, 100 seeds about 50 MB per commit. The game row carries the chained final digest so a pass needs no file
  read; files are read only to locate the first divergence.
- Storage: `$SCREENS_BENCH_DATA/traces/<sha>/<seed>.trace`; rows in `tool_games` with `tool = 'gate'` (tool runs
  never enter the natural funnel, Phase 1 D-17).
- Seeds: tool block 0-999 (D-17). Gate set = seeds 900-999 (100 seeds, documented constant `GATE_SEEDS` in
  `bench/seeds.py`). `gate` joins `TOOL_KINDS`.
- Watchdog endings depend on machine load (`play_compare.py` docstring; A/A seed 2073). A seed with a watchdog
  ending on either side is reported as `skipped`, never as pass; a gate with any skipped seed reports them and
  the verdict is `pass` only if all non-skipped seeds are identical and skipped <= 2.
- Existing comparator: `scripts/play_compare.py` compares result fields; the gate compares digests instead.

## 2. Commit labels and ratchets (CODE-02, CODE-04, D-14, D-15)

- `.git/hooks` holds only samples; `core.hooksPath` is unset. A tracked `githooks/` directory plus
  `git config core.hooksPath githooks` (install step in a script and in the README) is the simplest install.
- GSD tooling commits planning docs automatically (`gsd-tools commit`). A `commit-msg` hook that rejects every
  unlabelled commit would break those. Resolution: a `prepare-commit-msg` hook adds `Kind: docs` when every staged
  path is documentation (`.planning/**`, `*.md`), and `commit-msg` accepts `docs` only for such commits.
  **This adds a third label `docs` to D-14's two** for commits that touch no code. Flagged to the owner in the
  plan summary.
- Bench and script tooling (`bench/`, `scripts/`, `tests/`, `githooks/`) does not change how the bot plays. Rule:
  a commit touching `autoascend/` or `nethack_screensaver/` is `refactor` (needs `Gate: job <N>`) or `behavior`
  (needs `Stage:`, `Metric:`, `Experiment: job <N>` trailers; `Experiment: pending` allowed on the commit that
  precedes the run, with the job filled in by a later docs commit that cites it). Tooling-only commits use
  `Kind: refactor` without a gate line. The log test enforces the same rules from the Phase 2 start commit on.
- Phase 2 start commit: the commit that installs the hooks (recorded in `githooks/PHASE2_START`).
- Line counts today (`wc -l`): `agent.py` 2,142, `global_logic.py` 1,382, `inventory.py` 1,825,
  `objects/data.py` 1,046, `soko_solver/maps.py` 956. Limits go in a tracked `tests/ratchets.json` keyed by path;
  files not listed get the new-file cap 600. The test fails when a file exceeds its limit; a helper prints
  tightened limits when files shrink.
- Bare `except:`: one in `autoascend/item/item_manager.py`. Ratchet = count per file may not rise (AST walk for
  `ExceptHandler` with `type is None`).
- Agent internals: inside `autoascend/`, behaviour modules must not import `agent` (CLAUDE.md "keep behaviour
  modules free of agent imports"). Today only tests and `scripts/item_selftest.py` import `autoascend.agent`.
  Ratchet = the set of `(importing file, imported name)` pairs from `autoascend.agent` across `autoascend/`,
  `nethack_screensaver/`, `bench/` may not grow (tests and scripts are exempt).

## 3. Failure triage (SURV-01, D-09..D-11)

- Baseline job 7: 9,600 game rows with `job_id = 7` (`SELECT count(*) FROM games WHERE job_id=7` => 9600; the other
  400 of its 10,000 are reused rows). The triage reads rows by sha + seed window, not by job_id, so reused rows count.
- Fields available per game (`GameResult`): `end_reason`, `last_messages`, `hp_at_end`, `max_hp_at_end`,
  `hunger_at_end`, `xp_level`, `events`, `stage`, `milestone`, `depth_at_end`, `stuck_reports`, `ladder`.
  `bench/metrics.py` has `killer()` and `ended_stuck()` to reuse.
- Expected funnel gain (definition, Claude's discretion): for each game ending in group g, the gain is the
  conditional probability, estimated from all baseline games, that a game which reached the same last ladder rung
  goes on to reach the next rung. Summed over the group's games, this is the expected number of extra next-rung
  arrivals if that ending were removed. Deterministic, no LLM, one command.
- Replay check: `scripts/rewind.py` and `run_game(seed, max_steps)` replay exactly. For each top group, replay
  N = 5 sampled seeds to `turns_at_end - 50` (stop through `on_frame` once `blstats` turn reaches it), dump the
  screen, visible monsters and status, and write them next to the label for a human check. Replays are seeds
  1,000-10,999 replayed outside the bench: they write files only, never DB rows.

## 4. Character choice (SURV-06, D-01..D-04)

- `CHARACTER = "val-hum-fem-neu"` at `nethack_screensaver/game.py:40`.
- `plan_for` (`autoascend/plans.py:123`): human, elf, orc pilgrims go Sokoban first; dwarves and gnomes Mines first.
  `ROLE_TIERS["strong"] = (bar, sam, val, mon)`. `choose_strategy(role, rng)` picks strategy by tier weights, so a
  role change can also change the strategy mix: the A/B compares "character plus its plan" (D-03).
- Experiment API: `App.start_experiment(candidate, baseline, metric, mde, discordance, ...)`
  (`bench/server.py:112`) needs the MDE and a discordance; `DEFAULT_DISCORDANCE` 0.019 fits small changes only. A
  character change makes most games differ, so discordance must be estimated from a 200-seed pilot of each
  finalist against job 7 rows (pairs that disagree on dlvl10) and passed explicitly.
- With 2-3 finalists against one baseline, each comparison uses alpha = 0.05 / k (Bonferroni), declared beforehand.
- Window: dev seeds starting at 1,000, so the baseline side reuses job 7 rows of commit
  e5b5a7f525bc51b8008f665173600aba80de466d; each candidate commit must differ from it only in `CHARACTER` (checked
  with `git diff`).

## 5. Mines branch staircase (SURV-04, D-05..D-08)

- `autoascend/glyph/nh5.py:17` maps `S_brdnstair` to `S_dnstair` in `CANONICAL`, applied to every observation at
  `autoascend/agent.py:493`. After that the branch staircase cannot be told apart.
- Smallest change: before canonicalisation, record the positions whose raw glyph is the branch down-stair into a new
  `Level.branch_stairs` set (canonical glyphs stay as they are, so no other code changes behaviour).
- Today `explore_stairs` (`exploration_logic.py:106`) picks a random unexplored stair; `levels_to_explore_to_get_to`
  searches DoD 2-4 for the Mines. New pure module `autoascend/branch_stairs.py` decides per stair: wanted
  (milestone wants the Mines and stair is the branch stair), avoided (milestone does not want the Mines and stair is
  the branch stair), neutral.
- Accidental arrivals: `_on_wrong_branch` (`global_logic.py:296`) covers only FIND_SOKOBAN. D-07 extends it to any
  milestone that does not want the Mines: go back up at once.
- Evidence: `.planning/research/MINES-ENTRY-NH5.md` (17 of 50 accidental arrivals died on that first visit).
- Metric per D-08 is pre-registered from the triage and the fresh baseline at the chosen character, not fixed here.

## Open items for the owner

1. The `docs` label (section 2) is an addition to D-14.
2. The triage group list is reviewed by the owner once before it ranks anything (D-11): a checkpoint in plan 02-03.
3. The character shortlist and the pre-registration (MDE, alpha, discordance) are shown before the runs start:
   a checkpoint in plan 02-04.
