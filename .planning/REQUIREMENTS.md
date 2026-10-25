# Requirements: screens

**Defined:** 2026-10-22
**Core Value:** The bot achieves a real ascension on the pilgrim route (the only priority).

**How a requirement is "done" (applies to every behaviour requirement below):** the change is
committed and merged to local `main`, `uv run pytest -q -m ""` is green, and a seeded paired
`screens-bench` verdict against the stored pilgrim-only baseline is recorded in
`autoascend/PORTING.md`. A verdict of `better` keeps the change; `no measurable difference` or
`worse` drops it and logs the attempt. Where a requirement says "addressed", an attempt dropped on
that evidence, with its interval written down, counts as addressed; the phase success criteria
still demand a measurable rung gain overall.

Source key: items marked *(derived)* are not stated in the source docs; they were derived from
the roadmap sub-project text, rung targets, yardstick, or codebase concerns, and are open to veto.

## v1 Requirements

### Measurement Foundation (MEAS)

- [x] **MEAS-01**: A seeded A/A control (the same commit on both sides of a `screens-bench` experiment) reads "no measurable difference" with a paired interval clearly narrower than the unseeded bench's ~3.5-point smallest detectable difference.
- [x] **MEAS-02**: A pilgrim-only baseline of current `main` (seeds 0..575) is stored on the bench, and its 17-rung table (games reaching each rung, median turn against the real-ascension yardstick) is written into `autoascend/PORTING.md`, with earlier mixed-strategy numbers marked not comparable.
- [x] **MEAS-03** *(derived)*: Playing the same seed twice on the same commit gives the same game; any source of non-replay the A/A control exposes (module-level caches such as `_PRIZES` in `autoascend/global_logic.py` and the shared `STRATEGIES` in `autoascend/plans.py`, wall-clock effects) is fixed or documented.

### Midgame Survival (SURV)

- [x] **SURV-01**: The bot rests to full HP before exploring on (human games: survivors met a soldier ant at full HP in 100% of cases vs 80% of the dead).
- [x] **SURV-02**: Starvation deaths (about 13% of games) are addressed.
- [x] **SURV-03**: Deaths to wand and ray users (about 8% of games) are addressed.
- [x] **SURV-04**: Deaths to soldier ants, fire ants, giant ants and killer bees (about 8% of games) are addressed with an approach not already dropped (doorway fighting, threat numbers, fleeing upstairs).
- [x] **SURV-05** *(derived)*: The unmerged survival branches `threat-model`, `flee-upstairs` and `choke-points` are each re-judged once on the seeded bench against the pilgrim-only baseline (their earlier "no measurable difference" came from a bench that could not see 1-3 point effects); any `better` result is merged, the rest stay dropped.
- [x] **SURV-06**: More games reach Minetown and beyond: the final `main` of this phase against the pilgrim-only baseline gives a paired `better` verdict on `rung2` (Minetown+), with rungs 3-6 not worse.

### Real Descent (DESC)

- [ ] **DESC-01**: The bot recognises Mines' End in both 8-level and 9-level Mines (fixing the `(MINES, 9)` TODO in `autoascend/global_logic.py`), and ladder rung 6 uses that exact detection instead of the 1000-turn waiting proxy.
- [ ] **DESC-02**: After the Mines and Sokoban tour the bot keeps descending the main dungeon, past the Oracle and the Big Room, instead of stalling or turning back.
- [ ] **DESC-03**: The bot reliably finds the downstairs: games that end stuck on a level they cannot leave (`unsticks`, watchdog end reasons) at Dlvl 5 and deeper become measurably fewer.
- [ ] **DESC-04**: The share of games reaching Dlvl 15+ (rung 7, baseline 2%) is measurably higher: paired `better` on `rung7` against the Phase 1 result.
- [ ] **DESC-05** *(derived)*: The bot recognises the Quest portal level and steps through the magic portal on purpose, so rung 8 is reached by design (baseline: one game, by accident).

### Gearing Up (GEAR)

- [ ] **GEAR-01** *(derived)*: Bench results record gear facts per game (final XL and AC, magic resistance, reflection, bag of holding, wands and rings held) and show them beside the real-ascender figures (magic resistance 100%, bag of holding 99%, reflection 83%, median XL 23, AC -38).
- [ ] **GEAR-02**: The bot wears the best armour it finds and buys protection where it can (for example priest donations in a temple), so median final AC is measurably better.
- [ ] **GEAR-03**: The bot obtains a source of magic resistance in a measurable share of games.
- [ ] **GEAR-04**: The bot obtains a source of reflection (for example the Sokoban prize amulet) in a measurable share of games.
- [ ] **GEAR-05**: The bot identifies and uses wands (teleportation, digging, death, sleep and similar) in fights and escapes, and wand use shows up in recorded games without new crash types.
- [ ] **GEAR-06**: The bot puts rings to use (wears helpful ones, avoids harmful or cursed ones), without new crash types in ring parsing.
- [ ] **GEAR-07**: Better gear carries the bot deeper: the Dlvl 15+ share (rung 7) improves over the Phase 2 result, and games reaching Dlvl 15+ carry what Medusa needs (reflection or a blindfold, and a way over water) in a measurable share.

### Late-Game Test Harness (STAGE)

- [ ] **STAGE-01** *(derived)*: A bench game can start at a chosen late-game situation (level and kit) so Medusa, the Castle, the Quest, Gehennom and the Planes can be exercised without playing 20+ levels first. Candidate approach: NLE's `wizard=True` option (present in NLE 1.3.0), to be validated against `NetHackChallenge` and seeding. Staged games are reported separately and never mixed into natural-play rung rates.

### Medusa's Level (MED)

- [ ] **MED-01**: Rung 9 is detected exactly (Medusa's level itself, not the "seen Medusa or a third water" proxy), and a "crossed Medusa" fact is recorded when the bot arrives on the level below.
- [ ] **MED-02**: The bot survives Medusa's gaze using reflection, a blindfold or towel, or another cheesy means.
- [ ] **MED-03**: The bot crosses the water to Medusa's island and takes the downstairs (levitation, water walking or another way).

### Castle and Wishes (CAST)

- [ ] **CAST-01**: Rung 10 is detected exactly, and the bot gets into the Castle past its moat and drawbridge.
- [ ] **CAST-02**: The bot takes the wand of wishing from the Castle's storeroom tower.
- [ ] **CAST-03**: The bot makes wishes from a defined list (for example gray dragon scale mail, speed boots, blessed scrolls of charging and genocide) and wears or uses the results; the existing wishing TODO in `autoascend/agent.py` is replaced.

### The Quest (QUEST)

- [ ] **QUEST-01**: The bot reaches XL 14, the level the Quest leader demands, in a measurable share of games (median XL and XL 14 rate recorded).
- [ ] **QUEST-02**: The bot is accepted by its Quest leader and fights down through the Quest levels to the nemesis, across the roles it is randomly dealt.
- [ ] **QUEST-03**: The bot kills the nemesis and carries the Bell of Opening (and the role artifact) back; the Bell is a recorded bench-visible fact (the yardstick's Bell median is turn 30475).

### Gehennom (GEH)

- [ ] **GEH-01**: The bot drops from the Castle into Gehennom (rung 11) and descends its mazes, finding the downstairs on levels that are mazes rather than rooms.
- [ ] **GEH-02**: The bot enters Vlad's Tower (rung 12) and takes the Candelabrum of Invocation.
- [ ] **GEH-03**: The bot takes the Book of the Dead from the Wizard's Tower (rung 13, exact "Book of the Dead in inventory" check).
- [ ] **GEH-04**: The bot finds the vibrating square, performs the invocation with Bell, Candelabrum and Book (rung 14), and takes the Amulet of Yendor from the Sanctum.

### Planes and Ascension (PLANE)

- [ ] **PLANE-01**: The bot climbs back out of Gehennom and the dungeon carrying the Amulet while the Wizard of Yendor harasses it.
- [ ] **PLANE-02**: The bot crosses the four Elemental Planes (rung 15); portals on the planar levels are modelled (replacing the placeholder level numbers and TODOs in `autoascend/agent.py`).
- [ ] **PLANE-03**: The bot reaches the Astral Plane (rung 16), finds its own god's altar and offers the Amulet; the game ends with "ascended" (rung 17).

## v2 Requirements

Acknowledged and tracked, not in the current roadmap. Pulled into a phase only if one blocks the ascension work.

### Ascension odds

- **ROLE-01** *(derived)*: Choose or tilt the character role toward the ones that ascend most easily (Valkyrie, Samurai, Barbarian, Monk). The seeded bench refuses a pinned role with a seed, so this needs seeds pre-filtered by the role they deal.

### Technical debt (from `.planning/codebase/CONCERNS.md`)

- **DEBT-01**: Bench server hardening: explicit `Origin` check and a per-start token for writes; import URLs limited to known hosts.
- **DEBT-02**: `prune` must not remove a worktree a live worker is using (touch mtime per game, or skip live worktrees).
- **DEBT-03**: Split `autoascend/agent.py` by concern; replace the bare `except:` in `autoascend/item/item_manager.py` and `assert 0` control flow with explicit errors; direct tests for `global_logic.py`, `character.py`, `exploration_logic.py`.
- **DEBT-04**: zsh hook must not overwrite an existing `TMOUT` or `TRAPALRM`; `games.jsonl` stats read incrementally instead of the whole file each game.
- **DEBT-05**: Single status document: make `handoff.txt` a generated copy of `docs/STATUS.md`, or drop it; add CI or lint configuration and a single logging policy.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Improving or measuring daredevil, sightseer, treasure | Ascension-only priority (2026-10-21); plans parked behind `strategy = "random"` |
| Pushing, PRs, remotes | Git is local only; finished tested branches merge to `main` locally |
| Release, packaging, distribution; shells other than zsh; shared-game daemon; other bots | Screensaver spec out-of-scope list |
| Resuming a game across idle sessions | NLE has no clean save/restore |
| Bench ttyrec recordings, remote bench access, a web framework | Bench spec out-of-scope list |
| ML / RL combat scoring (torch, ray) | AutoAscend is rule-based; removed in the port |
| Showing strategy during play, uneven strategy weighting, rungs on the screensaver | Earlier specs; not planned |
| Re-trying dropped ideas without a new approach | Elbereth resting, waiting for peacefuls, hidden-passage search, digging down, boulder pushing, doorway fighting, threat numbers, flee-upstairs were measured or reverted; SURV-05 is the single exception |
| Changing the default verdict metric away from `dlvl6` | Ladder spec calls it a later one-line change; each experiment names its own rung metric instead |

## Traceability

Which phases cover which requirements. Each requirement maps to exactly one phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEAS-01 | Phase 1 | Complete |
| MEAS-02 | Phase 1 | Complete |
| MEAS-03 | Phase 1 | Complete |
| SURV-01 | Phase 1 | Complete |
| SURV-02 | Phase 1 | Complete |
| SURV-03 | Phase 1 | Complete |
| SURV-04 | Phase 1 | Complete |
| SURV-05 | Phase 1 | Complete |
| SURV-06 | Phase 1 | Complete |
| DESC-01 | Phase 2 | Pending |
| DESC-02 | Phase 2 | Pending |
| DESC-03 | Phase 2 | Pending |
| DESC-04 | Phase 2 | Pending |
| DESC-05 | Phase 2 | Pending |
| GEAR-01 | Phase 3 | Pending |
| GEAR-02 | Phase 3 | Pending |
| GEAR-03 | Phase 3 | Pending |
| GEAR-04 | Phase 3 | Pending |
| GEAR-05 | Phase 3 | Pending |
| GEAR-06 | Phase 3 | Pending |
| GEAR-07 | Phase 3 | Pending |
| STAGE-01 | Phase 4 | Pending |
| MED-01 | Phase 4 | Pending |
| MED-02 | Phase 4 | Pending |
| MED-03 | Phase 4 | Pending |
| CAST-01 | Phase 5 | Pending |
| CAST-02 | Phase 5 | Pending |
| CAST-03 | Phase 5 | Pending |
| QUEST-01 | Phase 6 | Pending |
| QUEST-02 | Phase 6 | Pending |
| QUEST-03 | Phase 6 | Pending |
| GEH-01 | Phase 7 | Pending |
| GEH-02 | Phase 7 | Pending |
| GEH-03 | Phase 7 | Pending |
| GEH-04 | Phase 7 | Pending |
| PLANE-01 | Phase 8 | Pending |
| PLANE-02 | Phase 8 | Pending |
| PLANE-03 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-22*
*Last updated: 2026-10-22 after initial roadmap creation*
