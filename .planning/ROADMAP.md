# Roadmap: NetHack Screensaver: Ascension

## Overview

The path to one clean ascension starts with numbers the owner can check: a reproducible install, a key-based natural-game funnel, a fresh baseline with A/A, sound paired statistics and a claim check that rejects anything without a job ID. Next, the full change loop (triage, refactor gate, paired experiment) is proven end to end on the first real fixes. The LLM analyst and pilot are built early, running locally on Ollama, alongside the scripted early-wall work and outside the deterministic bench. The early wall (food, getting stuck, safety) is then fixed by system and shown as higher funnel rates. After that the late wall is broken down: kit supply plus Medusa and the Castle, then Gehennom to Astral. Each late stage is a staged contract, and per stage the better of the scripted bot and the pilot is kept. The last phase joins the stages into natural games and records one verified, reproducible clean ascension.

Every phase ends with a measurable result (bench job, funnel metric or staged pass rate), not with a finished layer.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Measurement and Proof Foundation** - Reproducible install, key-based funnel, fresh baseline with A/A, paired statistics, claim check (completed 2026-11-14)
- [ ] **Phase 2: Proven Change Loop** - Triage, refactor gate and paired experiments shown end to end on the Mines branch fix and the character A/B
- [ ] **Phase 3: LLM Analyst and Pilot** - Local-first LLM labels deaths and plays handed-over sections with every call recorded, outside the bench
- [ ] **Phase 4: Early Wall by System** - Food, getting stuck and class-wide safety fixed as systems, shown as higher natural funnel rates
- [ ] **Phase 5: Medusa and Castle Wall** - Late-game kit on natural arrival at Medusa; staged contracts for Medusa, the Castle and wishes; scripted vs pilot per stage
- [ ] **Phase 6: Gehennom to Astral** - Staged contracts for Gehennom, the Quest, both towers, the invocation and the Planes
- [ ] **Phase 7: Clean Ascension** - Clean-run verifier, integrated natural runs, one recorded and reproducible clean ascension

## Phase Details

### Phase 1: Measurement and Proof Foundation
**Goal**: The owner can check every progress number against a fresh, reproducible natural-game funnel of `main`, and claims without proof are rejected automatically
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: MEAS-01, MEAS-02, MEAS-03, MEAS-04, MEAS-05, MEAS-06, MEAS-07, MEAS-08, MEAS-09, MEAS-10
**Success Criteria** (what must be TRUE):
  1. A fresh clone runs `uv sync` and finishes a small bench job without the gitignored `reference/nle-src`, and every job records the NLE commit, lock hash and full bot SHA (proof: job ID of a run from a fresh clone)
  2. The live bench database holds a natural baseline of `main` on the dev seed range and an A/A rerun with identical per-seed results; the funnel report lists every stage key (Mines through Astral and ascended) with Wilson intervals, and no decision path reads `rung` (proof: two job IDs plus the funnel query)
  3. The `lgen` pilot (two commits, about 400 seeds each) reports paired discordance with and without `lgen`, and the decision is recorded; the `sokoban_solved` detector is run against a known hand game and the 0/2304 result has a written cause (proof: pilot job IDs, detector test)
  4. The stats tool runs exact McNemar and an always-valid sequential test, a simulation shows its false-positive rate holds under repeated checking, and the power calculator gives the MDE and sample size an experiment must declare before running; dev, confirm and final seed ranges are fixed, and the bench refuses final-range seeds outside clean attempts (proof: simulation report, refusal test)
  5. Staged, scenario and rewind runs land in a separate `tool_games` table with job IDs and never reach the funnel; `check_claims.py` rejects a claim without a job ID, full commit hash or reproducible query; a job counts as started only once its first game row exists; NetHack facts carry a fact-ledger tag (5.0 source, measured or unverified) (proof: tests for each rule)
**Plans**: 16/16 plans complete

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — NLE from the local bare repo by pinned commit; env fingerprint; fresh-clone and rebuilt-NLE checks (wave 1)
- [x] 01-02-PLAN.md — exact McNemar, always-valid sequential test, power calculator, simulation report (wave 1)
- [x] 01-03-PLAN.md — check_claims.py Stop hook with read-only proof verification and hand-written labelled corpus (wave 1)
- [x] 01-04-PLAN.md — fact ledger tooling: FACTS.toml, citation test, source check, report, coverage (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-05-PLAN.md — lgen through game/worker/runner; Sokoban drop-cause telemetry; quest_portal stage (D-21) (wave 2)
- [x] 01-07-PLAN.md — fact ledger tranche 1a: the seven rule modules (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-06-PLAN.md — sokoban_solved detector run against a played hand game of the Sokoban top level, bot-path Facts (wave 3)
- [x] 01-08-PLAN.md — explicit seed windows, store schema 2 game key, lgen/replicate, env recording (wave 3)
- [x] 01-09-PLAN.md — fact ledger tranche 1b: UNVERIFIED research claims, quest-portal facts, coverage report (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 01-10-PLAN.md — seed-range refusal at API, scheduler and store; confirm gate field (D-22) (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 01-11-PLAN.md — resume interrupted jobs, "started" from game rows, tool_games with job IDs, MCP shutdown (wave 5)

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 01-12-PLAN.md — natural-game funnel (18 stages) with Wilson intervals; rung out of decisions (wave 6)

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 01-13-PLAN.md — experiments declare MDE, judged by the sequential test on seed prefixes; power surfaces (wave 7)

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 01-14-PLAN.md — walking-skeleton proof from a fresh clone; owner picks pilot commit B and rule; pilot queued via MCP (wave 8)

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 01-15-PLAN.md — lgen decision; A/A command; baseline and A/A pre-registered (D-23); baseline started, A/A queued (wave 9)

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 01-16-PLAN.md — A/A verdict by the pre-registered command, baseline funnel, Sokoban cause, proof index (wave 10)

**Research**: `lgen` discordance and the sequential test are unmeasured; both need pilot runs and simulation before use

### Phase 2: Proven Change Loop
**Goal**: The full change loop works end to end on real changes: evidence picks the fix, refactors are proven bit-identical, and behaviour changes are proven by a paired experiment, shown on the Mines branch fix and the character choice
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CODE-01, CODE-02, CODE-04, SURV-01, SURV-04, SURV-06
**Success Criteria** (what must be TRUE):
  1. The refactor gate replays the fixed gate seed set and compares frame-hash traces: a pure refactor commit passes, and a deliberately changed commit fails with the first divergent seed and turn reported (proof: two gate job IDs)
  2. Every commit from this phase on carries `Kind: refactor` or `Kind: behavior`, and behaviour commits name their funnel stage, metric and experiment job; ratchet tests (file size limits, no new bare `except`, no new imports of agent internals) fail the suite on violation (proof: ratchet test run, commit log query)
  3. Failure triage replays the baseline's deaths, extracts features and prints system-level causes ranked by expected funnel gain, reproducible with one command on the baseline job (no LLM needed) (proof: command plus baseline job ID)
  4. With the Mines branch staircase recognised, the share of natural games reaching the Mines rises above the Phase 1 baseline in a significant paired test on dev seeds and again on confirm seeds (proof: dev and confirm job IDs)
  5. The first-ascension character (role, race, alignment) is chosen by written research plus a paired bench A/B with the MDE declared beforehand; the winner sits in one `CHARACTER` constant, and a fresh baseline at that character exists (proof: A/B and baseline job IDs)
**Plans**: TBD

### Phase 3: LLM Analyst and Pilot
**Goal**: A local LLM labels deaths for triage and plays handed-over parts of a game through MCP tools, with Claude Code used only where the local model isn't good enough. Every call is recorded and all runs stay outside the deterministic bench
**Mode:** mvp
**Depends on**: Phase 2 (death dossiers from triage; Phase 1 `tool_games` and claim check). Can run alongside Phase 4
**Requirements**: PILOT-01, PILOT-02, PILOT-03, PILOT-04, PILOT-06
**Success Criteria** (what must be TRUE):
  1. The offline analyst labels death dossiers with system-level causes, and its agreement (kappa) with about 30 hand labels meets a bar fixed before the run; only then do its labels feed the triage ranking. A local Ollama model is tried first (proof: labelled set and agreement report)
  2. A model comparison records quality and speed of local models that fit 12 GB VRAM on the analyst and pilot tasks and names the backend chosen per task. Claude Code on the subscription is used only where no local model meets the bar, and there is no paid API call or cloud service (proof: comparison table with run records)
  3. The pilot plays staged starts through MCP tools (observe, act with a few keys and stop on change, route with the bot's pathing). The scripted bot hands over at defined triggers (arriving on Medusa's level, the stuck detector) and takes control back afterwards, and both handovers show in the run's event log (proof: `tool_games` job IDs)
  4. Every pilot call is recorded (turn, state hash, model, prompt hash); a recorded pilot game replays from its record to the same final state; pilot runs live in `tool_games` and never in the natural funnel (proof: replay test, table query)
  5. The pilot's staged pass rate at Medusa's level on a fixed staged seed set is reported. It is the bar that the scripted Medusa ability in Phase 5 is compared against (proof: job IDs)
**Plans**: TBD
**Research**: harness design, record format, local model choice on 12 GB VRAM, open-book policy

### Phase 4: Early Wall by System
**Goal**: More natural games survive the early and mid game because food, getting stuck and safety are fixed as systems in the order triage ranks them, shown as higher funnel rates on confirm seeds
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: SURV-02, SURV-03, SURV-05, SURV-07, CODE-03, KIT-04
**Success Criteria** (what must be TRUE):
  1. Starvation falls measurably below the 14.5% baseline (the bot keeps a food reserve, buys food in shops and paces its descent), with a significant paired test on dev seeds that the phase-gate run on confirm seeds confirms (proof: job IDs, starvation query)
  2. The share of natural games that never reach the Mines falls measurably (explorer completion; digging out with an owned dig tool), confirmed on confirm seeds (proof: job IDs, funnel query)
  3. Class-wide safety rules (prayer timeout and lockout; passive-damage monsters; cross-aligned unicorns; peacefuls, also while hallucinating; ray bounces) and dungeon awareness (the bot knows whether it is in the Dungeons, Mines, Sokoban, Quest or Gehennom, and uses no prayer, Elbereth or sacrifice in Gehennom) each pass a scenario test keyed on monster flags, not species names, and their death causes shrink in the triage ranking (proof: scenario job IDs, triage diff)
  4. 3.6-era behaviour such as the Excalibur dip is gone, and each removal cites its fact-ledger entry with the 5.0 source (proof: ledger entries, commits)
  5. Survival, food and resource logic sit in their own modules behind an ordered decision arbiter, and every extraction commit has a passing gate job; `agent.py` and `global_logic.py` shrink, and the size ratchets hold the new limits (proof: gate job IDs, line counts)
**Plans**: TBD
**Research**: the root cause of explorer stuck states is still unknown

### Phase 5: Medusa and Castle Wall
**Goal**: Natural games reach Medusa carrying the late-game kit, and the bot passes Medusa and the Castle on staged starts, using scripted code or the pilot, whichever is better per stage. Together this gives a predicted natural rate of getting past the Castle
**Mode:** mvp
**Depends on**: Phase 3 (pilot bar at Medusa), Phase 4 (enough natural arrivals at Medusa)
**Requirements**: KIT-01, KIT-02, KIT-03, KIT-05, LATE-01, LATE-02, LATE-03, PILOT-05
**Success Criteria** (what must be TRUE):
  1. A "needs met" check runs on every natural arrival at Medusa's level (levitation source, dig tool, reflection, telepathy, blindfold, poison and fire resistance). The needs-met rate is reported per job and rises above its first measurement in a paired test (proof: job IDs, arrival query)
  2. The cause of the AC gap is identified first. After that, AC at Medusa arrival moves toward human medians through scroll identification, altar curse testing, enchant armour and worn slots, and the arrival AC distribution beats the Phase 4 gate run (proof: job IDs, AC query)
  3. Medusa contract: digging down past Medusa (dry-square choice, attackers cleared), with levitation crossing as fallback and a return upward when needed, reaches a staged pass rate on at least 40 paired staged seeds. The rate is reported next to the natural arrival rate and the predicted natural conversion (proof: `tool_games` job IDs)
  4. Castle: both routes (back entry; front entry by passtune into the interior to the wand of wishing) run as staged tests on the same seeds. The route with the higher pass rate is kept and the decision is recorded. When the wand is obtained, the bot zaps it, wrests it and uses its wishes in the fixed priority order on staged runs (proof: job IDs per route)
  5. A per-stage scoreboard compares the pilot's staged pass rate with the scripted ability on the same seeds for Medusa and the Castle, and the better one per stage is kept and recorded (proof: scoreboard query)
**Plans**: TBD
**Owner gate**: any farming or exploit used to build kit (e.g. altar camping for gifts) is proposed to the owner before it is built
**Research**: AC gap cause; Medusa attacker clearing untested; Castle interior never tried

### Phase 6: Gehennom to Astral
**Goal**: Every stage after the Castle has a working contract, scripted or pilot, proven on staged starts, so that one game can go from the Valley to an offering on the Astral Plane
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: LATE-04, LATE-05, LATE-06, LATE-07, LATE-08
**Success Criteria** (what must be TRUE):
  1. Gehennom: staged starts at the Valley descend through the Gehennom mazes to the Vlad's Tower and Wizard's Tower levels at a reported staged pass rate (proof: `tool_games` job IDs)
  2. Quest: staged runs reach XL 14, complete the Quest and end holding the Bell of Opening at a reported pass rate (proof: job IDs)
  3. Towers: staged runs end holding the Candelabrum and the Book of the Dead at a reported pass rate (proof: job IDs)
  4. Invocation: staged runs holding the three items perform the ritual, enter the Sanctum and take the Amulet at a reported pass rate (proof: job IDs)
  5. Endgame: staged runs climb with the Amulet, pass the Elemental Planes and offer the Amulet on the Astral Plane. Every stage of this phase appears on the scoreboard (scripted or pilot kept) with its staged pass rate next to its natural arrival rate (proof: job IDs, scoreboard query)
**Plans**: TBD
**Owner gate**: reaching XL 14 by farming, or any other exploit, is proposed to the owner first
**Research**: every stage has no code yet; NetHack 5.0 hellfill levels and the monster table gap are unverified

### Phase 7: Clean Ascension
**Goal**: One fresh, clean game of NetHack 5.0 ascends, and the owner can verify and reproduce it
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: ASC-01, ASC-02, ASC-03
**Success Criteria** (what must be TRUE):
  1. The clean-run verifier checks a game (one process; no rewind, staged start or hand input; tagged commit; recorded seed and `lgen`; dumplog showing the ascension; pilot stages allowed only with every call recorded), and its tests show it rejecting each kind of tainted game (proof: verifier test run)
  2. Natural games on confirm seeds run with the kept performer per stage built in, and the unscreened funnel reports per-stage rates from start to ascended (proof: job IDs, funnel query)
  3. If dungeon screening is used, the selection rule is committed before the first attempt, and the rule commit predates every attempt job (proof: commit hash and job timestamps)
  4. One clean ascension on a final-range seed is recorded (seed, commit, dumplog) and passes the verifier, and replaying the seed at the tagged commit (with the pilot record if the pilot played) reproduces it (proof: attempt job ID, verifier output, replay job ID)
**Plans**: TBD
**Owner gate**: seed search beyond the approved `lgen` screening, and any exploit, is proposed to the owner first

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7. Phases 3 and 4 both depend only on Phase 2 and may run side by side.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Measurement and Proof Foundation | 16/16 | Complete    | 2026-11-14 |
| 2. Proven Change Loop | 0/TBD | Not started | - |
| 3. LLM Analyst and Pilot | 0/TBD | Not started | - |
| 4. Early Wall by System | 0/TBD | Not started | - |
| 5. Medusa and Castle Wall | 0/TBD | Not started | - |
| 6. Gehennom to Astral | 0/TBD | Not started | - |
| 7. Clean Ascension | 0/TBD | Not started | - |
