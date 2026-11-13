baseline_sha: e5b5a7f525bc51b8008f665173600aba80de466d
lgen: off
env_id: a8f58c2fda006264
window: 1000-10999
aa_window: 1000-2999
prereg_commit: 539b31eabc1b11c90f7f2b84cb5348a0acf1da63
baseline_job: 7
aa_job: 8
aa_result: pass
baseline_rows: total=10000 own=9600 reused=400

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

## Jobs

Baseline job 7 started, first game row at 2026-11-13 16:10:02, games_reused 400. A/A job 8 queued, not started. At about 30 games per minute the baseline needs about 5.4 h for its 9,600 own games and the A/A about 1.1 h after it. Plan 01-16 starts when both are done. After a reboot the owner restarts the server with `uv run screens-bench serve --resume` (Pitfall 10).

## Results (plan 01-16)

Baseline job 7 and A/A job 8 are done. Baseline job 7 holds 10,000 games of commit e5b5a7f525bc51b8008f665173600aba80de466d on dev seeds 1,000-10,999 with lgen off: 9,600 played by the job and 400 reused from pilot job 3. [query: SELECT COUNT(DISTINCT seed) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL => 10000] A/A job 8 replayed seeds 1,000-2,999 as replicate 1. [query: SELECT COUNT(*) FROM games WHERE job_id = 8 => 2000]

### A/A verdict: pass

Command, run verbatim from the pre-registration in 539b31eabc1b11c90f7f2b84cb5348a0acf1da63 (exit 0):

```
.venv/bin/python scripts/replay_check.py e5b5a7f525bc51b8008f665173600aba80de466d e5b5a7f525bc51b8008f665173600aba80de466d --rep-b 1 --lo 1000 --hi 3000 --lgen off --min 2000 --skip-both watchdog --json
```

```json
{"compared": 1999, "identical": 1999, "mismatched": 0, "mismatched_seeds": [], "skipped": {"watchdog": [2073]}, "common": 2000}
```

All 2,000 seeds are present on both replicates. 1,999 seeds were compared and all are identical. Seed 2073 ended with the watchdog on both replicates, so it is listed and not compared, as the definition says. No seed had a watchdog on only one replicate.

### Funnel

Command: `.venv/bin/python -m bench.cli funnel e5b5a7f525bc51b8008f665173600aba80de466d --lo 1000 --hi 11000 --lgen off`. It agrees with `curl -s 'http://127.0.0.1:8765/api/funnel?job=7'` (same n and rows).

```json
{"sha": "e5b5a7f525bc51b8008f665173600aba80de466d", "window": [1000, 11000], "lgen": "off", "env_id": null, "n": 10000, "excluded": {"no_ladder": 0}, "flagged": {"ladder_error": 0, "watchdog": 2, "exception": 74}, "rows": [{"key": "mines", "title": "Gnomish Mines", "order": 1, "hits": 6081, "n": 10000, "rate": 0.6081, "lo": 0.5984921916118726, "hi": 0.6176247879403871, "prev": null, "cond_hits": 6081, "cond_n": 10000, "cond_rate": 0.6081}, {"key": "minetown", "title": "Minetown", "order": 2, "hits": 2141, "n": 10000, "rate": 0.2141, "lo": 0.20617087503492845, "hi": 0.22224869523342441, "prev": "mines", "cond_hits": 2141, "cond_n": 6081, "cond_rate": 0.3520802499588883}, {"key": "oracle", "title": "Oracle", "order": 3, "hits": 4820, "n": 10000, "rate": 0.482, "lo": 0.47221532246884007, "hi": 0.4917985014725042, "prev": "minetown", "cond_hits": 1400, "cond_n": 2141, "cond_rate": 0.6539000467071462}, {"key": "sokoban", "title": "Sokoban", "order": 4, "hits": 2544, "n": 10000, "rate": 0.2544, "lo": 0.24595932604642828, "hi": 0.263029293953248, "prev": "oracle", "cond_hits": 2394, "cond_n": 4820, "cond_rate": 0.4966804979253112}, {"key": "sokoban_solved", "title": "Sokoban solved", "order": 5, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "sokoban", "cond_hits": 0, "cond_n": 2544, "cond_rate": 0.0}, {"key": "mines_end", "title": "Mines' End", "order": 6, "hits": 1163, "n": 10000, "rate": 0.1163, "lo": 0.11016348174910562, "hi": 0.1227311986005516, "prev": "sokoban_solved", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "dlvl15", "title": "Dlvl 15+", "order": 7, "hits": 608, "n": 10000, "rate": 0.0608, "lo": 0.05628292474217007, "hi": 0.06565437942663223, "prev": "mines_end", "cond_hits": 69, "cond_n": 1163, "cond_rate": 0.05932932072226999}, {"key": "quest_portal", "title": "Quest portal", "order": 8, "hits": 464, "n": 10000, "rate": 0.0464, "lo": 0.04244851437936254, "hi": 0.050699848942515245, "prev": "dlvl15", "cond_hits": 287, "cond_n": 608, "cond_rate": 0.4720394736842105}, {"key": "quest", "title": "Quest", "order": 9, "hits": 422, "n": 10000, "rate": 0.0422, "lo": 0.038432217996841815, "hi": 0.04631937091134967, "prev": "quest_portal", "cond_hits": 422, "cond_n": 464, "cond_rate": 0.9094827586206896}, {"key": "medusa", "title": "Medusa", "order": 10, "hits": 77, "n": 10000, "rate": 0.0077, "lo": 0.006165744043271591, "hi": 0.009612340752496585, "prev": "quest", "cond_hits": 29, "cond_n": 422, "cond_rate": 0.06872037914691943}, {"key": "castle", "title": "Castle", "order": 11, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "medusa", "cond_hits": 0, "cond_n": 77, "cond_rate": 0.0}, {"key": "gehennom", "title": "Gehennom", "order": 12, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "castle", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "vlad", "title": "Vlad's Tower", "order": 13, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "gehennom", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "wizard_tower", "title": "Wizard's Tower", "order": 14, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "vlad", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "invocation", "title": "Invocation", "order": 15, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "wizard_tower", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "planes", "title": "Elemental Planes", "order": 16, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "invocation", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "astral", "title": "Astral Plane", "order": 17, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "planes", "cond_hits": 0, "cond_n": 0, "cond_rate": null}, {"key": "ascended", "title": "Ascended", "order": 18, "hits": 0, "n": 10000, "rate": 0.0, "lo": 0.0, "hi": 0.00038399837067659573, "prev": "astral", "cond_hits": 0, "cond_n": 0, "cond_rate": null}]}
```

### Baseline of main (rechecked)

`git diff --stat e5b5a7f525bc51b8008f665173600aba80de466d main -- autoascend nethack_screensaver bench/worker.py bench/runner.py` printed nothing when these results were written (main at 9f2d97f738dd12e7c889d6f9c5e8a0663d8f8426).
