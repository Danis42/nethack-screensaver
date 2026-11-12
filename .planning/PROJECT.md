# NetHack Screensaver: Ascension

## What This Is

A terminal screensaver that plays NetHack 5.0 after the zsh prompt has been idle, driven by
AutoAscend, a hand-written rule/strategy bot ported to Python 3.13 / NLE 1.3.0. A benchmark
system (`bench/`) plays thousands of headless games per git commit and compares versions.
The project now aims at one goal: make the bot ascend. It's for the owner's own terminal and
curiosity, not for a product or for customers.

## Core Value

**The bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds
and no reseeding. Every claim of progress toward it can be checked.**

## Requirements

### Validated

<!-- Inferred from the existing code at 742b9e1 and the archived bench database (146,743 games). -->

- ✓ Screensaver starts on zsh idle, renders the bot's game with pacing, exits on any key — existing
- ✓ Bot plays complete NetHack 5.0 games through NLE (perception, glyph handling, actions, strategies, milestone plans) — existing
- ✓ Bot reaches mid-game regularly: in baseline `72ca0b6` (2304 natural games), 76% reach the Mines, 25% Sokoban or Mines' End, 8% Dlvl 15+ or the Quest portal, 1.1% Medusa's level — existing
- ✓ Bench runs many games per commit in parallel worktrees, stores results in SQLite, reports per-rung ladder metrics, and exposes MCP tools — existing
- ✓ Games are deterministic per seed (A/A run identical), so the same seed can be replayed and compared across commits — existing
- ✓ Test tools exist: rewind (`scripts/rewind.py`), staged starts near late levels (`scripts/staged_run.py`), scenarios (`scripts/scenario_run.py`), hand-play (`scripts/handplay.py`), human-game study on NLD (`scripts/nld_study.py`) — existing
- ✓ Large body of NetHack 5.0 research notes in `.planning/research/` (route, Medusa, Castle, food, prayer, wishes, survival) — existing

### Active

- [ ] Compare the possible routes to an ascension with evidence (prior NetHack bots, learning from human games, LLM as offline analyst or in-game planner, scenario and ability testing, statistics, large-scale search) and choose one before building
- [ ] A progress funnel on natural games from start to ascension (per-stage pass rates with confidence intervals) is the main metric; staged and rewind runs are test tools only
- [ ] The early wall is fixed by system, not by monster: food (about 14% starve), escape and HP management, getting stuck, resource and item use
- [ ] The late wall is fixed: the bot gets the missing late-game abilities (cross Medusa, enter and pass the Castle, Gehennom, Vlad's Tower, Wizard's Tower, invocation, Elemental Planes, Astral), each testable on its own
- [ ] The bot code stays clean: `autoascend/agent.py` (2142 lines) and `autoascend/global_logic.py` (1362 lines) split into understandable modules, guarded by a deterministic regression gate
- [ ] Every progress claim in a session has proof: bench job ID, commit hash, or a reproducible database query; no "started" without a checkable job
- [ ] One fresh, clean ascension recorded (seed, commit, dumplog), reproducible from the seed

### Out of Scope

- Counting a rewound, reseeded or staged game as the ascension — only allowed as test tools; the goal is one clean game
- Per-monster special-case fixes as the main method — this caused the last session's whack-a-mole, messy code and stalled progress
- Changing the screensaver experience (rendering, pacing, idle hook) — it works; only touched if the bot work needs it
- Supporting NetHack 3.6 — the target is NetHack 5.0 through the local NLE build
- Heavy session bookkeeping (many "state:" commits, hand-kept tracker files) — progress lives in the bench and git, not in prose

## Context

- **Fresh start:** commit `af6684a` removed the old plans, state, phases, roadmaps and specs after the last session got stuck. Research notes and hand-game notes were kept. A full backup lives in `archive/` (`screens-v0-final.tar.gz`, `screens-all-branches.bundle`), including the old bench database (146,743 games over 87 commits).
- **Live bench database is empty:** `~/.local/share/screens-bench/results.db` has 0 games. History is only in the archive. A fresh baseline of `main` is needed before any comparison.
- **What went wrong last time:** whack-a-mole fixes, the code got messy, and the assistant claimed it had started workloads while it actually sat idle.
- **Where games end (baseline `72ca0b6`, 2304 games):** 24% never reach the Gnomish Mines; starvation 334 games; no natural game ever got past Medusa in any of the 146k stored games. "Castle 8/20" figures came from staged starts next to the Castle, not from natural games.
- **Two walls:** the rewind study (`.planning/research/REWIND-20.md`) gave 20 seeds infinite lives. Two thirds of deaths were close calls one reroll avoided, but even with infinite lives no seed got past Medusa. Early on it's survival; late it's missing abilities.
- **Known state from the codebase map** (`.planning/codebase/CONCERNS.md`): NLE is installed from `reference/nle-src`, which `.gitignore` excludes, so a fresh clone can't `uv sync`. There is an open Elbereth-ignorer bug at the Castle, 60+ TODOs, bare `except` blocks, and no CI. Several docstrings point to the deleted `.planning/STATE.md`.
- **Codebase map:** `.planning/codebase/` (STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS), mapped 2026-11-12.

## Constraints

- **Game:** NetHack 5.0 via the local NLE 1.3.0 build (`reference/nle-src`, branch `screens-nh5`) — that's what the screensaver plays
- **Language/runtime:** Python 3.13 with uv; the existing `autoascend` / `nethack_screensaver` / `bench` packages — existing code and tooling
- **Hardware:** one local Linux machine; bench has 10 worker slots — this limits how many games each experiment can play
- **Determinism:** the bench must stay deterministic per seed (no randomness that breaks A/A comparison); any non-deterministic component (e.g. an LLM) needs a plan for measurement
- **Proof:** no progress claim without a job ID, commit or query result the owner can check — trust was broken last time
- **Clean goal:** the final ascension must be one straight game with no human input, rewind or reseed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Goal is one clean ascension, not a rate | Owner's definition of done | — Pending |
| Rewinds, reseeding and staged starts allowed as test tools only | Useful for reaching and testing late stages; the goal must be a clean game | — Pending |
| Evaluate approaches with evidence before choosing one | Owner is open to anything given proof or convincing arguments; the per-monster method stalled | — Pending |
| Natural-game funnel is the main metric | Staged results (castle 8/20) hid that no natural game got past Medusa | — Pending |
| Every progress claim needs checkable proof | The last session claimed it started work while idle | — Pending |
| LLM role (offline analyst vs in-game planner) decided by the research, not up front | Strong offline; in-game costs money and breaks determinism | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-12 after initialization*
