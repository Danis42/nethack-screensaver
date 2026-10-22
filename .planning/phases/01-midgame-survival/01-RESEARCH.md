# Phase 1: Midgame Survival - Research

**Researched:** 2026-10-22
**Domain:** Measurement-and-experiment loop on a seeded paired bot benchmark (`screens-bench`), plus NetHack 3.6.6 survival mechanics (starvation/prayer, resting, wand/ray users, ants and bees) for the AutoAscend bot
**Confidence:** HIGH on bench mechanics and determinism (code read, probes run this session); MEDIUM on NetHack mechanics (primary C source fetched through a summarising fetcher, wiki pages for strategy); LOW on any "what will work" prediction for the four killers (that is what the experiments are for)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Working method
- **D-01:** GSD runs Phase 1 and the roadmap from here on (discuss -> plan-phase -> execute-phase;
  plans in `.planning/phases/01-midgame-survival/`). Superpowers specs/plans in `docs/superpowers/`
  stay as history; new work does not add to them.
- **D-02:** `.planning/STATE.md` is the single source of truth for project status. `docs/STATUS.md`
  and `handoff.txt` are replaced by a short pointer to `.planning/STATE.md`; the owner's "save" habit
  now means updating STATE.md. This is a task in this phase. `autoascend/PORTING.md` stays the log of
  bench numbers, verdicts and dropped ideas (unchanged project rule).

### Measurement gate (MEAS-01..03)
- **D-03:** Order inside the phase: seeded A/A control + replay check first, then the pilgrim-only
  baseline (seeds 0..575), then bot experiments.
- **D-04:** If the A/A control does not read "no measurable difference", or the same seed does not
  replay the same game (MEAS-03), all bot experiments stop until the bench is fixed (module-level
  caches such as `_PRIZES` in `autoascend/global_logic.py` and `STRATEGIES` in `autoascend/plans.py`,
  wall-clock effects). No "proceed with caution".

### Experiment discipline
- **D-05:** Stacked baselines: every merged `better` change gets a fresh pilgrim-only baseline of the
  new `main`, and the next experiment is judged against it.
- **D-06:** Strictly one experiment on the bench at a time (all 11 workers). Bench wait time goes to
  research (diagnosis, human-game studies, wiki).
- **D-07:** Killer order: starvation first; then Claude orders the rest (rest to full HP, wand/ray
  users, ants and bees, the three re-judged branches) by expected gain per bench hour, recording the
  reasoning.
- **D-08:** One cause per experiment, never a bundle — including when a diagnosis finds several
  causes of the same killer.

### Starvation (SURV-02)
- **D-09:** Diagnose before fixing: pull the starvation deaths from the pilgrim-only baseline and
  classify them (e.g. prayer still on cooldown, no food carried, corpses refused, stuck on a level,
  weak role early on Dlvl 2-4 vs long 6000+ turn games), then fix the biggest bucket first.
- **D-10:** The diagnosis always includes a comparison with human games from NLD-NAO
  (`/ssd2/nethackFiles/db/nld.db`): how surviving humans on Dlvl 4-12 handle food and prayer timing.
  If `/ssd2` is not mounted, that is a blocker to raise with the owner, not a step to skip.
- **D-11:** Cheesy fixes are allowed (risky-but-usually-safe corpses, aggressive prayer timing,
  sacrificing to recover prayer, etc.) — owner preference "anything goes".

### Old branches (SURV-05)
- **D-12:** Keep SURV-05: rebase `threat-model`, `flee-upstairs` and `choke-points` onto current
  `main` and judge each once on the seeded bench against the then-current stacked baseline.
- **D-13:** After judging: merge any `better` branch; for the rest record verdict, interval and SHA
  in `autoascend/PORTING.md`, then delete the branch. Delete `survival-tuning` now (it has no commits
  `main` lacks). — **Reversibility:** one-way — deleted branch refs are only recoverable from the
  reflog for a limited time; the SHA must be logged in PORTING.md before deletion.

### Done bar (SURV-06)
- **D-14:** The phase closes only when the final `main` gives a paired `better` verdict on `rung2`
  (Minetown+) against the pilgrim-only baseline with rungs 3-6 not worse. If the planned fixes are
  exhausted without it, the phase stays open: diagnose the next-biggest Dlvl 4-12 killer from the
  latest baseline and attack it. No lowering the bar, no moving on early.

### Claude's Discretion
- Games per side for each experiment (576 for long shots, 1152 for promising changes; early stop at
  192/384/576 when the verdict is already clear); the choice and reason are recorded per experiment.
- Order of the killers after starvation (D-07).
- How each fix is implemented (rest trigger, wand/ray tactics, ant/bee approach), within the rule
  that dropped ideas are not retried without a new approach.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEAS-01 | Seeded A/A control reads "no measurable difference" with a paired interval clearly narrower than ~3.5 points | Same-commit A/A is refused by the server (`server.py:47-48`); use two SHAs with identical code. `9ff6a6f` and current `main` are already code-identical. With exact replay the paired interval is exactly [0, 0] (Wald formula), so the control mainly proves replay; a "divergence control" (agent RNG seed 1 vs 0) measures the real resolution. See Summary, Pitfalls 1-3, Code Examples 1-2. |
| MEAS-02 | Pilgrim-only baseline of `main` (seeds 0..575) stored; 17-rung table in `autoascend/PORTING.md`; older numbers marked not comparable | The A/A job itself plays the baseline side (seeds 0..1151). `GET /api/results?ref=<sha>` (`bench_results`) returns the 17-row `ladder` table (`hits`, `n`, `median_turn`, `yardstick_turn`). Name baselines by explicit code SHA, not by `main`. Pitfall 4, Code Example 3. |
| MEAS-03 | Same seed twice gives the same game; non-replay sources fixed or documented | Probed this session: 12 seeds x 2 fresh processes (different `PYTHONHASHSEED`, 11 parallel) and a same-process A,B,C,A,B,C sequence were frame-for-frame identical, so `_PRIZES`/`STRATEGIES` do not leak in those paths. Remaining non-replay sources: real-clock moon phase / Friday 13th / night (NLE `fix_moon_phase`), wall-clock deadline in the Sokoban live solver, watchdog. See Pitfalls 5-7. |
| SURV-01 | Rest to full HP before exploring on | Regen formula and hunger cost computed; existing code only heals by searching when nothing is left to explore (`global_logic.py:849`); dropped variant was narrower (rest on Elbereth). See Architecture Pattern 4 and Pitfall 10. |
| SURV-02 | Starvation deaths (~13%) addressed | Stored pilgrim games: 280 of 2042 (13.7%) starved. Prayer-safety numbers computed from the 3.6.6 `rnz`/`rne` code: a hunger prayer 400 turns after the last one is safe only ~77% of the time; a too-soon prayer costs Luck -3 and angers the god. NLD human baseline 2.1%. See Architecture Pattern 3, Pitfall 8-9. |
| SURV-03 | Wand and ray users (~8%) addressed | `killed by a wand` = monster wand of striking (2d12, `rnd(20) < 10 + u.uac`); monsters zap only when lined up. Metric `rays` also counts god lightning. Needs death-context instrumentation. See Pattern 5, Pitfall 11. |
| SURV-04 | Ants, fire ants, giant ants, killer bees (~8%) with a new approach | 198 of 2042 stored pilgrim games (9.7%). Dropped: doorway fighting, threat numbers, flee-upstairs. Untried here: full-HP entry (SURV-01), closing doors on handless pursuers, Elbereth kept as data not as plan. See Pattern 6. |
| SURV-05 | Re-judge `threat-model`, `flee-upstairs`, `choke-points` once each on the seeded bench | Merge-tree dry runs: `threat-model` and `choke-points` merge cleanly into `main`; `flee-upstairs` conflicts only in `nethack_screensaver/game.py`. Old commits cannot play seeded games and fail the job, so a rebase is mandatory. See Pattern 7. |
| SURV-06 | Final `main` vs baseline: paired `better` on `rung2`, rungs 3-6 not worse | Only the job's primary metric gets a paired verdict; `report.compare` intervals are unpaired. Re-submit the same candidate/baseline pair with `metric=rungN` to get paired verdicts for free from stored games. See Pitfall 3 and Code Example 4. |
</phase_requirements>

## Summary

Phase 1 is a loop, not a build: harden the bench, store a baseline, then run one change at a time through `screens-bench experiment` (576/1152 games per side, ~27 minutes per 1152 games per commit with 11 workers [VERIFIED: results.db job rows, e.g. job 8 took 28 min for 1152 + 1152 games, and per-sha span 27 min]). The bench is already seeded and paired; nothing seeded has ever been stored (`games` table: 0 seeded rows for every sha [VERIFIED: sqlite query this session]). The server is running and idle on 127.0.0.1:8765, started after the seeded-bench merge, so it runs the seeded scheduler [VERIFIED: `ps` start time 21:19 vs commit 23:48 on the previous day].

Three facts reshape the measurement plan. (1) The server refuses an experiment whose two refs are the same commit, so an A/A needs two SHAs with identical code; `9ff6a6f` and `main` (`2d5bbce`) already are (empty `git diff 9ff6a6f main -- autoascend nethack_screensaver bench scripts tests pyproject.toml uv.lock`). (2) With perfect replay the paired A/A has zero discordant pairs, so its interval is exactly [0, 0] and it ends "no measurable difference" only at the 1152 checkpoint (open before that); it proves replay, not resolution. Resolution comes from the discordance rate `q` of an experiment between two commits whose games diverge; with `q` around 0.15-0.25 the 95% half-width at 1152 games is 2.2-2.9 points and the 80%-power detectable effect is 3.2-4.1 points, barely better than the unpaired 3.7. Passing `lgen=seed` to NLE (level-generation RNG decoupled from play) and/or adding a 2304 checkpoint are the levers; a one-line "divergence control" (`Agent` RNG seed 1 instead of 0) measures `q` before any real experiment. (3) NLE 1.3.0 reads the real clock for moon phase, Friday the 13th and night unless `fix_moon_phase=True`; the bench does not pass it. Full moon gives Luck +1, Friday 13th Luck -1 (prayer then fails), and a Friday 13th falls on 2026-11-13, inside this phase's likely span. Passing `fix_moon_phase=True` for seeded games makes those effects a function of the seed (probed: 576 seeds give 74 new, 74 full, 3 Friday-13, 425 normal).

Replay is otherwise good today: 12 seeds were each played twice in fresh processes with different `PYTHONHASHSEED` while 11 ran in parallel, and every per-frame screen hash matched (up to 32,808 frames); a same-process sequence 10,2,3,10,2,3 also matched the fresh-process hashes. So the `_PRIZES` and `STRATEGIES` worries are not borne out on those paths; the real non-replay sources are the clock and the Sokoban solver's 10-second wall-clock deadline. For the killers, stored pilgrim games (mixed-era, unseeded, 2042 games, only a prior) show starvation 13.7%, ants+bees 9.7%, rays/breath 7.1% plus 5.1% "killed by a wand", hostile unicorns 4.8%, mimics 4.0%, weres 3.5%, and 2.6% of games ending "while praying" (a failed prayer leaves the hero vulnerable). The GameResult has no death-context fields, so SURV-02/03/04 diagnosis needs a behaviour-neutral instrumentation commit before the baseline.

**Primary recommendation:** Land one small determinism-and-instrumentation commit D (seeded games pass `fix_moon_phase=True`; Sokoban solver drops its wall-clock deadline; death-context stats added), prove it behaviour-neutral by exact replay against current `main`, run the A/A as D vs a docs-only twin (the D-02 pointer commit) with metric `rung2` to 1152 games (this also stores the pilgrim-only baseline for D), write the 17-rung table from `bench_results(D)`, then run starvation first with every experiment naming its baseline by explicit code SHA.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Which commit plays which seed, checkpoints, paired verdict | Bench server (`bench/scheduler.py`, `bench/stats.py`) | SQLite store (`bench/store.py`) | Scheduler hands out seeds 0..N-1 per commit and judges per checkpoint |
| Playing one seeded game, determinism of that game | Worker + game code from the commit's worktree (`bench/worker.py` -> `nethack_screensaver/game.py` -> NLE) | Bot RNG (`Agent(seed=0)`) | Code under test must come from the commit; worker imports nothing from `bench` |
| Process environment of workers (hash seed, nice) | Bench server (`bench/runner.py`) | — | Server-side; a change needs a server restart |
| Per-game diagnosis data (death cause, rung, new stats) | `GameResult` JSON built in `nethack_screensaver/game.py` from `stats_logger` | Bench metrics/filters (`bench/metrics.py`, `bench/filters.py`) | Metrics run on stored JSON; a missing field skips that game for that metric |
| Survival behaviour (rest, pray, eat, flee, wand tactics) | Bot (`autoascend/agent.py`, `global_logic.py`, `combat/fight_heur.py`) | `exploration_logic.py` for rest hooks | Existing strategy/preempt structure |
| Human-game comparison | Offline analysis over `/ssd2/nethackFiles/db/nld.db` + `nle.dataset` | — | Read-only study, no bench involvement |
| Verdict log and dropped ideas | `autoascend/PORTING.md` | `.planning/STATE.md` for status (D-02) | Project rule |

## Standard Stack

No new packages are needed. Everything below is already in the repo and verified present this session.

### Core
| Library / tool | Version | Purpose | Why standard |
|----------------|---------|---------|--------------|
| `screens-bench` (`bench/`) | repo HEAD | Seeded paired experiments, store, MCP tools | The project's measurement rule; entry point `[project.scripts] screens-bench = "bench.cli:main"` [VERIFIED: pyproject.toml] |
| NLE | 1.3.0 (exact pin) | NetHack 3.6.6 environment, `set_initial_seeds`, `fix_moon_phase`, `nle.dataset` | Pinned; changing it needs a fresh baseline [VERIFIED: `nle.__version__` = 1.3.0] |
| pytest | >=8 (project dev group) | Test gate `uv run pytest -q -m ""` | Green in 116 s this session [VERIFIED: ran it; output ".. [100%]", exit 0] |
| Python / uv | 3.13.15 / uv 0.12.10 | Runtime | `requires-python >=3.13,<3.14` |
| sqlite3 CLI | 3.53.4 | Ad-hoc queries of `results.db` and `nld.db` | Used for every number in this document |

### Supporting
| Tool | Purpose | When to use |
|------|---------|-------------|
| `bench_baseline`, `bench_experiment`, `bench_results`, `bench_games`, `bench_experiments`, `bench_status`, `bench_stop` (MCP) | Drive the server | Default path; JSON API with `curl` is the fallback (Code Example 1) |
| `uv run screens-bench wait <job-id>` | Blocks until the job ends, prints verdict JSON | Run as a background shell command to be notified |
| `nle.dataset.TtyrecDataset("nld-nao-aa", ...)` | Decode human ttyrecs (~27k frames/s measured) | Human food/prayer study (D-10) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rate verdict for A/A | Exact-replay comparison of whole game records (turns, end_reason, rung, role) per seed | Stronger proof of determinism than a rung rate; needs a small script reading `Store.games_by_seed` |
| Unseeded-style `report.compare` intervals | Re-submit the pair per metric to get paired verdicts | Free (stored games), but one job per metric |

**Installation:** none. **Version verification:** `uv --version`, `.venv/bin/python --version`, `nle.__version__` were run this session (table above). No `npm view`/`pip index` step applies because no package is added.

## Package Legitimacy Audit

No external packages are installed in this phase, so the legitimacy gate was not run.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

If a task proposes adding a dependency (for example a statistics library), it must go through the gate first; the existing Wilson/Newcombe/Wald code in `bench/stats.py` already covers the verdicts.

## Architecture Patterns

### System Architecture Diagram

```
 commit under test (git SHA)  ---->  worktree ~/.cache/screens-bench/worktrees/<sha>
        |                                  |  PYTHONPATH=<worktree>, nice -n 10, one worker per slot (11)
        v                                  v
 bench_experiment(candidate, baseline, metric)        worker.py: "play <seed>" -> run_game(seed)
        |                                                   |  NetHackChallenge + set_initial_seeds(seed,seed)
        v                                                   |  Agent(seed=0) -> bot plays to death/limit
 Scheduler.tick():                                          v
   _judge(): for checkpoint in 192,384,576,1152:      GameResult JSON (end_reason, rung, ladder, new stats)
     both sides have seeds 0..N-1? --no--> _dispatch()  --> Store.add_game(sha, job, json)   [SQLite]
        | yes                                                    ^
        v                                                        |
   pairs = [(metric(cand[s]), metric(base[s])) for s in 0..N-1]  |
   judge_paired(pairs) -> better | worse | open | no measurable difference
        |                                   (99% early, 95% at 1152)
        v
   job.result.verdict  --> `screens-bench wait <id>` prints it --> executor logs in autoascend/PORTING.md
                                                                       |
   better? --yes--> git merge --ff-only (candidate becomes main code SHA) --> next baseline = that SHA
            --no---> drop + log interval + SHA (D-13 for branches)

 Diagnosis side channel (while the bench runs, D-06):
   bench_games(ref, where="end_reason~starv,...")  and  nld.db + TtyrecDataset (humans)  --> next experiment's cause
```

### Recommended Project Structure
```
autoascend/            # bot: agent.py (prayer/eat/emergency), global_logic.py, combat/fight_heur.py
nethack_screensaver/game.py   # run_game: seeding, GameResult fields   <- determinism + instrumentation edits
bench/runner.py        # worker env (PYTHONHASHSEED pin would go here; needs server restart)
scripts/               # add replay_check.py (exact-replay compare), human-study scripts if kept
tests/                 # add slow replay test; unit tests per bot change (SimpleNamespace fakes, see tests/test_fight_heur.py)
.planning/phases/01-midgame-survival/   # plans, experiment log notes
autoascend/PORTING.md  # verdict log, 17-rung table, dropped ideas (unchanged project rule)
```

### Pattern 1: A/A control via two code-identical SHAs
**What:** The experiment spec needs `candidate != baseline` as SHAs; docs-only commits give a twin.
**When:** MEAS-01/03, and again whenever determinism-relevant code changes.
**Evidence:** `bench/server.py:47-48`:
```python
        if cand == base:
            raise ValueError(f"{candidate} and {baseline} are the same commit {cand[:10]}")
```
Code-identity of `9ff6a6f` and `main`: `git diff --stat 9ff6a6f main -- autoascend nethack_screensaver bench scripts tests pyproject.toml uv.lock` printed nothing [VERIFIED this session]. After the determinism commit D, the D-02 pointer commit (docs only) is the natural twin D'.
**Verdict mechanics** (`bench/stats.py:52-61` and `71-81`):
```python
def _verdict(diff, lo, hi, checkpoint):
    if lo > 0:
        state = "better"
    elif hi < 0:
        state = "worse"
    elif checkpoint == CHECKPOINTS[-1]:
        state = "no measurable difference"
    else:
        state = "open"
...
    half = z_for(checkpoint) * math.sqrt(max(n10 + n01 - n * diff * diff, 0.0)) / n
```
With zero discordant pairs `half = 0`, interval [0, 0], state `open` at 192/384/576 and `no measurable difference` at 1152. So the A/A takes the full 1152 games per side (~54 minutes for both sides; the baseline side doubles as MEAS-02).

### Pattern 2: Name baselines by code SHA; merge fast-forward
**What:** Stored games are keyed by SHA (`Store.seeds(sha)`, `store.py:71-75`). A docs commit on `main` changes the SHA and the new HEAD has zero games, so `baseline="main"` after any docs commit silently replays the baseline from scratch (~27 min per 1152). Use the explicit SHA of the last code-changing commit. When a candidate is `better`, merge with `git merge --ff-only` (experiments branch from `main`, so this works) so the candidate SHA becomes the code SHA of `main` and its already-played seeds become the next baseline for free; a `--no-ff` merge commit has the same tree but a new SHA and costs a replay.
**Caveat:** keep PORTING.md/STATE.md edits in separate commits after the code SHA; record "baseline SHA" in PORTING.md.

### Pattern 3: Starvation = prayer reliability + food supply (diagnose first, D-09)
**Facts from the 3.6.6 source (fetched raw, quoted):**
- Weak or worse is major trouble: `if (u.uhs >= WEAK) return TROUBLE_STARVING;` Hungry is minor: `if (u.uhs >= HUNGRY) return TROUBLE_HUNGRY;` [CITED: github.com/NetHack/NetHack NetHack-3.6.6_Released src/pray.c, in_trouble()].
- Too-soon test: `if ((p_trouble > 0) ? (u.ublesscnt > 200) /* big trouble */ : (p_trouble < 0) ? (u.ublesscnt > 100) : (u.ublesscnt > 0)) p_type = 0; /* too soon... */`; `else if ((int) Luck < 0 || u.ugangr || alignment < 0) p_type = 1; /* too naughty... */` [CITED: pray.c can_pray()].
- Failure costs: `p_type == 0`: `u.ublesscnt += rnz(250); change_luck(-3); gods_upset(u.ualign.type);` (god anger `u.ugangr++`); `p_type == 1`: `angrygods(u.ualign.type);`. Only `p_type == 3` sets `u.uinvulnerable`, so a failed prayer leaves the hero helpless for the prayer duration (matches 54 of 2042 stored games ending "while praying") [CITED: pray.c dopray()/prayer_done()].
- Success: `u.ublesscnt = rnz(350);` and hunger fixed by `init_uhunger()` (nutrition 900) [CITED: pray.c pleased()/fix_worst_trouble()].
- `rnz`/`rne` [CITED: rnd.c]: `tmp = 1000; tmp += rn2(1000); tmp *= rne(4);` then `if (rn2(2)) { x *= tmp; x /= 1000; } else { x *= 1000; x /= tmp; }`; `rne(x)`: `utmp = (u.ulevel < 15) ? 5 : u.ulevel / 3; tmp = 1; while (tmp < utmp && !rn2(x)) tmp++;`.
**Computed from that code (400k Monte-Carlo draws, script in Code Examples):** after a successful prayer the new timeout has percentiles 10/25/50/75/90/95/99 = 138/209/350/583/886/1228/1902. A prayer in major trouble is safe only if timeout - gap <= 200, so: gap 200 -> 55%, gap 400 -> 77%, gap 500 -> 88%, gap 800 -> 92%, gap 1000 -> 95%, gap 1200 -> 98% (assumes the timeout falls 1 per turn at Luck 0 [ASSUMED]).
**Current bot** (`autoascend/agent.py:790-796` and `1511-1516`):
```python
    def is_safe_to_pray(self, limit=500):
        return (
                (self.last_prayer_turn is None and self.blstats.time > 300) or
                (self.last_prayer_turn is not None and self.blstats.time - self.last_prayer_turn > limit)
        )
...
        food = self.edible_inventory_food()
        if prayer_trouble(self.blstats, self.is_safe_to_pray(500), self.is_safe_to_pray(400),
                          has_food=food is not None):
```
So hunger prayers use a 400-turn gap (77% safe) and HP prayers 500 (88%). The bot never learns that a prayer failed (only `last_prayer_turn` is stored), so after a failure it can pray again with Luck -3 or an angry god (every later prayer is `p_type 1`). The 12% failure rate in PORTING.md (566 of 643 succeeded) matches the computed 77-88% safety.
**Candidate causes (one per experiment, D-08), to be ranked by the baseline diagnosis:** (a) hunger-prayer gap 400 -> higher with an explicit "fainting is survivable for N turns" trade-off; (b) detect a failed prayer from its messages and stop praying; (c) food supply: pick up and carry non-corpse food, eat fresh corpses more eagerly, buy food in Minetown (cheesy, allowed by D-11); (d) sacrifice at an altar to cut the timeout (needs an altar and a fresh corpse; D-11 allows it); (e) the weak-role Dlvl 2-4 starvation (turn 1300-4500 per PORTING.md) may be a different cause from the 6000+ turn games, so test them separately.
**Corpse rules (eat.c):** `rotted = (monstermoves - age) / (10L + rn2(20));` tainted needs `rotted > 5L`, so a corpse younger than 60 turns is never tainted (divisor >= 10); "mildly ill" needs `rotted > 3L && rn2(5)` (age >= 40 possible); a non-rotten corpse still has `!rn2(7)` chance of `rottenfood()`; lizard and lichen never rot [CITED: eat.c eatcorpse()]. The bot's cutoff `if self.blstats.time - age_turn >= 50` (agent.py, `_is_corpse_editable`, "corpse aging") is therefore conservative-safe; its refusal list (poisonous unless orc, acidic, were, polymorphers, bats, dogs/cats, mimics, cannibalism) is where "risky-but-usually-safe" cheese (D-11) can be added one monster class at a time.
**Nutrition (wiki, LOW tier by the confidence seam):** 900 at start; Hungry at <150, Weak <50, Fainting below 0, 1 point per turn plus regeneration/encumbrance/rings/amulets [CITED: nethackwiki.com/wiki/Nutrition].
**Human baseline:** `nld.db` holds 39,210 games; among 3.6.x games reaching Dlvl 4+ (7,726) 160 died starving or fainted (2.1%), median turn of starvation deaths about 2,250 (offset-80 order statistic) [VERIFIED: sqlite queries on /ssd2/nethackFiles/db/nld.db]. Ours: 164 of 1570 stored pilgrim games with max_depth >= 4 (10.4%) and 280 of 2042 overall (13.7%), median starvation turn 7,828 [VERIFIED: results.db]. Humans also die "while praying" (141 of 7,726, 1.8%) so prayer failure alone is not the gap.

### Pattern 4: Resting to full HP (SURV-01)
**Facts:** HP regeneration (3.6 `regen_hp`): for level <= 9 `heal = 1` when `!(moves % (long) ((MAXULEV + 12) / (u.ulevel + 2) + 1))`; for level >= 10 every 3rd turn with Con-based heal; condition `encumbrance_ok = (wtcap < MOD_ENCUMBER || !u.umoved);` [CITED: allmain.c via fetcher; the fetched file header said 3.6.2-beta01, treat the formula as 3.6.x]. With MAXULEV = 30 [ASSUMED] that is one HP every 15 / 11 / 9 / 8 / 7 / 6 / 5 / 5 / 4 turns at XL 1..9. Resting 15 HP at XL 3 is about 135 turns, i.e. 135 nutrition (15% of a 900 meal). Resting competes with starvation, which is why D-07 puts starvation first and why the earlier "rest on Elbereth to 80%" attempt saw more fainting deaths [CITED: PORTING.md "Survival on Dlvl 6-9"].
**Existing code:** `autoascend/global_logic.py:848-849` already has `exploration_strategy(None).until(self.agent, lambda: self.agent.blstats.hitpoints >= 0.8 * self.agent.blstats.max_hitpoints)` but it sits after `exploration_strategy(0)` in the preempt list, so it only runs once nothing is left to explore. The rest primitive is `Agent.search(max_count=1)` (agent.py:877-885, count typed before `Command.SEARCH`). The dropped variant (stash `rest-on-elbereth`) rested only on an Elbereth square after a fight, below 50% up to 80%, with `hunger < Hunger.WEAK`.
**Design guidance:** a general trigger (no hostile in `get_visible_monsters()`, HP below a fraction, before leaving a level and before exploring on), gated by food (`hunger_state <= NOT_HUNGRY`, or carried food, or prayer safe), with a per-level turn cap, and interrupted by any monster appearing (NetHack interrupts counted searches). Record rest turns as a stat so the cost shows in the bench.

### Pattern 5: Wand and ray users (SURV-03)
**Facts (muse.c, mthrowu.c, 3.6.6):** a monster uses an offensive item only if `!lined_up(mtmp)` is false: `/* all offensive items require orthogonal or diagonal targetting */ if (!lined_up(mtmp)) return FALSE;`; `linedup()` requires `(!tbx || !tby || abs(tbx) == abs(tby))` within `BOLT_LIM` (8 [ASSUMED]) and a clear path. Peaceful, animal, mindless and handless monsters never use them. Items come from `rnd_offensive_item()`: `if (difficulty > 7 && !rn2(35)) return WAN_DEATH; switch (rn2(9 - (difficulty < 4) + 4 * (difficulty > 6)))` with cases striking, acid/confusion/blindness/sleeping/paralysis potions, magic missile (7, 8), then sleep, fire, cold, lightning for higher difficulty. Striking hits the hero when `rnd(20) < 10 + u.uac` for `d(2, 12)` and is blocked by magic resistance (`Boing!`) but not reflection: `losehp(tmp, "wand", KILLED_BY_AN);` [CITED: muse.c, mthrowu.c].
**Reading the stored deaths:** "killed by a wand" (104 of 2042, 5.1%) is therefore a monster's wand of striking, not a ray. "magic missile", "bolt of fire/cold/lightning", "blast of frost/fire", "death ray" total 146 (7.1%). The `rays` metric (`bench/metrics.py`: `RAYS = ("wand", "magic missile", "bolt of", "death ray", "blast of")`) mixes monster wands, monster breath (winter wolf cub "blast of frost", hell hound pup "blast of fire") and god smiting ("bolt of lightning" after an angry prayer), so it is not a clean target. Expect at least one of the 24-26 lightning deaths to be divine [ASSUMED: inferred from `angrygods`, not read from a death log].
**Instrumentation needed first:** the stored game has no context. Add behaviour-neutral stats: the last few messages at death, a counter for messages containing "zaps" and "wand", and the names of monsters in view at the last step.
**Candidate approaches (new, not on the dropped list):** step off the line when a visible handed hostile is within 8 squares and lined up and has already zapped (message "The <mon> zaps a wand!"), close to melee the zapper (they are mostly weak Mines/Dlvl 4-8 monsters), or leave via stairs. Elbereth does not stop zaps [ASSUMED]. Magic resistance (100% of real ascenders) is Phase 3.

### Pattern 6: Ants and killer bees (SURV-04)
**Facts:** soldier ant: speed 18, level 3, AC 3, bite 2d4 + sting 3d4 poison; killer bee: speed 18, level 1, AC -1, sting 1d3 poison, large groups; both always hostile [CITED: nethackwiki.com/wiki/Soldier_ant, /Killer_bee; pages show 5.0.0 values, 3.6 values may differ slightly]. Wiki tactics: avoid being surrounded, lead them to corridors or "close doors to block them off" (ants and bees have no hands), stairs as retreat, Elbereth works, kill quickly [CITED same pages]. Stored pilgrim deaths: soldier ant 92, killer bee 37, giant ant 35, fire ant 34 = 198 (9.7%), concentrated on Dlvl 5-7 (max_depth histogram 6:62, 5:42, 7:41, 4:22) [VERIFIED: results.db].
**Dropped (do not retry as is):** doorway fighting (`choke-points`), threat numbers (`threat-model`), fleeing upstairs (`flee-upstairs`), Elbereth resting. **Not tried:** arriving at full HP everywhere (SURV-01 itself addresses ants, and PORTING.md's human study found full-HP encounters 100% vs 80% for survivors vs dead); closing a door between the hero and a pack when a door is adjacent; poison-resistance gain (eat soldier ant 20% / killer bee corpses [CITED wiki]) after the first kill.
**Poison instadeath:** [ASSUMED] a poisonous sting that poisons (1/8 of hits) has a 1/30 chance of being deadly without resistance; not checked against `mhitu.c` this session.

### Pattern 7: Re-judging the three old branches (SURV-05)
**State** [VERIFIED: git commands this session]:

| Branch | SHA | Base | Commits ahead / behind `main` | Merge into current `main` |
|--------|-----|------|-------------------------------|---------------------------|
| `threat-model` | `fdf6b48e7ca9792c5944d6f969fc51f7adf434d9` | `2f75c61` | 8 / 12 | clean (`git merge-tree --write-tree` printed only a tree id) |
| `flee-upstairs` | `a535f7a872d0bf9fd790cddeddacaad781cf3c90` | `0c7acbc` | 2 / 11 | conflict in `nethack_screensaver/game.py` only (both sides add a `GameResult` field) |
| `choke-points` | `b31e9266c67b6dff19d0bf576577d887e9809adb` | `aa4b1cf` | 1 / 38 | clean |
| `survival-tuning` | `ade24fb74a0f141745633820eb0eba66cfd04ad5` | — | 0 / 50, listed by `git branch --merged main` | delete now (D-13); three stashes "On survival-tuning" remain independent |

**Constraint:** old commits predate seeding. `Scheduler._collect` fails the job when a result lacks `seed`: `self.error = f"commit {slot.sha[:7]} cannot play seeded games (its run_game has no seed)"` (`scheduler.py:79-83`). A rebase is mandatory, not optional.
**Procedure:** `git switch -c rejudge/<name> <name> && git rebase main` (keeps the old branch SHA intact until it is logged and deleted). `threat-model` has four variants (SHAs `46a7003`, `ace25e2`, `fdf6b48` plus the first `7c7cfaf`); judge exactly one (recommend the final `fdf6b48` "real danger only", least invasive: 39 lines in `monster_utils.py` plus `threat.py`) and say so in PORTING.md. Rebase lazily, each just before its judgement, because a merged `better` change in `fight_heur.py` or `monster_utils.py` changes what they must be rebased onto (D-05). `flee-upstairs` adds `GameResult.flee_upstairs`; keep it so the firing rate is visible.

### Pattern 8: Ordering by expected gain per bench hour (D-07 input)
Every experiment costs the same bench time (about 27-54 minutes per side to 1152 games), so ordering is by expected effect and by what unlocks others. Recommended order after starvation: (1) rest to full HP, because it acts on ants, striking wands and all HP-based deaths at once and uses plumbing the others reuse; (2) ants and bees (9.7%); (3) wand/ray users (5.1% + 7.1%, after instrumentation says who zaps); (4) the three old branches, each cheap to prepare during bench waits but with a prior near zero (the A/A of PORTING.md showed their earlier "worse" readings were baseline luck, so the true effect is probably small). If the done bar (D-14) is still open afterwards, next candidates from the stored data are hostile unicorns (99 deaths, 4.8%: white 42, gray 34, black 22), mimics (82, 4.0%), weres (72, 3.5%) [VERIFIED: results.db, prior only].

### Anti-Patterns to Avoid
- **Baseline by `main`:** after any docs commit it resolves to a SHA with no games (Pattern 2).
- **Reading `report.compare` intervals as the verdict:** `bench/report.py` `compare()` uses `newcombe(...)` (unpaired) for every metric: `row["diff"], row["lo"], row["hi"] = newcombe(c["hits"], c["n"], b["hits"], b["n"], Z95)`. Only `job.result.verdict` for the primary metric is paired.
- **Running heavy CPU beside a bench job** (pytest, parallel replay checks): wall-clock deadlines (Sokoban solver, watchdog) make games load-dependent until Pitfall 6 is fixed.
- **Bundling:** two causes in one commit make a `better` unattributable (D-08).
- **Restarting the server mid-job:** `Store.interrupt_unfinished()` marks queued and running jobs `interrupted` on start (`store.py:125-128`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Paired verdict and intervals | New statistics code | `bench/stats.py` `judge_paired`, `CHECKPOINTS` | Already tested against hand examples; changing it changes every verdict |
| Playing a seed twice to test replay | A second game loop | `nethack_screensaver.game.run_game(seed=...)` with `on_frame` hashing | Same path the bench uses (probe code in Code Examples) |
| Baseline table | Hand-assembled counts | `GET /api/results?ref=<sha>` -> `ladder` rows (`hits`, `n`, `median_turn`, `yardstick_turn`) | Already includes the 687-ascension yardstick turns |
| Pairing a second metric | Custom pairing code | Re-submit the same candidate/baseline as a new experiment with `metric="rungN"` | The scheduler finds all seeds stored and judges every checkpoint at once |
| Decoding human ttyrecs | Own tty parser | `nle.dataset.TtyrecDataset` + SQL `subselect_sql`/`gameids` | Probed: ~15.9k frames in 0.6 s |
| Prayer-safety math | Intuition | The `rnz`/`rne` simulation (Code Example 6) | Heavy-tailed; 400-turn spacing is 77% safe |

**Key insight:** the measurement layer is finished and tested; the risk is misusing it (wrong baseline ref, unpaired table, comparing across the clock), not missing features.

## Runtime State Inventory

Not a rename/refactor/migration phase. The only persistent state that matters:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `~/.local/share/screens-bench/results.db`: 9,262 games, none seeded; 687 reference ascensions | None. Old games stay for history; jobs ignore unseeded games |
| Live service config | Bench server (pid 8876) on 127.0.0.1:8765, started 2026-10-22 21:19 with seeded scheduler | Restart (when idle) after any `bench/` change, e.g. `PYTHONHASHSEED` pin in `runner.py` |
| OS-registered state | None | None |
| Secrets/env vars | `SCREENS_BENCH_DATA`, `SCREENS_BENCH_CACHE`, `SCREENS_BENCH_URL` (defaults used) | None |
| Build artifacts | 8 worktrees under `~/.cache/screens-bench/worktrees` (24 MB); 2 prunable pytest worktrees in /tmp listed by `git worktree list` | `git worktree prune` is harmless; `screens-bench prune` removes unused ones |

## Common Pitfalls

### Pitfall 1: Same-commit A/A is refused
**What goes wrong:** `bench_experiment("main", "main")` returns an error.
**Why:** `server.py:47-48`.
**How to avoid:** two SHAs with identical code (docs-only commit). Check with `git diff --stat A B -- autoascend nethack_screensaver bench scripts tests pyproject.toml uv.lock` (empty).
**Warning signs:** `{"error": "... are the same commit ..."}`.

### Pitfall 2: A perfect A/A proves replay, not resolution
**What goes wrong:** the "interval clearly narrower than 3.5 points" criterion is met trivially by [0, 0], giving false comfort about detecting 1-3 point effects.
**Why:** zero discordant pairs. A real change diverges the games after its first different action; only character, seed-fixed first level (and with `lgen`, all levels) stay shared.
**How to avoid:** add the divergence control: a commit whose only change is `AGENT_ARGS = dict(panic_on_errors=True, verbose=False, seed=1)` in `nethack_screensaver/game.py` (the agent's RNG drives exploration tie-breaks: `agent.py:81`, `exploration_logic.py:112,263,432`, `inventory.py:1262,1290`). Run it against the baseline on `rung2` to 1152; its discordance `q` and half-width are the bench's true resolution. Decide from that whether to adopt `lgen=seed` and/or a 2304 checkpoint (`CHECKPOINTS` in `bench/stats.py`; note `z_for` and the "no measurable difference" rule key off `CHECKPOINTS[-1]`).
**Illustrative sizing (formula `half = z*sqrt(q/n)`, `q` assumed):** q 0.15: 2.2 points at 1152, 1.6 at 2304; q 0.25: 2.9 at 1152, 2.0 at 2304. Unpaired at 1152 (p 0.3) is 3.7 points.

### Pitfall 3: Only the primary metric is paired
**What goes wrong:** reading `rung3..rung6` "not worse" off the job's metric table, which uses unpaired Newcombe intervals.
**How to avoid:** for SURV-06 and every "not worse" check, submit the same pair again with `metric="rung3"` ... `"rung6"`. Stored games make each re-judgement take seconds (`Scheduler._judge` walks the checkpoints as soon as `_played` reaches `need`, `scheduler.py:116-151`). Optionally make `report.compare` paired (small bench task); a server restart is needed after.
**Also:** each experiment names one primary metric. Per-killer rates exist as metrics (`starved`, `ants`, `rays`, `died`) and give larger relative effects than `rung2`; use them as mechanism checks and keep `rung2` (or the rung the fix targets) as the keep/drop rule, stated in the plan before the run to avoid metric shopping.

### Pitfall 4: MEAS-02 table must be written with explicit n and SHA
**What goes wrong:** `/api/results` summarises all games stored for the SHA (1152 after a full A/A), not seeds 0..575.
**How to avoid:** state n and the SHA in the PORTING.md table, or compute the 576-game table from `Store.games_by_seed(sha, range(576))`. Mark the 2026-10-21 mixed-strategy baseline (`2653410`, 576 games) and `aa4b1cf`/choke-points numbers "not comparable". The `rung` column semantics: `rungN` = highest rung reached >= N, so "rung2" includes games that reached Oracle or Sokoban without Minetown (Sokoban-first pilgrims for human/elf/orc, `plans.py` `SOKOBAN_FIRST_PILGRIM`).

### Pitfall 5: Real-clock effects leak into seeded games
**What goes wrong:** baseline and candidate are played hours or days apart; NLE derives moon phase, Friday the 13th, night and midnight from the system clock unless told otherwise. `nle/env/base.py:236-239`: "fix_moon_phase (bool): If True and seeds are set, derive deterministic time-based game effects (moon phase, friday 13th, night, midnight) from the seed instead of real system time. If False or no seeds are set, use real system time (default)." The bench builds `env = NetHackChallenge(no_progress_timeout=1000)` (`game.py:152`) without it.
**Why it matters:** full moon = Luck +1, Friday 13th = Luck -1 and, with Luck < 0, every prayer is `p_type 1` (see Pattern 3) [Luck effect: ASSUMED from `can_pray` quote plus standard moon rules; the `Luck < 0` clause is quoted]. 2026-11-13 is a Friday.
**How to avoid:** in `run_game`, `NetHackChallenge(no_progress_timeout=1000, fix_moon_phase=seed is not None)`. Verified to work with the class-method seeding on `NetHackChallenge` (kwargs pass through `tasks.py:324`): seeds 3/0/49/5 gave "Full moon", "New moon", "Friday the 13th", none; 576 seeds gave 74/74/3/425, which matches real frequencies. Screensaver (unseeded) games keep the real clock.

### Pitfall 6: Sokoban live solver has a wall-clock deadline
**What goes wrong:** games that reach Sokoban (rung 4+, about 9% of games) can diverge depending on machine load. `autoascend/soko_solver/search.py`: `def solve(floor, boulders, traps, player, max_states=300_000, max_seconds=10.0, alternatives=3, ...)`, `deadline = time.monotonic() + max_seconds`, checked at `if budget[0] < 0 or time.monotonic() > deadline: raise _OutOfBudget()`. Called from `global_logic.py:492-501` (`_solve_live_sokoban`).
**How to avoid:** make the state budget the only limit in bench runs (deadline disabled or very large, state budget calibrated), or document and keep CPU quiet. The 12-seed replay probe did not exercise it; after the A/A, pick seeds whose stored game has `rung` >= 4 (`bench_games(ref, where="rung>3")`) and replay them twice under deliberate CPU load.
**Also wall-clock:** the 120 s screen watchdog (`worker.py` passes `watchdog_seconds=120`) and `soko` 10 s; both are rare but real.

### Pitfall 7: Hash seed and module state are not currently a problem, but pin and test anyway
**Evidence:** replay probe, current `main` code: 12 seeds x {PYTHONHASHSEED=1, 2} fresh processes, 11 in parallel: 12/12 identical per-frame screen hashes (frames up to 32,808, ending in deaths such as soldier ant, gnome king, magic missile). Same process back to back: seeds 10,2,3,10,2,3 gave the same hashes as the fresh-process runs (`127e6dcfb33e`, `bd90cfc4b46a`, `ecfd53e50882`). `_PRIZES` is only used as `_prize_objects() & set(item.objs)` (`global_logic.py:259,267,488`), a pure intersection; `STRATEGIES` is a dict of frozen `StrategySpec` (`@dataclass(frozen=True)`); the `lru_cache`s in `item_manager.py:271,515`, `objects/utils.py`, `glyph/monster.py`, `utils.py:75` are pure functions of text or ids with `copy_result`.
**Residual risk:** paths not played (Sokoban prize looting is parked behind `strategy="random"`). Defence in depth: pin `PYTHONHASHSEED=0` in the worker environment (`bench/runner.py` line `env = {**os.environ, "PYTHONPATH": str(worktree)}`), cost: one line plus a server restart.

### Pitfall 8: The prayer rule fails 12-23% of the time and failure is silent
See Pattern 3. A failed prayer both removes the safety net and may kill (helpless while praying). Do not assume "prayer is the fix"; measure `starved` and "while praying" deaths together.

### Pitfall 9: The `starved` metric also counts "killed while fainted"
`bench/metrics.py`: `"starved" in g["end_reason"] or "fainted from lack of food" in g["end_reason"]`. Of 280 stored cases only 74 are "starved to death"; the rest are monsters killing a fainted hero (iguana 11, giant ant 11, killer bee 10, rothe 7, rock mole 7). Hunger fixes can look like ant/bee fixes and vice versa; read both metrics for every experiment.

### Pitfall 10: Resting spends the food the starvation fix just saved
See Pattern 4. Gate rests on food and cap turns per level; log `rest_turns`.

### Pitfall 11: Diagnosis data does not exist yet
`GameResult` (`game.py:31-52`) has no messages, prayers, hunger timeline, inventory-at-death or monsters-in-view. Without a behaviour-neutral instrumentation commit, D-09's "classify starvation deaths" can only use `turns`, `max_depth`, `role`, `milestone`, `xp_level`, `stuck_diving`, `unsticks`, `end_reason`. Prove the instrumentation neutral by exact replay (same `turns`/`end_reason`/`rung`/role per seed) against current `main` on 192 seeds before using it as the baseline.

### Pitfall 12: Old-commit or unseeded jobs
Experiments need `run_game(seed=...)` in the candidate; branch commits older than `4af6158` fail the job (Pattern 7).

## Code Examples

### 1. Launching and waiting (MCP and curl fallback)
```text
# MCP (tools registered by .mcp.json)
bench_experiment(candidate="<twin-sha>", baseline="<D-sha>", metric="rung2")   -> {"job_id": N}
# background shell, notifies when done:
uv run screens-bench wait N
```
```bash
# Same through the JSON API (Host must be 127.0.0.1/localhost; POST needs the JSON content type)
curl -s -X POST http://127.0.0.1:8765/api/jobs -H 'Content-Type: application/json' \
  -d '{"kind":"experiment","candidate":"<sha>","baseline":"<sha>","metric":"rung2"}'
curl -s "http://127.0.0.1:8765/api/results?ref=<sha>"            # summary + 17-rung ladder
curl -s "http://127.0.0.1:8765/api/games?ref=<sha>&where=end_reason~starv,max_depth>3&limit=200"
```
`where` clauses are `field=value`, `field>n`, `field<n`, `field~substring` joined by `,` (`bench/filters.py`).

### 2. Determinism edits in `nethack_screensaver/game.py` (sketch, not applied)
```python
# line 152 today: env = NetHackChallenge(no_progress_timeout=1000)
env = NetHackChallenge(no_progress_timeout=1000, fix_moon_phase=seed is not None)
if seed is not None:
    # existing line 155; lgen=seed is optional and untested here (nethack.py:293 accepts it)
    type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False)   # or (..., False, seed)
```
`lgen` makes level generation independent of in-game choices (`base.py:489-491`), which should raise pairing strength; validate by comparing the Dlvl 2 map of two different action sequences before adopting, and re-measure `q` (Pitfall 2).

### 3. MEAS-02 table source
`GET /api/results?ref=<D-sha>` returns `ladder` rows such as `{"rung": 2, "key": "minetown", "hits": 309, "n": 1152, "median_turn": 5347.5, "yardstick_turn": 3538}` (this is the old mixed-strategy `2653410` data, shown only for the shape) [VERIFIED: live API call].

### 4. Paired verdicts for the "rungs 3-6 not worse" check
Submit the same pair per metric; all games are stored so each ends within seconds:
```text
bench_experiment(candidate="<final-main-code-sha>", baseline="<baseline-sha>", metric="rung3")
... "rung4", "rung5", "rung6"
```

### 5. Exact-replay probe (verified to run; used for the findings above)
```python
# one process per (seed, tag); compare the printed hash across runs and PYTHONHASHSEED values
import sys, json, hashlib
sys.path.insert(0, ".")
from dataclasses import asdict
from nethack_screensaver import game
h, n = hashlib.sha1(), [0]
def on_frame(obs):
    h.update(obs["tty_chars"].tobytes()); n[0] += 1
r = asdict(game.run_game(seed=int(sys.argv[1]), watchdog_seconds=120, on_frame=on_frame))
print(json.dumps({"seed": int(sys.argv[1]), "hash": h.hexdigest()[:12], "frames": n[0],
                  "turns": r["turns"], "end": r["end_reason"][:60], "rung": r["rung"]}))
# xargs -P 11 -L1 sh -c 'PYTHONHASHSEED=$2 .venv/bin/python probe.py $0 $1'  for seeds x two hash seeds
```

### 6. Prayer-safety simulation (3.6.6 `rnz`/`rne` transcribed; verified output in Pattern 3)
```python
def rne(x, ul=5):
    t = 1
    while t < ul and random.randrange(x) == 0: t += 1
    return t
def rnz(i):
    x, t = i, (1000 + random.randrange(1000)) * rne(4)
    return x * t // 1000 if random.randrange(2) else x * 1000 // t
# P(safe major-trouble prayer after `gap` turns) = mean(rnz(350) - gap <= 200)
```

### 7. Human-game study access (verified: 15,872 frames in 0.59 s)
```python
import sqlite3, nle.dataset as nld
DB = "/ssd2/nethackFiles/db/nld.db"
ids = [r[0] for r in sqlite3.connect(DB).execute(
    "select gameid from games where version like '3.6%' and maxlvl>=4 and death like '%starv%'")]
ds = nld.TtyrecDataset("nld-nao-aa", batch_size=1, seq_length=512, dbfilename=DB, gameids=ids[:1], shuffle=False)
for mb in ds:                      # mb["tty_chars"]: [B, T, 24, 80]
    top = bytes(mb["tty_chars"][0, 0, 0]).decode(errors="replace")   # message line
```
Messages worth scanning: "You begin praying", "You feel that ... is well-pleased" (success) vs "is displeased" (too soon), "You are beginning to feel hungry", "You faint from lack of food". Table columns available without ttyrecs: `role, race, maxlvl, turns, death, version`.

## State of the Art

| Old approach | Current approach | Changed | Impact |
|--------------|------------------|---------|--------|
| Unseeded independent samples, Newcombe interval | Seeded pairs, Wald paired interval, 99% early / 95% at 1152 | 2026-10-22 (`9ff6a6f`) | Resolution depends on discordance `q`, not yet measured |
| Real-clock NetHack effects | NLE 1.3.0 `fix_moon_phase` derives them from the seed | NLE 1.3.0 (pinned) | Required for cross-day pairing; not yet used by the bench |
| Mixed four-strategy games | Pilgrim-only (`strategy = "pilgrim"`) | 2026-10-21 (`dbab398`) | All earlier numbers not comparable |

**Deprecated/outdated:** `scripts/benchmark.py` (fallback only); `docs/STATUS.md`/`handoff.txt` as status (D-02 replaces them with a pointer).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MAXULEV = 30 in the regeneration formula (turns per HP 15/11/9/8/7/6/5/5/4 at XL 1-9) | Pattern 4 | Rest-time estimates off; harmless to the design |
| A2 | `BOLT_LIM` = 8 (range of lined-up zaps) | Pattern 5 | Off-line avoidance radius wrong |
| A3 | Prayer timeout falls 1 per turn at Luck 0; starting timeout 300 | Pattern 3 | Safety percentages shift; wiki says "safe at turn 301, possible at turn 101" for the first prayer |
| A4 | Discordance `q` of 0.15-0.35 for real experiments (sizing table) | Pitfall 2 | Sample-size guidance off; measure with the divergence control |
| A5 | Some "bolt of lightning" deaths are divine smiting after failed prayers | Pattern 5 | `rays` metric less contaminated than feared |
| A6 | Elbereth does not stop monster wand zaps or breath | Pattern 5 | A wand-user fix via Elbereth might work |
| A7 | Poisonous sting instadeath is 1/30 of poisonings, poisoning 1/8 of hits | Pattern 6 | Poison resistance worth less/more |
| A8 | Friday the 13th / full moon luck effects as described (only the `Luck < 0` clause of `can_pray` was quoted) | Pitfall 5 | Moon fix less valuable, still harmless |
| A9 | `lgen=seed` works with `NetHackChallenge` class-method seeding and improves pairing | Code Example 2 | Extra work for no gain; validate before adopting |
| A10 | Wiki ant/bee pages show NetHack 5.0.0 stats; 3.6.6 values may differ slightly | Pattern 6 | Minor |

## Open Questions

1. **Which metric decides keep/drop for SURV-02..05?**
   - Known: REQUIREMENTS says a seeded paired verdict against the baseline; SURV-06 names `rung2`; PROJECT says each experiment names its own rung metric; per-killer rate metrics exist.
   - Unclear: whether a killer-rate verdict (e.g. `starved` better, `rung2` neutral) is enough to merge.
   - Recommendation: planner fixes the rule up front: keep requires `better` on the targeted rung metric (default `rung2`); killer rates are mechanism evidence. Tell the owner, since a 1-2 point `rung2` effect may stay invisible at 1152 games.
2. **Adopt `lgen`, a 2304 checkpoint, both, or neither?**
   - Unclear until the divergence control gives `q`. Both are small changes but alter every later verdict and need a fresh baseline; do them before the baseline is stored (nothing is stored yet).
3. **Which `threat-model` variant is "the" judged one?** Recommended `fdf6b48`; owner's call (D-12 says "each once").
4. **Does the owner want the divergence control (about 2-3 bench hours: baseline reused, one 1152-game candidate side, plus the `lgen` variant)?** It is the only way to make MEAS-01's intent (can the bench see 1-3 points) real.
5. **Prayer failure detection:** exact NLE message strings for success/failure should be taken from the human ttyrecs (Code Example 7) rather than from memory.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `/ssd2` NLD-NAO data | D-10 human study | ✓ (mounted, 819 GB free) | `nld.db` 39,210 games, dataset `nld-nao-aa` | — (blocker if absent per D-10) |
| Bench server | all experiments | ✓ idle, 11 slots | pid 8876, port 8765 | `uv run screens-bench serve` |
| uv / Python / NLE | runs | ✓ | 0.12.10 / 3.13.15 / 1.3.0 | — |
| git | branches, worktrees | ✓ | 2.55.0 | — |
| sqlite3 CLI | diagnosis queries | ✓ | 3.53.4 | Python `sqlite3` |
| CPU | 11 workers | ✓ | 12 cores | — |
| libfaketime | testing clock dependence | not checked | — | Reason from `fix_moon_phase` seeds (done) |

**Missing dependencies with no fallback:** none. **With fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8 (`pyproject.toml`, `testpaths = ["tests"]`, `addopts = "-m 'not slow'"`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`; slow marker "plays real games (minutes)"; `filterwarnings = ["error:overflow encountered:RuntimeWarning"]` |
| Quick run command | `uv run pytest -q` (excludes slow) |
| Full suite command | `uv run pytest -q -m ""` (116 s this session, green) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MEAS-01 | A/A verdict reads "no measurable difference" at 1152 | bench job (manual run, evidence = job result JSON) | `uv run screens-bench wait <id>` | n/a |
| MEAS-01 | Same-commit refusal and paired-interval math | unit | `uv run pytest -q tests/test_bench_stats.py tests/test_bench_server.py` | ✅ |
| MEAS-02 | Baseline stored and table written | bench + doc check | `curl -s ".../api/results?ref=<sha>"`; grep PORTING.md for the table | ❌ Wave 0 (doc step) |
| MEAS-03 | Seed replays frame-for-frame: fresh process, other hash seed, same process A,B,A | slow integration | `uv run pytest -q -m slow tests/test_replay.py` | ❌ Wave 0 |
| MEAS-03 | Seeded game uses `fix_moon_phase`; unseeded does not | unit (monkeypatch `NetHackChallenge`) | `uv run pytest -q tests/test_game.py -k moon` | ❌ Wave 0 |
| MEAS-03 | Sokoban solver ignores wall-clock in bench mode | unit | `uv run pytest -q tests/test_soko_search.py` | ✅ (extend) |
| SURV-01 | Rest trigger fires/doesn't fire (HP, food, monsters, turn cap) | unit with `SimpleNamespace` fakes | `uv run pytest -q tests/test_rest.py` | ❌ Wave 0 |
| SURV-02 | Prayer gating and failure detection | unit | `uv run pytest -q tests/test_prayer.py` | ❌ Wave 0 |
| SURV-03 | Off-line step / zapper handling | unit | `uv run pytest -q tests/test_fight_heur.py` | ✅ (extend) |
| SURV-04 | New ant/bee tactic | unit | `uv run pytest -q tests/test_fight_heur.py` | ✅ (extend) |
| SURV-05 | Rebased branches still pass their own tests | unit | `uv run pytest -q -m ""` on the rebase branch | ✅ (`tests/test_threat.py`, `test_flee_upstairs.py`, `test_choke_points.py` live on the branches) |
| SURV-06 | Paired `better` on `rung2`; rung3-6 not `worse` | bench jobs (5 judgements) | MCP `bench_experiment(..., metric="rungN")` | n/a |

### Sampling Rate
- **Per task commit:** `uv run pytest -q` (quick) plus the touched test file.
- **Per behaviour change before a bench job:** `uv run pytest -q -m ""` green, then 192-seed exact-replay check for behaviour-neutral commits.
- **Per bench job:** read `job.result.verdict`; check `crashes` in `bench_results` for new exception types ("no new exception types in a 576-game run").
- **Phase gate:** full suite green and the SURV-06 judgements recorded in PORTING.md before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_replay.py` (slow): play seeds twice (fresh process via subprocess with different `PYTHONHASHSEED`; same process A,B,A) and compare per-frame hash plus result fields; covers MEAS-03.
- [ ] `scripts/replay_check.py`: compare two SHAs' stored games per seed (turns, end_reason, rung, role) from `Store.games_by_seed`; covers MEAS-01/03 evidence and instrumentation neutrality.
- [ ] unit tests for `fix_moon_phase` wiring and the Sokoban deadline switch.
- [ ] per-fix unit tests (rest, prayer, wand off-line step) written with the change; fake pattern: `SimpleNamespace(mname=...)` tuples as in `tests/test_fight_heur.py`.
- Framework install: none.

## Security Domain

`security_enforcement` is not set in config (no `.planning/config.json`), so it is treated as enabled. The phase adds no network surface; it uses a localhost-only server.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local single-user server; DEBT-01 (token) is deferred |
| V3 Session Management | no | — |
| V4 Access Control | partial | `Handler._refused()` allows only Host 127.0.0.1/localhost and JSON content type for writes (`server.py:169-178`) |
| V5 Input Validation | yes | Filter clauses validated by regex (`bench/filters.py`); refs resolved by git (`gitrefs.resolve`); metric names checked against `METRICS` |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Foreign web page posting jobs to localhost | Tampering | Existing Host / Content-Type checks; do not weaken when editing `bench/server.py` |
| Worker running arbitrary commit code | Elevation | Only own commits are run; do not point jobs at refs from untrusted sources |
| Branch deletion losing work | Repudiation/loss | Log SHA in PORTING.md before `git branch -D` (D-13); stashes keep `survival-tuning` experiments |

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` and no project skills exist. Binding directives come from PROJECT.md, CONTEXT.md and the owner's standing rules (treated with the same authority):
- Git is local only: never push, add remotes or open PRs; finished, tested branches merge to `main` locally without asking.
- One change per experiment; every behaviour change judged on the seeded paired bench against a stored pilgrim-only baseline; "no measurable difference" is not a win; log verdicts and dropped ideas in `autoascend/PORTING.md`.
- `uv run pytest -q -m ""` green before and after each change; no new exception types in a 576-game run.
- `bench/worker.py` imports nothing from `bench`; `autoascend/ladder.py` stays standard-library only; a ladder error never ends a game.
- Agent logic stays as upstream except deliberate, measured changes.
- Do not retry dropped ideas without a new approach (Elbereth resting, waiting for peacefuls, hidden-passage search, digging down, boulder pushing, doorway fighting, threat numbers, flee-upstairs), except SURV-05's single re-judgement.
- Cheesy tactics allowed; an exciting deep run that dies beats a boring escape.
- D-01/D-02: status lives in `.planning/STATE.md`; `docs/STATUS.md` and `handoff.txt` become a pointer (a task in this phase; the resulting docs-only commit is the natural A/A twin).

## Sources

### Primary (HIGH confidence)
- Repository files read this session: `bench/{server,scheduler,stats,store,metrics,filters,report,runner,worker,cli,mcp_server}.py`, `nethack_screensaver/game.py`, `autoascend/{agent,global_logic,plans,env_wrapper,ladder}.py`, `autoascend/combat/{fight_heur,monster_utils}.py`, `autoascend/soko_solver/search.py`, `autoascend/PORTING.md`, `docs/superpowers/specs/{2026-10-21-seeded-bench-design,2026-10-20-bench-server-design}.md`, `.planning/{PROJECT,REQUIREMENTS,STATE}.md`, phase `01-CONTEXT.md`.
- NLE 1.3.0 installed package: `nle/env/base.py` (seed, `fix_moon_phase` docs), `nle/nethack/nethack.py` (`set_initial_seeds`), `nle/env/tasks.py` (`NetHackChallenge`), `nle/dataset/*`.
- Probes run this session: replay (12 seeds x 2 hash seeds; same-process sequence), `fix_moon_phase` (4 seeds, 576-seed distribution), `nld.db` queries and a ttyrec decode, `results.db` queries, `git merge-tree` dry runs, full test suite.

### Secondary (MEDIUM confidence)
- NetHack 3.6.6 C source via raw.githubusercontent.com (fetched through a summarising fetcher; quotes are the fetcher's verbatim excerpts): `src/pray.c`, `src/muse.c`, `src/mthrowu.c`, `src/eat.c`, `src/rnd.c`, `src/allmain.c` (header said 3.6.2-beta01).
- NetHack wiki: Prayer, Nutrition, Soldier ant, Killer bee, Wand of striking (https://nethackwiki.com/wiki/...). `classify-confidence` rates the fetch provider LOW, so strategy claims from these pages stay advisory.

### Tertiary (LOW confidence)
- WebSearch for "lined up" monster wand rules returned nothing usable; the rule comes from the C source above.

## Metadata

**Confidence breakdown:**
- Standard stack / bench mechanics: HIGH — code read and exercised.
- Determinism findings: HIGH for fresh-process and same-process replay on 12 and 3 seeds; MEDIUM for completeness (Sokoban and clock paths not exercised end to end).
- NetHack mechanics: MEDIUM — source excerpts through a summariser.
- Effect predictions for the four killers: LOW — to be settled by the experiments.

**Research date:** 2026-10-22
**Valid until:** 2026-11-21 for bench mechanics (stable code); re-check NLE behaviour only if the pin changes.
