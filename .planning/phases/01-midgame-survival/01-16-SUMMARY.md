---
phase: 01-midgame-survival
plan: 16
subsystem: repository
tags: [branch-cleanup, surv-05, d-13]
requires: [01-15]
provides:
  - "PORTING.md ### Branch cleanup (D-13): six branches with SHA, verdict, interval and outcome"
  - "local tags archive/{threat-model,rejudge-threat-model,choke-points,rejudge-choke-points,flee-upstairs,rejudge-flee-upstairs}"
affects: [phase-02]
key-decisions:
  - "Owner chose archive-tags (2026-10-25): SHAs kept as local archive/ tags, branches deleted"
---

# Plan 01-16 Summary: branch cleanup

Owner answer at the checkpoint: **archive-tags**. All six dropped branches (threat-model, choke-points,
flee-upstairs and their rejudge/ copies) are tagged `archive/<name>` at their logged SHA and deleted; every tag
was checked against the ledger SHA. Three stale scratchpad worktrees from the previous session were pruned
first (two held rejudge branches). No remote exists; nothing was pushed. Phase 1 plans 16 of 16 done.
