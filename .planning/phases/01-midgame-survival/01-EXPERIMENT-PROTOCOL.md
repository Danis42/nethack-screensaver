# Phase 1 Experiment Protocol (seeded paired bench)

Shared, binding procedure for every Phase 1 plan that submits a `screens-bench` job
(plans 01-05 .. 01-15 and any gap-closure plan). It turns CONTEXT decisions D-03..D-08 and
RESEARCH Patterns 1-2 / Pitfalls 1-7 into steps. Plans reference it with
`@.planning/phases/01-midgame-survival/01-EXPERIMENT-PROTOCOL.md`; where a plan says
"run the experiment protocol", every numbered step below applies.

## 1. Fixed names

| Name | Kind | Meaning | Created by |
|------|------|---------|------------|
| `p1-aa-base`, `p1-aa-twin` | local tags | A/A control #1: measurement code and its docs-only twin | 01-05 |
| `p1-valk-base`, `p1-valk-twin` | local tags | A/A control after the Valkyrie-only switch (owner, 2026-10-23); measurement code for everything after it | 01-06 |
| `p1-aa2-base`, `p1-aa2-twin` | local tags | A/A control #2, only if `lgen` is adopted | 01-06 |
| `p1-baseline` | local tag | MEAS-02 pilgrim-only baseline code SHA; never moved after 01-07 | 01-07 |
| `p1-final` | local tag | Code SHA of `main` judged for SURV-06 | 01-15 |
| `calib/agent-seed-1`, `calib/lgen`, `calib/lgen-agent-seed-1` | branches | Bench calibration (never merged except `calib/lgen` when adopted) | 01-06 |
| `exp/starvation-1`, `exp/starvation-2`, `exp/rest-to-full`, `exp/ants-bees`, `exp/zappers` | branches | One bot change each | 01-08 .. 01-11 |
| `rejudge/threat-model`, `rejudge/choke-points`, `rejudge/flee-upstairs` | branches | Old branches rebased onto `main` (SURV-05), one plan each | 01-12, 01-13, 01-14 |
| `exp/<killer>-<n>` | branches | Gap-closure experiments (D-14 loop) | later plans |

Tags and branches are local refs. Git is local only: never push, never add a remote, never open
a PR. Experiment branches are never deleted by this phase (deleting an unmerged branch is a
one-way door; only D-13's four old branches are deleted, behind the 01-16 checkpoint).

**Behaviour paths:** `autoascend nethack_screensaver pyproject.toml uv.lock` decide what a game
does. Two SHAs are *code-identical* when
`git diff --quiet A B -- autoascend nethack_screensaver pyproject.toml uv.lock` exits 0.
Stored games are keyed by SHA, so baselines are always named by an explicit code SHA (or one of
the tags above), never by `main` (a docs commit on `main` creates a SHA with zero games).

**Ledger lines in `autoascend/PORTING.md`** (section `## Phase 1: seeded pilgrim-only bench`):
- `A/A control: passed for \`<40-hex sha>\`` - written only when the D-04 gate passes (01-05, 01-06).
- `Bench resolution: ...` - written by 01-06.
- `Pilgrim-only baseline: \`<40-hex sha>\`` - written by 01-07.
- `Current baseline: \`<40-hex sha>\`` - exactly one such line; the stacked baseline (D-05).
  Only 01-07 and a `kept` experiment change it.

## 2. Standing rules

- **D-04 gate.** No bot experiment unless `autoascend/PORTING.md` contains
  `A/A control: passed for \`<sha of p1-baseline>\``. A failed A/A or a non-replaying seed stops
  all bot experiments until fixed. No "proceed with caution".
- **D-06.** One job on the bench at a time, all 11 workers. Bench wait time goes to research
  (diagnosis, NLD-NAO studies, wiki), not to heavy CPU: no `pytest -m slow`, no local
  `scripts/benchmark.py` runs while a job is running.
- **D-08.** One cause per experiment, never a bundle, even when a diagnosis finds several causes.
- **Dropped ideas** are not retried without a new approach: Elbereth resting, waiting for
  peacefuls, hidden-passage search, digging down, boulder pushing, doorway fighting
  (`choke-points`), threat numbers (`threat-model`), fleeing upstairs (`flee-upstairs`).
  SURV-05's single re-judgement of the three branches is the only exception.
- **D-11.** Cheesy tactics are allowed.
- **Primary checkout only.** Bench plans run in the primary checkout (the first line of
  `git worktree list`), not in a linked executor worktree:
  `test "$(git rev-parse --git-dir)" = "$(git rev-parse --git-common-dir)"` must succeed.
  The bench server spawns workers from this checkout's `bench/worker.py` and runs its own
  `bench/` code from here.
- **Main stays checked out while a job runs.** Build and commit a candidate on its branch only
  while the bench is idle, then `git switch main` before submitting. While a job runs: no branch
  switch in the primary checkout, no commit that touches `bench/`.

## 3. Steps for one experiment

1. **Idle check.** `curl -s http://127.0.0.1:8765/api/status` shows `"job": null` and the MCP tool
   `bench_experiments` lists no `queued`/`running` job.
2. **Branch.** `git switch -c exp/<name> main`. Implement exactly one change. Register any new
   counter name in `StatsLogger._values` (`autoascend/stats_logger.py`) and log it where the change
   fires (`self.stats_logger.log_event(...)` or `.add(name, n)`); non-zero counters reach every
   bench result through `GameResult.events` (plan 01-01). Add unit tests with `SimpleNamespace`
   fakes (pattern: `tests/test_fight_heur.py`).
3. **Gate.** `uv run pytest -q -m ""` exits 0.
4. **Smoke (bench idle only).**
   `uv run python scripts/benchmark.py --seeds 0-21 -j 11 --field events.<counter>` prints
   `events.<counter>>0: k of 22 games` with k >= 1. If k is 0, rerun with the seeds of baseline
   games that died of the targeted cause
   (`uv run python scripts/seeded_report.py deaths <current baseline sha> --killer <pattern>`).
   A game ending in `exception:` is acceptable only if the current baseline's stored game for
   the same seed ends in the same exception type
   (`uv run python scripts/seeded_report.py deaths <current baseline sha> --seeds 22 --killer exception`).
5. **Commit and return.** Commit on the branch (`experiment(<area>): <change>`), then
   `git switch main`.
6. **Pre-register (docs commit on `main`, before submitting).** Append the experiment entry
   (template in section 5) with `Verdict: pending`, naming:
   - **Primary metric.** `rung2` by default. Exception: if at least 60% of the targeted deaths in
     the current baseline happened in games whose `rung` was already >= 2, use the lowest N in
     3..6 such that fewer than half of those games had `rung` >= N. State the numbers.
   - **Games per side.** Diagnosis-backed changes run to the last checkpoint (the scheduler ends
     earlier by itself when the 99% interval excludes zero). A change recorded as a *long shot*
     is stopped with `bench_stop` if its 576 checkpoint is `open` with a negative difference, and
     logged as `stopped at 576 (open, negative)`. SURV-05 re-judgements always run to the end.
   - **Mechanism metrics** (evidence only, never the keep rule): e.g. `starved`, `ants`, `rays`,
     `died`, and the change's own counter.
7. **Submit.** MCP `bench_experiment(candidate="exp/<name>", baseline="<current baseline sha>",
   metric="<primary>")`, or the JSON API fallback:
   `curl -s -X POST http://127.0.0.1:8765/api/jobs -H 'Content-Type: application/json' -d '{"kind":"experiment","candidate":"exp/<name>","baseline":"<sha>","metric":"<primary>"}'`.
   Then run `uv run screens-bench wait <job id>` as a background command and do research until it
   ends.
8. **Read.** `uv run python scripts/seeded_report.py verdict exp/<name>` prints the job's verdict
   (state, checkpoint, diff, lo, hi). Mechanism:
   `uv run python scripts/seeded_report.py pairs exp/<name> <baseline sha> --metric <m> --seeds <checkpoint>`
   for each mechanism metric. Crashes: compare exception end reasons of both sides
   (`seeded_report.py killers` rows starting `exception`); a new exception type means drop, or a
   separate fix commit and a re-run.
9. **Decide.** Keep only if the pre-registered primary metric's verdict state is `better`.
   `no measurable difference`, `open` (stopped), and `worse` all drop (REQUIREMENTS "done" rule).
10. **Keep.** On `main`: `git merge --ff-only exp/<name>`; if `main` moved (docs commits), use
    `git merge --no-edit exp/<name>` and confirm code identity with
    `git diff --quiet exp/<name> main -- autoascend nethack_screensaver pyproject.toml uv.lock`.
    Run `uv run pytest -q -m ""` on `main`. The new `Current baseline` is the SHA of
    `exp/<name>` (its stored games are reused; the scheduler tops up missing seeds).
    **Drop.** `main` unchanged; the branch stays.
11. **Log (docs commit on `main`).** Fill the entry: verdict, interval in points, checkpoint,
    games per side, mechanism results, crash check, decision, and the new `Current baseline`
    line when kept. Add the table row.

## 4. Bench server restart (only when idle)

Needed after any change under `bench/` on `main` (it runs its own `bench/` code):
1. Idle check (step 1).
2. `pkill -INT -f "bench.cli serve"`; wait until `curl -s http://127.0.0.1:8765/api/status` fails.
3. From the primary checkout on `main`:
   `setsid nohup .venv/bin/python -m bench.cli serve >> ~/.local/share/screens-bench/server.log 2>&1 < /dev/null &`
   (any MCP bench tool also starts it when it is down, `bench/mcp_server.py` `_ensure_server`).
4. `curl -s http://127.0.0.1:8765/api/status` returns JSON with `"job": null`.
Restarting during a job marks it `interrupted` (`Store.interrupt_unfinished`); never do that.

## 5. PORTING.md experiment entry template

Table row (under `Current baseline:` in `### Experiments`):
`| <n> | \`exp/<name>\` | <cause> | \`<cand7>\` | \`<base7>\` | <metric> | <state> @ <checkpoint> | <diff> [<lo>, <hi>] | kept/dropped |`

Entry:
```
#### Experiment <n>: `exp/<name>` - <one-line cause>
- Requirement / decisions: SURV-0x (D-..)
- Change: <one sentence; file and function>
- Candidate `<40-hex>`; baseline `<40-hex>`; primary metric `<m>` (<reason>); games: <rule> (<reason>)
- Job <id>: Verdict: <state> at <checkpoint> games per side, diff <+x.x> points, 95%/99% interval [<lo>, <hi>]
- Mechanism: <metric> <diff> [<lo>, <hi>]; counter <name> fired in <k> of <n> games; crashes: <same/new types>
- Decision: kept (Current baseline -> `<sha>`) | dropped (branch `exp/<name>` kept at `<sha>`)
```
Intervals are written in percentage points (diff x 100).
