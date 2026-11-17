---
quick_id: 261117-l4a
status: complete
date: 2026-11-17
commits:
  - 858fe1b3484c5fbee1e0547813699fa0c5854024  # bench side (main)
  - b2b2bbe6d1c9341319b02e937aac7f37ec4db14d  # visit log (gate job 22, 100 of 100 identical)
---

# 261117-l4a Summary: skip seeds where a change cannot fire

## Done

- `bench/triggers.py` (main): `TRIGGERS` = {"mines_unwanted"}; `View` makes untriggered, unaudited candidate
  seeds count as concordant pairs with the baseline game standing in; audit = every untriggered seed with
  seed % 10 == 0 (plus any untriggered seed with a real candidate game); a divergence there fails the job.
  `check` refuses unknown triggers and baselines without visit logs. Scheduler / server / MCP take `trigger`.
  No trigger: pass-through, so jobs 19-21 judge the same. Ratchets: no pinned file grew.
- `nethack_screensaver/visits.py` (wip, branch `trigger-skip`): visit log in `snapshots["visits"]`. Seed 1003
  plays as on main (2,289 turns, killed by a gnome king).
- Tests: 913 passed, 6 skipped on the branch (`tests/test_bench_triggers.py`, `tests/test_visits.py`).

## Gate and merge

- Gate job 22: pass, 100 of 100 seeds identical. Merged to main as b2b2bbe6d1c9341319b02e937aac7f37ec4db14d before
  the fresh baseline (job 23), whose games carry the visit log.
- Gain for 02-05, corrected: the earlier estimate (about 2%) counted games that END in the Mines. Measured on the
  first 634 Monk games of job 23, the trigger fires in 282 (44.5%), mostly on the way back from Minetown under
  FIND_SOKOBAN. With the 10% audit the candidate plays about half the seeds: roughly 2x, not the 7x first hoped.
