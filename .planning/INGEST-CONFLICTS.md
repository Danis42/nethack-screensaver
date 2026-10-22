## Conflict Detection Report

Mode: new. Docs: 11 (9 SPEC, 2 DOC; 0 ADR, 0 PRD, 0 UNKNOWN). Precedence: ADR > SPEC > PRD > DOC,
with later-dated superseding decisions treated as evolution. Cycle detection: no cycles.

### BLOCKERS (0)

None. No ADRs exist in the set, so there are no locked decisions to contradict. No UNKNOWN
classifications. The ref graph (plans -> specs, ascension-ladder-design -> ROADMAP, STATUS -> ROADMAP)
is acyclic.

### WARNINGS (0)

None. No PRDs exist in the set, so there are no competing acceptance variants. No contradiction
without a clear successor was found.

### INFO (13)

[INFO] Auto-resolved: strategy default "random" (SPEC) superseded by "pilgrim only" (DOC, later)
  Note: docs/superpowers/specs/2026-10-18-secret-strategies-design.md and
  docs/superpowers/plans/2026-10-18-secret-strategies.md say the strategy is picked uniformly at random
  per game (config `strategy = "random"` default; plan `run_game(strategy=None)` -> `random.choice`). 
  docs/STATUS.md (2026-10-21, user directive "Ascension is the only priority") says every game plays the
  pilgrim route and the other plans sit behind `strategy = "random"`. The later directive wins; the code
  already has `Config.strategy = "pilgrim"` (nethack_screensaver/config.py). Both texts are kept in
  constraints.md with the supersession noted.

[INFO] Auto-resolved: "no Amulet/Quest/Castle/Gehennom logic" and "descend forever" (SPEC) superseded by roadmap sub-projects 2-8 (DOC, later)
  Note: docs/superpowers/specs/2026-10-18-secret-strategies-design.md declares those endings unreachable
  and out of scope, with pilgrim and daredevil ending in "descend forever". docs/ROADMAP.md (decided
  2026-10-20) makes a real ascension the main objective, with pilgrim and daredevil pursuing it for real
  and sub-projects 3-8 covering Medusa, Castle, Quest, Gehennom and the Planes. Treated as the project
  evolving its scope, not a contradiction. Sightseer and treasure keep escape goals in both.

[INFO] Auto-resolved: "no seeding patch" (screensaver SPEC) vs seeded games (seeded-bench SPEC, later)
  Note: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md lists the env wrapper as having
  "no seeding patch". docs/superpowers/specs/2026-10-21-seeded-bench-design.md adds `run_game(seed=None)`
  using `set_initial_seeds`. The later spec wins for bench use; the screensaver default (unseeded) is unchanged.

[INFO] Auto-resolved: unpaired verdicts and unseeded scheduling (bench-server SPEC) superseded by paired, seeded design (later SPEC)
  Note: docs/superpowers/specs/2026-10-20-bench-server-design.md (Newcombe interval on independent
  samples, bare `play` worker line, one game at a time to free workers) and its plan
  docs/superpowers/plans/2026-10-20-bench-server.md are refined by
  docs/superpowers/specs/2026-10-21-seeded-bench-design.md (paired Wald interval, `play <seed>`, lowest
  free seed per commit). Checkpoints (192/384/576/1152) and z values are unchanged. The later spec wins
  on the verdict formula, worker protocol and scheduling; rate-difference code in bench/stats.py remains for non-experiment use.

[INFO] Auto-resolved: dependency list differs between screensaver SPEC and plan
  Note: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md lists `nltk` among target runtime
  dependencies "(drop any that turn out unused after trimming)". docs/superpowers/plans/2026-10-16-nethack-screensaver.md
  Global Constraints exclude nltk (also torch, ray, matplotlib, seaborn, pandas, PIL, gym). The plan is the
  trimmed, concrete outcome of the SPEC's own drop-if-unused rule; the plan list is used.

[INFO] Auto-resolved: MCP tool signatures differ between bench-server SPEC and its plan
  Note: the spec lists `bench_import(source, url, limit=500)`, `bench_stop()` and no `bench_experiments`;
  the plan (and the shipped bench/mcp_server.py) has `bench_import(kind, url=None, limit=500)`,
  `bench_stop(job_id=None)` and an extra `bench_experiments()`. Plan and code agree, so the plan form is used.

[INFO] Note: ladder rung order is not strictly the median-turn order
  Note: docs/superpowers/specs/2026-10-21-ascension-ladder-design.md says the 17 rungs follow the median
  order of real ascensions, but its own yardstick shows Mines' End luckstone (rung 6, turn 10853) before
  Sokoban solved (rung 5, turn 12412). docs/ROADMAP.md and docs/STATUS.md use the same rung order, so the rung order is kept as written.

[INFO] Note: pilgrim acceptance figure vs measured baseline
  Note: docs/superpowers/specs/2026-10-18-secret-strategies-design.md acceptance 3 and the ladder spec's
  validation expect Mines in "about two thirds" of games; docs/STATUS.md reports 57% for the first
  576-game ladder baseline. Informational: the measured baseline is the current number.

[INFO] Note: two different watchdog values
  Note: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md uses a 60 s no-screen-change watchdog
  (`run_game` default); docs/superpowers/specs/2026-10-20-bench-server-design.md has bench workers call
  `run_game(watchdog_seconds=120)`. Different contexts (screensaver vs bench), kept as two separate values.

[INFO] Note: plan verification example uses an unsupported filter syntax
  Note: docs/superpowers/plans/2026-10-21-ascension-ladder.md Task 4 Step 5 shows
  `bench_games main where="end_reason LIKE 'exception%'"`; the bench filter language
  (docs/superpowers/specs/2026-10-20-bench-server-design.md) only has `=`, `>`, `<`, `~` joined by `,`.
  The equivalent is `end_reason~exception`. Not a design conflict.

[INFO] Note: reference handling in cycle detection
  Note: docs/ROADMAP.md lists the directories `docs/superpowers/specs/` and `docs/superpowers/plans/` as
  cross-refs. Directories were treated as non-edges (they are not doc nodes); expanding them would create
  a spurious ROADMAP <-> ascension-ladder-design cycle. docs/STATUS.md references to
  docs/ASCENSION-GUIDE.md, `autoascend/PORTING.md` and `handoff.txt` point outside the ingest set and are
  dangling external references, not cycles (per the orchestrator's instruction). Likewise bench-server-design
  refs (`scripts/benchmark.py`, `.mcp.json`, `nethack_screensaver/`) are code paths.

[INFO] Note: low-confidence SPEC classifications accepted via manifest
  Note: docs/superpowers/plans/2026-10-16-nethack-screensaver.md and docs/superpowers/plans/2026-10-20-bench-server.md
  were classified SPEC at low confidence (implementation plans, manifest override). They are not UNKNOWN,
  so they were extracted into constraints.md (their Global Constraints, Interfaces and Review Focus carry
  real contracts). All plans are implementation plans, not specs; the roadmapper should treat them as
  contract detail for already-built work.

[INFO] Note: no ADR or PRD content, so decisions.md and requirements.md are empty by design
  Note: all 11 docs are SPEC or DOC. Design "Decisions" tables remain in constraints.md as SPEC content;
  dated user directives (ROADMAP 2026-10-20, STATUS 2026-10-21) are in context.md. docs/STATUS.md states
  the project workflow is superpowers, "not GSD", which the downstream planner should keep in mind.
