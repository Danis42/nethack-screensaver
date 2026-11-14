---
gsd_state_version: "1.0"
current_phase: 2
current_phase_name: Proven Change Loop
status: planning
stopped_at: Phase 1 complete, ready to plan Phase 2
last_updated: "2026-11-14T12:31:35.488Z"
last_activity: 2026-11-14
last_activity_desc: Phase 1 complete, transitioned to Phase 2
state_head: fa85424c81a5df48323ead6145cc2f59d6761cf5
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 16
  completed_plans: 16
  percent: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-14)

**Core value:** The bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds and no reseeding. Every claim of progress toward it can be checked.
**Current focus:** Phase 2 — Proven Change Loop

## Current Position

Phase: 2 — Proven Change Loop
Plan: Not started
Status: Ready to plan
Last activity: 2026-11-14 — Phase 1 complete, transitioned to Phase 2

Progress: [█░░░░░░░░░] 14%

## Performance Metrics

**Velocity:**
- Total plans completed: 16
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 16 | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 10 min | 3 tasks | 7 files |
| Phase 01 P02 | 5 min | 3 tasks | 8 files |
| Phase 01 P03 | 5 min | 3 tasks | 6 files |
| Phase 01 P04 | 3 min | 2 tasks | 4 files |
| Phase 01 P05 | 16 min | 3 tasks | 14 files |
| Phase 01 P07 | 6 min | 2 tasks | 8 files |
| Phase 01 P08 | 6 min | 2 tasks | 11 files |
| Phase 01 P09 | 2 min | 2 tasks | 7 files |
| Phase 01 P10 | 4 min | 2 tasks | 10 files |
| Phase 01 P11 | 8 min | 3 tasks | 13 files |
| Phase 01 P12 | n/a | 2 tasks | 13 files |
| Phase 01 P13 | n/a | 2 tasks | 10 files |
| Phase 01 P14 | n/a | 3 tasks | 2 files |
| Phase 01 P06 | n/a | 2 tasks | 8 files |
| Phase 01 P15 | n/a | 3 tasks | 9 files |
| Phase 01 P16 | n/a | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Measurement and proof come first (Phase 1); no experiment runs before the fresh baseline, A/A and claim check exist
- [Roadmap]: LLM analyst and pilot built early (Phase 3), local Ollama first, Claude Code only where local isn't good enough, no extra cost; may run alongside Phase 4; pilot runs stay in `tool_games`
- [Roadmap]: Character fixed early in Phase 2 by research plus paired A/B, so later work uses the final `CHARACTER`
- [Roadmap]: Castle route chosen by staged pass rate (Phase 5); per late stage the better of scripted and pilot is kept (scoreboard, Phase 5 onward)
- [Roadmap]: Farming and exploits are owner gates (Phases 5, 6, 7); `lgen` screening already approved, rule committed first
- [Phase 01]: 01-01: nle is a git source (file://$HOME/git/nle-screens.git) pinned by full commit cb9d6572; bare repo has no remote, no backup tooling (D-01..D-04)
- [Phase 01]: 01-01: env_id hashes nle_commit, lock_sha256, python, numpy, numba and ignores the interpreter path
- [Phase 01]: Beta(1,1) mixture always-valid test (log LR >= log(1/alpha)) is the bench decision rule; exact McNemar reported alongside; simulation shows 1.1-3.7% false positives vs 7.0-7.7% legacy (job-free proof: 01-SIM-SEQUENTIAL.json seed 20261112)
- [Phase 01]: Sequential looks are contiguous seed prefixes only; sequential power simulated per 96-seed block with common random numbers; DEFAULT_DISCORDANCE stays None until plan 01-15
- [Phase 01]: Claim checker runs as a Stop hook; negated progress words are not claims; proofs inside inline code count — MEAS-09 / D-09..D-11: unproven progress claims must be blocked mechanically
- [Phase 01]: Fact ledger facts/FACTS.toml with three tags; code cites '# fact:<id>', notes '[fact:<id>]'; pytest fails on dangling citations — MEAS-10 / D-13..D-16
- [Phase 01]: Ladder has 18 rungs with quest_portal before quest; new stats counters must be registered in StatsLogger (KeyError otherwise); pilot and baseline need a commit at or after 4d7a342 — D-21, MEAS-03/04; play_compare 20/20 identical
- [Phase 01]: Fact tranche 1 (bot modules): 56 of 59 facts verified in the 5.0 source; prayer marker 'You feel better.' is not a 5.0 prayer message — MEAS-10, D-13/D-14/D-16
- [Phase 01]: Bench store schema 2: games keyed by (sha, seed, lgen mode, env_id, rep); jobs play explicit half-open seed windows and record env + lock blob — MEAS-07/MEAS-01/MEAS-04
- [Phase 01]: Fact tranche 1 complete: 66 ledger entries (63 5.0-source, 3 unverified); tranche 2 starts with the table files (soko maps, objects data, monflag, screen symbols) — MEAS-10, D-20 coverage ranking
- [Phase 01]: Seed ranges enforced at API, scheduler and store; final seeds only for clean_attempt jobs, which HTTP/MCP cannot create; confirm windows need a gate — D-07, D-17, D-22, MEAS-07
- [Phase 01]: Bench jobs resume under their own id (serve --resume); 'started' means a game row exists on every surface; tool runs record into tool_games — D-08, MEAS-08, MEAS-09
- [Phase 01]: 01-14 lgen pilot (owner, 2026-11-12): commit B = exp/elbereth-respect ported onto commit A; rule-strict; primary metric dlvl10 (owner delegated the metric: change fires mostly at Dlvl 5-8 via S_HUMAN elves/watch, so dlvl6 is settled before it acts; dlvl10 base ~32% in 81 screensaver games). Pre-registered in 01-LGEN-PILOT.md at Task 3.

- [Phase 01]: 01-15 lgen pilot decision keep-lgen-off (rule-strict; psi_on - psi_off +0.005, 95% [-0.0070, +0.0170]; jobs 3/4/5/6); DEFAULT_DISCORDANCE 0.019 is small because commit B changes little: pass --discordance for bigger changes
- [Phase 01]: 01-15 baseline commit e5b5a7f525bc51b8008f665173600aba80de466d (= bot of main), lgen off, job 7 (10,000 games, 400 reused); A/A job 8 (seeds 1000-2999, rep 1); pre-registered in 539b31e

- [Phase 01]: 01-16 A/A pass (1,999/1,999 identical, seed 2073 watchdog on both; job 8); Sokoban zero = all 2,256 drops are sokoban_unsolvable on the entry level (dunlev 4); open: which push fails first

- [Phase 01]: UAT 2026-11-14 (owner): prohibitions reworded/dropped. #2 now = no online LLM, network or paid API in claim checking (local LLM allowed); #4 source-quote, #5 seed-range/clean_attempt surface, #6 dungeon screening, #7 archive import dropped as prohibitions; their code guards stay as tooling

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1] RESOLVED by 01-01 (commit 937ef5c, fresh_clone_check passed): NLE builds only from the gitignored `reference/nle-src`; a fresh clone can't `uv sync` (blocks everything)
- [Phase 1] RESOLVED by 01-16: fresh baseline job 7 (10,000 games) replaces the archived `72ca0b6` reference numbers; funnel in 01-BASELINE.md
- [Phase 4]: Explorer stuck root cause unknown (research needed)
- [Phase 5]: Natural Medusa arrivals are rare (25/2304), so the needs-met rate has wide intervals until Phase 4 raises arrivals; AC gap cause still open
- [Phase 5]: Medusa reach bar is still an open owner decision, to be set from the first measurement
- [Phase 6]: No code yet for Gehennom, Quest, towers, invocation or Planes
- [Phase 2] Sokoban: all 2,256 Sokoban drops in job 7 are sokoban_unsolvable on the entry level; which push fails first is open

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-11-14T12:35
Stopped at: Phase 1 complete, ready to plan Phase 2
Resume file: None
