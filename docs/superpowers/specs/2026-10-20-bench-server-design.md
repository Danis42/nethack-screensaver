# Bench Server — Design

Date: 2026-10-20
Status: Approved design, pending spec review

## Goal

Measuring a bot change today means a 576-game shell run of the branch and another of
`main` (2 x ~15 min), reading logs by hand, and guessing whether a difference is noise.
The bench server replaces that: a local server plays games on demand, stores every
game, compares a candidate commit against a baseline with honest error margins, and
shows a live status page. Claude drives it through MCP. It also imports real
ascensions from public servers as a yardstick for the ascension work that follows.

Success:
- An experiment (candidate vs `main`) needs one command and no shell waiting; Claude is
  notified when it is decided.
- Baseline games are stored per commit and reused, so an experiment usually plays only
  the candidate.
- Verdicts do not call noise a win (the 286 vs 262 "Dlvl 6+" choke-point run must come
  out as "no difference measurable").
- Real ascensions from public servers can be imported and summarised.

## Decisions

| Topic | Decision |
|---|---|
| Modes | Both: baseline (play a commit up to N games, feeds the dashboard) and experiment (candidate vs baseline, A/B) |
| Load | On demand only: plays while a job is active, idle otherwise |
| Workers | 11 by default (configurable), started with `nice` |
| Status page | Local web page, `http://localhost:8765`, served by the server |
| Claude access | MCP stdio server, a thin client of the server's JSON API |
| Stack | Python standard library (`http.server`, `sqlite3`, `subprocess`); only new dependency is `mcp`, in its own dependency group `bench` |
| Code under test | Always a commit, run from a git worktree per commit; uncommitted changes cannot be benchmarked |
| Storage | SQLite at `~/.local/share/screens-bench/results.db`; whole `GameResult` JSON per game |
| Old tool | `scripts/benchmark.py` stays as a fallback |
| Out of scope | ttyrec recordings; remote access; a web framework |

## 1. Building blocks and data flow

```
Browser --http--> +--------- screens-bench serve (localhost:8765) ---------+
                  |  web page + JSON API                                    |
Claude --MCP----> |  scheduler --> worker processes (max 11, nice)          |
(stdio adapter,   |                 `- run from the commit's worktree        |
 starts the       |  results <-- one JSON line per finished game            |
 server if needed)|  SQLite: ~/.local/share/screens-bench/results.db        |
                  +---------------------------------------------------------+
```

- Package `bench/` in the repo, separate from `nethack_screensaver/` (which does not
  depend on it). Entry point `screens-bench` (`[project.scripts]`).
- **Commits and worktrees.** A ref (branch or SHA) is resolved to a full SHA when a job
  starts. The server creates `~/.cache/screens-bench/worktrees/<sha>` once
  (`git worktree add --detach`) and reuses it. Workers run with `PYTHONPATH=<worktree>`
  and the repo's `.venv/bin/python`.
- **Worker** (`bench/worker.py`, run inside the worktree's code): a process bound to one
  commit. It reads one line per game from stdin ("play"), runs
  `run_game(watchdog_seconds=120)` and prints the result as one JSON line
  (`dataclasses.asdict(GameResult)`) to stdout. The server stores each game immediately.
  A worker slot that has to switch commit closes its worker and starts one for the other
  commit.
- **Scheduler.** At most one active job, plus a FIFO queue. Job kinds:
  - `baseline(ref, games)`: play `ref` until it has `games` stored games.
  - `experiment(candidate, baseline, metric)`: per checkpoint, first top up the
    baseline commit to the checkpoint size (reusing stored games), then play the
    candidate to the same size; judge; stop when decided or at the last checkpoint.
  The scheduler hands out one game at a time to free workers, so a job can switch from
  baseline top-up to candidate without waiting for a batch.
- **Load.** Workers start with `nice -n 10`. The count is a server option (`--workers`, default 11).

## 2. Comparison and verdicts

- **Metrics** are small functions in a registry (`bench/metrics.py`): name, description,
  `game -> bool` (rates) or `game -> number` (medians). Defaults: reached Dlvl 6+,
  Dlvl 10+, escaped, crashed, died, starved, died to ants (soldier/giant/fire ant),
  killed by a wand or ray, unstuck at least once; medians of depth, turns, score.
  Metrics run on the stored JSON, so a new metric applies to every old game that has
  the fields it needs; games without the field are left out of that metric (and the
  count shown).
- **Rate comparison:** difference of two proportions with a Newcombe (Wilson score)
  interval, implemented in `bench/stats.py` without a statistics library.
- **Primary metric:** each experiment names one (default `dlvl6`). Only it decides; the
  other metrics are shown for information.
- **Checkpoints:** the verdict is computed only at 192, 384, 576 and 1152 games per
  side. Confidence 99% at 192/384/576, 95% at 1152.
- **Verdicts:** `better` / `worse` when the interval excludes 0 at a checkpoint;
  `no measurable difference` at 1152 otherwise, with the smallest difference that
  sample could have detected (half-width of the interval); `open` before that.
- **Medians** (depth, turns, score) are shown side by side without a verdict.

## 3. Status page and MCP

**Page** (`bench/static/index.html`, plain JavaScript, polls `/api/status` every 2 s
while a job runs, every 30 s when idle):
- Job panel: kind, refs (with short SHA and subject line), progress, games per minute,
  estimated time left, Start baseline / Start experiment / Stop.
- Experiment panel: verdict, primary metric with interval, table of all metrics
  (candidate, baseline, difference, interval).
- Dashboard for the newest `main` commit with stored games: top killers, depth
  histogram, outcomes per strategy, crashes with their call chains, games with the most
  unsticks.
- History: past experiments with refs, sizes and verdict.
- Ascenders: see section 5.

**JSON API** (all under `/api/`): `status`, `jobs` (POST to queue), `jobs/<id>`
(DELETE to stop), `results?ref=&metric=`, `games?ref=&where=&limit=`,
`experiments`, `reference/summary`, `reference/games?where=`, `import` (POST).
`where` filters are `field=value`, `field>value`, `field<value` and `field~substring`,
joined by `,` — no free-form code.

**MCP tools** (`bench/mcp_server.py`, stdio, registered in the repo's `.mcp.json`;
starts `screens-bench serve` in the background if the port does not answer):
- `bench_status()`
- `bench_baseline(ref="main", games=576)`
- `bench_experiment(candidate, baseline="main", metric="dlvl6")`
- `bench_results(ref, metric=None)`
- `bench_games(ref, where=None, limit=50)`
- `bench_stop()`
- `bench_import(source, url, limit=500)`
- `bench_reference(where=None)`

**Notification:** `screens-bench wait <job-id>` blocks until the job ends and prints its
verdict; Claude runs it as a background shell command and is notified when it exits.

## 4. Errors and lifecycle

- `screens-bench serve` refuses to start a second instance (port taken) and says the
  first one is running. Idle cost is one sleeping process.
- A game ending in a bot exception is a normal result (`crashed`), counted in metrics.
- A worker process that dies is restarted; three deaths in a row stop the job with the
  error shown on the page and in `bench_status`.
- A game without progress for 120 s ends through the existing watchdog.
- Stopped or interrupted jobs keep their stored games; the next job on that commit
  counts them.
- An unknown ref fails before anything starts, with git's message.
- `screens-bench prune` removes worktrees of commits not used for 14 days.
- The database schema has a version number; tables: `games(id, sha, job_id, finished_at,
  json)`, `jobs(id, kind, spec, state, created_at, ended_at, result)` (an experiment is a
  job of kind `experiment`, its verdicts in `result`), `reference_games(id, source, name,
  starttime, role, turns, json, dumplog)` (raw dumplog text; unique per source, name and
  start time).
- `screens-bench import results <file.jsonl> --ref <ref>` stores games from the old
  `scripts/benchmark.py --out` files under a commit, so earlier runs count.

## 5. Importing real ascensions

- `screens-bench import xlog <url>` downloads an xlogfile (e.g.
  `https://www.hardfought.org/xlogfiles/nethack50/xlogfile`), parses each line
  (`key=value` fields separated by tabs, or `:` in old files; achievements from `achieveX`
  names, or decoded from the 3.6 `achieve` bit field) and stores the ascended games in
  `reference_games`.
- `screens-bench import dumplogs [--limit 500]` downloads the dumplogs of stored
  ascensions that do not have one yet: one request per second, cached under
  `~/.cache/screens-bench/dumplogs/`, so each file is fetched once. Hardfought's pattern is
  `https://www.hardfought.org/userdata/<initial>/<name>/nethack/dumplog/<starttime>.nh.txt`
  (older files redirect to its S3 archive); sources without a known pattern are skipped.
- The dumplog parser splits by section heading and extracts: final inventory, attributes,
  intrinsics, conducts, killed monsters count, and the major-events timeline with turn
  numbers where the server's version writes one (NetHack 5.0 dumplogs have "Major
  events"; 3.6 dumplogs do not). Raw text is kept so later parsers need no new
  download.
- Ascenders page and `bench_reference`: number of ascensions, turns to ascend
  (median, quartiles), role mix, achievement order and turn of each milestone (where a
  timeline exists), share carrying reflection / magic resistance / a bag of holding, most
  common wands, final experience level and AC.

## Testing

- `bench/stats.py`: interval values against worked examples; verdicts at each
  checkpoint; the choke-point numbers (286/576 vs 262/576) give `open` at 576.
- Scheduler with a fake worker that emits made-up results instantly: baseline top-up
  reuses stored games, stop, restart after a worker death, three-deaths stop,
  checkpoint verdicts.
- Storage and metrics: store games, add a metric, apply it to old games, skip games
  missing a field.
- API: start the server in-process with the fake worker and query the endpoints.
- Parsers: one saved xlogfile excerpt and one shortened dumplog in `tests/data/`; no
  network in tests.
- One slow test (`-m slow`): two real games on the current commit through a real
  worktree, end to end.

## Order of work

1. Storage, metrics, stats.
2. Worker, scheduler, CLI (`serve`, `wait`, `prune`).
3. JSON API and status page.
4. MCP server and `.mcp.json`.
5. Importers and the Ascenders page.
6. Check against known numbers: experiment `choke-points` vs `main` should end as
   `no measurable difference`.

Afterwards the ascension brainstorm resumes (roadmap sub-projects 0-8).
