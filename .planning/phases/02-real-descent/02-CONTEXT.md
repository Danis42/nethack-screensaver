# Phase 2: Real Descent - Context

**Gathered:** 2026-10-25 (written by Claude under the owner's standing delegation for ascension work:
"proceed autonomously - spec, plan, build, measure"; no discuss-phase session)
**Status:** Ready for planning

<domain>
## Phase Boundary

The bot completes the Mines, goes back up and keeps descending the main dungeon past the Oracle and the
Big Room, reliably finds downstairs, and enters the Quest portal on purpose (rungs 6-8). Requirements:
DESC-01..05.

Not in this phase: gear (wands, armour, reflection, MR: Phase 3), Medusa (Phase 4), staged starts
(STAGE-01). Survival killers from Phase 1 (starvation, ants) are only attacked here when the stuck-level
diagnosis shows they are caused by being stuck.

</domain>

<decisions>
## Implementation Decisions

### Working method (carried over from Phase 1, still binding)
- **D-01:** The Phase 1 experiment protocol applies unchanged
  (`.planning/phases/01-midgame-survival/01-EXPERIMENT-PROTOCOL.md`) with the Phase 2 names in
  `02-EXPERIMENT-PROTOCOL.md`: one cause per experiment, pre-registered primary metric, paired verdict,
  keep only on `better`, stacked baselines, one job on the bench at a time, bench waits go to research.
- **D-02:** `.planning/STATE.md` stays the status source; `autoascend/PORTING.md` gets a
  `## Phase 2: real descent` section for baselines, diagnoses, experiments and the phase result.

### Measurement first
- **D-03:** Order: measurement changes (exact Mines' End rung, stuck-level and watchdog context in every
  result) -> Phase 2 baseline `p2-baseline` -> experiments -> done bar. Measurement changes must not change
  what the bot does: `replay_check` against `p1-final` must show 0 mismatches on every field both sides
  record except `ladder` / `rung` (rung 6 is redefined) and the new fields.
- **D-04:** The ladder (a measuring instrument) may read the game's true dungeon layout from NetHack's
  memory (`dungeons[]`, `dungeon_topology` in the loaded libnethack): Mines' End is "on the last Mines
  level", the Quest portal level is known exactly. The **bot never reads memory**: everything it decides
  comes from the screen, as before. If the memory read fails, the ladder falls back to the old proxy and
  counts `ladder_truth_error`; it never ends a game.
- **D-05:** The Phase 2 numbers come from `p2-baseline` (2304 seeds), not from the ROADMAP text: the
  ROADMAP's "rung7 baseline 2%" and "single accidental Quest game" are from the mixed-strategy bench; on
  `p1-final` rung 7 is 9.1% (210 of 2304) and 20 games entered the Quest.

### Fair play and cheese
- **D-06:** Cheesy tactics stay allowed (owner, "anything goes"): reading unknown scrolls when stuck,
  kicking, forcing locks, jumping into holes and trap doors on purpose, praying for a way out are fair game.
  Not allowed: reading memory or files to decide moves (D-04), wizard mode, save scumming.
- **D-07:** Dropped ideas are not retried without a new approach (PROJECT.md Out of Scope): "smarter
  hidden-passage search" and "digging down" were dropped before, and Phase 1 experiment 2 (far-side wall
  search bonus) was dropped. A stuck-level tactic must name what is new about it.

### Done bar
- **D-08:** The phase closes only when the final `main` against `p2-baseline` gives: paired `better` on
  `rung7` (DESC-04); paired `better` (fewer) on the stuck metric defined in plan 02-03 (DESC-03); rung 8
  reached in more games, paired not worse and the count higher, with one recorded game showing a
  deliberate portal entry (DESC-05); rungs 2-6 not worse; DESC-01 shown on one 8-level and one 9-level
  Mines game. If not met, the phase stays open and the next stuck cause is attacked (as Phase 1 D-14).

### Claude's Discretion
- Order of experiments after the diagnosis, by expected gain per bench hour; reasons recorded.
- Thresholds of the tactic-choice rules, fixed in each plan before its numbers are read.
- How each change is implemented.

</decisions>

<specifics>
## Specific Ideas

- Owner idea (2026-10-25, Phase 1 UAT): keep a stock of non-perishable food. Starvation is 26% of games;
  it becomes a Phase 2 experiment only if the stuck diagnosis shows stuck-level starvation is the biggest
  stuck outcome, otherwise it stays a STATE.md todo for a survival gap-closure.

</specifics>

<deferred>
## Deferred Ideas

- Food-stock experiment (see Specific Ideas) unless the diagnosis promotes it.
- Watchdog hangs deep in the dungeon are diagnosed (stack in the result) here; fixing them is in scope
  only where the stack points at descent code, otherwise it is recorded for Phase 3+.

</deferred>
