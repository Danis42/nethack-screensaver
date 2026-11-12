# Phase 1: Measurement and Proof Foundation - Context

**Gathered:** 2026-11-12
**Status:** Ready for planning

<domain>
## Phase Boundary

The owner can check every progress number against a fresh, reproducible natural-game funnel of `main`,
and claims without proof are rejected automatically. Covers MEAS-01..MEAS-10: reproducible NLE install,
natural-game funnel with Wilson intervals (replacing `rung` for decisions), `sokoban_solved` detector check,
`lgen` pilot, fresh baseline + A/A, valid paired sequential stats with declared MDE, dev/confirm/final seed
ranges, separate `tool_games` table, claim checker, and fact ledger.

Already fixed by requirements (not re-discussed): exact McNemar + always-valid sequential test validated by
simulation; `lgen` pilot of two commits x ~400 seeds, decision driven by measured discordance.

</domain>

<decisions>
## Implementation Decisions

### NLE reproducibility (MEAS-01)
- **D-01:** The NetHack 5.0 NLE fork (branch `screens-nh5`, 21 commits on upstream NLE `70cb9b526`, a ~388k-line diff — too large for a patch series) moves into a **local bare git repo at `~/git/nle-screens.git`**. Nothing is pushed to GitHub or any remote. — **Reversibility:** reversible — repo can later be pushed anywhere.
- **D-02:** `pyproject.toml` depends on it as a **uv git dependency pinned to a commit SHA** (e.g. `nle = { git = "file://$HOME/git/nle-screens.git", rev = "<sha>" }`), replacing the `path = "reference/nle-src"` source. `uv.lock` records the exact NLE commit; every bench job records NLE commit, lock hash and full bot SHA (success criterion 1).
- **D-03:** "Fresh clone" means a fresh clone of screens **on this machine** (the bare repo is a local path). Off-machine reproducibility is not a goal.
- **D-04:** **No off-disk backup step.** Owner accepts the risk that the fork exists only on this disk (verified: neither `archive/screens-v0-final.tar.gz` nor `archive/screens-all-branches.bundle` contains `nle-src`). Record this risk; don't add backup tooling.
- `reference/nle-src` has an untracked `paniclog`; the fork's working tree must be clean/committed before the SHA is pinned.

### Baseline, A/A and seed ranges (MEAS-05, MEAS-07)
- **D-05:** Fresh natural baseline of `main`: **10,000 games** on dev seeds (~7 h unattended at ~25 games/min on 10 slots).
- **D-06:** A/A rerun: **2,000 seeds, a subset of the baseline seeds**; must show identical per-seed results.
- **D-07:** Seed ranges: **dev 0–99,999 · confirm 100,000–199,999 · final 1,000,000+**. Confirm seeds only at phase gates; final seeds only for clean attempts — the bench refuses final-range seeds otherwise. — **Reversibility:** costly — once games are stored on these ranges, moving boundaries invalidates the separation guarantees.
- **D-08:** **Interrupted jobs become resumable**: on server restart, a job marked `interrupted` (`Store.interrupt_unfinished`) can be resumed and plays only the seeds not yet stored. Supports multi-hour baseline runs surviving reboots.
- Context given to owner: the bench server (`uv run screens-bench serve`) runs jobs unattended; Claude only submits via MCP and receives a job ID.

### Claim checking (MEAS-09)
- **D-09:** `check_claims.py` checks **Claude's replies to the owner**, run by a **Claude Code Stop hook** on the final message of each turn. Commit messages and planning docs are not checked by it.
- **D-10:** Cited proof is **verified to exist**, not just format-matched: job ID looked up in `results.db`; a "started" claim requires the job's first game row to exist; a commit hash must resolve in git (full hash); a cited query is re-run.
- **D-11:** On failure the hook **blocks** the reply; Claude must add proof or drop the claim.

### Fact ledger (MEAS-10)
- **D-12:** Scope: all existing NetHack facts in `.planning/research/*.md` and in code (`autoascend/`, constants, thresholds, rules) get tagged, plus every new fact from then on. **Revised 2026-11-12 by D-20:** Phase 1 delivers the tooling and a first time-boxed tranche; the rest continues tranche by tranche.
- **D-13:** Tags: `5.0-source` (with file:line in `reference/nethack-5.0.0/` or the NLE fork), `measured` (with job ID/query), or `unverified`.
- **D-14:** **Web research step**: facts **not confirmed in the 5.0 source** get a web search (NetHackWiki, forums, bot write-ups) for extra context or better information; sources found are recorded in the entry. Facts already confirmed in 5.0 source skip it. Web material often describes 3.6 — note differences; **the 5.0 source wins on conflict**.
- **D-15:** Format: **one ledger file** (e.g. `.planning/FACTS.md` or a structured TOML/YAML file) with one entry per fact (id, claim, tag, evidence, web sources); code cites facts by ID (e.g. `# fact:prayer-timeout`); a test checks every cited ID exists in the ledger.
- **D-16:** Bot code **may use unverified facts**, but a report lists every unverified fact the bot depends on.

### Owner decisions at plan-phase (2026-11-12, from RESEARCH.md open questions)
- **D-17:** Seeds **0–999 are a reserved tool-seed block** (rewind, staged, scenario, hand games) and are never judged. The natural baseline runs on dev seeds **1,000–10,999**; the A/A subset is drawn from those. This refines D-05/D-07; the D-07 range boundaries are unchanged.
- **D-18:** If `check_claims.py` **itself crashes**, the Stop hook **exits 0 (passes) and writes the crash loudly to an audit log**. A claim that fails its check is still blocked (D-11 unchanged for real failures).
- **D-19:** The success-criterion-1 fresh-clone proof run: **stop the live server briefly, run the fresh clone's server against the live `--data` dir on a spare commit, then restart the live server**, so the job ID resolves in the live `results.db`.
- **D-20:** Fact ledger in Phase 1 = **tooling + tranches**: ledger format, ID-citation test, unverified-dependency report and a coverage report, plus a **first time-boxed tranche** (the planning research notes and the most-used bot modules). Remaining facts are tagged in later tranches, with coverage tracked by the report.
- **D-21:** *(owner answer to plan-phase question, 2026-11-12)* The funnel gets a separate **`quest_portal` stage** with its own detector (magic portal found or entered), placed before the existing `quest` stage (entered Home 1). MEAS-02's "Quest portal" maps to `quest_portal`, not `quest`.
- **D-22:** *(owner answer to plan-phase question, 2026-11-12)* Confirm-seed authorisation = a required **`gate` field** naming the phase gate; a confirm-range job without it is refused. No owner token (owner judged the gate field enough).
- **D-23:** *(orchestrator default, not asked; owner may override — it only keeps current behaviour)* Games stay keyed by **commit sha**; the baseline names its sha explicitly (RESEARCH Pitfall 6). Keying by bot-tree hash is deferred (see Deferred Ideas).

### Claude's Discretion
- Depth of the per-fact web research (left to Claude's judgement by the owner).
- Ledger file format details (Markdown vs TOML/YAML), fact-ID naming.
- How the Stop hook detects a progress claim (should be deterministic — e.g. pattern-based — not an LLM).
- Funnel report presentation (dashboard/CLI/MCP) and `tool_games` schema details.
- Statistical implementation details within MEAS-06.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` §"Phase 1: Measurement and Proof Foundation" — goal, 5 success criteria, research flags
- `.planning/REQUIREMENTS.md` §"Measurement and Proof (MEAS)" — MEAS-01..MEAS-10
- `.planning/PROJECT.md` — core value, constraints (determinism, proof, no extra cost), key decisions

### Codebase maps
- `.planning/codebase/ARCHITECTURE.md` — bench layer, worker protocol, determinism
- `.planning/codebase/CONCERNS.md` — NLE gitignored install problem, other known issues
- `.planning/codebase/TESTING.md` — test conventions

### Prior measurements and research to tag / reconcile
- `.planning/research/PITFALLS.md` — throughput (~1500 games/h), sequential-testing and power notes
- `.planning/research/SUMMARY.md` — research summary (contains UNVERIFIED marks)
- `.planning/research/LADDER-NH5.md` — ladder/rung definitions behind the funnel stage keys
- `.planning/research/*.md` — all notes are in fact-ledger scope (D-12)
- `reference/nethack-5.0.0/` — 5.0 source, authority for `5.0-source` tags

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bench/stats.py`: `wilson`, `newcombe`, `judge_paired` — Wilson intervals exist; sequential test and exact McNemar are new.
- `bench/metrics.py`: `METRICS` registry incl. `rung`/`rungN` — funnel metric replaces `rung` for decisions.
- `autoascend/ladder.py` `RUNGS` + `GameResult.ladder` (dict of rung key -> first turn, `nethack_screensaver/game.py:66`) — per-game stage keys already recorded; funnel can be computed from them.
- `GameResult.stage` (`game.py:82`) — staged games already flagged; basis for routing to `tool_games`.
- `bench/store.py`: `games_by_seed`, `interrupt_unfinished` — seed lookup supports resume (D-08).
- `bench/mcp_server.py`: MCP tools (`bench_baseline` etc.) — how Claude submits jobs.
- `scripts/rewind.py` uses NLE `set_current_seeds(..., lgen)` — fork commit `cb9d6572f` adds lgen semantics.

### Established Patterns
- Scheduler plays seeds `0..N-1` per job (`bench/scheduler.py` docstring) — must change to explicit seed ranges (D-07).
- `start_baseline` default is 576 games (`bench/server.py:33`).
- Worker must not import `bench` (old commits lack it).
- `PYTHONHASHSEED=0` and single-thread BLAS for determinism (`bench/runner.py`).

### Integration Points
- `pyproject.toml` `[tool.uv.sources]` — NLE source switch (D-02).
- `.claude/settings.json` (not present yet; only `settings.local.json`) — Stop hook for claim check (D-09).
- `~/.local/share/screens-bench/results.db` — live DB, currently empty; bench server currently running (PID seen during discussion).

</code_context>

<specifics>
## Specific Ideas

- Owner wants facts never taken as-is: a light web-research pass for more context/better information (D-14).
- Multi-hour runs happen unattended (overnight); the bench must not depend on a Claude session being open.

</specifics>

<deferred>
## Deferred Ideas

- Off-disk backup of the NLE fork and screens repo (bundle to another drive or private mirror) — declined for now; risk accepted.
- Checking commit messages and planning docs with the claim checker — not chosen; could be added later.
- Keying bench games by bot-tree hash instead of commit sha (avoids re-baselining after docs/bench-only commits) — not required by MEAS; revisit before Phase 2 (D-23).

</deferred>

---

*Phase: 01-measurement-and-proof-foundation*
*Context gathered: 2026-11-12*
