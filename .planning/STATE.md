---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: 2
current_phase_name: Real Descent
status: executing
stopped_at: gap experiment 15 exp/passive (bench)
last_updated: "2026-10-25T13:04:19.487Z"
last_activity: 2026-10-26
last_activity_desc: knowledge sweep; job 38 exp/quest-portal
state_head: dabd11d7d8e36e84ba2fce3ab57e36dc6084f538
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 24
  completed_plans: 17
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-25)

**Core value:** The bot achieves a real ascension on the pilgrim route (the only priority).
**Current focus:** Phase 2 — Real Descent (rungs 6-8)

## Current Position

Phase: 2 (Real Descent) — READY TO EXECUTE
Plan: 3 of 8
Status: EXECUTING Phase 2 gap experiments (2026-10-26) - Exp 14 exp/quest-portal KEPT (job 38, baseline 6a840f2). Exp 15 exp/passive DROPPED (job 39: dlvl10 no measurable difference @2304, free5 worse -1.4). Exp 16 exp/elbereth-respect DROPPED (job 40). Exp 17 exp/boulder-push (push boulders when the level looks finished; 160 of 315 stuck starvers had a boulder in view): pre-registered primary starved, mechanism free5/died/dlvl10/rung7/boulder_pushed; smoke 22 boulder-stuck starver seeds: pushed in 10/22, starved/fainted 22 -> 11, seed 3 Dlvl 1 -> 13, 1 crash of a baseline type (inventory assertion, seed 9, 107 pushes -> cap 30/level added); job 41: no measurable difference @2304, starved -1.4 [-2.9, +0.1] (122 -> 96 starvation deaths, pushes in 849 games) -> DROPPED by protocol, branch kept as near-miss to bundle with a food/prayer fix. Exp 18 exp/prayer-timing (+ boulder-push) KEPT, merged 8ae7686 (job 42: starved -2.3 [-4.3, -0.4]; bench label bug for lower-is-better metrics fixed f867d84). NEW BASELINE for next experiments: main 8ae7686 (bot code = 893797a6). Exp 19 exp/deadly-trouble (bd8ab3d vs 893797a6; pray/eat lizard on Stone/Slime/Strangled/FoodPois/TermIll via NLE status mask, lizards kept as medicine, no cockatrice corpse sacrifice pickup, no bare-handed cockatrice melee): pre-registered primary petrified (new bench metric, lower is better), mechanism died/free5/dlvl10/rung7; smoke 22 affected seeds: petrified 4 -> 2, corpse-pickup deaths gone; job 43 @1152: petrified -2.2 [-3.3, -1.0] better BUT free5 -2.2 worse, starved +1.9 open; cause: acid blob corpse pickup diverged 567/1152 games -> not merged; rerun 3be8413 (lizard-only pickup) job 44 @384: petrified -2.6 [-4.5, -0.7] better, mechanism all open -> KEPT, merged c8792f3. NEW BASELINE: 3be8413. Follow-up: inventory.py:91 assertion on big piles ('Pick up what?') is the top crash (8/384). Exp 20 exp/poison-resistance (eat poisonous corpses that give poison resistance >= 20% (killer bee, scorpion, soldier ant, giant beetle) when HP >= 21 and Str >= 14; any once resistant): pre-registered primary poisoned (new bench metric, lower is better) vs 3be8413, mechanism died/dlvl10/rung7/free5/starved; smoke 22 poison-death seeds: poisoned 22 -> 9, resistance gained in 6, 0 exceptions; job running. ROUTE AUDIT done (.planning/research/ASCENSION-ROUTE-AUDIT.md): pick-axe is the key item (skips Medusa, needed on Earth, unsticks levels); Castle entry = striking at drawbridge; no prayer in Gehennom. ITEMS AUDIT done (.planning/research/ITEMS-EFFECTS-AUDIT.md): bot never reads/puts on, armour by AC only; ranked next experiments: (1) pray/eat lizard when stoning starts (82 petrified deaths, 47 saw the warning), (2) eat poisonous corpses for poison resistance (120 poison deaths), (3) pick-axe dig down when stuck. FULL KNOWLEDGE SWEEP (owner request 2026-10-25: go through ALL wiki pages + source): ledger .planning/phases/02-real-descent/sweep/wiki-ledger.tsv, 5667 pages: read-topic 2056, read-monster 367, read-item 420, skipped variant 1671 / translation 533 / meta 616 / stub 4; pages are summarised by a LOCAL Ollama model (qwen2.5:14b on the GPU, no Claude tokens): scripts/wiki_sweep/ollama_sweep.py -> sweep/wiki-facts.jsonl (resumable; restart if stopped). Then filter by script, read the short list, verify against src, rank in 02-KNOWLEDGE-SWEEP.md. Then same for src/*.c. Status page: scripts/status_page.py (http://127.0.0.1:8770). Owner rule: NO subagents without consent. Follow-up: 3 one-game exception types from job 37
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

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

Tracked but unscheduled (REQUIREMENTS.md v2): ROLE-01 role choice, DEBT-01..05 technical debt.

## Session Continuity

Last session: 2026-10-26T23:20 (local). PC shuts down at 05:45; resume 2026-10-27.
Stopped at: Exp 20 exp/poison-resistance (d83ed40) vs 3be8413 running as bench job 45, primary `poisoned`.
Resume steps:
1. Job state: MCP `bench_status` / `bench_results`, or `uv run screens-bench wait 45`. If the shutdown cut it off
   (the server marks it interrupted), resubmit the same experiment: candidate `exp/poison-resistance`, baseline
   `3be8413`, metric `poisoned`; stored games are reused, only the rest is played.
2. Evaluate (95%): `uv run python scripts/seeded_report.py pairs --metric M --confidence 95 d83ed40 3be8413` for
   M = poisoned, died, free5, dlvl10, rung7, starved, crashed. Per-seed flips, identical-game count, exception
   types: scratchpad script pattern (Store(DATA/results.db).games_by_seed); events poisonous_corpse_eaten,
   poison_resistance_gained. Watch Str loss side effects (died/dlvl10).
3. Better and mechanism not worse -> merge exp/poison-resistance to main, run tests, log PORTING Experiment 20,
   new baseline = d83ed40. Otherwise log as dropped.
4. Next candidates: fix inventory.py:91 assertion on big piles ("Pick up what?"; top crash, 8/384 in job 44);
   then pick-axe: keep one and dig down when stuck (ASCENSION-ROUTE-AUDIT.md).
Resume file: None
