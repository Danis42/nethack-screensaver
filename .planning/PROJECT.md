# screens — NetHack terminal screensaver driving the AutoAscend bot

## What This Is

screens is a zsh terminal screensaver: after 5 idle minutes the terminal switches to a live
NetHack game played by the AutoAscend bot (NeurIPS 2021 NetHack Challenge winner, rule-based,
vendored and ported to Python 3.13 / NLE 1.3.0). Any key returns to the untouched prompt.
The project has since become a bot-improvement effort: a local seeded, paired benchmark server
(`screens-bench`) judges every change to the bot, and the bot is being driven toward a real
ascension. One developer (the owner, who also watches the screensaver) and Claude as builder.

## Core Value

The bot achieves a real ascension on the pilgrim route. This is the only priority; every other
strategy and feature is parked behind it (user directive, 2026-10-21).

**Success metric:** the ascension ladder — 17 rungs (Mines, Minetown, Oracle, Sokoban, Sokoban
solved, Mines' End, Dlvl 15+, Quest, Medusa, Castle, Gehennom, Vlad's Tower, Wizard's Tower,
invocation, Planes, Astral, ascended). A game scores the highest rung it reached. Progress is
climbing rungs, judged on the seeded paired bench; the end state is rung 17 ("ascended").

## Requirements

### Validated

<!-- Already built and working on local main (HEAD 90ad9a0). Not phases to build. -->

- ✓ Screensaver: zsh `TMOUT`/`TRAPALRM` idle hook, launcher that always restores the terminal, any key exits and is swallowed, 80x24 centered diff renderer, `config.toml`, `games.jsonl` game log, SIGWINCH/too-small handling, watchdog — v0.1.0 (2026-10-17)
- ✓ AutoAscend port: vendored upstream `8527910`, Python 3.13 / NLE 1.3.0 / gymnasium wrapper, per-step callback, every port change logged in `autoascend/PORTING.md` — v0.1.0
- ✓ Secret strategies (pilgrim, daredevil, sightseer, treasure), escape recognition, `reveal_goal`, outcome field, smart pacing (`fast_delay`), Sokoban solver fixes — v0.2.0 (2026-10-18)
- ✓ Crash reduction 9 -> 2 per 576 games (Overtaxed drops, refused armour, 80-char inventory lines, worn rings, containers, pit-edge items, wounded-legs kicking) plus an unstick safety net (`unsticks` in results) — 2026-10-21
- ✓ Bench server `screens-bench`: stdlib HTTP server on 127.0.0.1:8765, JSON API, live status page, MCP tools (`.mcp.json`), SQLite store, one git worktree per commit, 11 `nice`d workers, baseline/experiment jobs, checkpoints 192/384/576/1152 games, `serve`/`wait`/`prune`/`import` CLI — 2026-10-20
- ✓ Real-ascension import: 687 hardfought.org ascensions in the bench database as the yardstick, with dumplog parsing and an Ascenders summary — 2026-10-20
- ✓ Ascension ladder (roadmap sub-project 0): 17 rungs in `autoascend/ladder.py`, `GameResult.ladder` / `rung`, bench metrics `rung` and `rung1`..`rung17`, ladder table against the yardstick; first baseline (mixed strategies, 576 games) recorded in `PORTING.md` — 2026-10-21 (main `2653410`)
- ✓ Ascension-only switch: `Config.strategy` defaults to `"pilgrim"`; `strategy = "random"` brings the other plans back — 2026-10-21 (`dbab398`)
- ✓ Seeded, paired bench: `run_game(seed=...)`, worker protocol `play <seed>`, scheduler hands out seeds 0..N-1 per commit, paired (Wald) verdict — merged 2026-10-22 (`9ff6a6f`). Its own acceptance check (the seeded A/A control) has not been run yet; that is Phase 1 work.

### Active

<!-- Roadmap sub-projects 1-8 from docs/ROADMAP.md, one phase each. Detail: REQUIREMENTS.md. -->

- [ ] Phase 1 — Midgame survival, Dlvl 4-12: sharpen-and-baseline the bench, then cut the deaths that end most games on Dlvl 4-8 (rungs 2-6)
- [ ] Phase 2 — Real descent past Mines' End and the Big Room, reliably finding downstairs (rungs 6-8)
- [ ] Phase 3 — Gearing up: wands, rings, armour, protection, reflection, magic resistance (rungs 7-9)
- [ ] Phase 4 — Medusa's level (rung 9)
- [ ] Phase 5 — Castle and wishes (rung 10)
- [ ] Phase 6 — Quest: XL 14, Bell (rung 8)
- [ ] Phase 7 — Gehennom: Vlad's Tower, Wizard's Tower, invocation (rungs 11-14)
- [ ] Phase 8 — Elemental and Astral Planes, ascension (rungs 15-17)

### Out of Scope

- Improving or measuring daredevil / sightseer / treasure — ascension-only priority; the plans stay built but parked behind `strategy = "random"`
- Pushing to any remote, opening PRs, adding remotes — git is local only
- Releasing, packaging or distributing the screensaver; shells other than zsh; a shared-game daemon; other bots (LLM, simple bot) — screensaver spec "out of scope"
- Resuming a game across idle sessions — NLE has no clean save/restore
- Bench ttyrec recordings, remote access to the bench, a web framework for it — bench spec "out of scope"
- ML / RL (torch, ray) combat scoring — AutoAscend is rule-based; removed in the port
- Showing the strategy during play, weighting strategies unevenly, showing rungs on the screensaver — earlier specs; not planned
- Re-trying dropped ideas without a new approach: resting on Elbereth, waiting for peaceful monsters, smarter hidden-passage search, digging down, pushing boulders, fighting packs from doorways (`choke-points`), judging monsters by NetHack's numbers (`threat-model`), fleeing upstairs from insects (`flee-upstairs`). One exception: REQUIREMENTS.md SURV-05 re-judges the three branches once on the sharper seeded bench.

## Context

**Current numbers (the only ones on record, all from the mixed-strategy era).** First ladder
baseline, 576 games of main `2653410`: Mines 57%, Minetown 29%, Oracle 22%, Sokoban 9%, Sokoban
solved 5%, Mines' End 4%, Dlvl 15+ 2%, Quest 1 game, nothing higher; median game rung 1, Dlvl 5,
5258 turns. Pilgrims reached Minetown+ in 35% of 1152 games, the other plans in 20%. These numbers
are not comparable with pilgrim-only runs; a new pilgrim-only baseline is Phase 1 work.

**Yardstick (687 real ascensions, 131 with timelines):** median turn Mines 1173, Minetown 3538,
Sokoban 9022 (solved 12412), Mines' End luckstone 10853, Quest 22426, Medusa 29317, Bell 30475,
Gehennom 34155, Vlad 44189, invocation 49741, Astral 53518, ascended 53630. At the end: magic
resistance 100%, bag of holding 99%, reflection 83%, median XL 23, AC -38; wands of teleportation
89%, death 83%, digging 64%. Our bot: median game about 4900 turns, ends on Dlvl 5, best games Dlvl 10-22.

**Killers worth attacking:** starvation about 13% of games, wand/ray users about 8%, soldier ants
and killer bees about 8%.

**Bench noise.** Unseeded: two identical 576-game halves differ by 3.6 points; an A/A control
(same code both sides, 1152 games each) read -2.3 [-5.9, +1.2]; the smallest detectable difference
was about 3.5 points, so real 1-3 point gains were invisible. Seeded pairing (same character and
dungeon per game number) is meant to remove that dungeon luck.

**Human game data.** NLD-NAO part `aa` (39,210 alt.org games, 510 ascensions) unpacked at
`/ssd2/nethackFiles/nld-nao-unzipped/`, index `/ssd2/nethackFiles/db/nld.db` (`nle.dataset`).
Soldier-ant study: survivors went upstairs 31% vs 6%, met the ant at full HP (100% vs 80%), Elbereth
no difference.

**Dropped ideas (all recorded in `autoascend/PORTING.md`).** Threat model in three variants (worse,
then two "no difference"), flee-upstairs ("no difference"), choke-points ("no difference"); earlier
Elbereth resting, waiting for peacefuls, smarter hidden-passage search, digging down, boulder pushing.
Unmerged branches: `threat-model`, `flee-upstairs`, `choke-points`, plus an older `survival-tuning`
(last commit: status notes).

**Codebase.** `autoascend/` (vendored bot; `agent.py` 1646 lines, `global_logic.py` 899, `strategy.py`,
`plans.py`, `ladder.py`), `nethack_screensaver/` (player, game, render, config, gamelog), `bench/`
(server, scheduler, store, metrics, stats, report, importers, reference, mcp_server, worker, runner,
gitrefs), `tests/` (default run: 247 passed, 5 skipped, 13 deselected on 2026-10-22). Map: `.planning/codebase/`.
Known tech debt (agent.py god module, unfinished `character.py` parsers, bare `except:` in item parsing,
module-level caches, bench-server hardening) is tracked as deferred in REQUIREMENTS.md.

**Working method.** `docs/STATUS.md` records the project's method as superpowers (brainstorm, spec,
plan, then build), "not GSD"; specs live in `docs/superpowers/specs/`, plans in `docs/superpowers/plans/`.
`.planning/` was added on 2026-10-22 by a GSD ingest of those docs. How the two coexist is the owner's call
(see STATE.md concerns). `docs/ASCENSION-GUIDE.md` (the human route, step by step, mapped to rungs and
sub-projects) exists but was left out of the ingest on purpose; read it as background for Phases 2-8.

## Constraints

- **Tech stack**: Python `>=3.13,<3.14` with `uv`; `nle==1.3.0` exact pin (NetHack 3.6.6); numpy, numba, opencv-python-headless, scipy, toolz; no torch, ray, pandas or matplotlib. Changing `nle` needs the full suite plus a fresh bench baseline.
- **Platform**: Linux/POSIX terminal, zsh hook; the NLE screen is 80x24 (80x25 with the status line).
- **Git**: local only. Never push, never add remotes, never open PRs. Finished, tested branches are merged to `main` locally without asking (owner's standing rule). Only committed code can be benchmarked.
- **Measurement**: every behaviour change is one change per experiment, judged on the seeded paired bench (`screens-bench`) against a stored pilgrim-only baseline; checkpoints 192/384/576/1152 games per side (99% interval early, 95% at 1152). "No measurable difference" is not a win. Single 576-game unpaired runs mislead (286 vs 262 was noise). Results and dropped ideas are logged in `autoascend/PORTING.md`.
- **Bench**: server on `127.0.0.1:8765` only; 11 workers under `nice -n 10`; DB `~/.local/share/screens-bench/results.db`; `bench/worker.py` imports nothing from `bench` (old commits' worktrees lack it); a pinned role with a seed is refused (the role loop never matches a fixed seed).
- **Bot code**: agent logic stays as upstream except for deliberate, measured changes; `autoascend/ladder.py` stays standard-library only (the bench imports it); a ladder error must never crash or end a game; a rung reached while hallucinating must not be recorded.
- **Quality gate**: `uv run pytest -q -m ""` green before and after each change; no new exception types in a 576-game run; the screensaver must still never leave the terminal broken or crash on screen.
- **Play style**: cheesy tactics are allowed; an exciting deep run that dies beats a boring escape (owner's preference).

## Key Decisions

<!-- No ADRs exist in the source set, so nothing here is ADR-locked. These are owner directives and
     SPEC design decisions; they bind future work but can be revisited by the owner. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Main objective is a real ascension (2026-10-20); ascension is the only priority (2026-10-21) | The screensaver is eye candy; the bot's strength is the interesting problem | — Pending |
| Success is a 17-rung ladder in the median order of 687 real ascensions | A binary "ascended" signal is too rare to steer by; rungs give partial credit | ✓ Good (recorded live, baseline measured) |
| Every game plays the pilgrim route; other plans behind `strategy = "random"` | Mixed strategies diluted every measurement (pilgrim 35% vs others 20% Minetown+) | ✓ Good |
| Every game is a dwarvish Valkyrie until the first ascension (2026-10-23, `0b09707`); `CHARACTER = "@"` brings random roles back | Melee roles reach Minetown 45-51% vs 8-17% for weak starts; BotHack (first bot ascension, 2015) also played only dwarvish Valkyries; Mines natives are peaceful to dwarves | — Pending (new baseline and A/A) |
| Vendor rule-based AutoAscend rather than write or train a bot | Upstream won the NeurIPS 2021 challenge; no ML dependencies | ✓ Good |
| Every change measured on the local bench; one change per experiment | Intuition about bot changes was repeatedly wrong (threat model, flee, choke-points) | ✓ Good |
| Seeded, paired experiments replace independent samples | Unseeded noise (about 3.5 points) hid real 1-3 point gains | ✓ Replays exactly (A/A job 10); resolution weaker than hoped: a bot-RNG change alone flips 32% of seeds on rung2 (job 11) |
| Code under test is always a git commit run from a worktree | Reproducible, baselines reusable per SHA | ✓ Good |
| Rungs 9-17 start as simple proxies, refined when their phase arrives | Rungs 1-8 must be accurate now; later ones cannot be exercised yet | — Pending |
| Local git only; merge finished tested branches to `main` | Owner's standing rule | ✓ Good |
| Workflow is superpowers (brainstorm, spec, plan, build) per `docs/STATUS.md` | Owner's method before the GSD ingest | ⚠️ Revisit (GSD now also tracks the roadmap) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:** requirements invalidated -> Out of Scope with reason; validated ->
Validated with the phase reference; new requirements -> Active; decisions -> Key Decisions; "What This
Is" still accurate?

**After each milestone:** full review of all sections; Core Value check; audit Out of Scope; refresh
Context with the latest ladder numbers.

---
*Last updated: 2026-10-22 after roadmap creation from the doc ingest*
