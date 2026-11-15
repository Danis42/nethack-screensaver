# Refactor gate proof (plan 02-02, CODE-01, ROADMAP Phase 2 criterion 1)

refactor_gate_job: 9
negative_gate_job: 11
refactor_commit: 536089e87fe35ef4097af477318bdc38995565ad

Command: `uv run python -m bench.gate <candidate> --baseline <baseline>`; seeds 900-999 (tool block), frame-hash
trace per step (`bench/frame_trace.py`), rows in `tool_games`.

## Pure refactor passes (job 9)

Commit 536089e87fe35ef4097af477318bdc38995565ad moves `dive_stairs` from `autoascend/global_logic.py` into
`autoascend/stairs.py`. Gate job 9 ran on the same tree (candidate 73d62df01311f7db4c0df9eb0f56727aeabc1c8c, the
pre-amend commit) against main at the time: verdict pass, 100 of 100 seeds identical, none skipped, 440 s.
[query: SELECT json_extract(result,'$.verdict'), json_extract(result,'$.identical') FROM jobs WHERE id=9 => pass|100]

## Deliberate change fails (job 11)

Commit d2f4941fc4b09be586bf7e913ed747d6cd8d1a81 (branch `gate-negative`, never merged) makes the bot leave Dlvl 1
at XL 1 instead of at XL 8 or when hungry. Gate job 11 against 536089e87fe35ef4097af477318bdc38995565ad (baseline
traces reused from job 10): verdict fail, 99 of 100 seeds differ (seed 941 identical), first divergence seed 900,
step 407, turn 271 on the baseline vs 272 on the candidate.
[query: SELECT json_extract(result,'$.verdict'), json_extract(result,'$.first_divergence.seed') FROM jobs WHERE id=11 => fail|900]

## A change that never fires passes (job 10)

The first negative try, commit f88235cbc190e5c96776584f601778fb826656bb (leave Dlvl 1 at XL 7 instead of 8), passed
in gate job 10: in all 100 gate games the bot left Dlvl 1 hungry before reaching XL 7, so play really was
identical. The gate compares play, not code.
