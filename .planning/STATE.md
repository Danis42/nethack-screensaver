---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: 01
current_phase_name: Midgame Survival
status: executing
stopped_at: Completed 01-01-PLAN.md
last_updated: "2026-10-23T16:24:45.504Z"
last_activity: 2026-10-23
last_activity_desc: Phase 01 execution started
state_head: ddca9c3d31ec49a90b8efc04a1b66dbce621e5f5
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 16
  completed_plans: 1
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-22)

**Core value:** The bot achieves a real ascension on the pilgrim route (the only priority).
**Current focus:** Phase 01 — Midgame Survival

## Current Position

Phase: 01 (Midgame Survival) — EXECUTING
Plan: 2 of 16
Status: Ready to execute
Last activity: 2026-10-23 — Phase 01 execution started

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
| Phase 01 P01 | 6 min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Full log in PROJECT.md Key Decisions. Recent, affecting current work:

- [Pre-roadmap]: Ascension is the only priority; every game plays the pilgrim route (`strategy = "pilgrim"`), others behind `strategy = "random"`
- [Pre-roadmap]: Every change is one experiment on the seeded paired bench; "no measurable difference" is not a win
- [Pre-roadmap]: Git is local only; finished tested branches merge to `main` locally
- [Phase 01]: 01-01: fix_moon_phase=seed is not None - only seeded bench games are calendar-independent, screensaver keeps the real moon
- [Phase 01]: 01-01: _DeathContext observes observations only; agent reads (_food_at_end/_events) happen after the game

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1] The seeded A/A control and the pilgrim-only baseline have not been run; all stored numbers predate the pilgrim-only switch and are not comparable (PORTING.md baseline, `choke-points` 1152 games, `aa4b1cf` 576 games).
- [Phase 1] `docs/STATUS.md` and `handoff.txt` (identical copies) still list "seed both sides" as the next step, but the seeded bench is already merged (`9ff6a6f`); both are stale on that point. Not edited by this roadmap pass.
- [Workflow] `docs/STATUS.md` says the method is superpowers (brainstorm, spec, plan, build), "not GSD"; `.planning/` now also tracks the roadmap. Owner to decide how the two coexist when planning Phase 1.
- [Phase 1] Unmerged branches to re-judge or leave dropped: `threat-model`, `flee-upstairs`, `choke-points`; an older `survival-tuning` also exists. They predate pilgrim-only and seeding, so a rebase may be needed.
- [Phase 1] Human-game studies need the NLD-NAO data at `/ssd2/nethackFiles/` (`nld.db`) to be mounted.
- [Phases 4-8] Nothing above rung 8 has been reached in natural play; these phases depend on the staged-start harness (STAGE-01, whose `wizard=True` route is unvalidated against `NetHackChallenge` and seeding).
- [Phase 1] Module-level caches (`_PRIZES` in `global_logic.py`, shared `STRATEGIES` in `plans.py`) may leak state between seeds in a long-lived bench worker (MEAS-03).

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

Tracked but unscheduled (REQUIREMENTS.md v2): ROLE-01 role choice, DEBT-01..05 technical debt.

## Session Continuity

Last session: 2026-10-23T16:24:45.477Z
Stopped at: Completed 01-01-PLAN.md
Resume file: None
