# Handover: the NetHack ascension bot (frozen at `ascension-bot-v1`)

This file is for anyone who wants to pick up the bot work. It says what the project tried, what was built,
what was measured (every number with a bench job, a full commit or a query), what was learned, and where to
continue. The bot work stopped on 2026-11-18; after the tag `ascension-bot-v1` the `main` branch turns into a
screensaver that replays recorded games instead of playing live.

## Commit hashes in this repository

Before publishing, the history was cleaned: the author email became a GitHub no-reply address, and local home
paths and a few personal quotes in the notes were replaced in every commit. That changed all commit hashes. The
documents and the bench jobs quote the **original** hashes (e.g. baseline
`e5b5a7f525bc51b8008f665173600aba80de466d`); hashes inside commit messages were updated. `.planning/COMMIT-MAP.tsv`
maps each original hash to its published one. The bot and game code are unchanged, so a game played from either
commit is the same.

## 1. The goal

A terminal screensaver that plays NetHack after the zsh prompt has been idle. From 2026-10-21 on the project had
one goal: **the bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds and no
reseeding, and every claim of progress can be checked.**

It did not get there. No natural game of this bot has ever passed Medusa's level: 0 of 146,743 games in the
archived database (87 commits) and 0 of the 20,000 games of the two fresh baselines below.

## 2. What exists

| Part | Where | What it does |
|---|---|---|
| Bot | `autoascend/` | [AutoAscend](https://github.com/maciej-sypetkowski/autoascend) (winner of the NeurIPS 2021 NetHack Challenge, MIT, upstream @ 8527910), ported to Python 3.13, NLE 1.3.0 and NetHack 5.0. Rule/strategy bot: generator strategies (`strategy.py`), milestone plans (`plans.py`, `global_logic.py`), one big `Agent` (`agent.py`). |
| Screensaver | `nethack_screensaver/`, `bin/`, `zsh/` | zsh idle hook, launcher, renderer with pacing, game log. |
| Bench | `bench/` | Plays thousands of headless games per git commit (10 slots, each commit from its own worktree), stores them in SQLite, judges experiments with paired statistics, HTTP dashboard on :8765, MCP server for Claude Code. |
| Patched NLE | `vendor/nle/` (credits and our changes: `vendor/nle/SCREENS.md`; diff: `vendor/nle-screens.patch`) | [NLE](https://github.com/NetHack-LE/nle) moved to NetHack 5.0 (Lua 5.4.8 level files, 3.6-like default options, seed control for rewinds); upstream base `NetHack-5-upgrade` @ `2a0e3baf`. Same source as the NLE commit `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72` that the bench jobs record; seed 1001 replays identically to job 23. NetHack General Public License. |
| Tools | `scripts/` | `rewind.py` (replay with extra lives), `staged_run.py` (wizard-mode starts near late levels), `scenario_run.py`, `handplay.py`, `replay_check.py` (A/A identity), `triage_replay.py`, `futility.py`, `sim_sequential.py` / `sim_sprt.py` (statistics simulations), `nld_study.py` (human games from the NLD dataset), `wiki_sweep/`, `check_claims.py`. |
| Fact ledger | `facts/FACTS.toml` | NetHack facts the code relies on, each tagged "5.0 source", "measured" or "unverified"; code cites `# fact:<id>`, and a test fails on dangling citations. |
| Research | `.planning/research/` | 29 notes on NetHack 5.0 (route, Medusa, Castle, food, prayer, wishes, telepathy, AC, character choice, ...); see section 7. |
| Plans and proofs | `.planning/` | Roadmap, requirements, phase plans with summaries, pre-registrations, result files. |

Tests: `uv run pytest` (fast, about 920 tests at the last full run) and `uv run pytest -m slow` (real games).

## 3. How it was measured

The process was built because an earlier session made unverifiable claims. These rules held from Phase 1 on:

- **Determinism.** A game is fixed by (commit, seed, environment). A/A job 8 replayed seeds 1,000-2,999 of the
  baseline: 1,999 of 1,999 compared seeds identical (seed 2073 hit the watchdog on both sides).
- **Funnel, not "highest rung".** Each game logs the turn it first reached each stage (Mines, Minetown, Oracle,
  Sokoban, Mines' End, Dlvl 15, Quest portal, Quest, Medusa, Castle, ... Astral, ascended). Rates have Wilson
  intervals: `uv run python -m bench.cli funnel <sha> --lo 1000 --hi 11000 --lgen off`.
- **Seed ranges.** Dev seeds 1,000-10,999; confirm and final ranges are reserved, and the bench refuses final seeds
  outside a clean attempt.
- **Paired experiments.** Candidate and baseline play the same seeds; the decision uses discordant pairs (b, c),
  an always-valid sequential test (Beta(1,1) mixture, jobs up to 21) or a Wald SPRT (default from quick task
  261117-kpa), with exact McNemar alongside. Simulations: `01-SIM-SEQUENTIAL.json`, `261117-kpa-SIM-SPRT.json`.
- **Pre-registration.** Metric, MDE, alpha and seed window are committed before a job runs
  (e.g. `02-CHARACTER-PREREG.md`, `04-PREREG-TEMPLATE.md`).
- **Commit labels.** Every commit carries `Kind: refactor | behavior | docs`; bot changes need `Gate: job N`
  (refactor: games must stay identical) or `Stage:`, `Metric:`, `Experiment: job N` (`githooks/commit_kind.py`).
- **Claim check.** `scripts/check_claims.py` runs as a Claude Code Stop hook and blocks progress claims without a
  job ID, a full commit or a query.
- **Tool games apart.** Rewind, staged and scenario runs go to a separate `tool_games` table, never into the funnel.

## 4. Results

### Baselines (10,000 natural games each, dev seeds 1,000-10,999, lgen off)

| Stage | Job 7: Valkyrie (human, female, neutral), `e5b5a7f525bc51b8008f665173600aba80de466d` | Job 23: Monk (human, male, neutral), `b2b2bbe6d1c9341319b02e937aac7f37ec4db14d` |
|---|---|---|
| Gnomish Mines | 60.8% | 65.4% |
| Minetown | 21.4% | 24.9% |
| Oracle | 48.2% | 56.3% |
| Sokoban (entered) | 25.4% | 29.3% |
| Sokoban solved | 0 | 0 |
| Mines' End | 11.6% | 14.0% |
| Dlvl 10+ (`max_depth >= 10`) | 38.9% | 47.1% |
| Dlvl 15+ | 6.1% | 5.4% |
| Quest portal level | 4.6% | 4.8% |
| Quest | 4.2% | 3.5% |
| Medusa's level | 0.77% (77) | 0.64% (64) |
| Castle and beyond | 0 | 0 |

Source: `bench.cli funnel` for both commits (job 7 full JSON in
`.planning/phases/01-measurement-and-proof-foundation/01-BASELINE.md`), Dlvl 10 from
`SELECT avg(json_extract(json,'$.max_depth')>=10) FROM games WHERE job_id=23` (job 7: same over its commit and
window). Job 23 also: mean max depth 9.27, deepest 29, mean game length 9,604 turns.

Top causes of death in job 23: leocrotta 478, mumak 425, white unicorn 384, soldier ant 296, starvation 252,
troll 247, spotted jelly 198, owlbear 197, black unicorn 196, gargoyle 179 (`GROUP BY end_reason`, job 23).

### Bench jobs

| Job | Kind | What | Outcome |
|---|---|---|---|
| 1-2 | baseline | fresh-clone proof (10 games each, `e0229dc`) | install from a clean clone works |
| 3-6 | baseline | lgen pilot: does fixing the dungeon layout separately from the dice help? | keep lgen off (`01-LGEN-PILOT.md`) |
| 7 | baseline | Valkyrie baseline, 10,000 games | table above |
| 8 | baseline | A/A of job 7 on 2,000 seeds | identical |
| 9, 11 | gate | refactor gate, positive and negative proof | gate catches a behaviour change (`02-GATE-PROOF.md`) |
| 12-18 | baseline / gate | character pilots and Samurai parser fixes | see `02-04-SUMMARY.md` |
| 19 | experiment | dwarvish lawful Valkyrie vs job 7, Dlvl 10 | stopped for futility, no win |
| 20 | experiment | human lawful Samurai | worse (estimate -8.1 points) |
| 21 | experiment | human neutral Monk | **better** (+11.0 points, n 672); `CHARACTER = "mon-hum-mal-neu"` on main (`6e8a2c9a59a3dfddfa77f966efb1627410d93a7c`) |
| 22 | gate | visit log / trigger-gated experiments | passed |
| 23 | baseline | Monk baseline, 10,000 games | table above |
| 24 | baseline | pilot of the Mines change (`ae5b628`, branch `mines-candidate`) | interrupted at 554 of 960 games |
| 25 | baseline | pilot of the unicorn change (`a4431346d842cb5bda83227921c58d59cd6be8b7`, branch `unicorns`) | queued, never ran |

The bench database (about 29,000 games, 600 MB) was not published; the numbers above are the summary. An older
database with 146,743 games over 87 commits (NetHack 3.6 and early 5.0 work) is in the owner's local archive.

## 5. What was learned

1. **Two walls.** Early on the bot dies of survival problems (fights it should flee, food, getting stuck); late it
   lacks whole abilities. The rewind study (`.planning/research/REWIND-20.md`) gave 20 seeds up to 60 lives: 68%
   of 182 deaths were avoided by rerolling 100 turns back, yet even with near-infinite lives no seed passed Medusa.
   Crossing Medusa, the Castle, Gehennom, the Quest, the towers, the invocation and the Planes have no working code.
2. **Fix by system, not by monster.** The pre-Phase-1 work patched single monsters and the code got messy without
   moving the funnel. Measured changes that moved it were systemic (character choice: +11 points at Dlvl 10).
3. **Sokoban is never solved.** All 2,256 Sokoban drops in job 7 go through the "unsolvable" branch on the entry
   level: stored solution and live solver both fail (`01-SOKOBAN-CAUSE.md`). Which push fails first is still open.
4. **NetHack 5.0 differs** from the 3.6 the bot was written for: no Mines branch stairs shown before use,
   Elbereth rules, prayer messages, Sokoban maps, level files in Lua. The fact ledger records what was checked.
5. **Statistics matter.** 0 ascensions in 146,743 games bounds the rate at about 2e-5, so only funnel stages can be
   optimised; a single "it got deeper" game proves nothing. Paired seeds cut the needed games several times.
6. **Prior art.** No scripted bot has ascended NetHack 3.6 or later. Imitation learning (HiHack) and online RL
   score far below AutoAscend; whole-game LLM agents reach about Dlvl 2-3 (`.planning/research/STACK.md`).
7. **Speed.** About 30 games per minute on 10 slots; a 10,000-game baseline takes about 5.5 hours. The `speedup`
   branch saves 7-11% CPU with identical games on 5 seeds but was never gated.

## 6. Where to continue

Open work, in the order it was planned (`.planning/STATE.md`, `.planning/phases/02-proven-change-loop/.continue-here.md`):

1. **Finish the two pilots.** `uv run screens-bench serve --resume` resumes job 24 (Mines) and runs job 25
   (unicorns). Pre-registrations: `02-MINES-PREREG.md`, `04-02-PREREG.md`.
2. **Plan 02-05:** leave unwanted Mines levels at once (branch `mines-candidate`). Mines stairs cannot be
   recognised before use in 5.0, so "avoid entering" is impossible.
3. **Plan 04-01:** a Monk wears no shield (branch `monk-shield`).
4. **Death list of job 23:** leocrotta, mumak, unicorns, soldier ants, starvation (252 games), Cyclic Panic
   crashes (110 games, all of the "exception" endings) and no-progress aborts.
5. **Sokoban:** find the first failing push (above); the Sokoban prize is a big lever (reflection or magic resistance).
6. **Late wall:** staged contracts per stage (`staged_run.py`), starting with Medusa (`MEDUSA-NH5.md`) and the
   Castle (`.planning/ROADMAP.md`, Phases 5-7).
7. **Ideas discussed, not started:** a parallel late-game track on staged games; the big levers (Sokoban prize,
   protection, 5.0 Elbereth, Castle wish); a small local fine-tuned model for narrow decisions judged on the bench;
   an LLM late-game pilot that stays outside the deterministic bench (`ROADMAP.md`, Phase 3).

Unmerged branches: `mines-candidate`, `mines-follow-plan`, `monk-shield`, `unicorns`, `speedup`, the character
finalists `char/*`, and proof branches (`gate-negative`, `pilot/lgen-b`, `proof/fresh-clone`).

## 7. Reading map

| Start with | Why |
|---|---|
| `.planning/PROJECT.md` | Goal, constraints, key decisions |
| `.planning/ROADMAP.md` | The seven planned phases and their success criteria |
| `.planning/research/SUMMARY.md` | Research summary: approaches, two walls, what not to do |
| `.planning/research/STACK.md` | Approaches compared (scripted, LLM, RL, search) |
| `.planning/phases/01-.../01-BASELINE.md` | Baseline and A/A, with commands |
| `.planning/phases/02-.../02-CHARACTER-RESULT.md` | A full worked experiment |
| `.planning/research/REWIND-20.md` | The two-walls evidence |
| `.planning/research/ASCENSION-PLAN-NH5.md`, `ASCENSION-PLAYBOOK-NH5.md` | A route to ascension for this bot |
| `.planning/codebase/` | Code map: stack, architecture, conventions, testing, concerns |
| `facts/FACTS.toml` | Checked NetHack 5.0 facts |

## 8. Reproduce

```sh
git clone https://github.com/Danis42/nethack-screensaver && cd nethack-screensaver && git checkout ascension-bot-v1
uv sync                                  # builds the patched NLE from vendor/nle (needs cc, cmake)
uv run pytest
uv run screens-bench serve               # dashboard on http://localhost:8765
uv run python -m bench.cli funnel e5b5a7f525bc51b8008f665173600aba80de466d --lo 1000 --hi 11000 --lgen off
```

Seeded games repeat only with the same NLE source, `uv.lock` and the fixed-clock shim (`nethack_screensaver/fixed_clock.py`);
the bench sets `PYTHONHASHSEED=0` and single-thread BLAS. Each job records an `env_id` built from these. Jobs 1-25 recorded the NLE as git commit `cb9d6572`; since NLE
lives in `vendor/nle` the bench records the folder's git tree id instead (`bench/nle_build.py`), so new jobs get a
new `env_id` although the games are the same.
