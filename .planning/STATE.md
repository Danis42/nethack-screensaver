---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: "02.1"
current_phase_name: Port to NetHack 5.0
status: discussing
stopped_at: Phase 02.1 inserted (port to NetHack 5.0), ready to discuss
last_updated: "2026-10-27T19:15:01.515Z"
last_activity: 2026-10-27
last_activity_desc: owner decision - port to NetHack 5.0; exp 20 dropped
state_head: 38dabbf62e8ded80cfb276eb4a74c11820197984
progress:
  total_phases: 9
  completed_phases: 1
  total_plans: 24
  completed_plans: 23
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-25)

**Core value:** The bot achieves a real ascension on the pilgrim route (the only priority).
**Current focus:** Phase 2 — Real Descent (rungs 6-8)

## Current Position

Phase: 02.1 (Port to NetHack 5.0) — INSERTED, ready to discuss
Plan: 0 of TBD
Status: Port to NetHack 5.0 started 2026-10-27 (owner decision). 3.6 experiments paused: Exp 20 exp/poison-resistance DROPPED at stop (job 46 @1152: poisoned +0.4 [-0.6, +1.4]); exp/pickup-crash parked unbenched (smoke-clean on 20 crash seeds). Earlier Phase 2 history: see PORTING.md and git log.
Last activity: 2026-10-25 — 02-01 exact Mines End rung, 02-02 stuck reports/free5; p2-baseline job 33 running

Progress: [█░░░░░░░░░] 13%

## Performance Metrics

**Velocity:**
- Total plans completed: 16
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 16 | - | - |

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
- [Phase 1]: COMPLETE 2026-10-25 - UAT 17/17, SECURITY threats_open 0, VERIFICATION passed; Phase 2 baseline to start from = p1-final (3fca503)
- [Phase 1]: pilgrim-only baseline p1-baseline = 0b09707 (dwarvish Valkyrie); bench resolution 2.8 points on rung2 at 2304 (PORTING.md); starvation ends 25% of games

### Pending Todos

- [done 2026-10-25] 01-REVIEW.md findings: WR-01, IN-01, IN-02 fixed; IN-03 deferred to the food-stock check; IN-04 no change needed
- Candidate (seen 2026-10-25, seed 2242 replay): the explorer searches for hidden passages in the Mines (about 1400 turns on one dead end, Mines level 2), where filler levels have none; "no searching in the Mines" is a candidate for 02-06 or a gap plan
- exp/stuck-1 (frontier-first, `73c4584`) built on main ahead of time; rebase onto exp/mines-end if experiment 10 is kept; smoke + full suite when the bench is idle
- Candidate (seen 2026-10-25, replays 75/896/760): fight standoff - combat/movement_priority "engage, but ensure striking first" keeps the bot at distance 2 from a monster that never comes (asleep water nymph 709 turns, spotted jelly 1305 turns, blue jelly/acid blob); 2 of 6 stuck seeds lost 1100-1350 of their 2500 stuck turns. Fix idea: a monster that stood still 20+ turns and is not adjacent does not start or keep fight2. Gap experiment after 02-06
- Candidates (2026-10-25, 02-HUMAN-CHECK.md): no searching on Mines fillers (source: minefill has no secret doors); use trap doors/holes when diving; dig down with a pick-axe when stuck; never melee spotted/blue jellies. Human ttyrec counts still to do on an idle bench
- [Idea, owner 2026-10-25] Food-stock experiment: keep 1-2 non-perishable food items (rations, lembas, cram, tins), take or buy them when none; first check with nld_study.py whether human survivors eat more non-corpse food (meal text names the food)
- [Phase 1 leftover] 01-VALIDATION.md is still a draft (/gsd-validate-phase 1 not run); non-blocking

### Blockers/Concerns

- [Phase 2] Every game is a dwarvish Valkyrie since `0b09707` (owner, until the first ascension). Baseline `p1-baseline` = `0b09707` (2304 seeds stored); older numbers are not comparable.
- [Phase 1+] 46/2304 baseline games (median Dlvl 24) end on the 120 s watchdog: the bot hangs deep in the dungeon. Needs a stack dump on watchdog and a fix before the deep rungs can be measured.
- [Phase 1] 2026-10-24 fix `16a6cb8`: a panic loop that keeps the screen changing (empty-bag loot menu) grew workers to 11 GB; the watchdog now also fires when the game turn stalls for 120 s and only 20 panics are kept. The empty-bag menu itself is not fixed (parse in item_manager / loot).
- [Phases 4-8] Nothing above rung 9 (Medusa, 14 of 2304 games) has been reached; these phases depend on the staged-start harness (STAGE-01, whose `wizard=True` route is unvalidated against `NetHackChallenge` and seeding).

### Roadmap Evolution

- Phase 02.1 inserted after Phase 2: Port to NetHack 5.0: port NLE 1.3.0 (NetHack 3.6.7) to NetHack 5.0.0 and the AutoAscend bot to it; compare against the 3.6 baseline 3be8413, keep it if the numbers fit, else new 5.0 baseline (owner 2026-10-27; 3.6 experiments paused) (URGENT)

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

Tracked but unscheduled (REQUIREMENTS.md v2): ROLE-01 role choice, DEBT-01..05 technical debt.

## Session Continuity

Last session: 2026-10-27.
Stopped at: Phase 02.1 (Port to NetHack 5.0) inserted after the owner's decision (2026-10-27): stop the 3.6 experiments,
port NLE 1.3.0 (runs NetHack 3.6.7; no NLE release supports 5.0, the original repo is archived) to NetHack 5.0.0
(released 2026-05-02) and port the AutoAscend bot. Do NOT retire the 3.6 baseline 3be8413: run the ported bot and
compare; if the numbers fit, keep it; if they are all over the place, make a new 5.0 baseline and retire the 3.6 data.
3.6 leftovers: Exp 20 exp/poison-resistance DROPPED (job 46 stopped @1152: poisoned +0.4 [-0.6, +1.4], died worse only
because the baseline crashed in those seeds). Branch exp/pickup-crash (c2dfcd1, f0cd61a; worktree ../screens-pickup)
parked unbenched: inventory refresh + parser fixes, smoke-clean on 20 crash seeds; most parser fixes will matter on 5.0 too.
Wiki: 5.0 is now the right version; facts from 3.6.6 source no longer automatically apply.
KEY FINDING 2026-10-27: NLE upstream (github.com/NetHack-LE/nle, cloned to reference/nle-src) has a branch
origin/NetHack-5-upgrade (Stephen Oman, 12 commits 2026-06..2026-10-25) that imports NetHack 5.0 and adapts nle.c,
winrl.cc, pynethack.cc; seeding (set_initial_seeds, fix_moon_phase) kept; glyph layout changed (MAX_GLYPH enum).
NetHack 5.0.0 source cloned to reference/nethack-5.0.0 (tag NetHack-5.0.0_Released). Building the branch was blocked
by the auto-mode classifier (compiles downloaded code) -> owner must allow: scratch venv build via
`uv pip install reference/nle-src` (branch checked out).
Resume steps:
0. With owner permission: build the NH5 branch in a scratch venv, run one random-action game, then one AutoAscend game.
1. /gsd-discuss-phase 02.1 (scope: NLE port approach, seeding/bench compatibility, comparison gate vs 3be8413).
2. Feasibility map: clone NetHack 5.0.0 source and NLE source into reference/; list NLE's hooks into NetHack (win/rl,
   blstats, glyphs, seeding, NetHackChallenge) and what changed in 5.0 for each.
Resume file: None
