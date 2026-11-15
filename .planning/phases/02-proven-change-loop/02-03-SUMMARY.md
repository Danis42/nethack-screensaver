---
phase: 02-proven-change-loop
plan: 03
status: complete
requirements: [SURV-01]
commits:
  - 8d365c5ccb3ef83334a3ed704d1b564a4a842c90  # triage draft
  - c7589925c028b30ce81e4f0fd16bb6bb3a15bcec  # owner-reviewed
  - 455224d5455733d91bb02d33ef139d98ce77b7fe  # replay script
  - 7bd119384f5428cd5820f60c0051372b68085cf8  # rule fixes from the replay check
  - 5da464b889cd7205d6e2e8d902d94dbf4c2f552f  # ranking and replay results
jobs: [7]
---

# 02-03 Summary: failure triage

- `bench/triage_groups.py`: 19 system groups, first match wins, recorded fields only; monster traits (speed,
  difficulty, group generation) from NetHack's own monster data, facts normal-speed-is-12 and
  group-generation-flags.
- `python -m bench.triage <ref>` ranks groups by expected next-stage gain and Dlvl 10 gain; owner approved the group
  list 2026-11-15 without changes.
- Baseline job 7 ranking: starvation and lost melee fights lead (about 590 expected next-stage arrivals each),
  then pack monsters (468). Full table in 02-TRIAGE.md.
- Replay check: 25 games, agree 19 of 25; four rule bugs fixed, groups unchanged.

Deviations:
- The triage CLI is `python -m bench.triage`, not `screens-bench triage` (plan check: bench/cli.py stays untouched).
- `scripts/ratchets.py tighten` no longer pins files created after the Phase 2 start (D-15 new-file cap).
