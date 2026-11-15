# Phase 2: Proven Change Loop - Context

**Gathered:** 2026-11-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The full change loop works end to end on real changes. Evidence picks the fix (failure triage). Refactors are proven bit-identical (refactor gate). Behaviour changes are proven by a paired experiment. Commits are labelled and ratchets keep the code from getting worse. Two real changes show the loop: the first-ascension character choice and the Mines branch staircase fix.

Requirements: CODE-01, CODE-02, CODE-04, SURV-01, SURV-04, SURV-06. Splitting `agent.py` / `global_logic.py` (CODE-03) is not in this phase.

</domain>

<decisions>
## Implementation Decisions

### Order of work
- **D-01:** **Character first, then the Mines fix.** The race changes the plan (`plan_for`: dwarves go Mines first; humans, elves and orcs go Sokoban first), so the Mines fix is built and measured on the final `CHARACTER`. A fresh natural baseline at the chosen character comes before the Mines experiment. — **Reversibility:** costly — every later experiment and the Phase 2+ baselines are keyed to the chosen character; changing it means new baselines.

### Character choice (SURV-06)
- **D-02:** Written research (5.0 source, wiki, real 5.0 ascension dumplogs) shortlists **2-3 finalists** from the strong roles and their races (`ROLE_TIERS["strong"]`: bar, sam, val, mon). The bench A/B compares the finalists against today's `val-hum-fem-neu`.
- **D-03:** Winner metric: **reaching Dlvl 10** (`dlvl10`, 38.76% in baseline job 7). The MDE is declared before the run (MEAS-06 rule). Each candidate plays with its own `plan_for` plan; the comparison is character plus its plan as one package.
- **D-04:** The winner sits in one `CHARACTER` constant (`nethack_screensaver/game.py:40` today).

### Mines staircase behaviour (SURV-04)
- **D-05 (superseded 2026-11-15):** ~~The bot tells the Mines branch staircase from the main downstairs.~~ Not possible in 5.0: branch stairs look ordinary until used ([fact:branch-stairs-shown-only-after-use]); the owner chose D-06/D-07 without it. Original note: Today `autoascend/glyph/nh5.py:17` maps `S_brdnstair` onto `S_dnstair`, so the two look the same.
- **D-06:** **Follow the plan:** on the branch level, take the Mines stairs only when the current milestone wants the Mines; otherwise take the main-dungeon stairs.
- **D-07:** **On a Mines level the plan does not want** (trap hole, arrived before the stairs were known, etc.): **go back up at once.** Evidence: `.planning/research/MINES-ENTRY-NH5.md`, where 17 of 50 accidental arrivals died on that first visit (median stay 1,212 turns).
- **D-08:** **Success metric fits the behaviour, declared beforehand.** Owner accepts that ROADMAP success criterion 4 ("share reaching the Mines rises") may not fit a follow-the-plan change. The experiment pre-registers the funnel stage and metric it should move (e.g. reaching Sokoban, or dlvl10), then a paired test on dev seeds and again on confirm seeds (with a `gate` field, Phase 1 D-22). ROADMAP criterion 4 wording is updated to match when planned.

### Failure triage (SURV-01)
- **D-09:** Scope: **every game ending**, not only deaths. That covers the 9,364 deaths in job 7 plus panics (71 "Cyclic Panic"), aborts, watchdog endings and stage stalls (e.g. all 2,256 Sokoban drops are `sokoban_unsolvable`).
- **D-10:** Method: classify all games from **recorded data** (`end_reason`, `last_messages`, HP/max HP, hunger, XL, `events`, `stage`, `milestone`, depth, `stuck_reports`). Then **replay a sample from each top group** to just before the end, to check the label. No LLM in this step.
- **D-11:** Cause groups: **Claude drafts the system-level group list and rules from the data; the owner reviews it once** before it ranks anything. Groups name systems (e.g. fights it should flee, food, stuck, bot bug), not single monsters. The ranking is by expected funnel gain, reproducible by one command on the baseline job.

### Refactor gate (CODE-01)
- **D-12:** Gate seed set: **100 fixed seeds**, full games (~5 min on 10 slots). It compares frame-hash traces and reports the first divergent seed and turn.
- **D-13:** Runs **on demand** as a bench job. A refactor commit counts only with a passing gate job ID. No per-commit automatic run.

### Commit labels and ratchets (CODE-02, CODE-04)
- **D-14:** Every commit from Phase 2 on carries `Kind: refactor` or `Kind: behavior`. Behaviour commits name their funnel stage, metric and experiment job. Enforced by a **git commit-msg hook** that rejects unlabelled commits, **plus a test** that checks the log from the Phase 2 start commit on.
- **D-15:** File size ratchet: **no file may grow.** Today's line counts are the limits and may only go down (`agent.py` 2,142, `global_logic.py` 1,382). New files get a fixed cap (around 600 lines; Claude may tune it). Other ratchets per CODE-04: no new bare `except` (one exists today, `autoascend/item/item_manager.py`), no new imports of agent internals.

### Prohibitions carried from the Phase 1 UAT (owner, 2026-11-14)
- **D-16:** Claim checking: no online LLM, network or paid API; a local LLM is allowed. Prohibitions on source-quote tags, final-seed surfaces, dungeon screening and archive import were dropped as prohibitions; their code guards stay as tooling.

### Claude's Discretion
- Which 100 seeds form the gate set (fixed, documented, from the reserved tool block or dev range).
- Frame-hash trace format and storage.
- Exact new-file size cap.
- How the triage tool presents its ranking (CLI, dashboard, MCP).
- Sample size per triage group for the replay check.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 2: goal and success criteria (criterion 4 to be reworded per D-08)
- `.planning/REQUIREMENTS.md`: CODE-01, CODE-02, CODE-04, SURV-01, SURV-04, SURV-06
- `.planning/PROJECT.md`: core value, constraints (determinism, no extra cost, exploits need approval)

### Prior phase decisions and measurement rules
- `.planning/phases/01-measurement-and-proof-foundation/01-CONTEXT.md`: D-05..D-08 seeds and resume, D-17 tool seeds, D-22 confirm gate
- `.planning/phases/01-measurement-and-proof-foundation/01-BASELINE.md`: baseline job 7 funnel
- `.planning/phases/01-measurement-and-proof-foundation/01-SOKOBAN-CAUSE.md`: Sokoban zero explained (feeds triage)
- `.planning/phases/01-measurement-and-proof-foundation/01-UAT.md`: owner prohibition amendments

### Mines and character research
- `.planning/research/MINES-ENTRY-NH5.md`: accidental Mines arrivals, first-visit deaths, AC vs XL evidence
- `.planning/research/ASCENSION-PLAN-NH5.md`, `.planning/research/ASCENSION-ROUTE-AUDIT.md`: route context for the character choice
- `.planning/research/SURVIVAL-NH5.md`, `.planning/research/FOOD-NH5.md`: system causes for triage groups

### Code
- `autoascend/glyph/nh5.py`: branch-stair glyph mapping (line 17)
- `autoascend/plans.py`: `STRATEGIES`, `SOKOBAN_FIRST_PILGRIM`, `plan_for`, `ROLE_TIERS`
- `nethack_screensaver/game.py`: `CHARACTER` (line 40), `run_game`, `GameResult`
- `bench/metrics.py`, `bench/funnel.py`, `bench/sequential.py`, `bench/power.py`: metrics and paired judging
- `scripts/play_compare.py`, `scripts/replay_check.py`: seed-by-seed comparison, base for the refactor gate
- `scripts/rewind.py`: replay to a turn, base for the triage sample replays
- `facts/FACTS.toml`, `scripts/facts.py`: fact ledger; new NetHack facts get ledger entries

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/play_compare.py`: plays the same seeds under two trees and compares per seed. The refactor gate extends it from result fields to frame-hash traces.
- `scripts/replay_check.py`: A/A identity on stored rows; has the pre-registration pattern.
- `bench/metrics.py` (`killer`, `ended_stuck`, `Metric`, `evaluate`): starting points for triage features.
- Recorded per-game JSON (`games.json`): `end_reason`, `last_messages`, `hp_at_end`, `hunger_at_end`, `xp_level`, `events`, `stage`, `milestone`, `stuck_reports`, `snapshots`. That's enough to classify without replays.
- Bench experiment API (`start_experiment`, MDE required, sequential judging): runs the character A/B and the Mines experiment.

### Established Patterns
- Pure logic modules without game access (`autoascend/ladder.py`, `castle.py`) are the pattern for new rule code (e.g. branch-stair choice).
- Facts cited as `# fact:<id>`; pytest fails on dangling IDs.
- Claims need a job ID, full commit hash or query (Stop hook).

### Integration Points
- Branch-stair recognition: `autoascend/glyph/nh5.py` mapping, then stair choice in `global_logic.py` milestone handling (`FIND_SOKOBAN`, `FIND_GNOMISH_MINES`).
- Commit-msg hook: `.git/hooks/` has no active hooks today; ship it as a tracked script plus an install step.
- Ratchet tests: `tests/` via pytest, default suite.

</code_context>

<specifics>
## Specific Ideas

- Baseline job 7 top killers: white unicorn 264, mumak 253, soldier ant 220, leocrotta 197, Woodland-elf 172, starvation 156. Triage should turn these into system groups.
- Owner works in plain terms: explain decisions without jargon and show the proof (job IDs).

</specifics>

<deferred>
## Deferred Ideas

- Splitting `agent.py` / `global_logic.py` (CODE-03): later phase, guarded by the gate built here.
- Changing the route (e.g. Mines first for every race): only if triage or the character research points to it.

</deferred>

---

*Phase: 02-proven-change-loop*
*Context gathered: 2026-11-14*
