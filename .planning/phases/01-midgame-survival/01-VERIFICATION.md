---
phase: 01-midgame-survival
verified: 2026-10-25T13:05:00Z
status: passed
score: 4/4 must-haves verified
covered_files: [".planning/phases/01-midgame-survival/01-01-PLAN.md", ".planning/phases/01-midgame-survival/01-01-SUMMARY.md", ".planning/phases/01-midgame-survival/01-02-PLAN.md", ".planning/phases/01-midgame-survival/01-02-SUMMARY.md", ".planning/phases/01-midgame-survival/01-03-PLAN.md", ".planning/phases/01-midgame-survival/01-03-SUMMARY.md", ".planning/phases/01-midgame-survival/01-04-PLAN.md", ".planning/phases/01-midgame-survival/01-04-SUMMARY.md", ".planning/phases/01-midgame-survival/01-05-PLAN.md", ".planning/phases/01-midgame-survival/01-05-SUMMARY.md", ".planning/phases/01-midgame-survival/01-06-PLAN.md", ".planning/phases/01-midgame-survival/01-06-SUMMARY.md", ".planning/phases/01-midgame-survival/01-07-PLAN.md", ".planning/phases/01-midgame-survival/01-07-SUMMARY.md", ".planning/phases/01-midgame-survival/01-08-PLAN.md", ".planning/phases/01-midgame-survival/01-08-SUMMARY.md", ".planning/phases/01-midgame-survival/01-09-PLAN.md", ".planning/phases/01-midgame-survival/01-09-SUMMARY.md", ".planning/phases/01-midgame-survival/01-10-PLAN.md", ".planning/phases/01-midgame-survival/01-10-SUMMARY.md", ".planning/phases/01-midgame-survival/01-11-PLAN.md", ".planning/phases/01-midgame-survival/01-11-SUMMARY.md", ".planning/phases/01-midgame-survival/01-12-PLAN.md", ".planning/phases/01-midgame-survival/01-12-SUMMARY.md", ".planning/phases/01-midgame-survival/01-13-PLAN.md", ".planning/phases/01-midgame-survival/01-13-SUMMARY.md", ".planning/phases/01-midgame-survival/01-14-PLAN.md", ".planning/phases/01-midgame-survival/01-14-SUMMARY.md", ".planning/phases/01-midgame-survival/01-15-PLAN.md", ".planning/phases/01-midgame-survival/01-15-SUMMARY.md", ".planning/phases/01-midgame-survival/01-16-PLAN.md", ".planning/phases/01-midgame-survival/01-16-SUMMARY.md", "autoascend/PORTING.md", "autoascend/agent.py", "autoascend/exploration_logic.py", "autoascend/global_logic.py", "autoascend/level.py", "autoascend/prayer.py", "autoascend/soko_solver/search.py", "autoascend/stats_logger.py", "bench/mcp_server.py", "bench/runner.py", "bench/stats.py", "nethack_screensaver/fixed_clock.py", "nethack_screensaver/game.py", "scripts/benchmark.py", "scripts/nld_study.py", "scripts/replay_check.py", "scripts/seeded_report.py"]
covered_digest: "v3:sha256:3a0a6577ba344fbd931039df8a381da529ea260e430ba45edd1eaa284a0a19ec"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 1: Midgame Survival Verification Report

**Phase Goal:** The pilgrim bot dies measurably less often on Dlvl 4-12, so more games reach Minetown, Sokoban and Mines' End, and the bench can see 1-3 point effects.
**Verified:** 2026-10-25T13:05:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A seeded A/A control ends "no measurable difference" with an interval clearly narrower than the unseeded ~3.5-point detectable difference | ✓ VERIFIED | PORTING.md ### A/A control: job 10 (`e3f0dd7` vs docs twin) and job 13 (Valkyrie `0b09707` vs twin), rung2, 1152 seeds: 0.0 [0.0, 0.0]; replay_check 0 mismatched (watchdog seeds skipped and listed). Bench resolution 2.8 points on rung2 at 2304 (### Bench resolution) |
| 2 | A pilgrim-only baseline of `main` (seeds 0..575) is stored, its 17-rung table is in PORTING.md, older numbers marked not comparable | ✓ VERIFIED | PORTING.md ### Pilgrim-only baseline `0b09707`, "Ladder, seeds 0..575, n = 576" table (rungs with median turn vs ascenders); 2304 seeds stored; 18 "Not comparable with Phase 1 numbers" notes on the older sections |
| 3 | Rest-to-full, starvation, wand/ray users and ants/bees each have a paired verdict; better merged, rest dropped with interval; threat-model, flee-upstairs, choke-points re-judged once | ✓ VERIFIED | PORTING.md ### Experiments 1-9: starvation-1/-2 (jobs 17, 19), rest-to-full, ants-bees, shop-door (kept, only `better`), zappers, rejudge threat-model/choke-points/flee-upstairs (jobs 25-27); each entry has job, verdict, interval, decision. `git branch --merged main` lists only `exp/shop-door` |
| 4 | Final `main` vs pilgrim-only baseline: paired `better` on rung2, rungs 3-6 not worse | ✓ VERIFIED | `seeded_report.py verdict p1-final --baseline p1-baseline --metric rung2 --expect better` exit 0 (job 28: +3.1 [+0.8, +5.4] at 384); rung3-6 `--forbid worse` exit 0 (jobs 29-32, all `better`). `p1-final` = `3fca503`; `git diff 3fca503 main` touches only PORTING.md and planning files |

**Score:** 4/4 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `nethack_screensaver/fixed_clock.py` | seeded start time (shopkeeper names) | ✓ VERIFIED | tests/test_fixed_clock.py; used by bench/runner.py and scripts/benchmark.py |
| `nethack_screensaver/game.py` | fix_moon_phase for seeded games, death context, turn-stall watchdog, Valkyrie character | ✓ VERIFIED | tests/test_game.py, tests/test_replay.py (slow, 3 passed) |
| `autoascend/prayer.py` | prayer_outcome classifier from human census | ✓ VERIFIED | tests/test_prayer.py; used by seeded_report.py and nld_study.py |
| `scripts/seeded_report.py`, `scripts/replay_check.py` | read-only verdict/pairs/ladder/killers/deaths tools | ✓ VERIFIED | tests/test_seeded_scripts.py; no Store write calls |
| `scripts/nld_study.py`, `01-HUMAN-STUDY.md` | human prayer/food study | ✓ VERIFIED | tests/test_nld_study.py; study passed UAT test 13 |
| `autoascend/agent.py`, `level.py`, `exploration_logic.py` | closed-shop-door guard (exp/shop-door) | ✓ VERIFIED | merged at `3fca503`; counter `shop_door_spared` |
| `autoascend/PORTING.md` | baseline, A/A, experiments, Phase 1 result, branch cleanup | ✓ VERIFIED | all sections present; "Phase 1 result: met" |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| bench/runner.py | fixed_clock shim | `fixed_clock.preload_env` in worker env | ✓ WIRED | with PYTHONHASHSEED=0 and one BLAS thread |
| game.run_game | fixed_clock.pin | `fixed_clock.pin(seed)` before env creation | ✓ WIRED | unseeded games clear the pin |
| global_logic live Sokoban | soko_search.solve | `max_states=SOKOBAN_LIVE_MAX_STATES, max_seconds=None` | ✓ WIRED | state budget only |
| exploration_logic door kicking | level.closed_shop_door | set from "Closed for inventory" message in agent | ✓ WIRED | |
| tag p1-final | tag p1-baseline | bench_experiment jobs 28-32 | ✓ WIRED | stored verdicts read back by seeded_report.py |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full fast suite | `uv run pytest -q` | 416 passed, 5 skipped, 16 deselected | ✓ PASS |
| Same seed replays across fresh processes | `uv run pytest -q -m slow tests/test_replay.py` | 3 passed | ✓ PASS |
| Done bar | `seeded_report.py verdict ... --expect better` / `--forbid worse` (rung2..rung6) | all exit 0 | ✓ PASS |
| Screensaver plays on final code | UAT test 16 (owner watched) | pass, player.log empty | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MEAS-01 | 01-05, 01-06 | seeded A/A control, narrower interval | ✓ SATISFIED | Truth 1 |
| MEAS-02 | 01-07 | pilgrim-only baseline and 17-rung table | ✓ SATISFIED | Truth 2 |
| MEAS-03 | 01-01, 01-02, 01-05 | same seed, same game; non-replay sources fixed or documented | ✓ SATISFIED | PORTING.md ### Determinism; slow replay tests pass; watchdog endings documented as the remaining non-replay |
| SURV-01 | 01-09 | rest to full HP | ✓ SATISFIED (judged, dropped) | Experiment 3: -1.5 [-4.2, +1.2], dropped per success criterion 3; resting traded ant deaths for starvation |
| SURV-02 | 01-08 | starvation addressed | ✓ SATISFIED (judged, dropped) | Experiments 1-2, diagnosis table; cause recorded as food supply (open for Phase 2+) |
| SURV-03 | 01-11 | wand and ray users addressed | ✓ SATISFIED | Experiment 5 shop-door kept (`better`), experiment 6 zappers dropped |
| SURV-04 | 01-10 | ants and killer bees addressed with a new approach | ✓ SATISFIED (judged, dropped) | Experiment 4 ants-bees (poison resistance from corpses): -1.5 [-2.6, -0.3], dropped |
| SURV-05 | 01-12, 01-13, 01-14, 01-16 | old branches re-judged once | ✓ SATISFIED | Experiments 7-9 (jobs 25-27), none kept; branches archived as `archive/*` tags |
| SURV-06 | 01-15 | rung2 better, rungs 3-6 not worse | ✓ SATISFIED | Truth 4 |

No orphaned requirements: REQUIREMENTS.md maps exactly MEAS-01..03 and SURV-01..06 to Phase 1.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | no TBD/FIXME/XXX/TODO added this phase | - | - |

Code review (01-REVIEW.md): 0 critical, 1 warning (WR-01 shim build race on first run), 4 info; all
recorded open in 01-REVIEW-DISPOSITION.md, to be fixed at the start of Phase 2 so `main` stays
code-identical to the judged `p1-final`. None blocks the goal.

### Human Verification Required

None outstanding. The owner's UAT (01-UAT.md, 17 of 17 passed) covered the human study, the experiment
log, acceptance of the done bar, the live screensaver and the branch cleanup.

### Gaps Summary

No gaps. The goal is met with a small margin: one kept change (exp/shop-door) gives +1 to +3 points on
rungs 2-6, and rung6's interval starts at +0.1. Starvation is still the largest killer (25% of baseline
games); the human study points at food supply rather than prayer timing, and no food-stock experiment
has been run yet.

---

_Verified: 2026-10-25T13:05:00Z_
_Verifier: Claude (inline, gsd-verifier rules)_
