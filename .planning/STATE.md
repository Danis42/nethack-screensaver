---
gsd_state_version: "1.0"
milestone: v0.1.0
current_phase: "02.2"
current_phase_name: Full Ascension Ruleset
status: executing
stopped_at: Phase 02.1 inserted (port to NetHack 5.0), ready to discuss
last_updated: "2026-10-29T00:00:00.000Z"
last_activity: 2026-11-11
last_activity_desc: exp/float-past dropped (castle staged 7/20 vs 8/20)
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

- [Phase 2] Every game is a neutral human Valkyrie since experiment 37 (d5f032c, 2026-11-01); dwarvish before that. Older numbers are not comparable.
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
2026-10-30 (session end): TRACK B started (owner yes). On main: staged-game harness (nethack_screensaver/staging.py,
run_game(stage=...), scripts/staged_run.py; stages medusa/castle/quest/valley; wizard mode via StagedChallenge,
character passed as options, wizard-only prompts answered, skill parser reads wizard format; natural play unchanged,
seeds 1-4 identical). Branch track-b/medusa-dig (off exp/dig-down + main): divers from Dlvl 21 dig down on arrival
(bc76bc6): staged medusa 1-12 -> 7/12 dug to the Castle level, median T1138 (was 150); 1576f92 pit retry is MIXED
(seed 10 fixed, seed 4 worse) - revert or rework. Open: explorer spins without a game turn when nothing is
reachable (go_to_level_strategy/open_visit_search; also most of the 12 natural baseline watchdogs) -> natural
bench experiment candidate "explorer idle turn". Staged results: scratchpad only, never in the bench store.
2026-10-30 session resumed: job 52 was gone after a restart; server env checked (NH5 python, one server); exp 23
restarted as job 53 (exp/dig-down vs 6c7bfef, metric starved; stored games reused).
Resume steps:
1. Exp 23 DONE: job 53 @2304 starved +0.2 [-0.8, +1.3], no measurable difference -> dropped from main (branch kept;
   track-b/medusa-dig keeps the dig code). Baseline stays 6c7bfef.
   Exp 24 exp/idle-turn (worktree ../screens-idle): CAUSE of the explorer hang: go_to_level_strategy `while 1` spins
   when every strategy declines (no game turn, so stuck/bail watches never run); 17 watchdogs on 6c7bfef, 6 at Dlvl
   22-27. Fix: one search when a pass used no turn. Unfixed control: 9/9 seeds hang at the stored turn.
   Fix 57addd2: 9/9 hang seeds end normally, suite 487 passed. Job 54 = exp/idle-turn vs 6c7bfef, metric hung (new,
   cc971b5; `crashed` does not count watchdogs). Watch rung7, rung9. After a kill the server can stay a zombie: restart with setsid.
   Then exp 25 exp/pry-chests (worktree ../screens-pry, on top of exp/idle-turn): smoke 6 seeds 20 locks forced, boxes
   looted; bench vs 57addd2 if exp 24 is kept (else rebase), metric starved; watch potions lost to destroyed boxes.
   Bots hit 2-12 locked boxes per game. Also measure the guaranteed ration on the Mines branch level.
   Side finding: some games re-check 'an empty bag named #0' hundreds of times (seeds 107, 118); not investigated.
   exp/pry-chests now ffe4685: pry with a blade, one retry, bash only without one (FOOD-NH5.md had said so). Suite 489.
   Starvers rarely reach food: Minetown 141/599, Sokoban 16/599, 192 never reach the Mines; bot reaches the Mines at
   T3575 (yardstick T1173). Next probe: where early turns go (FOOD-NH5.md end).
   Pace probe (12 seeds 201-212, scratchpad pace.py): 44% of pre-Mines turns are Agent.search; cause trap_search_offset=1
   (global_logic.py explore1, vendored AutoAscend): a search before each new square. exp/no-trap-search (worktree
   ../screens-traps, on exp/idle-turn): offset 0: 11/12 reach the Mines (was 6/12), levels 300-600 turns (was ~750),
   5 vs 3 fainted deaths, Dlvl 1 time grew (up to 3331, unexplained: check). BENCH ORDER after job 54: exp/no-trap-search
   (metric starved, watch rung1, rung2, trap deaths), then exp/pry-chests.
   Exp 24 KEPT (job 54 @576: hung -1.4 [-2.6, -0.1], 0 hangs), merged to main; new baseline 57addd2 (not 6c7bfef).
   Job 55 = exp/no-trap-search vs 57addd2, metric starved. Next candidate exp "leave Dlvl 1 sooner": milestone
   BE_ON_FIRST_LEVEL (global_logic.py current_strategy) keeps the hero on Dlvl 1 until XL 8 or Hungry, by design, so the
   first food budget is spent there; explains most Dlvl 1 time. Build after job 55 (the two interact).
   Exp 25 KEPT (job 55 @2304: starved +0.0 [-2.5, +2.6], but rung2 +5.8 [+3.0, +8.6]; crashed +1.0, free5 -2.5, see
   PORTING.md), merged to main 592ee8c. NEW BASELINE 671cd32 (game code = main, 2304 games stored). Job 56 =
   exp/pry-chests vs 57addd2, metric starved, running: if kept, rebase on main and merge. Then, server idle: restart it
   (loads metric shopkeeper), rebase exp/scuffed-shop-sign on main, bench vs 671cd32 metric shopkeeper. Open: the new
   crashes and stuck endings need a look before more pace work.
   Exp 26 DROPPED (job 56 @2304: starved +1.7 [-0.7, +4.1], nothing else moved). exp/scuffed-shop-sign rebased: 0a627f9.
   Exp 27 KEPT (job 57 @2304: shopkeeper -0.4 [-0.6, -0.1]), merged; NEW BASELINE 0a627f9 (replaces 671cd32). Exp 28 KEPT (job 58 @2304: crashed -0.4 [-0.7, -0.1]), exp/item-names merged. NEW BASELINE 5ae7ab0 (combines exp 27 and 28), job 59 playing 2304 games. Exp 29 KEPT (job 60 @1152: crashed -1.2 [-2.0, -0.4]), exp/form-apply merged; NEW BASELINE 6449a12 (1152 games, extend to 2304 when needed). Baseline 6449a12 has 2304 games. Exp 30 exp/leave-dlvl1 DROPPED (job 62 @2304: rung2 -0.1 [-0.9, +0.7]; Mines T2927 vs T2966, the XL gate does not explain pre-Mines time, still unknown where T2966 vs yardstick T1173 goes). Pre-Mines turns (44 seeds, pace2.py): Dlvl 1 38%, level 2 29%, level 3 18%, level 4 10%; main cost = exploration_strategy(0) preempt, full exploration of every level. exp/dlvl1-stairs (worktree ../screens-stairs): leave Dlvl 1 once > is seen; Dlvl 1 turns 1226 -> 179, Mines T2449 -> T1268 but 30 vs 34 of 44 reached. Exp 31 DROPPED for now (job 63: rung2 -3.0 [-5.8, -0.2], starved -3.9, early mimic deaths in shops at XL 1). Exp 32 exp/skip-shops DROPPED (job 64 @2304: mimic -0.3 [-1.0, +0.4]; 64 vs 71 mimic deaths, early deaths 60 vs 59; hand: rung1 +1.8, starved -2.0, weak).
   Dlvl 2-4: 16 seeds show both > seen 45-725 turns into the branch level, then full exploration anyway, random stair pick, and wrong picks fully explore the next level (Dlvl 5 visits). exp/mines-branch 30ce233 (worktree ../screens-branch, off main, suite 493): stop exploring once a level shows two > with one untried; 24 seeds Mines T2370 -> T1909, reached 17 -> 18, mean turns Dlvl 2/3/4/5 1831/1001/578/129 -> 1750/833/304/0. NOT BENCHED. Owner stopped for today 2026-10-31.
   2026-11-01 session resumed: server env checked (NH5 python, one server), exp 33 = job 65 exp/mines-branch vs 6449a12, metric rung2.
   Exp 33 exp/mines-branch DROPPED (job 65 @2304: rung2 -1.9 [-4.2, +0.4]; rung1 +5.6, Mines T2260 vs T2966, but rung3 -3.6 [-5.9, -1.3]; Mines deaths before Minetown 692 vs 586, 197 vs 113 at XL <= 5, rothes 53 vs 31). Pace changes buy arrival, not survival: baseline stays 6449a12.
   Exp 34 exp/storeroom-chests KEPT, merged (job 66 @2304: mimic -0.5 [-0.9, -0.2], 59 vs 71; rung1 +0.6): Storerooms (dat/themerms.lua:250, 3 of 4 chests are mimics, no mindiff) are only 12 of 71 deaths. NEW BASELINE 4da0769 (2304 games).
   Replay of 56 mimic seeds (all reproduced; scratchpad mimtrace.py, wraps Agent.update_state; run with PYTHONHASHSEED=0 and the fixtime LD_PRELOAD, 35 s on 11 procs): 43 of 54 traced deaths inside a shop. Hero enters while exploring, shop_interior only appears then, check_items walks item to item. Exp 32 filtered goals only, and not items.
   exp/shop-wall (worktree ../screens-shopwall, off main, suite 499): XL < 8: bfs never enters shop_interior, and no exploration/item/container goal inside even from inside. 56 seeds: mimic deaths 56 -> 6, none in shops, median T7924 (seeds selected, so biased). Exp 35 = job 67 vs 4da0769, metric mimic (watch starved, rung2, stuck: no shop food below XL 8). If kept: merge, new baseline, retry exp/dlvl1-stairs; exp/mines-branch stays parked until the upper Mines are survived.
   Exp 35 exp/shop-wall KEPT, merged fa04add (job 67 @576: mimic -2.1 [-3.9, -0.3]; rung1 +5.2, starved -4.5, crashed -1.2). NEW BASELINE ffe48bd (576 games, job 68 extends it as needed).
   Exp 36 = job 68 exp/dlvl1-stairs 48a2051 (rebased on main; retry of exp 31) vs ffe48bd, metric rung2; watch early deaths and Mines deaths at XL <= 5 (exp 31, 33: faster can mean weaker).
   Human ascension food study (FOOD-NH5.md end): humans eat what they burn (950-1000 per 1000T), bot 883 -> 707 -> 538; corpses equal, gap is rations and kills. Next food step: measure how much of NH5's placed food (Mines branch item, supply chests) the bot collects.
   Exp 36 exp/dlvl1-stairs DROPPED (job 68 @2304: rung2 -1.3 [-4.0, +1.5], rung5 -2.3, deaths by T1500 81 vs 32, Mines T1490 vs T2941). Baseline ffe48bd, 2304 games. rung metrics count that rung or higher, so rung2 is not 'reached Minetown'.
   All ~/screens-* worktrees removed 2026-11-01 (owner): worktrees now only in .worktrees/, removed after use; branches kept.
   Mines check done (FOOD-NH5.md end): branch food collected, Sokoban already before Mines' End, stuck reports do not predict starvation; 61% of starvers die before Minetown. Gap: corpses T3000-6000 (peaceful gnomes/dwarves for a dwarf) and permafood after T6000.
   Owner delegated the race question 2026-11-01 ('argue with the facts and choose'). Exp 37 = job 69 exp/human-valk (.worktrees/human-valk, val-hum-fem-neu, plan_for gives Sokoban first) vs ffe48bd, metric starved. Keep only if starved better AND dlvl10, rung7, rung8 not worse (rule set before results).
   Exp 37 KEPT, merged 3d163d9 (job 69 @576: starved -9.0 [-14.7, -3.3]; rung3 +12.5, rung4 +9.0, dlvl10 +1.0, rung7 +2.3, rung8 +0.9, deaths by T1500 15 vs 6). Every game is now val-hum-fem-neu; replaces the dwarvish rule. NEW BASELINE d5f032c (576 games). Race and route changed together.
   Exp 38 = job 70 exp/dwarf-soko ac51970 (.worktrees/dwarf-soko: dwarf on Sokoban-first) vs d5f032c, metric starved: the control separating race from route. If dwarf is better or equal on starved and deep rungs, the route did the work: reconsider race. Else human stands.
   Exp 38 exp/dwarf-soko DROPPED (job 70 @576: dwarf starved +6.6 [+0.9, +12.3], rung5 -5.7, rung7 -3.8, deaths by T3000 22 vs 57). Human stands: race did most of exp 37. Worktrees all removed.
   Research (.planning/research/MINES-ENTRY-NH5.md, owner: back ideas with research first): no XL gate. 5.0 ascenders enter the Mines at T1173, XL mostly below 6, 3 of 110 Sokoban first. Bot: 50 of 107 arrive by the wrong stairs on FIND_SOKOBAN, stay 1212 turns, 17 die. Exp 39 = job 71 exp/mines-detour (.worktrees/mines-detour) vs d5f032c, metric rung4; keep if better and starved, dlvl10, rung7 not worse. Smoke same seeds: first visit 1212 -> 13 turns, deaths 17 -> 1.
   Untested from that research: human on Mines-first route; AC at arrival (AC 3 or better 2/72 vs AC 4+ 8/55).
   Direction change 2026-11-01 (owner agreed): stop chasing single killers (top killer 2.9% of deaths). Track A: compare XL, AC, HP, key items per rung, human ascensions vs bot, build a build-up phase around the biggest gaps, permafood is part of it. Track B: offline rewind tool, research only, never in play: replay seed + actions, branch at -10/-100/-1000/-5000 turns, about 20 reseeds per option, few big options, first prove replay is exact, then about 200 deaths.
   Owner 2026-11-01: (1) store rich stats per game: snapshot at first arrival per depth, at each rung, at death and about 200 turns before it (XL, HP, AC, stats, gear, item counts, kills, damage taken); recording only, same seeds must play identically; rerun the baseline once. (2) Rewind tool (track B). (3) Stage requirements: which arrival stats predict surviving each stage; thresholds from data, checked on held-out games, then a gate tested on the bench.
   Exp 39 KEPT (job 71): rung4 +2.0 [+0.4, +3.6], merged eb72207, baseline 56a6fab (2304 games). Gain fades below Sokoban.
   Strength per depth (.planning/research/STRENGTH-PER-DEPTH.md): XL and HP match humans to Dlvl 10-12; AC is the gap, bot stops at -3/-4, humans -6 at Dlvl 10, -12 at Dlvl 18. Why it stops is unknown.
   2026-11-02: stats recording DONE, merged 87e0af5 (nethack_screensaver/snapshots.py, GameResult.snapshots: depth/rung/end/before_end;
   XL, HP, AC, attributes, kills, damage taken, gear, class counts, full inventory; ~12 KB/game). 44 seeds of 56a6fab replay identically.
   Job 72 = baseline 87e0af5, 2304 games (same game code as 56a6fab plus recording). Next: AC/gear analysis on job 72, then stage requirements.
   Job 72 done (87e0af5, 2304 games with snapshots). AC gap (research/AC-GAP-NH5.md): ench never grows (bot never reads scrolls),
   gloves rare, 1/3 no body armour; protection unaffordable (Minetown gold median 121 at XL 8, NH5 price ~2400+).
   Rewind tool step 1 DONE: NLE screens-nh5 cb9d6572f (nle_set_seed lgen 0 = dice only; venv rebuilt); seed 0 reseeded at T3000
   twice -> identical (T13166), other seed differs, unreseeded = stored. Scratch: reseed.py. Step 2: infinite-lives runner
   (scripts/rewind.py: on death replay from start with reseed at D-100 x5, then D-1000, D-5000), ~20 seeds. Step 3: death sorter ~200 deaths.
   Rewind step 2 DONE (scripts/rewind.py, research/REWIND-20.md): 20 seeds, 182 deaths: 68% saved by reseed 100 back, 16% 1000,
   9% 5000 (mostly hunger), 8% never. Ceiling with infinite lives = Medusa's level (1 seed); nobody passes Medusa.
   Bench and rewind now default to 10 workers (owner). Bench server restarted (NH5 python, 10 workers).
   OWNER 2026-11-02: implement the full ascension ruleset (ROADMAP Phase 02.2), then bot-plays/Claude-steers check, then
   playbook + infinite-lives runs, then survival. Early-game bench experiments PAUSED. Part 1 starts with item skills (a).
   Part 1a survey: commands used today: APPLY, DIP, EAT, ENGRAVE, LOOT, OFFER, PRAY, QUAFF, TAKEOFF, WEAR, WIELD, ZAP; none of
   PUTON/REMOVE/READ/PLAY/FORCE/INVOKE. AC cause found: unknown-B/U/C armour is never worn (AC-GAP-NH5.md), fix in Part 4.
   NEXT (was): stats recording (with gear detail, to answer why AC stops), rerun baseline once, stage requirements, rewind tool, refresh the Medusa and later-stage audit (ASCENSION-ROUTE-AUDIT.md is 3.6). XL 14 cannot be ground: see XL14-NH5.md. Later: get_items_below_me 556 (8), stuck endings.
   Exp queue also: exp/scuffed-shop-sign (worktree ../screens-sign, off main, metric rung2 or a shopkeeper metric):
   7 of 24 replayed shopkeeper deaths are kicks at a scuffed sign. See LADDER-NH5.md "Angry peacefuls".
   XL 14 plan: .planning/research/XL14-NH5.md (Castle before Quest; pluslvl sets XP to threshold; chest gain level; eels
   +1000 XP; wand has 1 charge; kill-leader bypass is last resort; return past Medusa unsolved).
   Return past Medusa: .planning/research/MEDUSA-RETURN-NH5.md (cursed gain level rises from her island, 12/12 in spike).
   Wish budget: .planning/research/WISHES-NH5.md (charge + wrest 2 at the Castle, spike 6/6; found charging +1; Vlad throne, Amulet).
   Replay caveat: seed 206 diverged from its stored game under tracing; 340 of 599 starvation deaths are in the Mines.
   Prayer study (6c7bfef, 2304 games): 339 games anger Tyr; 368 later prayers, 0 recognised successes; ends 281 starved,
   34 wrath, 24 other, median 472 turns left; 34/36 wrath deaths Fainting with no food. So "no prayer after a failed
   prayer" only relabels deaths: DEMOTED. Anger is a symptom; the lever is food supply.
   2026-11-02 late: Phase 02.2 Part 1a built on feat/item-skills (plan .planning/phases/02.2-full-ascension-ruleset/02.2-01-PLAN.md):
   rings/amulets, armour by property, unicorn horn, scrolls, wish list, pry chests, levitation/tune primitives; staged
   kit-* tests pass 11-12/12. Job 73 = no-harm bench f4870b4 vs 87e0af5, metric rung2. If no significant loss: merge, then
   Part 1b (Medusa: dig down; levitation crossing with reflection/blindfold). AC-GAP code cause was WRONG (corrected).
   SESSION END 2026-11-02 (owner): playbook written: .planning/research/ASCENSION-PLAYBOOK-NH5.md (whole route, stage by
   stage, HAVE/BUILT/MISSING per rule). Branches (local, unmerged, stacked): main 605089d <- feat/item-skills (Part 1a,
   f4870b4 + state 7a9bf52) <- feat/medusa (dig for GO_DOWN + rise_one_level 9f3d261, passtune solver c4123d1, playbook
   6772def). Checked out: feat/medusa. Job 73 (no-harm bench f4870b4 vs 87e0af5, metric rung2) was left RUNNING.
   2026-11-03: job 73 was INTERRUPTED at 192 pairs (rung2 +0.0, open; server restart). Restarted as job 74 (same spec, stored games reused).
   Job 74 DONE: WORSE (rung2 -3.4 [-6.0, -0.8] @2304; rung1 -3.8, rung4 -3.4). Cause: prying_blade wielded unknown-BUC
   daggers (item_manager stores unknown as UNCURSED); cursed ones welded: cursed weapon wielded at death 215 vs 46,
   dagger wielded on reaching Dlvl 4 49 vs 7. Fix c49e3ee on feat/item-skills (blade must have known BUC); feat/medusa
   rebased on it. Job 75 = c49e3ee vs 87e0af5, metric rung2 (no-harm check again). Merge only if not worse.
   Hand play: scripts/handplay.py (checked commands, game's own square descriptions); seed 1 at T1444 Dlvl 4,
   notes .planning/hand-games/seed1/NOTES.md (F1-F17).
   2026-11-03 later: Job 76 queued = exp/known-buc-wield 65d3307 (off main: weapons only of known B/U/C; baseline
   87e0af5 ends 46/2304 games wielding a cursed weapon) vs 87e0af5, metric rung2. Hand play: staged starts work
   (handplay.py --stage); staged Medusa (seed 1) died T42: dig-down never progresses under attack (dig.c:1355,
   attacks stop the occupation before dig() runs) and Elbereth fails against a crowd (monmove.c:918 panic
   attack); notes .planning/hand-games/medusa-seed1/NOTES.md. Key logs removed (owner).
   2026-11-03 TESTING CHANGE (owner): targeted scenarios first, bench only as no-harm gate for common-path changes, a
   full ladder run per milestone. scripts/scenario_run.py + scripts/scenario_lib.py (wizard setups + pass/fail
   checks; --tree any checkout, e.g. ~/.cache/screens-bench/worktrees/<sha>; SCENARIO_HOOK debug file).
   Validated: pry-cursed-dagger f4870b4 0/4 -> c49e3ee 4/4; wield-unknown-cursed 87e0af5 0/4 -> 65d3307 3/4 (no weld
   4/4); eye-telepathy current 1/4 (bot throws once, wanders; kitten eats corpse); medusa-dig flooded 3/4 -> 0/4 after
   5497600 (update_level never stored water; unseen = -1). Nobody gets below Medusa yet (map 3 no dry square, map 2
   dies to titan/gremlin). Research notes: MEDUSA-NH5.md, TELEPATHY-NH5.md, GUIDE-MAG-R342.md (no Excalibur: neutral).
   Job 75 DONE: c49e3ee no measurable difference (rung2 -1.1 [-3.6, +1.5]; rung1 -2.3 [-4.6, -0.1] watch); cursed
   weapon at death 42 (base 48, f4870b4 245). feat/item-skills MERGED to main 656c7c2 (game code = c49e3ee: NEW BASELINE,
   2304 games stored under c49e3ee). Job 76 (exp/known-buc-wield vs 87e0af5) running; rebase it on main if kept.
   2026-11-03 END (usage limit): exp/eye-telepathy (worktree .worktrees/eye-telepathy, off main 656c7c2) built:
   scenario eye killed 5/8 -> 8/8, corpse eaten 7/8 -> 8/8; next: measure eye/blindfold frequency (eyetrace,
   needs idle cores), then bench vs c49e3ee. Job 76 (exp/known-buc-wield vs 87e0af5) running: read it, rebase on main if kept.
   feat/medusa: water fix 5497600 validated by scenario medusa-dig; next Medusa problem: nobody gets below (map 3 no dry
   square -> levitation/cold crossing; map 2 titan). Remove .worktrees/eye-telepathy after use.
   Job 76 DONE: 65d3307 rung2 -0.5 [-1.2, +0.2] no difference; rung4 -0.9 [-1.6, -0.1] borderline (2nd borderline
   side dip after job 75 rung1: watch); cursed weapon at death 48 -> 6. MERGED: main c49c201 = c49e3ee + weapon rule
   (no stored games yet: needs a baseline run). exp/eye-telepathy rebased on main (381899d). Eye trace of 100 natural
   games on main running (scratchpad eyetrace.py) to decide whether the telepathy rule is worth a bench.
   Later 2026-11-03: eye trace (100 games, main): 87 see an eye, 79 kill one, 48 telepathic, 31 kill eyes but lose the
   corpse, 15 carry a blindfold -> next telepathy rule = eat the eye corpse right after any kill (exp/eye-telepathy
   blind-melee part fires rarely). Levitation crossing built on feat/medusa (41b3284, medusa.py + _cross_medusa):
   scenario medusa-levitate 8 seeds: crossed 1/8 (seed 5), 0 drowned, but heroes die in 30-150 turns (master mind
   flayer, water troll, xorn, titan): stage requirement problem; telepathy setup failed 3/8 (eat step); 2 crashes
   (Cyclic Panic assertion, seeds 2 and 7) to look at. Job 77 = baseline c49c201 (new main) 2304 games, running.
   2026-11-04: Job 77 DONE (baseline c49c201 = main, 2304 games): rung2 56.6%, rung4 33.8%, rung6 15.9%, rung7 7.9%,
   rung8 4.6%, rung9 7 games, dlvl10 35.8%; starved 15.7%, ants 5.0%, rays 3.3%, eye 3 games, crashed 0.5% (13),
   median depth 8. main c49c201 is now the stored baseline. Crashes: corpse-prefix names (pickled/deep fried <monster>,
   monster.py:45) 3, heavy iron ball prompt 2, "cannot reach the doorway" 2, go_to no reachable neighbor 2.
   2026-11-04: bench web page got "Stop all jobs" and "Shut down bench" buttons (main 41a783c). Medusa-levitate crashes
   (seeds 2, 7) fixed: pickup while levitating, #terrain while confused (menu answer sent as a move), #apply in a
   handless form. feat/medusa 1a84cc0; all scenarios: 0 crashes, crossed 1/8 (stage strength problem remains).
   Same fixes for main: exp/disoriented 7514591 (worktree .worktrees/disoriented); job 78 = 7514591 vs c49c201,
   metric rung2 (no-harm gate). Job 78 STOPPED by the owner at 1152/1400 games: rung2 +0.1 [-1.5, +1.7], no
   difference; crashed 6/1400 (0.43%) vs 12/2304 (0.52%). MERGED: main 7514591 (game code changed: the stored
   baseline is still c49c201; 1400 games stored under 7514591; finish job 78's spec to get 2304). main merged into
   feat/medusa 8ea898b (suite 543 passed). Worktree main-check removed.
   NEXT SESSION (2026-11-05): eat-the-eye-corpse rule (exp/eye-telepathy, .worktrees/eye-telepathy: rebase on
   main first) -> scenario eye-telepathy, then no-harm bench vs 7514591 (first finish its baseline to 2304); then
   Medusa stage strength (heroes die after crossing) and hand play per the owner plan below.
   2026-11-05: exp/eye-telepathy rebased on main 7514591 (93fb928) + eat_eye_corpse rule e1d8086: after any eye
   kill go to the corpse and eat it at once, Satiated too unless "hard time getting all of it down" was seen
   (choke needs >= 2000 nutrition, eat.c:3138; warning at 1500). Scenario eye-natural (3c4876b on feat/medusa, no
   towel, 12 seeds): kills 7/12; branch eats the one corpse main leaves (seed 12); 5 kills drop no corpse, 1 pet ate.
   Job 79 = e1d8086 vs 7514591, metric rung2 (no-harm gate; also plays 7514591 baseline games). Merge if not worse.
   2026-11-05 later: Job 79 STOPPED at 1152 (owner rule: stop when clear; watcher lo >= -2 pts): rung2 +1.8
   [-1.5, +5.2]; MERGED main 0e6f5f4 (game code = e1d8086, 1152 games stored). main merged into feat/medusa.
   Medusa stage strength (feat/medusa 08f3834..6696b63): humans at Medusa arrival (72 NLD 3.6 ascensions, 59 with
   a Medusa kill): AC -14 (p75 -11, p90 -9), XL 13, max HP 110; Castle arrival AC -17. Stage now adds cloak of
   protection + leather gloves (about -14). Stage fixes: eye eaten before the teleport; wizard luck prompts
   answered n (forced prayer success was ON before: older staged results too optimistic); bot refuses seducers
   ("Shall I remove your"); ^X "You are telepathic" read. Crossing: travel stalled at Medusa's locked doors
   (no kicking while levitating, dokick.c:921) -> land at the door: crossed 1/10 -> 4/10, seed 1 went down.
   OPEN: 7/10 staged heroes still die (crowd at T85, jabberwock T48, minotaur, storm giant, Aleax, fire
   elemental, giant eel drowning). Next: classify these deaths against human play (escape items, Elbereth,
   retreat upstairs, speed) before building anything.
   2026-11-05 evening (session end, PC shut down): Job 81 = exp/stationary-passive a810318 (never melee spotted/
   ochre jelly, green/red/yellow mold: ONLY_RANGED_SLOW_MONSTERS) vs e1d8086, rung2 no-harm gate. Stopped at
   shutdown with 1152 pairs: -2.7 pts [-6.7, +1.3] (192: -3.6, 384: -4.2, 576: -4.0). Gate NOT passed (needs lo >= -2).
   NEXT: rerun/extend job 81 to 2304 with scripts/bench_watch.py --gate <id>; if still negative, look at stuck games
   (jelly/mold blocking a Mines passage) and the jelly death counts before any fix.
   Research (all in .planning/research/): SURVIVAL-NH5.md, SCROLL-ID-NH5.md; external/PROMPTS.md R01-R16 for
   ChatGPT/DeepSeek (Gemini dropped: worst answers); answers in external/R0x-<agent>.md. Claude's own R03, R05, R07
   written and compared with ChatGPT (R05: elves carry elven mithril 1/4; R07: confused genocide kills the hero,
   blessed destroy armour cancel keeps the random target, cursed genocide 'none' still makes a monster). 2026-11-08: R03, R06 compared (stairs shed all four killers;
   soldier-ant poison; 5.0 priest: answer the 2nd suggested number, first buy = AC -2..-4 for 2400-4000 gold at XL 8;
   vault = ~200 + 200 x depth gold). R08-R10 compared too
   (eels drown a levitating hero; Medusa digging down lands outside the Castle moat; Castle has no down stairs,
   trap doors only; castle chest locked: force with a spare blade, never blunt). R11-R16 checked
   (5.0 Valkyrie starts with a +1 spear and gets stealth at XL 3; ritual: ring the Bell < 5 turns before
   reading the Book; R14/R15 web-only, CodeHack paper unread). All 16 prompts answered. Compare each new answer
   with R0x-claude.md (write Claude's own first if missing).
   Planned build after job 81: scroll price-ID: 1) NLE option price_quotes, 2) item parser '{buy X sell Y}' suffix,
   3) sell-offer ID in shops buying scrolls (drop on costly square, answer n; ignore 'only'/credit/'uninterested'),
   4) read safe groups; plus prompt handlers: blessed fire position (never escape), blessed destroy armour (cheapest
   piece, escape is not a cancel), genocide by BUC. Candidates: damage-based retreat threshold (R03), unicorns (gems,
   never melee hostile), elven mithril pickup/wear check, gloves/cloak cause checks.
   NEXT SESSION (owner plan): 1) read job 73; if no significant loss merge feat/item-skills to main (then feat/medusa
   after its staged medusa batch, 12 seeds, needs the bench idle: 10-core rule). 2) Claude PLAYS SOME GAMES BY HAND.
   OWNER GOAL for these games: refine ASCENSION-PLAYBOOK-NH5.md until the Python bot can use it as a ruleset. Every
   rule gets: trigger (message / blstats / map / inventory the program can see), action (exact keys, prompt answers,
   order), done-when (message or state), if-it-fails, evidence (game seen in or source line). Mark vague, wrong and
   missing rules; record XL/AC/HP/items per stage; unreached stages stay "unchecked". 3) Then back
   to testing with the bot (Part 1b-1g).
   2026-11-07 (session end): bench restarted (`uv run screens-bench serve --workers 10`; watcher
   `uv run python scripts/bench_watch.py --gate <id>`). Job 81 rerun as JOB 82 (a810318 vs e1d8086, rung2), reused the
   1152 stored pairs, DONE at 2304: rung2 -1.5 pts [-3.6, +0.7] "no measurable difference", but the no-harm GATE is NOT
   passed (lo -3.6 < -2). Not merged. Candidate stats (1193 stored games before the rest ran): spotted jelly deaths
   28/2304 on baseline, gone from the candidate's top killers; dlvl6 77.0 vs 76.5, dlvl10 37.0 vs 36.8, crashed
   0.42 vs 0.52%; small dips in rung1 (74.5 vs 75.3) and rung4 (33.0 vs 34.6). Bench and watcher stopped, no job open.
   NEXT SESSION: 1) start the bench; per-seed diff of job 82: seeds where baseline reaches Minetown and the candidate
   does not -> replay a few (guess, unchecked: a jelly/mold blocks a narrow Mines passage, so the bot can neither
   kill nor pass it). Fix idea if confirmed: allow melee when the passive monster blocks the only path (or ranged
   attack/throw daggers), then re-bench. If not explainable, drop exp/stationary-passive and remove .worktrees/stationary.
   2) then the scroll price-ID build (plan above); 3) owner's new ChatGPT answers, compare with R0x-claude.md.
   2026-11-08: step 1 DONE. Job 82 per-seed: Minetown lost 252 / gained 224 seeds (p~0.2, chance); deaths in the
   Mines before Minetown 302 cand vs 309 base, so NO Mines-blocking jelly. Candidate ~1 pt lower on every rung
   (mines 57.5/58.6, minetown 17.9/19.1, sokoban 24.7/26.7, dlvl15 6.3/7.3); jelly/mold deaths 15 vs 38.
   Dropped exp/stationary-passive, removed .worktrees/stationary. Weapon check (e1d8086, 2304 end snapshots): the bot
   wields the starting +1 spear in 2029, nothing in 148, daggers in ~46; it never upgrades (5.0 start = spear, not
   long sword). Candidate experiment (research first): wield a better found weapon (long sword d8/d12, Valkyrie
   Expert) and find why 6 % end bare-handed. All 16 ChatGPT prompts answered and checked (R0x-claude.md).
   Price-ID steps 1-2 DONE on branch feat/price-quotes (from main, a773502): options.py GAME_OPTIONS = NLE
   defaults + price_quotes, used by game.py and staging.py; parser strips " {buy X sell Y}" (also cut at 80
   chars); 4 tests; 538 pass; 10 seeded games 0 exceptions (not benched yet). handplay.py exists only on
   feat/medusa: pass options=GAME_OPTIONS there after merging. NetHack records seen prices per real type
   (shk.c:439), so after one sell offer every item of that type shows {sell X}: step 3 = in a shop that buys
   scrolls, drop an unknown scroll, answer n, read the suffix; base = 2X normal or 8X/3 (1/4 of keepers, R04).
   Then 4) read safe groups; then bench all steps together (common-path change).
   2026-11-08 later: step 3 BUILT differently. Steps 1-2 REVERTED on feat/price-quotes (d72f4ad): NetHack also
   records "offers only" (keeper short of gold) and credit offers in that price memory, so the {sell X} suffix is
   not reliable and nothing would read it (no-unused-records). Step 3 (3aeef1a + doc 07e8e81): new
   autoascend/item/shop_sell.py (offer parser, shk.c set_cost replica incl. dunce/shirt base/3 and m_id%4 keepers
   3/4, costs_for_offer), ItemManager.sell_offer_identification narrows possible objects by cost,
   Inventory.sell_offer_identify (in gather_items before read_scrolls): in shop types 1/3/10 or unknown (0), on a
   shop-interior square with nothing below, drop 1 unknown scroll, answer n, narrow, pick it up. Step 4 already
   existed (scrolls.py reads when all remaining identities are SAFE_UNKNOWN). 4 tests (tests/test_shop_sell.py).
   20 seeded games: 18 offers in 3 games, 0 mismatches, every scroll picked up again. Lesson: StatsLogger raises
   KeyError on an unregistered event name and Strategy swallows it -> register every new log_event name.
   Pre-existing bug (23 stored games, many SHAs): OverflowError global_logic.py:116 add_item (float infinity).
   scripts/bench_watch.py is only on feat/medusa: from other branches run a copy with `python3 -I <copy> --gate <id>`.
   JOB 83 (07e8e81 vs e1d8086, rung2, no-harm gate): @1152 -1.9 pts [-5.4, +1.6]; DONE @2304: -1.7 pts [-3.6, +0.2] "no measurable
   difference", GATE NOT PASSED (lo < -2), NOT merged. Almost the same as job 82 (-1.5 [-3.6, +0.7]).
   Determinism check (stored games, same seed): 07e8e81 vs e1d8086 identical end (turns, score, rung) in 866/2304
   seeds; games ending before turn 1500: 66/71 identical (so ~7 % divergence even where shops cannot matter).
   a810318 vs e1d8086: 462/2304. Bench JSON has no per-game event counts, so how often sell_offer_identify ran
   cannot be counted from stored games. JOB 84 queued at session end: A/A test main 0e6f5f4 (game code identical to
   e1d8086) vs stored e1d8086, rung2. If 0e6f5f4 is also ~-1.5 pts, the stored e1d8086 baseline is lucky / the
   environment drifted: then re-store a fresh baseline and judge 82/83 again against it (merge feat/price-quotes
   if it passes). If job 84 is ~0, job 83's loss is real: per-seed look at the lost Minetown seeds.
   2026-11-09: A/A job 84/85 (0e6f5f4 vs stored e1d8086): 199/199 seeds IDENTICAL (turns, score, depth, end).
   The bench is deterministic; the stored baseline is not lucky; the "7 % short-game divergence" was the code change,
   not noise (item 2 of the old plan closed). Watcher caveat: bench_watch.py stops an A/A at once (hi < +2) - don't run it on A/A.
   Job 83 cause (action trace, seed 1112): 1438/2304 games diverged, only 213 had an offer. shop_type 0 squares
   include outline spill outside the door (agent._update_level_shops BFS), and squares seen after the welcome
   never got the type: the bot dropped every unknown scroll outside an armour shop, no offer, marked tested.
   Fix 230339b: TRY_SHOPS = known scroll-buying types only; the known type spreads over the keeper's outline;
   a drop with no keeper answer (shk.c sellobj reactions) marks the square, not the scroll. Seed 1112 replays
   identical to e1d8086. JOB 86 (230339b vs e1d8086, rung2, gate): +0.0 [-1.9, +1.9] @384 PASSED; diverged
   94 vs 318 (07e8e81) on the same seeds, games with an offer 70 vs 37, 0 mismatches. MERGED main c074c1c.
   main merged into feat/medusa (555 pass). JOB 87 = no-harm gate feat/medusa vs main c074c1c, rung2 (also
   stores the c074c1c baseline). If it passes: merge feat/medusa to main; c074c1c+medusa is the new baseline.
   JOB 87 PASSED (+0.9 [-1.4, +3.2] @1152; crashes 6 vs 10; agent_panic per game 537 vs 435, watch it).
   feat/medusa MERGED main e586de2 (tree = dec417a). BASELINE = dec417a games (1152; extend to 2304 when needed).
   Job 88: baseline dec417a extended to 2304 games.
   Weapon study (dec417a end snapshots, 1158 games): +1 spear wielded in 984; better melee weapons almost never
   found (3 long swords, 1 katana). ~100 end bare-handed: spear stolen by wood nymphs (steal.c:436 takes uwep
   when the pick is gloves), or lycanthropy; most carry unknown-status daggers/spears/scimitars they will not wield
   (known-buc rule 65d3307). 60 artifact weapons carried, NONE wielded (41 Mjollnir = altar gifts, always uncursed,
   pray.c bestow_artifact). JOB 89 = exp/wield-artifacts 72ca0b6 (.worktrees/wield-artifacts) vs dec417a, dlvl10:
   artifacts count as known-status for wielding; Demonbane = silver mace in 5.0. Smoke: seeds 1322, 1250 wield
   Mjollnir. Rule set before results: keep if dlvl10 lo > 0; if not significant, merge only if lo >= -2 and the
   artifact-wielding games reach deeper on average. Owner: stop for today after job 89.
   JOB 89 KEPT: dlvl10 +0.8 [+0.2, +1.5] @2304 ("better"); 126 games end wielding an artifact: mean max depth
   11.0 vs 9.3, Dlvl 10+ 75 vs 58, median turns 11840 vs 9536; 0 crashes. MERGED main fba3d33 (557 pass),
   worktree removed. NEW BASELINE 72ca0b6 (2304 games; game code = main fba3d33).
   Where we are (72ca0b6, 2304 games): Mines 76 %, Minetown 59 %, Oracle 56 %, Sokoban 35 %, Sokoban solved /
   Mines' End 19 %, Dlvl 15+ 9 %, Quest 6 %, Medusa 1.1 % (25), Castle 0; deepest Dlvl 29. Ceiling with current
   code = Medusa's level (no Castle/Gehennom code; infinite-lives runs never passed Medusa).
   OWNER DECISION 2026-11-09: switch the working order next session (~1-2 sessions for the switch):
   main track = end game in staged starts (Medusa crossing reliable first, then Castle, Valley, Gehennom,
   invocation, Planes), each skill measured by staged success rate; infinite-lives runs (scripts/rewind.py) as the
   deep-game progress measure. Background track = strength package on the natural bench (armour/AC gap), with
   batched no-harm gates for independent fixes, an experiment queue that runs unattended, and a log of when new
   code first fires. Rough estimate given to owner: switch 1-2 sessions; Medusa 2-3, Castle 3-5, strength 3-5,
   Gehennom to invocation 10-15, Planes 5-8 sessions (25-40 to a first possible ascension, very uncertain).
   OWNER 2026-11-09 (added to the switch): THIRD TRACK = Claude-steered teaching games. The bot plays, Claude
   decides at hard points (Medusa, Castle, Planes, emergencies); every Claude decision is logged with the game
   situation; recurring decisions become bot rules (playbook-to-ruleset); progress measure = Claude interventions
   per game -> 0. Not benchable (not deterministic): bot rules derived from it still go through the bench.
   Steered ascension = milestone; the goal stays a bot-alone ascension. Start from scripts/handplay.py.
   Also take into the switch: read BotHack / nethack_astra end-game logic (ideas, not code) and make
   "dig for victory" the default Gehennom route (code only Valley, Vlad's, Wizard's Tower, vibrating square,
   invocation, way up). SUBAGENTS (owner yes 2026-11-09, with guards): only after Medusa is solved;
   2 per wave (wave 1 Castle + Vlad's or Wizard's Tower; wave 2 Valley/dig route + invocation, way up); ask the
   owner again before each wave with the concrete tasks; each subagent gets one bounded stage with a clear
   finish test and must report a working, tested step early; stop a subagent that burns tokens without progress;
   never start a wave late in the token budget.
   NEXT SESSION: 0) DO THE SWITCH: rewrite ROADMAP.md working order, build the bench queue/batched gate/trigger
   log, make infinite-lives a routine job, then start the Medusa staged track.
   1) start the bench if not running; baseline for experiments = 72ca0b6.
   2) exp: bare-handed fallback - with no weapon in hand, wield the best unknown-status one-handed weapon
   (risk ~10 % cursed vs bare d2); separate experiment. 3) nymphs: kill at range or avoid melee (they steal the
   weapon). 4) agent_panic per game rose 537 vs 435 with feat/medusa - find which panics. 5) OverflowError
   global_logic.py add_item (float infinity).
   2026-11-11 SESSION (owner away 2-3 h, "do what gets us closer"): SWITCH started. ROADMAP.md has a
   "Working Order" section (3 tracks), commit 23f8dad. MEDUSA STAGED TRACK, measure = staged medusa seeds 1-20
   (`.venv/bin/python scripts/staged_run.py medusa --seeds 1-20 --jobs 10 --out .planning/staged/<name>.jsonl`),
   "below Medusa" = max depth > depth at the first snapshot (NOT min depth: stair escapes go up).
   Results (all files in .planning/staged/): old stage on main fba3d33: 0/20 below Medusa, 20/20 dead (no
   levitation in the kit). Stage fixed (kit2: + ring of levitation + eaten floating eye): 5/20. Natural arrival
   (kit3: hero ON the up stairs via wizard ^T + getpos '<', 17/20 seeds; ring carried, not worn): 4/20 + 2 crashes
   on "statue of a knight named Perseus" (parser; fixed). Stair escape (escape4/5): 5/20, early deaths 3 -> 2.
   Crossing fixes (cross6): 10/20. MERGED main 8cea210 (564 passed). What was built:
   - combat/stair_escape.py: Dlvl >= 21, HP < 50 %, up stairs within 8 steps, a non-M2_STALK hostile adjacent ->
     walk/climb, rest to 90 % above (only stalkers follow: dog.c keepdogs, mondata.c levl_follower; minotaur,
     dragons, ettin, xorn, titan, giants, mind flayers are not stalkers; trolls, gremlins, devils, Aleax are).
     A blocked step marks a 20-turn fail ('stair_escape_failed'). action_str needed the new action type (an
     unknown action raised inside fight2 and was swallowed: no events at all - watch for this with new actions).
   - _cross_medusa: AgentChangeStrategy during the trip -> retry next turn ('medusa_interrupted'; before: hover
     200 turns over water); any travel stall -> stall_landing; landing_square only on squares reachable floating
     (medusa.float_reach) - seed 7 hovered 1000 turns in the moat inside Medusa's walls.
   DROPPED: hold-the-stairs (no moving off the up stairs in deep fights): 8/20 vs 10/20, reverted (hold8.jsonl).
   NOT a Medusa problem: heroes past Medusa die on the next level (Castle) after 1000s of turns, most fainting
   (hero has 2 food rations + 2 lizards; natural Dlvl 20+ games carry a median of 3 food items) -> stuck at the
   Castle = the next stage (Castle code: passtune/drawbridge, trap doors; ASCENSION-PLAN-NH5.md).
   Remaining Medusa failures (cross6): early swarm deaths 4 (map 2 titan "summon nasties" next to the arrival:
   seeds 4, 13, 17 at T<60; seed 13/17/10 are the 3 seeds where the hero does not start on the stairs);
   'medusa_no_reflection' in seeds 10/18 in hold8 (reflection lost? not checked); seed 8 starved on the level.
   Castle stage baseline (castle-base1.jsonl, seeds 1-20): 0/20 below the Castle, 6 dead before T110 (minotaurs:
   maze level), the rest stall and starve/die (no Castle code: dig_undiggable, no passtune use).
   JOB 90 STARTED (session end): main 9054ea1 vs 72ca0b6, dlvl10, no-harm gate; watcher bench_watch.py --gate 90.
   NEXT: 1) read job 90 (natural no-harm job for main 8cea210 vs 72ca0b6 (also stores the new baseline; game code changed only
   at Dlvl 21+ and statue names). 2) Castle stage (staged_run castle) baseline + first Castle rules. 3) Medusa:
   titan map arrival (kill/avoid the caster, or escape at once when "Monsters appear from nowhere").
   2026-11-11 (2nd part, owner: "start on the castle rules while job 90 runs"): JOB 90 DONE: no-harm shown at 192
   pairs, diff +0.0 (stopped by the watcher) -> main 9054ea1 is the natural baseline candidate (game code unchanged
   above Dlvl 21). CASTLE TRACK (autoascend/castle.py, global_logic _pass_castle/_castle_breakout), measure =
   staged castle seeds 1-20, "below" = max depth > arrival depth:
   - STAGING BUG FIXED (affects all staged results before today): the wizard identify menu was cancelled with ESC
     (needs Enter) -> kits were UNIDENTIFIED (4 murky potions never quaffed, amulet unknown) and the levitation ring
     was put on at stage time (the "levitation" skip saw "a coral ring") -> heroes floated from turn 1 (could not
     dig, engrave or kick). Medusa re-measured with the fix (medusa-ident9): 9/20 (was 10/20: same level).
   - Castle stage now = Medusa kit + flute (+ cloak/gloves, eaten floating eye): humans are at least as armoured.
   - Castle facts (5.0 castle.lua/src): map at screen (y3, x8), mirrored left-right on some seeds (noflipy only),
     the hero arrives on the WEST side either way (so sometimes on the back side); raised drawbridge shows on the
     portcullis (display.c:2394) which sits in a dark wall and is seldom seen -> detect by the lit courtyard +
     moat; key square mid-courtyard edge = moat (front) / floor (back). Back door (map 56,8) is locked, trap door
     right behind it (55,8) -> Valley. No kicking while levitating (dokick.c:921); levitation does not stop eel
     drowning (uhitm.c:3389); maze fill: 0-1 minotaur (sp_lev.c:2956), boulders, random traps.
   - Rule: reach map (57,8) (walk if reachable, else levitate round the moat over a template path), land, kick the
     door, step west onto the trap door. Breakout (castle candidate = DoD Dlvl>=25 without '>' seen, no frame
     yet, nothing reachable left): known traps walkable on that level (agent.trap_walk_levels), then break the
     nearest boulder with the pick-axe (boulders.break_candidate, agent.dig_toward). _castle_due() in the dive
     loop's until-condition (else the rule ran only ~8 times in 1500 turns).
   - Results: castle-base1 0/20 (12 seeds boxed in maze pockets by boulders+traps, starved) -> back2 (no
     breakout) 2/20 -> back3 5/20, no starvation, all deaths in fights: eels drowning 4 (1, 6, 10, 15), sharks
     3, xorns 3, minotaurs 2, master mind flayers 2. The float crosses ~26 moat squares (no dry way round) and
     every interruption stops the hero over the water. Medusa-stage games now also pass the Castle (medusa-ident9
     seed 10: Dlvl 27 -> 30 Valley; seed 3 fell too).
   NEXT (Castle): eel grip escape (wiki Giant eel: putting on a levitation ring makes a holding eel let go;
   Elbereth scares eels; oilskin cloak prevents the grip), keep floating past sea monsters instead of fighting
   over water; why prayers right before death did not save (seeds 4, 9, 12, 16 in back3); medusa_no_reflection
   7x in medusa-ident9 seed 16 and medusa_no_levitation seed 15 with an identified kit (check).
   2026-11-11 (3rd part, owner "yes go" on eels): MERGED main d77ff25 (staged castle 5/20 -> 8/20 below the Castle).
   - Eel grip (agent.held from messages, the later of grip/release wins; water_holder = adjacent monster on water or
     an unseen ; class): 5.0 FACT: putting levitation ON does nothing to a hold (trap.c float_up), floating DOWN
     breaks it ("Startled, ... can no longer hold you!", trap.c:4087); a fleeing monster lets go (monmove.c:473),
     eels respect Elbereth -> emergency: levitating over DRY ground -> take the ring off ('grip_land'); on the
     ground -> engrave Elbereth ('grip_elbereth', verified: "You get released! The giant eel turns to flee").
     Over water: nothing (landing there = "You sink like a rock", drowned seeds 6/11 in castle-pray6).
   - Castle float only at HP >= 80 % (CASTLE_FLOAT_HP, the dive loop's rest share).
   - STAGING BUG 2: every wish adds 50-149 to the prayer timeout (zap.c:6421): staged heroes started at ~1700 and
     every low-HP prayer failed ("Thou hast angered me"/"arrogant"). staging.reset_prayer_timeout: forced wizard
     prayers (rnz(350)) until ^X shows <= 300 (fresh game value, what agent.is_safe_to_pray assumes). After it:
     prayers succeed (castle-pray6: 5 seeds "shimmering light"). Results: grip4/grip5 5/20 (rule fires, same
     count), pray6 8/20, grip7 8/20 (no drowning by landing). Remaining deaths: fights while floating (castle_interrupted
     on nearly every float), eels drowning over water (6, 11), xorns, wraith+gas (1), vampire lord in the Valley.
   Medusa re-measured with the prayer fix (medusa-pray10): 13/20 below Medusa (ident9: 9/20), 1 also fell through
   the Castle trap door. Job 92 no-harm: diff +0.0 at 192 pairs (stopped).
   DROPPED (castle-quiet8, reverted): start the float only with no hostile in view: 9/20 vs 8/20 (noise); floats
   are still interrupted (attackers appear DURING the float: underwater sharks "something you can't see", xorns
   from the throne court walking through the castle walls, seed 9 trace T891-930), and seeds 5/14 waited 266/378
   times for a monster that never came (seed 14 never floated). Better idea, not built: while castle-floating,
   do not stop to fight (fight2 activation) unless a monster blocks the next path step: hero Fast ~15 outruns
   shark 12 and xorn 9 over the ~75-square float. Entry point: agent.fight2 first block (the `if not coming ...`
   return), add a castle-float flag set by global_logic._pass_castle around its step loop.
   NEXT (Castle): stop floating into fights: keep moving past sea monsters/slow ones while levitating (or float only
   when no hostile is in view); Medusa re-measure with the prayer fix (not done yet); job 92 = no-harm gate for
   d77ff25 (grip rule runs at every depth) vs 9054ea1.
   2026-11-11 (4th part, resume): DROPPED exp/float-past (1220445, branch kept unmerged): while castle-floating, skip
   fight2 unless a monster is on the next path square or holds the hero (castle.float_past, agent.float_next).
   castle-past9: 7/20 vs grip7 8/20 (noise; bar was >= 11). The rule fired 279x, castle_interrupted 52 -> 17, but the
   deaths moved: sharks keep biting along the moat path (seeds 9, 18 now die to sharks), eel drowning (6), minotaur
   (15), xorn (20); gained 14, 17. 5 seeds (3, 8, 11, 12, 16) die with 0-1 floats: before or right at the float start
   (unaffected by any float rule). Conclusion: running vs fighting over the moat is a wash; the moat float itself
   is the risk (sea monsters follow along the water). NEXT (Castle) candidates: shorten/avoid the moat float
   (front entry with the passtune: drawbridge open, cross on the bridge), or kill/scare sea monsters before
   floating; and look at the 5 early deaths (no float involved).
2. Next natural experiments, one at a time (baseline = main's stored SHA unless natural-play code changed):
   explorer idle turn; no prayer after a failed prayer; Mines branch-stair glyph; pry chests; unicorns; mimics;
   hallucination/unicorn horn; gas spores near peacefuls; Sokoban food.
3. Track B next: fix the post-dig hang, then the Castle (passtune Mastermind with an instrument, pry the wand chest,
   trap doors), per .planning/research/ASCENSION-PLAN-NH5.md.
Resume file: None
