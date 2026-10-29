---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: "02.1"
current_phase_name: Port to NetHack 5.0
status: discussing
stopped_at: Phase 02.1 inserted (port to NetHack 5.0), ready to discuss
last_updated: "2026-10-29T00:00:00.000Z"
last_activity: 2026-10-29
last_activity_desc: main is NetHack 5 now (nh5-port merged); exp 22 running as job 51
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

Last session: 2026-10-28.
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
2026-10-27 evening: NetHack 5.0 RUNS under NLE. Build: reference/nle-src branch `screens-nh5` (local only) on top of
upstream NetHack-5-upgrade 2a0e3baf1: d9c5ded27 link fixes (glyphmap/tileidx, glyph_to_cmap copy, hacklib.c),
dda836441 startup fixes (Lua 5.4.8 pinned, level files in nhdat via NLE_DAT glob, file prefixes set after
early_init), a0800e46a TEMPORARY debug (panic/impossible to stderr + backtrace; drop before any real use).
Venv: ~/.cache/screens-nh5/venv (`VIRTUAL_ENV=... uv pip install --reinstall-package nle reference/nle-src`;
PyPI allowed in .claude/settings.local.json sandbox). Checks: seeded val-dwa-fem-law game starts, 3000 random steps
fine, MAX_GLYPH 9624 (3.6: ~5976), blstats 27; same seed -> identical tty hash, other seed differs.
NLE also 1ff62e859: _pynethack fills mons[]/objects[] at import (NH5 copies them at run time), `mname` is a property
again (neutral name, else male) plus new `pmnames` (male, female, neutral). Bot deps installed in the NH5 venv.
BOT PORT status: glyph tables import fine now; first stop is autoascend/objects/data.py (hand-written 3.6 object
table, asserted against nh.objdescr). 3.6 453 objects -> 5.0 481: 17 "generic <class>" placeholders (to None),
new: silver mace, helm of caution, gold dragon scale mail/scales, shield of drain/shock resistance, amulet of
guarding/flying, enormous meatball (was huge chunk of meat), mail (scroll), spellbooks chain lightning/stasis,
venoms renamed (splash of blinding/acid venom); appearance changes: helm of brilliance crystal helmet, small
shield wooden shield, grappling hook no descr. Stats (wt/cost/prob/damage) of existing items still to compare.
BOT PORT (branch nh5-port, local): 20e6a14 objects/data.py generated from NH5 objects.h (scripts/gen_objects_data.py)
+ NH5 constants; ac29501 glyph layer autoascend/glyph/nh5.py (female->male glyphs, branch walls->main, altars->one,
branch stairs->stairs, engraved floor->floor; applied in Agent.step), screen_symbol_consts regenerated, monster list
format, wooden shield, #loot without "loot it?"; 301cdc1+de890fe = cherry-picked exp/pickup-crash fixes; next commit:
gendered names (pmnames), kill-message word boundary, empty-bag menu. NLE (screens-nh5): + notutorial, autounlock:none
defaults (8314c9271, 3f7a52967). Seed 7 on NH5: ends normally (killed by a watch captain T9584 Dlvl 6), only routine
panics. Smoke helper: scratchpad smoke_tb.py (prints swallowed exceptions as CAUGHT).
More port commits: bb5b2dc tests + dungeon_truth on NH5 (suite 478 passed, 6 skipped in the NH5 venv; 7 of 8 Sokoban
levels unchanged, soko2-2 new and solved by the live solver), 9a6b179 bench SCREENS_BENCH_PYTHON, 395c5ed disarm-this-box,
quivered wield, bag --More--, secret door wand. NLE c03cfdf73 nosafe_wait. Sweep 24 seeds (sweep6): 24/24 normal ends,
max Dlvl 16; note 3/24 deaths "frozen by a floating eye's gaze" (check the floating-eye rule on NH5).
BENCH: server restarted on the nh5-port tree with SCREENS_BENCH_PYTHON=~/.cache/screens-nh5/venv/bin/python (log
~/.cache/screens-nh5/bench-server.log). Job 47: candidate 395c5ed (NH5) vs baseline 3be8413 (3.6, 1152 games stored),
metric dlvl6. A guard loop stops it at the 1152 checkpoint so no 3.6 baseline game is ever played on NH5.
IMPORTANT: while the server runs with the NH5 python, never bench 3.6 commits.
2026-10-28: Job 47 (395c5ed NH5 vs 3be8413 3.6, 1152 pairs): values do NOT fit (rung5 -9.2, rung7 -7.9, dlvl10 -7.4,
crashed +7.1, poisoned -3.5, rays -3.2) -> per owner rule: new NH5 baseline, 3.6 data retired (kept in the DB, not used).
Job 47 "failed" afterwards: it tried 3.6 baseline games on the NH5 python (worker died 3x) - nothing stored; never run
3.6 commits on this server. Speed: 5.0 = 3.6 per turn (~216k turns/min); 21.6 games/min (shorter games).
Release notes checked: doc/fixes5-0-0.txt triaged by local Ollama (scripts/fixes_triage.py -> phase dir
fixes-triage.jsonl), strict LLM pass useless, keyword shortlist (121 entries) read; resulting changes: NLE defaults
paranoid_confirmation:pray, notips (0cc8e934b); kick prompt only with autounlock (off). Wiki NetHack 5.0.0 read:
strategy deltas for later: Valkyrie starts with (dwarvish) spear not long sword (Excalibur plan dead), monsters rarely
drop food on death, poison never instakills, peacefuls can be displaced, special levels incl. Sokoban/Minetown/Mines' End
mirrored (Oracle noflip), natural regen lower. Ascension kit deltas: .planning/research/ASCENSION-KIT-NH5.md.
Port fixes since: 2a671eb mirrored Sokoban (the top crash), a118488/fb5924f class-word items, status texts, unpadded
monster lines, 32f1dc1/579c4d5 no looting when too loaded. Ollama runs as user: OLLAMA_MODELS=/var/lib/ollama ollama serve.
NEW BASELINE: tag p5-baseline = 579c4d5, bench job 48 (2304 games) started 2026-10-28, STOPPED by the owner the same
night (stored games are reused): restart with bench_baseline ref=579c4d5 games=2304 on the NH5 bench server
(SCREENS_BENCH_PYTHON=~/.cache/screens-nh5/venv/bin/python).
2026-10-28 (session 2): the bench server had been auto-started WITHOUT SCREENS_BENCH_PYTHON (would play 3.6!);
restarted by hand with `SCREENS_BENCH_PYTHON=$HOME/.cache/screens-nh5/venv/bin/python nohup .venv/bin/python -m
bench.cli serve >> ~/.cache/screens-nh5/bench-server.log 2>&1 &` - ALWAYS check /proc/<pid>/environ before benching.
Baseline resumed as job 49 (same target: 579c4d5, 2304 games; job 48 had stored 19).
Floating eye: NH5 renamed the helpless reason "frozen by a monster's gaze" -> "frozen by a floating eye's gaze"
(uhitm.c:6044). Rate: 3.6 baseline 16/1446 (1.1%), NH5 job 47 18/1152 (1.6%) -> an old bot problem, not a port bug;
the melee filter drop_floating_eye_melee (fight2 only) is bypassed somewhere. Trace script: scratchpad eye_trace.py
(wraps Agent.step, prints the call stack of the step that froze the hero); seeds 5, 11, 19, 31 of 579c4d5.
Floating-eye cause FOUND: Agent.zap sent the direction key even when no "In what direction?" came (empty wand:
"Nothing happens" first, zap.c dozap) -> the key moved the hero into the eye. Fix on branch exp/zap-prompt (ed55aa8,
off nh5-port; suite 479 passed): seeds 5/11/19 no longer frozen; seed 31 still dies identically (another path, not
traced yet). Seed 31 traced: hero CONFUSED in a doorway with 3 floating eyes adjacent, attacked a ghoul NW, confdir
sent the hit into an eye. Fix on branch exp/eye-confusion (off nh5-port): with confusion/stun and an adjacent eye no
melee and no move (fight2 then waits); seed 31 no longer frozen (starves at T13745 instead); suite 481 passed.
Experiments 21 (exp/zap-prompt) and 22 (exp/eye-confusion) vs p5-baseline once job 49 is done; both target the
~1.6% "frozen by a floating eye's gaze" deaths. OWNER: bench as ONE -> branch exp/floating-eye (df77d20 = both
merged, suite 481 passed) is experiment 21 vs p5-baseline after job 49.
2026-10-29: job 49 DONE - p5-baseline (579c4d5) 2304 games: dlvl6 65.8%, dlvl10 28.0%, rung2 46.9%, rung4 17.4%,
rung6 14.1%, rung7 4.8%, rung8 2.6%, rung9 1 game; starved 25.1%, ants 6.7%, rays 4.0%, eye 1.5% (35), crashed 2.3%
(65 non-death ends). Crash types (none >= 1%): monster_tracker.py:40 22 (0.95%, NH5 wraps long ;M lines),
inventory.py:387 14 (prompt left open in check_container_content), watchdog 12, item_manager 302/507 3+3,
inventory.py:399 3, agent.py:541 wield loop 3, others <= 2.
Bench server trap fixed: the MCP server auto-starts `bench.cli serve` WITHOUT SCREENS_BENCH_PYTHON (3.6!);
.mcp.json now sets it (8ca9bb8, active from the next session). Still check /proc/<pid>/environ before benching.
8ca9bb8 also adds metric `eye` (killed while frozen by a floating eye's gaze).
Experiment 21 KEPT: job 50 exp/floating-eye (df77d20) vs p5-baseline, metric eye: better at 192 pairs,
-4.2 [-7.9, -0.5] (0 vs 8 eye deaths); same seeds: crashed 5 vs 7, rung4 +2.6, starved +3.6 (noise, watch it).
Merged into nh5-port as bf0c7d9 (suite 481 passed). Experiment 22: job 51 = exp/monster-wrap vs p5-baseline, metric crashed.
exp/monster-wrap (980395e, off p5-baseline, worktree ../screens-wrap): ;M skips wrapped lines; suite 481 passed;
crash seeds 125 152 280 398 512 end normally, 202 later hits agent.py:541. Experiment 22 (metric crashed) after job 50.
Resume steps:
1. Wait for job 51 (`uv run screens-bench wait 51`); keep -> merge exp/monster-wrap into main.
2. (done) exp 21 kept.
3. (done 2026-10-29, owner yes) nh5-port fast-forwarded into main; work continues on main. pyproject: nle from
   path reference/nle-src (branch screens-nh5); .venv now = NH5 build (identical .so/nhdat to the NH5 venv).
   3.6 is gone from main; the 3.6 tree lives at tag 3be8413 / p1-final only.
4. Then experiments on NH5: starting weapon (spear vs mattock/long sword), food supply, inventory.py:387 crash.
Resume file: None
