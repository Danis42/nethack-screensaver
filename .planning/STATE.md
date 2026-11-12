---
gsd_state_version: "1.0"
current_phase: 01
current_phase_name: Measurement and Proof Foundation
status: executing
stopped_at: Completed 01-14; pilot jobs 3-6 running (3 started, 4-6 queued); next 01-15 when job 6 is done; 01-06 paused at its checkpoint
last_updated: "2026-11-12T23:06:06.107Z"
last_activity: 2026-11-12
last_activity_desc: Phase 01 execution started
state_head: b83ca3227a7c1f81ac7ba249b2507a27ad116a1b
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 16
  completed_plans: 13
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-12)

**Core value:** The bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds and no reseeding. Every claim of progress toward it can be checked.
**Current focus:** Phase 01 — Measurement and Proof Foundation

## Current Position

Phase: 01 (Measurement and Proof Foundation) — EXECUTING
Plan: 14 of 16
Status: Ready to execute
Last activity: 2026-11-12 — Phase 01 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

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

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1] RESOLVED by 01-01 (commit 937ef5c, fresh_clone_check passed): NLE builds only from the gitignored `reference/nle-src`; a fresh clone can't `uv sync` (blocks everything)
- [Phase 1]: Live bench DB is empty; all reference numbers (58.3% Mines, 14.5% starvation, 1.1% Medusa) are from the archived `72ca0b6` baseline until re-measured
- [Phase 4]: Explorer stuck root cause unknown (research needed)
- [Phase 5]: Natural Medusa arrivals are rare (25/2304), so the needs-met rate has wide intervals until Phase 4 raises arrivals; AC gap cause still open
- [Phase 5]: Medusa reach bar is still an open owner decision, to be set from the first measurement
- [Phase 6]: No code yet for Gehennom, Quest, towers, invocation or Planes
- 01-06 paused at a blocking checkpoint: Sokoban hand game (seed 7) unsolved at T42; owner chose to run 01-10..01-13 first; 01-14 needs 01-06

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-11-12T23:06:05.999Z
Stopped at: Completed 01-14; pilot jobs 3-6 running (3 started, 4-6 queued); next 01-15 when job 6 is done; 01-06 paused at its checkpoint
Resume file: None
