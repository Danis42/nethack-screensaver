---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: 01
current_phase_name: Midgame Survival
status: executing
stopped_at: Completed 01-16-PLAN.md
last_updated: "2026-10-23T17:17:43.229Z"
last_activity: 2026-10-25
last_activity_desc: 01-16 done - all Phase 1 plans complete
state_head: e0691aa5c2b7540d1a588a329e8191df315a297e
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 16
  completed_plans: 16
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-22)

**Core value:** The bot achieves a real ascension on the pilgrim route (the only priority).
**Current focus:** Phase 01 — Midgame Survival

## Current Position

Phase: 01 (Midgame Survival) — EXECUTING
Plan: 16 of 16
Status: 01-15 done 2026-10-25 - Phase 1 result: met (p1-final 3fca503 vs p1-baseline 0b09707, jobs 28-32: rung2 +3.1 [+0.8, +5.4], rungs 3-6 all better). 01-16 done 2026-10-25 (owner chose archive-tags: six old branches tagged archive/<name> and deleted). All 16 plans done; next: verify/close Phase 1, then Phase 2 (Real Descent)
Last activity: 2026-10-25 — 01-15 done: Phase 1 result met; five paired verdicts, all better

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

- [Phase 01]: 01-08: starvation is a food-supply and stuck-level problem, not prayer timing; both experiments dropped (PORTING.md experiments 1-2)
- [Phase 01]: 01-09: rest target scales with food (owner, 2026-10-24): full HP with food or safe prayer, about 85% without food, none when Hungry with no fallback
- [Phase 01]: 01-09: rest-to-full dropped (-1.5 [-4.2, +1.2]); resting trades ant deaths for starvation while food is short
- [Phase 1]: 01-15: Phase 1 result: met - p1-final (3fca503, exp/shop-door the only kept change) better than p1-baseline on rung2..rung6 (jobs 28-32); Phase 2 can start after 01-16
- [Phase 1]: pilgrim-only baseline p1-baseline = 0b09707 (dwarvish Valkyrie); bench resolution 2.8 points on rung2 at 2304 (PORTING.md); starvation ends 25% of games

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1] Every game is a dwarvish Valkyrie since `0b09707` (owner, until the first ascension). Baseline `p1-baseline` = `0b09707` (2304 seeds stored); older numbers are not comparable.
- [Phase 1+] 46/2304 baseline games (median Dlvl 24) end on the 120 s watchdog: the bot hangs deep in the dungeon. Needs a stack dump on watchdog and a fix before the deep rungs can be measured.
- [Phase 1] 2026-10-24 fix `16a6cb8`: a panic loop that keeps the screen changing (empty-bag loot menu) grew workers to 11 GB; the watchdog now also fires when the game turn stalls for 120 s and only 20 panics are kept. The empty-bag menu itself is not fixed (parse in item_manager / loot).
- [Phase 1] Old survival branches resolved 2026-10-25 (01-16): judged, dropped, kept only as local archive/ tags.
- [Phases 4-8] Nothing above rung 9 (Medusa, 14 of 2304 games) has been reached; these phases depend on the staged-start harness (STAGE-01, whose `wizard=True` route is unvalidated against `NetHackChallenge` and seeding).

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

Tracked but unscheduled (REQUIREMENTS.md v2): ROLE-01 role choice, DEBT-01..05 technical debt.

## Session Continuity

Last session: 2026-10-23T17:17:43.204Z
Stopped at: Completed 01-09-PLAN.md
Resume file: None
