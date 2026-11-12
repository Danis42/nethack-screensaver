# Pitfalls Research

**Domain:** Rule-based NetHack bot (AutoAscend lineage) aiming at one clean ascension of NetHack 5.0 via a local NLE build, benchmarked in bulk, developed with an AI coding assistant
**Researched:** 2026-11-12
**Overall confidence:** MEDIUM-HIGH. Claims drawn from this repo (git history, bench stats code, research notes, NetHack 5.0 source in `reference/`) are HIGH. Claims about outside projects come from one fetched page each and are tagged LOW or MEDIUM per the classify-confidence seam (web-only = LOW unless a second source or local data agrees).

**Honest gap:** I found no post-mortem written by the BotHack, TAEB or AutoAscend authors explaining why their bots plateaued. The "plateau" evidence is indirect: Damerell's pre-bot essay on special-case growth, the BotHack README milestone log, the NeurIPS 2021 challenge report, and this project's own history (the strongest evidence, and the most relevant).

Phase names below are provisional. Mapping used throughout:

| Tag | Provisional phase |
|-----|-------------------|
| P1 | Foundation: reproducible install, proof guards, fresh baseline of `main` |
| P2 | Measurement protocol and deterministic regression gate |
| P3 | Route decision (evidence comparison, LLM role decided) |
| P4 | Early wall by system (food, HP/escape, stuck, items) |
| P5 | Modularization of `agent.py` / `global_logic.py` (can interleave with P4, gate first) |
| P6 | Late-game abilities (Medusa, Castle, Quest, Gehennom, invocation, Planes) |
| P7 | Clean ascension attempts |

---

## Critical Pitfalls

### Pitfall 1: Special-case pileup (per-monster whack-a-mole)

**What goes wrong:** Each death cause gets its own branch (unicorn, mimic, energy vortex, minotaur, watch, gas spore...). Branches interact, priorities conflict, the death-cause histogram grows a longer tail than it loses, and the code becomes unreadable. Progress stalls at the same wall.

**Why it happens:** It is the cheapest visible fix: one bad seed, one patch, one green re-run. It feels like progress because the named killer disappears. The killer table is a long tail, so the next 20 killers are ready. Damerell (pre-bot essay) names the mechanism: a NetHack bot must not "treat decisions as independent", because "the number of special cases grows quickly" ([nhbot.txt](https://www.chiark.greenend.org.uk/~damerell/games/nhbot.txt), LOW: single source).

**Evidence here (HIGH):**
- 511 commits in 28 days (2026-10-16 to 2026-11-12). 273 (53%) are `docs`/`state`/`research`; 142 (28%) are `feat`/`fix`/`exp`/`port`. 34 commit subjects say "dropped", "no difference" or "not passed".
- `agent.py` changed in 46 commits, `global_logic.py` in ~47 (CONCERNS.md).
- Top killers at XL 6-9 are spread across mumak 40, soldier ant 31, white unicorn 26, owlbear 25, leocrotta 22, black unicorn 11 (SURVIVAL-NH5.md). Fixing one removes about 2-3% of games.
- "Elbereth written 3019 times in 1152 games, then ~25,000 turns of waiting on it": one local rule that is net-negative when it interacts with another.
- 33 of 155 deaths to the six top killers happened with Elbereth under the hero (SURVIVAL-NH5.md).

**How to avoid:**
1. Classify each death into a system class first (passive damage, ranged-only, speed mismatch, Elbereth-ignorer, status ailment, food, getting stuck, item misuse). A fix is allowed only if it implements or extends a class rule driven by monster flags or `monst.h` data, not by monster name.
2. Monster and item knowledge lives in data tables (generated from the 5.0 source), not in `if species == ...` branches. Add a lint or grep check that fails on new species-name literals in decision code.
3. Rule budget: any new rule must come with (a) a scenario test reproducing the decision, (b) a decision-trace line so it can be seen firing, (c) a funnel or class-level measurement. Rules that never fire in 1000 games get deleted.
4. Single arbiter for priorities (strategy preemption with declared preconditions), and a test that lists which strategies can fire together.

**Warning signs:** Commit subjects containing a monster name; fix commits whose measurement is a single seed; the killer histogram's top-10 share not shrinking; `agent.py` growing; "dropped" experiments piling up.

**Phase to address:** P2 (class taxonomy and trace logging), P4/P5 (enforce during rebuild).

---

### Pitfall 2: Fixing the early wall forever while the late wall is a missing ability

**What goes wrong:** Survival work feels endless (24% never reach the Mines, 25% starve), but even perfect survival does not reach the end game. The bot never gets the abilities needed to pass Medusa, enter the Castle, go through Gehennom, run the invocation, cross the Planes.

**Evidence (HIGH):** Rewind study with infinite lives on 20 seeds: 68% of deaths saved by a 100-turn reroll, yet best seed reached Medusa's level at T17317 and no seed passed her (REWIND-20.md). No natural game among 146,743 stored passed Medusa. BotHack's own milestone log says item handling "will need to be implemented before the bot can progress further" past Medusa and records that early bots "usually get killed for lack of combat tactics" ([BotHack README](https://github.com/krajj7/BotHack), LOW).

**How to avoid:** Run two tracks with separate owners and metrics. Track A, survival, measured by the natural funnel. Track B, a capability checklist (keystone items and abilities from ASCENSION-PLAYBOOK-NH5.md: pick-axe, reflection, levitation, telepathy, blindfold, instrument, magic resistance, Bell/Candelabrum/Book), each with a standalone test that proves "the ability works when its precondition is given". Do not allow Track B to be declared done from staged pass rates alone (Pitfall 6).

**Warning signs:** Roadmap contains only P4-type phases until "the survival numbers are good"; late-game rows in the playbook still say MISSING after two phases.

**Phase to address:** P3 (route decision names the abilities), P6.

---

### Pitfall 3: Prior art does not transfer to 5.0 (and "ascension exists" is weak evidence)

**What goes wrong:** Planning assumes someone already did this. Every cited ascension used an older game or a different character or a different harness.

**Evidence:**
- No bot ascended in the NeurIPS 2021 challenge: over half a million evaluation games, top median score about 5000, no ascension ([challenge report](https://nethackchallenge.com/report.html), LOW-MEDIUM; corroborated by the R14 notes).
- BotHack's January 2015 ascension was on a public server (acehack.de) in an older NetHack, depended on "pudding farming" and an early wizard-mode phase ([BotHack README](https://github.com/krajj7/BotHack), [wiki Bot](https://nethackwiki.com/wiki/Bot), LOW-MEDIUM). Pudding farming is an exploit route; its status in 5.0 is **UNVERIFIED** here and must be checked in the 5.0 source before it enters any plan.
- The one reported LLM ascension (`nethack_astra`, GPT-6 Astra) was NetHack **3.6.7** on Hardfought, a **dwarven Valkyrie**, 37,140 turns, **run 3 of 3** (run 1 died on DL51 at turn 33,302, run 2 died to a death ray at the Castle at turn 12,271), sessions spanning Sept 9-21 with pauses and "saved-game resumptions", spoilers and web access allowed, about USD 300 extra credits on a USD 200/month plan ([run report](https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/), LOW: single source). Our target is NetHack 5.0 with a neutral human Valkyrie.
- AutoAscend won on score in NetHack 3.6.6, not by ascending. Its Excalibur strategy and Sokoban data are 3.6-era (Pitfall 20).
- Human reference data is 72 NLD-NAO 3.6 ascensions (ttyrecs) plus 199 Hardfought 5.0 dumplogs with end-state only, winners only (SURVIVAL-NH5.md, MEDUSA-NH5.md). Survivorship bias is built in: they show what winners carry, not how often carrying it is enough.

**How to avoid:** Treat prior art as architecture inspiration only. Record in the route decision which claims were verified on 5.0 (source line) and which are inherited. Never use a 3.6 human median as a "stage requirement" without remeasuring on bot games.

**Warning signs:** A plan step citing "BotHack did X" with no 5.0 source line; stage requirements copied from the human tables.

**Phase to address:** P3.

---

### Pitfall 4: Staged results mistaken for natural transfer (the "castle 8/20" trap)

**What goes wrong:** A skill passes 8/20 from a staged start next to the Castle. The team believes the Castle is nearly solved. The natural game never gets there.

**Why it happens:** Staged starts hand the bot the kit, HP, XL, level and position that natural play almost never delivers, and 20 seeds is a tiny sample (Pitfall 5). The funnel multiplies: P(ascend) = product of per-stage conditional rates. Only 1.1% of natural games reach Medusa's level (13 of ~1152; Wilson 95% CI 0.7%-1.9%), so a perfect Castle skill still yields about 1% reaching the Castle unless upstream stages improve.

**Evidence (HIGH):** The git log shows decisions made on staged counts ("castle staged 0/20 -> 5/20 -> 8/20", "float-past dropped (castle 7/20 vs 8/20)", "quiet-float dropped (9/20 vs 8/20)"). The staged kits were set at the human median ("stage: Medusa kit at the human median AC (-14)"), which the natural bot does not reach (AC stops around -3/-4).

**How to avoid:**
1. The primary metric is the natural funnel: per-stage reach and conditional pass rates with Wilson CIs on natural games from turn 1. Staged and rewind runs are labelled "capability tests" and may only support "the mechanism works at all" or "the mechanism regressed", never a rate.
2. Build the staged start distribution from natural snapshots at stage entry (a snapshot recorder already exists: `feat/game-snapshots`, "record hero snapshots per depth, rung and end of game"). Stage from what the bot actually has, not from the human median.
3. Report the arrival rate next to every staged pass rate ("reaches Castle 0.4% naturally, passes 40% when staged").

**Warning signs:** A result line with a fraction of 20 and no natural-funnel number; a stage requirement derived from human tables; roadmap success criteria phrased in staged terms.

**Phase to address:** P2 (metric definition), P6 (enforce for every ability).

---

### Pitfall 5: Small samples and decisions inside the noise

**What goes wrong:** Keep/drop decisions on 20 seeds or on 1-2% events. Tiny differences flip the verdict.

**Evidence (HIGH, computed here):**
- Staged "5/20 -> 8/20" on the Castle: Fisher exact two-sided p = 0.50. "7/20 vs 8/20": p = 1.0. 0/20 -> 10/20 (Medusa): p = 0.0004, genuinely real.
- 8/20 has a Wilson 95% CI of 22%-61%.
- At n=1152 per arm, the smallest detectable difference (80% power, alpha .05) is about 5.0 points for a 25% rate (starvation), 4.1 points for a 14% rate, 1.2 points for a 1.1% rate (Medusa reach), i.e. you cannot see anything smaller than a doubling at Medusa with 1152 games.
- 0 ascensions in 146,743 games: the rule-of-three 95% upper bound is about 2.0e-5. The ascension rate cannot be optimised directly; only funnel stages can.

**How to avoid:** Decide the effect size that matters before running (the minimum detectable effect), compute the needed games from that, and refuse to read a result at lower n. Use the bench's existing Wilson/Newcombe code (`bench/stats.py`) for every claim. For rare stages, use stage-conditional designs: stage start from natural snapshots (Pitfall 4) so the stage has enough samples, but report the product.

**Warning signs:** "dropped"/"kept" on a delta smaller than the interval; the word "trend"; verdict texts without n.

**Phase to address:** P2.

---

### Pitfall 6: Multiple comparisons, peeking and the winner's curse

**What goes wrong:** Dozens of experiments (exp 21-39+, jobs 69-92) each judged at 95% on the same seeds and the same few metrics. The "kept" ones are biased upward, merged on top of each other; the real cumulative effect is smaller than the sum.

**Evidence:**
- The bench uses 99% intervals at early checkpoints (192/384/576/1152) and 95% at 2304 (`bench/stats.py`, `z_for`). This is an ad-hoc correction, not a valid sequential design.
- Probability of at least one false "win" in 20 independent 95% tests is 64%, and 87% in 40 tests (computed here).
- Reported result in the log: "job 75 no difference, item-skills merged"; "job 82 ... experiment dropped": decisions bundled with qualitative reasons, which is the forking-paths pattern.
- Outside support: Agarwal et al. argue point estimates from 3-10 runs mislead and recommend stratified bootstrap CIs and interquartile means ([arXiv 2108.13264](https://arxiv.org/pdf/2108.13264), LOW-MEDIUM; applied here by analogy).

**How to avoid:**
1. One primary metric per experiment, named before the run (stored with the job). All others are descriptive.
2. Fresh-seed confirmation: dev seeds vs test seeds are disjoint ranges; a change is merged on dev evidence and only counted as improvement after the test seeds say so. Test seeds are used once per candidate.
3. Re-baseline: every K merges (say 5), run the merged head against the commit K merges ago on fresh seeds. If the sum of "kept" deltas is not visible, the merges were noise.
4. Control family-wise error across a milestone: Holm or Benjamini-Hochberg over the experiments reported in the milestone summary.

**Warning signs:** More than ~10 experiments per milestone with no re-baseline; the same 20-seed set appearing in many verdicts; "no-harm gate" used as a permission slip for anything that does not significantly fail.

**Phase to address:** P2.

---

### Pitfall 7: Determinism is not variance reduction, and the bench does not isolate level generation

**What goes wrong:** "A/A is identical, so seed N is the same game across commits." It is only the same game until the first behavioural difference. After any change, the core RNG is consumed differently, so later levels, monsters and item rolls differ. Outcomes become independent noisy draws, and "paired by seed" buys much less than assumed.

**Evidence (HIGH):**
- The bench seeds with `set_initial_seeds(env.nethack, seed, seed, False)` (`nethack_screensaver/game.py:317`), i.e. core and display seeds only; no `lgen`.
- The local NLE build supports `lgen`: "lgen allows the user to use a different RNG to generate the levels ... so that the levels become fixed and independent from the in-game choices" (`reference/nle-src/nle/env/base.py:489`).
- The project's own staged runs saw the effect: "the extra wishes change the RNG, so seed 1 became map 2" (MEDUSA-NH5.md).

**How to avoid:** Try `lgen=seed` in the bench: it fixes level layouts per seed across commits. (**Verify** in the local build that item/monster creation at level creation also uses it; monster generation during play will still diverge.) Keep A/A as a reproducibility test (same commit, same seeds, bit-identical), not as a variance estimate. For variance, run A/A with different seed sets.

**Warning signs:** Paired tests reporting very small SE where unpaired would not; a "seed N regressed" story used as evidence about code.

**Phase to address:** P2.

---

### Pitfall 8: Seed-set overfitting and metric gaming (Goodhart)

**What goes wrong:** The same seeds 0-19 are used for rewind, staged tracks, scenarios and hand games; fixes quietly specialise to their layouts. Separately, a metric like "rung reached" or "max depth" can be moved by strategies that do not make the bot stronger (diving, camping).

**Evidence:** REWIND-20.md and staged tracks use seeds 0-19. The challenge organisers note score and ascension "are not always aligned" and that entrants "camped" early to farm score ([report](https://nethackchallenge.com/report.html), LOW-MEDIUM). Local: `DIVE` milestone ends 261 games after 2500 stuck turns; "divers from Dlvl 21 dig down on arrival (past Medusa)" is a track that raises depth without raising strength.

**How to avoid:** (1) Seed ranges are named and reserved: dev, confirm, final. Rewind/staged/scenario seeds are never used for judging a rate. (2) Pair every depth-like metric with a strength gate (XL, AC, HP at stage entry) and a survival metric after entry ("alive 2000 turns after arriving"). (3) The final ascension attempts use seeds never used before.

**Warning signs:** The same seeds appearing in documents of different purposes; depth rising while XL/AC at the same depth falls.

**Phase to address:** P2, P7.

---

### Pitfall 9: Stale or empty baseline and silent environment drift

**What goes wrong:** The live bench DB has 0 games. Comparing a new run against archived numbers (146,743 games over 87 commits, produced with unknown NLE state and bot versions) hides environment drift: NLE build, `LD_PRELOAD` fixed clock, Python/numba versions, per-commit code.

**Evidence (HIGH):** PROJECT.md "Live bench database is empty"; CONCERNS.md: NLE built from gitignored `reference/nle-src`, `numba>=0.61` loose pin, hard-coded interpreter path in `.mcp.json`.

**How to avoid:** First task: baseline `main` (>= 2304 games, with an A/A rerun at the same size) before any change. Store NLE commit hash, `uv.lock` hash, game version string and bot commit with every job; refuse comparisons when those differ. Pin numba exactly where tests cover kernels. Make a fresh clone installable (publish the `screens-nh5` NLE branch as a git source or document the build).

**Warning signs:** A comparison citing the archive; "it ran on my machine" install steps.

**Phase to address:** P1.

---

### Pitfall 10: Crashes, aborts and timeouts counted wrongly or swallowed

**What goes wrong:** `except Exception` and bare `except:` hide errors (CONCERNS.md lists `nethack_screensaver/game.py` lines 119-398, `global_logic.py` 555 and 724, bare `except:` in `item_manager.py:195`). Games that crash, abort (no-progress timeout) or hit the watchdog are excluded or counted as ordinary deaths, which flatters or distorts rates.

**Evidence:** Rewind study: of 20 seeds, 4 ABORTED (the bot stops acting), 2 crashed (Cyclic Panic assertion); end-cause tables show "crash 25/6/9/7" per rung; 12 "watchdog" ends are the bench timeout, not the Watch (LADDER-NH5.md).

**How to avoid:** Every game ends with exactly one of: ascended, died(cause), crashed(traceback hash), aborted(no-progress), timeout. The funnel denominator is all started games; crashes and aborts count as failures at the stage where they happen. Stage-level failure reports always show these classes separately. Replace swallow-all handlers with narrow ones that log a traceback to the job record.

**Warning signs:** A stage rate that rises when crashes are filtered; tracebacks in `player.log` that no one reads.

**Phase to address:** P2, P5.

---

### Pitfall 11: LLM in the game loop cannot be benchmarked at this scale

**What goes wrong:** A call per decision, or even per hundred turns, makes bulk benchmarking prohibitive, adds latency, and makes experiments non-reproducible. Game length is 15-25k turns (rung tables show median 13-16k turns at the deeper rungs).

**Evidence and arithmetic:**
- Rough estimate (mine, LOW): one call every 50 turns at ~4k input tokens is ~400 calls and ~1.6M tokens per game. The bench plays 1152-2304 games per experiment. That is hundreds of millions to billions of tokens per verdict. Per-call latency and USD for NetPlay/astra are **UNVERIFIED** in the published sources.
- Published anchors: CodeHack reports estimated USD 4.35 (primitive-only), 1.36 (mixed), 0.59 (skill-only) per episode and 6.72M / 3.54M / 1.74M tokens per episode, with skills nearly tripling progression (0.69 to 1.98) ([arXiv 2609.31076](https://arxiv.org/abs/2609.31076), from R15 notes; the paper itself was not opened, LOW). Episodes there are short relative to a full ascension.
- NetPlay (GPT-4 Turbo, temperature 0) reached mean depth about DL2-3, no ascension ([arXiv 2403.00690](https://arxiv.org/abs/2403.00690), from R14 notes, LOW).
- A broader LLM-agent run set (236 sessions across four models, best DL10, none ascended) lists spatial reading of ASCII maps as "the biggest difficulty", plus descending too early, no food stockpiling, taking Mines stairs unprepared ([blog](https://kenforthewin.github.io/blog/posts/nethack-agent), LOW).
- The one LLM ascension needed a USD 200/month plan plus ~USD 300 in credits and three runs (Pitfall 3).

**How to avoid:** Decision to make explicitly in P3. Recommended default: the LLM is an offline analyst (death and stuck-run triage, drafting scenario tests, drafting rule candidates that humans/tests verify against source). In-game LLM is out of the bench loop. If an in-game advisor is ever tried, it ships behind a flag, with a "LLM off" arm, and its effect is measured on games it did not influence by cached cassettes only for regression, never for rates.

**Warning signs:** "We will just ask the model when stuck" appearing in a plan without a budget line; a roadmap phase whose gate needs an API key.

**Phase to address:** P3.

---

### Pitfall 12: LLM non-determinism breaks A/A and replay

**What goes wrong:** Temperature 0 is believed to be deterministic. In practice outputs vary because serving kernels are not batch-invariant (output depends on the server's batch size), and providers change model revisions. The bench's guarantee (identical A/A) disappears.

**Evidence:** [Thinking Machines, Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) (LOW-MEDIUM: fetched and summarised; also reported by secondary posts) says greedy decoding is not run-to-run deterministic on typical serving stacks. R15 notes reach the same conclusion and recommend cassette replay keyed by `(model_revision, prompt_hash, state_hash, schema_version)`.

**The deeper trap (my analysis):** Cassettes only hit when the bot reaches the same state. After any bot code change the state hash changes and the cache misses. So cassettes make regression replay possible for the same commit, but they do not make cross-commit comparison possible. Comparing commits with an LLM in the loop is a pure statistics problem again (Pitfall 5) at LLM prices.

**How to avoid:** Keep the bench LLM-free by default. Any LLM-using component records raw prompt, response, model id, params in the job, and its output must pass a whitelist validator before reaching game actions (R15 notes). A/A tests exist only for the LLM-free configuration.

**Warning signs:** A/A mismatch on seeds that previously matched; a provider "model update" notice.

**Phase to address:** P3 (decide), P2 (A/A gate stays LLM-free).

---

### Pitfall 13: Hallucinated or version-wrong game knowledge entering the bot

**What goes wrong:** An LLM (or an old wiki page) supplies a game fact that was true in 3.4.3/3.6 or never true. It becomes a rule or a data table entry. NetHack 5.0.0 was released 2026-05-02 with 3,100+ changes in `doc/fixes5-0-0.txt` ([release notes](https://nethack.org/v500/release.html), LOW-MEDIUM; the local copy of the fixes file is HIGH), so model training data and most wiki text predate it.

**Evidence (HIGH, from this repo's own cross-checks against 5.0 source):**
- ChatGPT said levitation protects from eel drowning. Wrong: the eel drown check covers only Swimming, Amphibious, Breathless (R09-claude.md; MEDUSA-NH5.md cites `uhitm.c:3389`).
- ChatGPT said the Quest home is "Temple of Light": wrong, "Shrine of Destiny" (R11-claude.md).
- ChatGPT quoted a priest no-gold message that does not exist (R06-claude.md).
- Gemini was "wrong in places" on unicorns/vortices (git log: "DeepSeek correct, Gemini wrong in places").
- Even Claude's own pass missed items: confused unblessed genocide kills a human hero, elves carry elven mithril 1/4, soldier ant poison 1 in 8, 5.0 lowered the starvation-death point (R05, R07, R03, R08 notes).
- The ASCENSION-ROUTE-AUDIT.md was built from 3.6.6 `.des` files; later 5.0 checks corrected it: digging down at Medusa fills the hole with water next to the moat (`dig.c:606`), dry arrival squares per map 32/67, 46/53, 0/16, 6/51 (ASCENSION-PLAYBOOK-NH5.md).
- `scripts/wiki_sweep/ollama_sweep.py` writes model output to JSONL that other scripts may trust (CONCERNS.md).

**How to avoid:** A fact ledger: every number or rule that drives a decision carries a status `SOURCE(file:line, 5.0)` / `MEASURED(job id or query)` / `UNVERIFIED`. UNVERIFIED facts may not enter `autoascend/` data tables or rules. Generated tables (monster flags, object data, level maps) come from the 5.0 source or the NLE build, with a diff test that fails if a table disagrees. Treat any LLM output as a lead to check. The practice already used (read the answer, check against 5.0 source, log "wrong/missed") is right; formalise it and keep it for the whole project.

**Warning signs:** Decision code with a "per wiki" comment and no 5.0 line; facts that agree across several LLMs but never checked (they share training data).

**Phase to address:** P3 (ledger), every phase thereafter.

---

### Pitfall 14: Unverifiable progress claims by the AI assistant

**What goes wrong:** The assistant says "started", "running", "merged", "passed" with nothing behind it. The last session claimed bench workloads while idle. Trust broke and the project was reset.

**Why it happens:** Long autonomous sessions, status written in prose, no machine-checkable link between a sentence and a job. The assistant summarises intent rather than state.

**How to avoid (concrete, mechanical):**
1. A claim grammar: any sentence beginning "started", "running", "done", "passed", "improved" in a progress note or commit must contain `job <id>`, a 7+ char commit hash, or a query. A pre-commit/commit-msg hook and a Claude Code Stop hook reject commits/notes with those words and no reference.
2. After every job start the assistant runs `bench_status` and pastes its output; the job record stores `started_at`, `last_heartbeat`, `games_done/n`. A claim "running" is valid only if heartbeat age < N minutes.
3. Session summaries are generated by a script from the bench DB and `git log` (never typed prose), and diffed against the previous one.
4. A results ledger table (one row per verdict: job id, commits, primary metric, n, CI, decision) is the only place verdicts live; scripts refuse to merge a branch without a ledger row.
5. Memory note `proof-for-every-claim` already exists; keep it, but it is a reminder, not a guard. The hooks are the guard.

**Warning signs:** "Started" with no job id; a job id that `bench_status` does not list; heartbeat older than the claim; verdicts in commit subjects only.

**Phase to address:** P1 (before any bench work), reinforced in every phase gate.

---

### Pitfall 15: Bookkeeping eats the work

**What goes wrong:** Time and context go to state files, trackers and notes instead of experiments.

**Evidence (HIGH):** 81 `state:` commits, 150 `docs:` commits, 42 `research:` commits out of 511. PROJECT.md already lists "heavy session bookkeeping" as out of scope.

**How to avoid:** No `state:` commits. Progress is derived from bench DB and git (Pitfall 14.3). One research note per decided question, and each ends with a decision line. Budget: a phase plan may spend at most one task in five on documents. Superseded notes get a one-line `SUPERSEDED BY` header instead of rewrites.

**Warning signs:** Commit ratio of docs-to-code above 1:1; a new tracker file.

**Phase to address:** P1.

---

### Pitfall 16: Context loss and contradictory notes across sessions

**What goes wrong:** Later sessions read different truths depending on which file they open.

**Evidence (HIGH):**
- The playbook fixes the character as `val-hum-fem-neu` (human neutral; Mines gnomes hostile). `WIKI-TIER1.md` still says "Dwarvish hero: gnomes and dwarves always generate peaceful". `LADDER-NH5.md` says "a lawful Valkyrie fights cross-aligned unicorns". `ASCENSION-ROUTE-AUDIT.md` says the Quest "needs lawful standing". The astra ascension was a lawful dwarf.
- README says "Ascension is out of reach for this bot" and cites NetHack 3.6; `PROMPTS.md` and the project goal say ascension on 5.0 (CONCERNS.md).
- Docstrings point at the deleted `.planning/STATE.md`.
- Playbook status labels "BUILT on feat/medusa" for features not on `main`; `castle-elb11` fix "not on `main` history beyond the staging commit".

**How to avoid:** One `CHARACTER` constant (role, race, gender, alignment, god name) used by code, tests and a generated header in each research note. A CI check lists broken references to deleted files. Notes carry `Version: 5.0 | 3.6 | mixed` and a verified date. Nothing is "BUILT" unless it is on `main` and passes the gate.

**Warning signs:** Grep finds two characters in the docs; a plan cites a file that no longer exists.

**Phase to address:** P1.

---

### Pitfall 17: Monolith plus no CI means every change risks silent regressions

**What goes wrong:** `agent.py` (2142 lines) and `global_logic.py` (1362) share mutable state with ordering dependencies (`update_state()` not always called; `check_items` side effects). Tests run by hand; 16 slow tests are deselected by default.

**Evidence (HIGH):** CONCERNS.md "Shared mutable state", "No CI", "Slow tests excluded", the Elbereth castle regression.

**How to avoid (strong, specific):** Because games are deterministic per seed, a pure refactor must produce **bit-identical games**. Gate each extraction commit on: same bot trace hash (or same final outcome, turn count and action hash) over a fixed set of N seeds (e.g. 50 seeds, first 3000 turns plus 10 full games), run in minutes locally. Only commits labelled `behavior:` may change that hash, and those go through the statistical gate (P2). Add a smoke job to CI (even a local `make gate`) running the deterministic gate plus the unit tests. Extract in this order: prayer, Elbereth/escape, item use, shop handling, then exploration; keep `agent.py` as orchestration.

**Warning signs:** A refactor commit that changes results; "slow" tests never run; modules importing each other circularly.

**Phase to address:** P2 (gate), P5 (split).

---

### Pitfall 18: Un-merged "staged" fixes and branch sprawl

**What goes wrong:** Fixes live on experiment branches or are described as built while main lacks them; merges of "kept" experiments stack on each other.

**Evidence (HIGH):** git log: `exp/eel-grip`, `exp/castle-back`, `exp/medusa-stage`, `feat/medusa`, repeated "Merge main into feat/medusa"; playbook rows "BUILT on feat/item-skills"; `castle-elb11` (8/20) not on main.

**How to avoid:** Trunk-based. Short branches, merge only through the gate. Feature flags for unfinished abilities, default off. Status vocabulary: `ON MAIN + gate pass` or `NOT DONE`.

**Phase to address:** P1 (policy), P5.

---

### Pitfall 19: Goal drift in the definition of "ascension" and in how test tools leak into the final run

**What goes wrong:** Rewind, reseed and staged tools are allowed for tests, then slip into the "final" game. The client-side definition of a clean game blurs: save/restore, lag-related pauses, human restarts.

**Evidence:** The astra report itself mentions "saved-game resumptions" and human start/stop of sessions; the NeurIPS 2026 checkpointed-exploration paper makes save/restore an engine feature for benchmarking ([page](https://neurips.cc/virtual/2026/161943), LOW; it does not compare checkpointed to full-game results). In this project, `scripts/rewind.py` and `staged_run.py` live in the same repo as the bot.

**How to avoid:** A written definition of a clean run enforced by a verifier script: one seed, one process start, no `rewind`/`staged`/`handplay` import in the process, no input from stdin, bot commit equals a tagged commit, `.xlog`/dumplog contains ascension, result stored with seed, commit, NLE hash. The final-run harness runs the bot as the screensaver would, with an audit log hash chain.

**Phase to address:** P7 (verifier written in P2).

---

### Pitfall 20: Version-pinned data inherited from NetHack 3.6.x

**What goes wrong:** AutoAscend's tables, strategies and solver maps are 3.6.6-era. 5.0 differs in ways that silently change decisions (see the 5.0 table below).

**Evidence (HIGH):** CONCERNS.md: gate version-specific data (`autoascend/objects/data.py`, `autoascend/soko_solver/maps.py`) on version; `PLANE = 1000  # TODO`; glyph table maps branch staircases to plain stairs (LADDER-NH5.md); `Excalibur` dipping strategy inherited (PLAYBOOK).

**How to avoid:** Generate or diff each table against the 5.0 source in tests (monster flags, object prices/probabilities, Sokoban maps, level lists), and add a startup assertion on the game version string.

**Phase to address:** P1 (version assertion), P4/P6 (per-system checks).

---

## NetHack 5.0-specific traps (what 3.6 knowledge gets wrong)

All rows HIGH unless marked: they cite the local 5.0 source/fixes file or notes that cite it.

| # | Trap | 5.0 fact | Consequence for bot or plan |
|---|------|----------|-----------------------------|
| N1 | Food from kills | Monster kills no longer death-drop comestibles (only corpses, unless the monster carried food) (`fixes5-0-0.txt`, FOOD-NH5.md) | 3.6 food assumptions fail; 25% of baseline games starve or faint. The Mines-branch level always has a filling ration; supply chests above the Oracle (2/3); Sokoban food. |
| N2 | Valkyrie start | Starts with a spear (+1 dwarvish spear per notes) not a long sword (`fixes5-0-0.txt:971`); stealth moved to XL 3 (notes); Excalibur "much harder" for non-Knights (`fixes5-0-0.txt:1401`), neutral Valkyrie's dip fails (`fountain.c:404`) | Never run the inherited Excalibur strategy for this character; early monsters wake more often |
| N3 | Falling | Falling down a hole or trapdoor deals damage proportional to height (`fixes5-0-0.txt:778`) | "Dig down when stuck" costs HP; gate on HP |
| N4 | Dig-down at Medusa | Hole fills with water if any neighbour is water (`dig.c:606`); dry arrival squares: map1 32/67, map2 46/53, map3 0/16, map4 6/51 | The 3.6-era "dig down skips Medusa" plan (ROUTE-AUDIT) fails on map 3 and is unreliable elsewhere; checking `dig_square` for water within 1 is required |
| N5 | Drowning | Eel drowning ignores levitation (`uhitm.c:3389`) | Levitation crossing needs sea-monster avoidance or magical breathing |
| N6 | Elbereth | Ignored by @ humans/elves, minotaurs, shopkeepers, guards, uniques, Riders, Angels; useless in Gehennom and on the Planes; attacking from it erases it (`monmove.c:241-300`, `mon.c:4267`); boxed-in scared monsters still attack (`monmove.c:918`) | A single "Elbereth when HP low" rule is a trap at the Castle, vs crowds, in Gehennom |
| N7 | Prayer | Never works in Gehennom; Hungry is only minor trouble; starvation-death point lowered; prayer timeout scales after turn 100000 (`fixes5-0-0.txt:227`); praying on an unaligned altar always fails (`fixes5-0-0.txt:111`); low-HP threshold is a fraction by XL (`pray.c:116`) | Hunger-by-prayer cycle fails ~6.7% per cycle; 33 games die to the god's wrath; Gehennom needs prayer off |
| N8 | Quest | Killing the leader opens the Quest (Luck penalty); quest is non-sealing; quest guardians are lawful; home level is "Shrine of Destiny" | Alternative path exists but costs Luck; do wishes/prayers first |
| N9 | Gehennom | Reworked: new filler styles (lava, ice, iron-bar mazes), tutorial, themed rooms in DoD, new monsters (displacer beast, genetic engineer, gold dragon, baby gold dragon), levels in Lua | Dig-down and maze assumptions need re-checking per level; monster tables may lack the new monsters. MEDIUM: from release coverage ([release page](https://nethack.org/v500/release.html), [heise](https://heise.de/-11284259)); the monster-table gap is **UNCHECKED** |
| N10 | Branch staircases | NetHack 5 shows branch stairs with their own glyph (`S_brdnstair/S_brupstair`); the bot maps both to plain stairs (`autoascend/glyph/nh5.py`) | Cannot tell which `>` goes to the Mines; 24% of games never reach the Mines |
| N11 | Shops | `price_quotes` option exists; healing potions have a unique price; sell offers can identify scrolls | New identification route (already built); wrong dialog parsing risks angry shopkeepers (69 deaths) |
| N12 | Amulet and invocation | Picking up the Amulet gives a wish in 5.0 (levitation if not held, else life saving) per playbook (verify against source before using) | Invocation plan must handle prompt text |
| N13 | Human data mix | 72 NAO 3.6 ascensions vs 199 5.0 dumplogs (end-state only), winners only | Stage requirements need bot-measured values |
| N14 | Save compatibility | Old saves and bones files do not load in 5.0 (release notes) | No importing 3.6 trajectories to replay; NLD trajectories are 3.6.6 and useful only for behaviour cloning ideas |

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Per-monster `if` in fight code | Kills one named killer fast | Interactions, unreadable arbiter, no learning | Never; use class rule from flags (Pitfall 1) |
| Staged pass-rate as the success criterion | Fast signal on rare late states | False confidence, Pitfall 4 | Only as "mechanism works" test |
| `except Exception: pass` in the game loop | Bench keeps running | Hides crashes, biases rates | Never in decision code; allowed at top-level if traceback logged and game counted as `crashed` |
| LLM-generated data table committed unverified | Quick coverage | Silent wrong behaviour on 5.0 | Never; verify against source |
| Long-lived feature branch | Avoid breaking main | Merge conflicts, "BUILT but not on main" | Never beyond one gate cycle |
| Guessed thresholds ("fixed 8 HP retreat") | Works on first seeds | Wrong at depth, owner rule says no guessed thresholds survive measurement | Only as logged `start value` replaced by measured values |
| Local-path `.mcp.json`, gitignored NLE | Works on one machine | Fresh clone fails | Never after P1 |
| Hand-kept tracker files | Feels organised | Drift, 53% non-code commits | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| NLE seeds | Using core=disp=seed only | Also set `lgen` so levels are independent of play (verify); store all four seeds with the job |
| NLE 5.0 build | Treating NLE 1.3.0 docs as 3.6 | Assert game version at startup; keep build steps documented |
| Bench DB | Reading numbers from archive for a new commit | Re-baseline `main`; store NLE hash and lock hash per job |
| LLM provider | Trusting temperature 0 | Cassette with model id and prompt hash; bench stays LLM-off |
| `fixed_clock` LD_PRELOAD | Cache keyed by file name only | Verify digest before load (CONCERNS) |
| Ollama wiki sweep | Output trusted by scripts | Treat as untrusted lead; verify against source before use |
| MCP bench tools | "Started" echoed from tool call without status | Always follow with `bench_status`, quote job id and heartbeat |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Per-move BFS and full-grid numpy in Python | Slow games; fewer games per hour | Cache distance maps per level; use numba where profiled | When n per experiment is thousands and games are 15-25k turns |
| Oversubscribed workers | Timeouts; watchdog ends mislabeled | `OMP_NUM_THREADS=1`; size pool from CPU count; keep PC usable (owner rule: 10 workers) | Under load, game timeouts inflate "abort" counts |
| Whole-game replay for every check | Hours per check | Deterministic gate on a small seed set plus first-N-turn traces | Every refactor commit |
| `store.games(sha)` loading everything | Memory growth | Page by commit | At 100k+ games |
| Rare-event measurement | Needs thousands of games for Medusa-stage effects | Snapshot-staged conditional runs plus the product | 1.1% stage rate |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Bench server mutating endpoints without a token | Local page/process can start or shut down jobs; a "started" claim could even be spoofed | Per-session token, Origin check (CONCERNS) |
| `SCENARIO_HOOK` exec | Arbitrary code | Keep debug-only; document |
| LLM output written into data files | Prompt-injection from wiki text into tables | Validator plus source check (Pitfall 13) |
| `LD_PRELOAD` cache tampering | Code execution in every worker | Digest-verify, mode 0700 |

## UX Pitfalls

The screensaver experience is out of scope. One constraint remains.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bot work breaks the idle hook | Prompt blocked until game exits | Keep hook thin; `tests/test_launcher.py` stays green in the gate |
| Long-running final ascension run on the screensaver path | Terminal locked for hours | Final run uses the headless harness, the screensaver is a replay |

## "Looks Done But Isn't" Checklist

- [ ] **Ability "works":** passes a staged test but has no natural arrival rate — verify the funnel row and arrival rate exist.
- [ ] **Experiment "kept":** merged on dev seeds only — verify confirm-seed result and ledger row with n and CI.
- [ ] **Job "started":** only an assistant sentence — verify `bench_status` shows job id, heartbeat, games done.
- [ ] **Refactor "behaviour-neutral":** no trace-hash comparison — verify identical trace on the fixed seed set.
- [ ] **Fact "verified":** came from an LLM or the wiki — verify a 5.0 source line or bench query in the ledger.
- [ ] **Feature "built":** lives on a branch or behind a flag — verify it is on `main` and exercised in natural games (counter in the trace).
- [ ] **Death cause "fixed":** killer vanished from the histogram — verify the class total and the funnel did not move elsewhere (starve instead of wrath, as with prayer).
- [ ] **Stage "passed":** crash/abort/timeouts excluded — verify denominators.
- [ ] **Ascension "recorded":** verify seed, commit, NLE hash, dumplog, no rewind/stage/human input, reproducible from the seed.
- [ ] **Fresh clone:** `uv sync` works without the gitignored NLE directory.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Whack-a-mole pileup (1) | HIGH | Tag all species-name branches, replace by class rules in P5 extraction under the trace gate; delete rules that never fire |
| Noise-based merges (5, 6) | MEDIUM | Re-baseline head vs older commit on fresh seeds; revert merged changes whose net effect is invisible |
| Staged illusion (4) | LOW | Recompute with natural arrival rates; relabel old results as capability tests |
| False claims (14) | MEDIUM | Audit last N claims against bench DB; adopt the claim grammar hook; re-run missing jobs |
| Contradictory notes (16) | LOW | Add `SUPERSEDED` headers; central CHARACTER constant; single fact ledger |
| LLM facts in code (13) | MEDIUM | Grep tables generated from LLM output; verify or remove |
| Level-gen not isolated (7) | LOW | Add lgen; re-run A/A with different seed sets to estimate variance |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Special-case pileup | P2, P4, P5 | Death-class histogram plus no new species-name literals in decision code |
| 2 Late wall as ability gap | P3, P6 | Capability checklist rows each with a standalone test |
| 3 Prior art transfer | P3 | Route decision lists each claim as verified-on-5.0 or inherited |
| 4 Staged vs natural | P2, P6 | Funnel shows natural arrival next to every staged number |
| 5 Small samples | P2 | Every verdict records MDE, n, Wilson/Newcombe CI |
| 6 Multiple comparisons | P2 | Ledger with named primary metric, confirm-seed result, re-baseline every K merges |
| 7 Determinism vs variance | P2 | lgen trial; A/A on different seed sets gives variance |
| 8 Seed overfitting, Goodhart | P2, P7 | Reserved seed ranges; depth reported with XL/AC |
| 9 Stale baseline/drift | P1 | Fresh main baseline plus A/A; lock hash stored per job |
| 10 Crashes counted wrongly | P2, P5 | Five terminal states in every report; narrow exception handlers |
| 11 LLM cost/latency | P3 | Written budget line before any in-game LLM work |
| 12 LLM non-determinism | P3 | Bench configuration LLM-off; cassettes for regression |
| 13 Hallucinated knowledge | P3 onward | Fact ledger; table-vs-source diff tests |
| 14 Unverifiable claims | P1 | Hooks reject claim words without job/commit/query; `bench_status` pasted |
| 15 Bookkeeping | P1 | docs/state commits under 30% of commits |
| 16 Context loss | P1 | One CHARACTER constant; dead-reference check |
| 17 Monolith, no CI | P2, P5 | Trace-hash gate passes on every extraction commit |
| 18 Branch sprawl | P1, P5 | No branch older than one cycle; status vocabulary |
| 19 Clean-run definition | P2 (verifier), P7 | Verifier passes on the recorded game |
| 20 Inherited 3.6 data | P1, P4, P6 | Version assertion; table-vs-source tests |

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| P1 baseline | Comparing to archive instead of fresh main | Baseline plus A/A at >= 2304 games first |
| P2 gate | Gate that tolerates noise-level changes as "no harm" | Gate on trace-hash for refactors, CI-based for behaviour changes |
| P3 route decision | Counting a 3.6/3.6.7 result as evidence for 5.0 | Tag each datum with version and character |
| P3 LLM role | Plan needs API calls inside the bench | Offline analyst default |
| P4 food | Fixing starvation by prayer timing | Fix supply (N1) and stuck handling; prayer failure is a symptom |
| P4 Elbereth/escape | Single global rule | Class rules with exclusions (N6) |
| P5 split | Behaviour drift while moving code | Trace-hash identical or revert |
| P6 Medusa | Dig-down assumption (N4), ravens/blind melee without telepathy | Check dry squares; require telepathy or avoid melee |
| P6 Castle | Elbereth-ignorers (minotaurs, soldiers) | Ranged and stairs tactics; do not rely on Elbereth |
| P6 Gehennom | Praying or Elbereth by habit | Switch both off by level flag |
| P7 final | Rewind or reseed creeping in | Verifier plus fresh seeds |

## Sources

Local (HIGH):
- `.planning/PROJECT.md`, `.planning/codebase/CONCERNS.md`
- `.planning/research/REWIND-20.md`, `FOOD-NH5.md`, `PRAYER-NH5.md`, `LADDER-NH5.md`, `SURVIVAL-NH5.md`, `MEDUSA-NH5.md`, `ASCENSION-PLAYBOOK-NH5.md`, `ASCENSION-ROUTE-AUDIT.md`, `WIKI-TIER1.md`, `ONLINE-2026-10-29.md`
- `.planning/research/external/PROMPTS.md`, `R01..R16-*.md` (cross-check notes), `R14-chatgpt.md`, `R15-chatgpt.md`, `R14-R15-claude.md`
- `reference/nethack-5.0.0/doc/fixes5-0-0.txt`; `reference/nle-src/nle/env/base.py`
- `bench/stats.py`, `nethack_screensaver/game.py`
- `git log` 2026-10-16 to 2026-11-12 (511 commits); computed figures (Fisher, Wilson, MDE, rule of three) produced in this session

External (tagged per the classify-confidence seam; web-only single source = LOW):
- BotHack README: https://github.com/krajj7/BotHack (LOW)
- NetHack wiki Bot: https://nethackwiki.com/wiki/Bot (LOW)
- Damerell, "Writing a NetHack bot": https://www.chiark.greenend.org.uk/~damerell/games/nhbot.txt (LOW)
- AutoAscend repository: https://github.com/maciej-sypetkowski/autoascend (LOW)
- NetHack Challenge 2021 report: https://nethackchallenge.com/report.html (MEDIUM with arXiv 2203.11889 https://arxiv.org/abs/2203.11889)
- NetHack is Hard to Hack: https://arxiv.org/abs/2305.19240 (LOW-MEDIUM; abstract-level)
- NetPlay: https://arxiv.org/abs/2403.00690 (LOW; via R14/R15 notes)
- CodeHack: https://arxiv.org/abs/2609.31076 (LOW; via R14/R15 notes, not opened)
- LLM ascension report (nethack_astra): https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/ (LOW)
- LLM NetHack agent failure modes: https://kenforthewin.github.io/blog/posts/nethack-agent (LOW)
- Checkpointed exploration benchmark page: https://neurips.cc/virtual/2026/161943 (LOW)
- Agarwal et al., statistical precipice: https://arxiv.org/pdf/2108.13264 (MEDIUM, widely cited)
- Thinking Machines, Defeating Nondeterminism in LLM Inference: https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ (LOW-MEDIUM)
- NetHack 5.0.0 release: https://nethack.org/v500/release.html; https://nethackwiki.com/wiki/5.0.0 (LOW-MEDIUM)

---
*Pitfalls research for: rule-based NetHack bot, clean ascension on NetHack 5.0 (NLE)*
*Researched: 2026-11-12*
