---
quick_id: 261117-l4a
status: incomplete
date: 2026-11-17
commits:
  - 858fe1b3484c5fbee1e0547813699fa0c5854024  # bench side (main)
  - baa15c7363869df89dc929e9c3fd09a73055e738  # wip visit log (branch trigger-skip, gate pending)
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

## Open

- Refactor gate for the visit log: `bench.gate` refuses to run beside bench jobs; run it after jobs 20/21 and
  before the fresh baseline, amend `Gate: job N`, merge. Without it the fresh baseline has no visit logs and
  `trigger` experiments are refused (by design).
- Expected gain for 02-05: about 2% of baseline games reach the trigger (job 7: 186 of 9,600 end in the Mines while
  FIND_SOKOBAN; the trigger is wider, also counting visits that did not end there), plus the 10% audit: the
  candidate plays roughly 12-15% of seeds.
