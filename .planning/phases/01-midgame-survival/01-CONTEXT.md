# Phase 1: Midgame Survival - Context

**Gathered:** 2026-10-22
**Status:** Ready for planning

<domain>
## Phase Boundary

The pilgrim bot dies measurably less often on Dlvl 4-12, so more games reach Minetown, Sokoban and
Mines' End (rungs 2-6). The phase first proves the seeded bench can see 1-3 point effects (seeded A/A
control, replay determinism) and stores a pilgrim-only baseline; then it attacks the four known
killers (starvation, resting to full HP, wand/ray users, ants and bees) and re-judges the three old
survival branches, one measured change at a time. Requirements: MEAS-01..03, SURV-01..06.

Not in this phase: descent past Mines' End / Big Room, finding downstairs (Phase 2), gear (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Working method
- **D-01:** GSD runs Phase 1 and the roadmap from here on (discuss -> plan-phase -> execute-phase;
  plans in `.planning/phases/01-midgame-survival/`). Superpowers specs/plans in `docs/superpowers/`
  stay as history; new work does not add to them.
- **D-02:** `.planning/STATE.md` is the single source of truth for project status. `docs/STATUS.md`
  and `handoff.txt` are replaced by a short pointer to `.planning/STATE.md`; the owner's "save" habit
  now means updating STATE.md. This is a task in this phase. `autoascend/PORTING.md` stays the log of
  bench numbers, verdicts and dropped ideas (unchanged project rule).

### Measurement gate (MEAS-01..03)
- **D-03:** Order inside the phase: seeded A/A control + replay check first, then the pilgrim-only
  baseline (seeds 0..575), then bot experiments.
- **D-04:** If the A/A control does not read "no measurable difference", or the same seed does not
  replay the same game (MEAS-03), all bot experiments stop until the bench is fixed (module-level
  caches such as `_PRIZES` in `autoascend/global_logic.py` and `STRATEGIES` in `autoascend/plans.py`,
  wall-clock effects). No "proceed with caution".

### Experiment discipline
- **D-05:** Stacked baselines: every merged `better` change gets a fresh pilgrim-only baseline of the
  new `main`, and the next experiment is judged against it.
- **D-06:** Strictly one experiment on the bench at a time (all 11 workers). Bench wait time goes to
  research (diagnosis, human-game studies, wiki).
- **D-07:** Killer order: starvation first; then Claude orders the rest (rest to full HP, wand/ray
  users, ants and bees, the three re-judged branches) by expected gain per bench hour, recording the
  reasoning.
- **D-08:** One cause per experiment, never a bundle — including when a diagnosis finds several
  causes of the same killer.

### Starvation (SURV-02)
- **D-09:** Diagnose before fixing: pull the starvation deaths from the pilgrim-only baseline and
  classify them (e.g. prayer still on cooldown, no food carried, corpses refused, stuck on a level,
  weak role early on Dlvl 2-4 vs long 6000+ turn games), then fix the biggest bucket first.
- **D-10:** The diagnosis always includes a comparison with human games from NLD-NAO
  (`/ssd2/nethackFiles/db/nld.db`): how surviving humans on Dlvl 4-12 handle food and prayer timing.
  If `/ssd2` is not mounted, that is a blocker to raise with the owner, not a step to skip.
- **D-11:** Cheesy fixes are allowed (risky-but-usually-safe corpses, aggressive prayer timing,
  sacrificing to recover prayer, etc.) — owner preference "anything goes".

### Old branches (SURV-05)
- **D-12:** Keep SURV-05: rebase `threat-model`, `flee-upstairs` and `choke-points` onto current
  `main` and judge each once on the seeded bench against the then-current stacked baseline.
- **D-13:** After judging: merge any `better` branch; for the rest record verdict, interval and SHA
  in `autoascend/PORTING.md`, then delete the branch. Delete `survival-tuning` now (it has no commits
  `main` lacks). — **Reversibility:** one-way — deleted branch refs are only recoverable from the
  reflog for a limited time; the SHA must be logged in PORTING.md before deletion.

### Done bar (SURV-06)
- **D-14:** The phase closes only when the final `main` gives a paired `better` verdict on `rung2`
  (Minetown+) against the pilgrim-only baseline with rungs 3-6 not worse. If the planned fixes are
  exhausted without it, the phase stays open: diagnose the next-biggest Dlvl 4-12 killer from the
  latest baseline and attack it. No lowering the bar, no moving on early.

### Claude's Discretion
- Games per side for each experiment (576 for long shots, 1152 for promising changes; early stop at
  192/384/576 when the verdict is already clear); the choice and reason are recorded per experiment.
- Order of the killers after starvation (D-07).
- How each fix is implemented (rest trigger, wand/ray tactics, ant/bee approach), within the rule
  that dropped ideas are not retried without a new approach.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase scope
- `.planning/PROJECT.md` — constraints (measurement rule, git local-only, quality gate), Context numbers
- `.planning/REQUIREMENTS.md` — MEAS-01..03, SURV-01..06 wording
- `.planning/ROADMAP.md` §Phase 1 — goal and success criteria
- `docs/ROADMAP.md` — sub-project 1 description and rung targets (owner's roadmap)

### Bench and measurement
- `docs/superpowers/specs/2026-10-21-seeded-bench-design.md` — seeded games, `play <seed>`, paired Wald verdict, A/A expectations
- `docs/superpowers/specs/2026-10-20-bench-server-design.md` — bench API, checkpoints 192/384/576/1152, metrics
- `docs/superpowers/specs/2026-10-21-ascension-ladder-design.md` — rung definitions and metrics `rung`, `rung1`..`rung17`

### Prior findings (do not repeat dropped work)
- `autoascend/PORTING.md` §"Hunger (2026-10-19)" — starvation diagnostics already done: most starving characters carry no food and live on prayer (566 of 643 prayers succeeded); death when a prayer comes too early; deaths split into weak roles on Dlvl 2-4 (turn 1300-4500) and long 6000+ turn games; "eat carried food at Weak" and "dive after 2500 turns" already merged
- `autoascend/PORTING.md` (soldier-ant study, A/A control 0c7acbc, threat-model / flee-upstairs / choke-points verdicts) — dropped ideas and their numbers

### Codebase map
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` — module layout, module-level caches, known fragile areas

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `autoascend/agent.py:56` `prayer_trouble()` — prays at Weak with no food; `is_safe_to_pray(limit)` (`agent.py:790`) uses 500 (HP) / 400 (hunger) turn limits; `last_prayer_turn` tracking.
- `autoascend/agent.py:1391` `eat_corpses_from_ground()`, `agent.py:1538` `eat_from_inventory()` — current eating logic.
- `autoascend/global_logic.py:230` — "out of food and prayer on cooldown" check; `global_logic.py:730` leaves Dlvl 1 when Hungry; `global_logic.py:873-884` corpse eating conditions.
- `autoascend/combat/monster_utils.py` `INSECTS` list; `autoascend/combat/fight_heur.py` wand path simulation (`simulate_wand_path`, `get_potential_wand_usages`).
- `bench/` MCP tools (`bench_baseline`, `bench_experiment`, `bench_results`, `bench_games`) for jobs, verdicts and per-game death causes.

### Established Patterns
- One change per git commit/branch; experiments run committed SHAs from worktrees; verdicts and dropped ideas logged in `autoascend/PORTING.md`.
- Finished, tested branches merge to `main` locally without asking; never push.
- Agent logic stays upstream except deliberate, measured changes; `uv run pytest -q -m ""` green before and after.

### Integration Points
- Bot behaviour changes land in `autoascend/agent.py` / `global_logic.py` / `combat/`.
- Determinism fixes (MEAS-03) touch module-level state in `autoascend/global_logic.py`, `autoascend/plans.py`, and the worker loop in `bench/worker.py` (which must import nothing from `bench`).

</code_context>

<specifics>
## Specific Ideas

- Human soldier-ant study (PORTING.md): survivors went upstairs 31% vs 6% and met the ant at full HP 100% vs 80% — the basis for SURV-01 (rest to full) and for re-judging `flee-upstairs`.
- Owner's play-style preference: an exciting deep run that dies beats a boring escape; cheesy tactics allowed.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-midgame-survival*
*Context gathered: 2026-10-22*
