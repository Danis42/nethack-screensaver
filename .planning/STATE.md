---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: 01
current_phase_name: Midgame Survival
status: executing
stopped_at: Completed 01-06-PLAN.md
last_updated: "2026-10-23T17:17:43.229Z"
last_activity: 2026-10-23
last_activity_desc: 01-06 calibration done; Valkyrie-only A/A passed (gate 0b09707)
state_head: e0691aa5c2b7540d1a588a329e8191df315a297e
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 16
  completed_plans: 6
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-22)

**Core value:** The bot achieves a real ascension on the pilgrim route (the only priority).
**Current focus:** Phase 01 — Midgame Survival

## Current Position

Phase: 01 (Midgame Survival) — EXECUTING
Plan: 7 of 16
Status: Ready to execute
Last activity: 2026-10-24 — 01-06 done: Valkyrie-only A/A passed, calibration recorded, 2304 checkpoint, screen-then-confirm

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
| Phase 01 P02 | 9 min | 2 tasks | 5 files |
| Phase 01 P03 | 8 min | 3 tasks | 4 files |
| Phase 01 P04 | 31 min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Full log in PROJECT.md Key Decisions. Recent, affecting current work:

- [Pre-roadmap]: Ascension is the only priority; every game plays the pilgrim route (`strategy = "pilgrim"`), others behind `strategy = "random"`
- [Pre-roadmap]: Every change is one experiment on the seeded paired bench; "no measurable difference" is not a win
- [Pre-roadmap]: Git is local only; finished tested branches merge to `main` locally
- [Phase 01]: 01-01: fix_moon_phase=seed is not None - only seeded bench games are calendar-independent, screensaver keeps the real moon
- [Phase 01]: 01-01: _DeathContext observes observations only; agent reads (_food_at_end/_events) happen after the game
- [Phase 01]: 01-02: SOKOBAN_LIVE_MAX_STATES=40,000 with max_seconds=None (8.4 s worst case measured); bench workers pinned to PYTHONHASHSEED=0
- [Phase 01]: 01-03: analysis scripts (seeded_report.py, replay_check.py) are read-only on the bench store and reuse judge_paired/METRICS/killer/ladder_rows; killer-table category rows overlap so counts equal the bench's own metrics
- [Phase 01]: 01-04: prayer_outcome classifies 'You die...' in the prayer window as failed; a failed prayer with no god-like answer stays unknown — Human games: 134 of 141 'while praying' deaths show monsters hitting a hero with no shimmering light
- [Phase 01]: 01-04: humans fail 2.8% of prayers on Dlvl 4-12 (bot 12%); human starvers die early (median turn 2,206) while the bot's median is 7,828; eating rate is equal (2.8-2.9 per 1000 turns) — NLD-NAO food study, 01-HUMAN-STUDY.md

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1] Every game is a dwarvish Valkyrie since `0b09707` (owner, until the first ascension). Measurement code `p1-valk-base`, A/A passed (job 13). Resolution: ±3.9 points rung2 at 1152, about ±2.8 at 2304 (now the last checkpoint). The baseline (01-07) must be stored on Valkyrie code; all older numbers are not comparable.
- [Phase 1+] 19/1152 Valkyrie games (all Dlvl 11-28) end on the 120 s watchdog: the bot hangs deep in the dungeon. Needs a stack dump on watchdog and a fix before the deep rungs can be measured.
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

Last session: 2026-10-23T17:17:43.204Z
Stopped at: Completed 01-04-PLAN.md
Resume file: None
