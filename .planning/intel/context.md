# Context (DOC intel)

Topic-keyed notes from the two DOCs (docs/ROADMAP.md, docs/STATUS.md) plus context-only material
from the SPECs (out-of-scope lists). docs/STATUS.md (2026-10-21) and docs/ROADMAP.md describe the
current project state and priority and supersede older SPEC text where they evolve the same topic.
docs/ASCENSION-GUIDE.md is referenced by STATUS.md but was excluded from this ingest (external, dangling reference).

---

## Project direction and priority
- source: docs/ROADMAP.md ; docs/STATUS.md
- Roadmap: "Decided 2026-10-20: the main objective of the project is a real ascension. Pilgrim
  (ascension) and daredevil (ascension in disgrace) pursue it for real; sightseer and treasure keep
  their reachable escape goals."
- STATUS (2026-10-21): "Ascension is the only priority (user, 2026-10-21): every game plays the
  pilgrim route; the other plans are behind `strategy = "random"`; cheesy tactics are allowed."
- STATUS: "Your preference: an exciting deep run that dies beats a boring escape."
- STATUS: Version 0.2.0 is released; everything after is on local `main`, not yet released.
- STATUS workflow note: "Workflow: superpowers (brainstorm, spec, plan, then build), not GSD."
- STATUS: "Never push; merge finished, tested branches to `main` locally."
- ROADMAP "How we work": each sub-project gets its own spec, plan and build (superpowers); every
  change is measured on the bench server, one change per experiment.

## Success ladder
- source: docs/ROADMAP.md ; docs/STATUS.md
- Every game is scored by the highest of 17 rungs reached: Mines, Minetown, Oracle, Sokoban, Sokoban
  solved, Mines' End, Dlvl 15+, Quest, Medusa, Castle, Gehennom, Vlad's Tower, Wizard's Tower,
  invocation, Planes, Astral, ascended. Climbing a rung is progress; a real ascension is the last rung.
- Implemented in `autoascend/ladder.py`; `GameResult.ladder` / `rung`; bench metrics `rung`,
  `rung1`..`rung17` and a ladder table on the dashboard (details: constraints.md).

## Roadmap sub-projects
- source: docs/ROADMAP.md
- 0 Ascension ladder: record rungs, bench metrics, yardstick table. Measurement only. Done 2026-10-21 (baseline in `autoascend/PORTING.md`).
- 1 Midgame survival, Dlvl 4-12 (most games die on Dlvl 4-8). Targets rungs 2-6. Open.
- 2 Real descent past Mines' End and the Big Room; reliably finding downstairs. Rungs 6-8. Open.
- 3 Gearing up: wands, rings, armour, protection, reflection, magic resistance. Rungs 7-9. Open.
- 4 Medusa's level. Rung 9. Open.
- 5 Castle and wishes. Rung 10. Open.
- 6 Quest (XL 14, Bell). Rung 8. Open.
- 7 Gehennom: Vlad's, Wizard's Tower, invocation. Rungs 11-14. Open.
- 8 Elemental and Astral Planes. Rungs 15-17. Open.
- Specs live in `docs/superpowers/specs/`, plans in `docs/superpowers/plans/`, benchmark numbers in `autoascend/PORTING.md`.

## Current state (2026-10-21)
- source: docs/STATUS.md
- Sub-project 0 done (main `2653410`, 239 tests). First baseline, 576 games: Mines 57%, Minetown 29%,
  Oracle 22%, Sokoban 9%, Sokoban solved 5%, Mines' End 4%, Dlvl 15+ 2%, Quest 1 game, nothing higher.
  Median game: rung 1, Dlvl 5, 5258 turns.
- Later state: main `dbab398`.
- Sub-project 1, first idea dropped (2026-10-21): judging monsters by NetHack's real numbers did not
  raise Minetown+ in three variants (worse, then two "no difference"); code kept on unmerged branch
  `threat-model`; details in `autoascend/PORTING.md`. Noise between two identical 576-game halves is about 3.6 points.
- Control test showed the shared baseline came out high: earlier "worse"/"no difference" results are
  really "no difference".
- Flee-upstairs rule (from the human-game study): no measurable difference (branch `flee-upstairs`).
- Start next here (STATUS): make the bench sharper by seeding both sides with the same games (now
  specified in the seeded-bench design), then a pilgrim-only baseline, then the next survival rule
  (rest to full HP before exploring on, from the human data).

## Human game data
- source: docs/STATUS.md
- NLD-NAO part `aa` (39,210 alt.org games, 510 ascensions) unpacked at `/ssd2/nethackFiles/nld-nao-unzipped/`,
  index `/ssd2/nethackFiles/db/nld.db` (`nle.dataset`).
- Soldier-ant study: survivors went upstairs 31% vs 6%, met the ant at full HP (100% vs 80%), Elbereth no difference.

## Yardstick: 687 real ascensions (hardfought.org)
- source: docs/ROADMAP.md ; docs/STATUS.md
- 687 real ascensions in the bench database. Median turn of each step (131 NetHack 5.0 timelines): Mines
  1173, Minetown 3538, Sokoban 9022 (solved 12412), Mines' End luckstone 10853, Quest 22426, Medusa
  29317, Bell 30475, Gehennom 34155, Vlad 44189, invocation 49741, Astral 53518, ascended 53630.
- At the end: magic resistance 100%, bag of holding 99%, reflection 83%, median XL 23, AC -38; wands of
  teleportation 89%, death 83%, digging 64%.
- Our bot: median game about 4900 turns, ends on Dlvl 5; best games Dlvl 10-22.

## Bench server usage
- source: docs/STATUS.md
- `uv run screens-bench serve` -> http://localhost:8765 (job, experiment verdict, dashboard, history,
  ascenders). Plays only while a job runs; 11 workers with `nice`.
- Claude: MCP tools from `.mcp.json` (reconnect MCP once: `/mcp`), or the JSON API. Start an experiment,
  then run `uv run screens-bench wait <job>` in the background.
- Experiments judge one metric (default "reached Dlvl 6+") at 192/384/576/1152 games per side (99% early,
  95% at the end); stored games of a commit are reused. Commit first: only committed code can be measured.
- DB `~/.local/share/screens-bench/results.db` holds 576 games of `aa4b1cf` (current bot code), 1152 of
  `choke-points`, and the 687 reference ascensions. `scripts/benchmark.py` still works as a fallback.

## Done and kept (2026-10-21)
- source: docs/STATUS.md
- Crashes 9 -> 2 per 576 games: drop spare items when Overtaxed, stop refused armour, parse 80-character
  inventory lines and worn rings, empty containers, pit-edge items, no kicking with wounded legs, plus a
  safety net (after 100 steps without game time, search once; `unsticks` in results). Crash reports show the bot's call chain.
- Bench server with status page, MCP tools and the ascension import.

## Tried and dropped
- source: docs/STATUS.md
- Earlier: resting on Elbereth, waiting for peaceful monsters, smarter hidden-passage search, digging
  down, pushing boulders (git stashes / reverts).
- 2026-10-21: fighting packs of fast monsters (soldier ants, killer bees) from doorways and corridors: no
  measurable difference (branch `choke-points`). Ants + killer bees still kill about 8% of games.

## Working notes
- source: docs/STATUS.md
- One change per measurement; single 576-game runs mislead (286 vs 262 was noise).
- Killers to look at: wand/ray users (~8%), ants (~8%), starvation (~13%).

## SPEC out-of-scope lists (context only)
- source: docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md ; docs/superpowers/specs/2026-10-18-secret-strategies-design.md ; docs/superpowers/specs/2026-10-21-ascension-ladder-design.md
- Screensaver, "Out of scope (later)": smart pacing (fast-forward resting/searching/corridors, slow down for
  combat and new levels); resuming a game across idle sessions (NLE lacks clean save/restore); other bots
  (LLM, simple bot), shared-game daemon, shells other than zsh, packaging/distribution.
- Secret strategies, out of scope: any Amulet, Quest, Castle or Gehennom logic (superseded in direction by
  roadmap sub-projects 2-8); showing the strategy during play; weighting strategies unevenly.
- Ladder, not in sub-project 0: changing any strategy, fixing the bot's own Mines' End check, showing rungs
  on the screensaver, making a rung metric the default verdict.
- Bench server, out of scope: ttyrec recordings; remote access; a web framework. After the bench server the
  ascension brainstorm resumes (roadmap sub-projects 0-8).
