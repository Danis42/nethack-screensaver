baseline_sha: e5b5a7f525bc51b8008f665173600aba80de466d
lgen: off
env_id: a8f58c2fda006264
window: 1000-10999
aa_window: 1000-2999

# Natural baseline and A/A: pre-registration (MEAS-05, D-05, D-06, D-17, D-23)

Written and committed before the baseline and A/A jobs exist.

## What runs

- Baseline: commit A (`e5b5a7f525bc51b8008f665173600aba80de466d`, the A side of the lgen pilot; it holds all Phase 1 bot code), 10,000 games on dev seeds 1,000-10,999 (D-05, D-17), lgen `off` (decision keep-lgen-off in 01-LGEN-PILOT.md, pilot jobs 3/4/5/6), replicate 0.
- A/A: the same commit, mode and env on the 2,000-seed subset 1,000-2,999, replicate 1 (D-06). It is queued behind the baseline.

## Keying (D-23)

Games stay keyed by commit sha. Phase 2 experiments name `baseline_sha` above as their baseline explicitly (Pitfall 6). Keying by bot tree hash is a deferred idea, not built.

## Baseline of main

`git diff --stat e5b5a7f525bc51b8008f665173600aba80de466d main -- autoascend nethack_screensaver bench/worker.py bench/runner.py` printed nothing at pre-registration (main at 14493a5b56cda92bb0ecb9eb3bcff3356f0d5217): the commits after A touch only bench policy, scripts and docs, so the baseline of commit A is the baseline of main's bot.

## Reuse

The 400 commit-A games of pilot job 3 (seeds 1,000-1,399, lgen off, env a8f58c2fda006264, replicate 0) are already stored under the baseline's key and are reused by the baseline job, so it plays 9,600 games itself. Results are reported as the total, the job's own rows and games_reused.

## A/A identity definition (fixed; not changed after the A/A runs)

Every seed of 1,000-2,999 is compared, replicate 1 against replicate 0, on the replay_check FIELDS. A seed whose end_reason is watchdog on both replicates is listed and counted, not compared. A watchdog on only one replicate is a mismatch. The A/A passes if and only if every compared seed is identical and all 2,000 seeds are present on both sides. Any mismatch is a determinism bug to investigate.

Exact command (run by plan 01-16):

```
.venv/bin/python scripts/replay_check.py e5b5a7f525bc51b8008f665173600aba80de466d e5b5a7f525bc51b8008f665173600aba80de466d --rep-b 1 --lo 1000 --hi 3000 --lgen off --min 2000 --skip-both watchdog --json
```
