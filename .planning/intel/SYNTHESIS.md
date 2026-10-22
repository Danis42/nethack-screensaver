# Synthesis Summary

Entry point for gsd-roadmapper. Regenerated 2026-10-22 from the manifest re-run (mode: new,
11 docs; docs/ASCENSION-GUIDE.md deliberately excluded). Overwrites the previous run's intel.

## Doc counts by type
- ADR: 0
- SPEC: 9 (5 design specs, 4 implementation plans; all manifest-typed; 2 plans at low confidence)
- PRD: 0
- DOC: 2 (docs/ROADMAP.md, docs/STATUS.md)
- UNKNOWN: 0

## Decisions locked
0. No ADRs in the set. See `decisions.md` for where decisions live instead.

## Requirements extracted
0 `REQ-*` entries (no PRDs). Goals and acceptance criteria inside SPECs are in `constraints.md` (type nfr).
Roadmap work items are in `context.md` ("Roadmap sub-projects", sub-projects 1-8 open, 0 done).

## Constraints: 27 entries
- by type: protocol 8, schema 5, api-contract 6, nfr 8
- Screensaver (S/P 2026-10-16): launcher protocol, runtime constraints, config schema, game log schema, module interfaces, error handling, testing, plan review focus
- Secret strategies (2026-10-18): strategy plans, milestone behaviour, result/reveal/config schema, interfaces, acceptance
- Bench server (2026-10-20): architecture, worker/scheduler protocol, metrics/verdict rules, JSON API, MCP tools, DB schema, importers, success/testing
- Ascension ladder (2026-10-21): 17-rung schema, components/interfaces, error handling/testing/validation
- Seeded bench (2026-10-21): game/worker seed protocol, scheduler and paired verdict, store/testing

## Context topics: 11
Project direction and priority; success ladder; roadmap sub-projects; current state; human game data;
yardstick (687 ascensions); bench server usage; done and kept; tried and dropped; working notes; SPEC out-of-scope lists.

## Conflicts
- 0 blockers
- 0 competing variants (warnings)
- 13 info (auto-resolved or noted): see `.planning/INGEST-CONFLICTS.md`

Key supersessions applied (later-dated / current-state wins): default strategy is pilgrim-only (not random);
Amulet/Quest/Castle/Gehennom now in scope via roadmap; seeded, paired bench experiments replace unpaired ones.

## Files
- `.planning/intel/decisions.md`
- `.planning/intel/requirements.md`
- `.planning/intel/constraints.md`
- `.planning/intel/context.md`
- `.planning/INGEST-CONFLICTS.md`

## Notes for downstream
- docs/STATUS.md says the project workflow is superpowers (brainstorm, spec, plan, build), not GSD; local git only (never push).
- References from STATUS.md to docs/ASCENSION-GUIDE.md are dangling external refs by design.
