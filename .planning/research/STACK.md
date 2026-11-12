# Approach Stack: how to get ONE clean NetHack ascension from this codebase

**Project:** NetHack Screensaver: Ascension (AutoAscend port, NetHack 5.0 / NLE 1.3.0)
**Researched:** 2026-11-12
**Mode:** Comparison / feasibility (adapted: "stack" = approaches, not libraries)
**Overall confidence:** MEDIUM. The historical facts are HIGH (primary papers and repos). The ranking of what works for THIS bot on NH5 is MEDIUM-LOW, because no published system matches the hybrid proposed here.

Tooling note: no research providers (exa, brave, context7, ...) are enabled in `.planning/config.json`, so the research-plan seam was not used. Everything below came from WebSearch/WebFetch against primary sources. Confidence tags: HIGH = primary paper/repo/dumplog read directly; MEDIUM = self-reported blog or secondary summary, consistent across sources; LOW = single unverified source.

---

## 1. Verdict (read this first)

1. **No scripted bot has ever ascended NetHack 3.6 or later. One LLM agent has.** The only scripted ascensions are BotHack's, 2014-2015, on pre-3.6 rules, and they leaned on pudding farming, which 3.6.0 removed. The NeurIPS 2021 report says explicitly: no bot had ascended 3.6.6, and no agent in >500k evaluation games got close. On 2026-09-21 an LLM agent (GPT-6 "Astra" in a self-built harness) ascended a dwarvish Valkyrie on NetHack 3.6.7 (Hardfought), at 37,140 turns, on its 3rd run, open-book and human-supervised. (HIGH that it happened; MEDIUM that it is reproducible.)
2. **Learning from AutoAscend or from humans is a dead end for this goal.** HiHack's best neural policy gets mean score ~1,550 versus AutoAscend's ~8,500 and about 1.1-1.4 mean Dlvl versus 3.1. Data and model scaling flatten near a score of ~1,000. Do not spend phases on imitation or RL. (HIGH)
3. **Our binding constraint is not search volume, it is capability.** 0 of 146,743 stored games passed Medusa. The rule-of-three 95% upper bound on the per-game probability of passing Medusa is ~2e-5. At that rate seed search is hopeless. Search only works as the last multiplier once the natural per-game ascension probability is >= ~1e-3. (HIGH, arithmetic)
4. **The only evidence of anything passing Medusa at scale comes from LLM play.** In Creus's 113-game Astra study, 8 of the 10 highest-scoring completed games killed Medusa, 6 entered Gehennom, one performed the invocation. Cost was about $10.7k in tokens. (MEDIUM, one blog, but it is consistent with the Kenny ascension.) Our scripted bot's rate is ~0 past Medusa. This is the gap an LLM can fill, and it is the one place where the LLM's weakness (cost, spatial errors, memory) is cheapest to contain.
5. **Recommended stack, in order:** (A) keep the scripted AutoAscend core and fix it by system with the natural funnel and death-moment replay; (B) add a bounded, cached, replayable LLM "late-game pilot" (handover at Medusa-ish readiness), built and tested first on staged starts; (C) use search (role/race A/B now, lgen-dungeon screening later) only as the final amplifier. Do NOT do imitation/RL, pure-LLM-from-turn-1, pudding-style exploits, in-game fork lookahead, or per-monster patches.

Honest probability that this milestone yields a clean ascension: A alone ~5-10%, A+B ~15-30%, with large uncertainty. (LOW. These are my judgement, not measured.)

---

## 2. Evidence by approach

### 2.1 Scripted bots (the only line with ascension history)

| System | Best result | What made the difference | Source / confidence |
|---|---|---|---|
| BotHack (Clojure, one developer, ~Mar 2014 to Jun 2015) | Wizard-mode full-auto win Oct 2014; non-wizard ascension 2015-01-25 (smartbot3 on acehack.de); modified copies ascended a Samurai and a Knight at Junethack 2015 (22 Jun 2015). A dev landing page says "three games in 2015". | Complete internal game model plus hand-coded logic everywhere ("all bot logic is hand-coded"). Early game by cautious fighting and Elbereth; armour by robbing dwarves; Excalibur by dipping; Sokoban solved for every level (6 Dec 2014). Reached the Castle, did the Quest, cleared many Gehennom levels (Dec 2014) before dying to Orcus-spawned Demogorgon. The final step was **pudding farming** (25 Jan 2015): farm black puddings for unlimited items and corpses so that the resource problem disappears. | BotHack README + NetHackWiki "Bot" (HIGH); Pudding_farming wiki (HIGH); 2015 academic paper calls success "at least partially reliant" on it (MEDIUM) |
| Saiph, TAEB (Perl) | Long survival, no ascension recorded. BotHack reused their monster/item dictionaries. | Frameworks, not winners. | NetHackWiki Bot (MEDIUM) |
| Borg-style / Angband analogy | No NetHack equivalent. A 1990s Usenet analysis said NetHack bots are far harder because strategy and food/time pressure punish aimless play. | Not applicable. | chiark nhbot.txt (LOW, undated opinion) |
| AutoAscend (NeurIPS 2021 winner, behaviour-tree style strategies) | Median ~4.9-5.3k points, mean max Dlvl ~3.1 over random roles; ~1 in 20 of its Valkyries reached Dlvl 10 / XL 10 / 30k points. Never ascended. Roughly 3x the best neural agent's median. | Meticulous observation parsing into an internal state, hierarchical strategies (fight, pickup, explore, Sokoban solver, altar tricks, Excalibur dipping). | arXiv 2203.11889; nethackchallenge.com report; HiHack paper Table 2 (HIGH) |

Takeaways for us (HIGH on the facts, MEDIUM on the inference):

- **BotHack's order of work is a template.** It validated the late game first with a pre-equipped wizard-mode bot (Oct 2014), then fixed the early game, then solved resource supply. That is exactly this project's "staged tests for late abilities + natural funnel", so keep Track B.
- **BotHack's key crutch is gone.** Pudding farming is dead since 3.6.0 (no corpses or death drops from puddings). NH5 also cut food death drops. There is no known NH5 equivalent, so a scripted ascension has to be earned with ordinary resources. I found no published scripted ascension under 3.6+ rules, so there is no existence proof for the scripted-only path on our version.
- **BotHack took ~15 months of single-developer work to reach the first ascension and then ascended only a handful of times.** An ascension from a scripted bot is plausible but rare; plan for a per-game rate far below 1%.

### 2.2 NetHack Challenge 2021 and AutoAscend's known limits

- Symbolic bots took the top three overall places; the best neural entry (RAPH) was itself a symbolic/neural hybrid. Best symbolic median was ~3x the best neural median. 631 submissions, 483 entrants. (HIGH, report)
- No agent ascended in >500k evaluation games; "NetHack is far from solved"; the ~5k median is "several orders of magnitude short of typical human ascensions". The organisers' own recommendation: use external knowledge (wiki, source), learn from human ttyrecs, and checkpoint achievements. (HIGH)
- Known failure pattern: depth is capped by survival and food; starvation/fainting was prominent because entrants restricted themselves to shallow levels. Same as our data (24% hunger deaths in the rewind study; 14% starve in baseline). (MEDIUM)
- Our port is already well past the Challenge-era AutoAscend (76% reach the Mines, 8% Dlvl 15+, 1.1% Medusa). The remaining wall is capability (crossing Medusa, Castle, Gehennom navigation, invocation), which AutoAscend never implemented. (HIGH, project data)

### 2.3 Learning approaches

| Approach | Result | Verdict for us |
|---|---|---|
| NLD (NetHack Learning Dataset): NLD-NAO 10B transitions / 1.5M human games; NLD-AA 3B transitions / 100k AutoAscend games | Offline RL and BC "can use the dataset", human-level play remains unsolved. | Use NLD-NAO only as a **knowledge base for analysis** (the project already has `scripts/nld_study.py`), not as a training set. |
| HiHack (hierarchical BC on AutoAscend strategy labels; NeurIPS 2023) | Best offline model mean 1,318 / median 914; best online (APPO+BC, hierarchical LSTM) mean 1,551 / median 972. AutoAscend: mean 8,556 / median 4,918. Neural games mostly end on level 1 (mean Dlvl 1.1-1.4 vs 3.1). Scaling saturates near ~1,000. | **Do not pursue.** The paper's own conclusion: neural policies cannot learn the long-range low-level behaviours that hand-coded strategies supply. |
| Motif / MaestroMotif (LLM-preference intrinsic reward, then LLM-written skill composition) | Motif beats score-reward PPO on NLE score and on sparse tasks; MaestroMotif reaches the Gnomish Mines in ~46% of runs (secondary summary) vs 9% Motif vs 0.1% direct LLM policy. | Research on early/mid sparse tasks only. Nothing near Medusa. **Skip.** |
| LuckyMera (hybrid symbolic/neural modular framework) | Secondary summary: mean ~1,047, top-6 on the old leaderboard. | Framework idea (skills as modules) is already what AutoAscend's strategies are. **Skip.** |
| Plain RL (PPO/APPO, Sample Factory) | ~400-700 mean at baseline, ~5x improvement across NeurIPS 2020 to 2021, still ~3x below symbolic. | **Skip.** |

Confidence: HIGH (primary papers) for HiHack/NLD numbers; MEDIUM for Motif/MaestroMotif/LuckyMera because I only read abstracts and secondary summaries.

### 2.4 LLM agents

| System | Result | Cost | Source / confidence |
|---|---|---|---|
| NetPlay (GPT-4-Turbo, skills + event interrupts, Valkyrie) | Unguided: score 285, Dlvl 2.6, 1,292 turns. Guided: score 405. AutoAscend on same setup: score 11,342, Dlvl 4.0, 21,170 turns. Beat a rule-based baseline only slightly. Failures: timeouts/menu loops, looping on peacefuls, rotten corpses, starvation. | not reported | arXiv 2403.00690 (HIGH) |
| BALROG (zero-shot LLM/VLM benchmark) | Best original NetHack progression ~1.5% (o1-preview). Models "near-zero". | n/a | arXiv 2411.13543 (HIGH). Later leaderboard figures conflict across aggregators (LOW). |
| kenforthewin harness, Jan 2026 (execute_code tool over NLE API) | gpt-5.2 avg Dlvl 3.5, max 10, BALROG 2.6% avg; gemini-3-flash 2.1; claude-opus-4.5 1.3 (suspected harness interaction). No ascensions. Failure modes: spatial/ASCII misreading, descending too early, no food stockpiling, taking Mines stairs unprepared, hidden stairs, waiting for phantom monsters. | not reported | blog "It's 2026. Can LLMs Play Nethack Yet?" (MEDIUM) |
| Astra research loop (Creus, ~1 week) | 113 games under BALROG settings, random characters: median ~7% progress, mean ~18%; 21 games >50%, 10 >70%; ten passed Dlvl 30, four reached 45+. Of the 10 best completed games: 9 won the Sokoban prize, **8 killed Medusa**, 6 entered Gehennom, 4 took the Bell, 2 the Candelabrum, 1 performed the invocation and reached the Sanctum (Dispater took the real Amulet; notes lost track, it later grabbed a fake; died at Dlvl 38). **No ascension in these games.** | ~$10.7k tokens (5.3B input mostly cached, 280M output); about $95/game average including harness R&D | roger-creus.github.io (MEDIUM, single author but detailed) |
| Astra ascension (Kenny), 3 runs on Hardfought NetHack 3.6.7 | Run 1 died of sliming at Dlvl 51 (T33,302); run 2 killed by a death ray at the Castle (T12,271); run 3 **ascended**, T37,140, lawful dwarvish Valkyrie, 1.77M points. Checked against the server dump by a third party (dunnolab PR #114). | ~$200/mo plan + ~$300 credits, no per-run breakdown | kenforthewin blog, nethack_astra repo, dunnolab/nethackers PR #114 (HIGH that it happened) |

What made the LLM runs work (all MEDIUM, from the two Astra write-ups):

- **Not raw model strength: the harness.** `act` sends up to 8 keystrokes and stops on any change; guard predicates (refuse batches below 2/3 HP, stop on unexpected displacement/damage/level change) are plain code, not LLM; route-proposal graph search over remembered terrain; Sokoban solver (replaying a public AutoAscend solution in some arms); a 6,000-character notebook rewritten each turn because only the last 6 decisions stayed in view; source-labelled "reference cards" from the wiki (one floating-eye card cut attacks on them from 7-in-10 to zero in replay); max reasoning effort for every move.
- **Method, not just model:** Astra replayed the exact moment of a death with a proposed fix and sampled ~10 fresh decisions before spending full games. Declared study groups with control arms, every game counted. (This is the same idea as our `scripts/rewind.py`, applied to LLM prompts and rules.)
- **Weaknesses:** memory errors (lost the fact that Dispater held the Amulet), unchecked Elbereth, floating-eye melee, spatial misreads, cost. The ascension run was open-book (wiki, spoilers, source code), used wishes, genocide and bones, was human-started/resumed over 12 calendar days, and the harness was patched mid-game. It is therefore **not** a clean-game result by this project's definition. It shows what is possible, not what is reproducible.

### 2.5 Hybrid: scripted bot plus learned/LLM components

- No published system combines a strong scripted NetHack bot with an LLM at specific decision points and reports full-game results. (HIGH that I found none.) NetPlay is the closest (LLM chooses among scripted skills) but it was built on a handcrafted baseline far weaker than AutoAscend. The evidence for the hybrid is therefore inferential:
  - the scripted bot is strong exactly where the LLM is weak (early survival, exploration, pathing, fight tactics, food flow; cost ~0, deterministic);
  - the LLM is strong exactly where the bot has zero capability (item reasoning, Medusa/Castle improvisation, notes about identities, rare situations);
  - the late game is only ~1% of games and is long (humans: median Valkyrie ascension 45,918 turns), so LLM spend can be gated to the few games that get there.
- **Offline LLM analyst:** The Astra team's death-moment replay and study-group discipline is a proven workflow. The risk is the thing the owner already named: per-monster whack-a-mole. LLM analysis must be asked to cluster failures by *system cause* (food, escape, HP management, stuck, item use), not to produce one patch per monster. dunnolab/nethackers (ships AutoAscend, lets a coding agent propose changes, scores them in isolated games, MAP-Elites over lineages) shows others are already running this loop on AutoAscend. I found no published results from it (LOW).

### 2.6 "Massive search" (seeds, roles, dungeons)

- Determinism is already there (A/A runs identical). NLE in `reference/nle-src` supports `lgen`, a separate level-generation seed: with `lgen` fixed the dungeon layout does not depend on the hero's actions (`nle/env/base.py:489`, test `test_seed_lgen`). The project currently runs `lgen=None` or 0 in places (`scripts/rewind.py` sets lgen 0). (HIGH, read the source)
- Throughput reference: nethackers reports 1,024 natural-random AutoAscend games in ~56 min with 8 jobs (about 18/min); our 10 slots give order 20-30k short games/day. Late games are longer, so plan on ~10-20k per day. (MEDIUM, third-party figure)
- Arithmetic: with `p` the natural per-game ascension probability, expected games = 1/p. At p=1e-3 that is ~1,000 games, about an hour to a day. At 2e-5 (current bound for passing Medusa) it is ~50,000+ games for Medusa alone and effectively never for the full run. **Search multiplies capability; it does not create it.**
- Role/race: the project already targets Valkyrie (humans: 4,363 Valkyrie games in NLD, 61 ascensions = 1.4%; every Valkyrie ascender killed Medusa; those who killed Medusa ascended ~41%). The Astra ascension was a **dwarvish lawful** Valkyrie. `nethack_screensaver/game.py:40` currently sets `CHARACTER = "val-hum-fem-neu"` (human neutral). ASCENSION-PLAN-NH5 assumes dwarvish lawful (Mines gnomes/dwarves peaceful, infravision, pet-killed dwarves give pick-axes). **Verify which character the bench uses and A/B human-neutral vs dwarvish-lawful on the natural funnel; it is a one-flag experiment.** NetHackWiki role-difficulty data (2011, streak-filtered) puts Valkyrie first at 62.6% wins; 5.0 community opinion says Valkyrie was nerfed (ONLINE-2026-10-29.md), so re-measure instead of trusting. (MEDIUM)
- Purity: choosing a start seed is not a rewind. Screening `lgen` seeds by dungeon features before the run (e.g. Medusa map with 75% levitation-boots statue, Sokoban variant with the reflection amulet, Castle orientation) is "seed selection". It stays reproducible from the seed, but it is a gray area under "no reseeding". **Owner decision required; default recommendation: allow it only for the final attempt, publish the selection rule before running, and keep the unscreened natural funnel as the headline metric.**

---

## 3. Recommended approach stack

### Tier 1 (adopt now): Scripted core, fixed by system, measured by the natural funnel

| Element | Detail | Why (evidence) |
|---|---|---|
| Keep AutoAscend as the core | Refactor `agent.py`/`global_logic.py` behind a deterministic regression gate | Only line with ascension history; 3x+ any neural line; already 8% to Dlvl 15+ |
| Natural-game funnel as the headline metric | Per-stage pass rates with confidence intervals, from the first rung to ascension. Fresh baseline of `main` first (bench DB is empty) | Staged results hid the Medusa wall; rule-of-three keeps claims honest |
| System fixes first | Food/prayer/escape/HP/stuck/item use before any monster rule. Rewind study: 68% of deaths saved by a 100-turn reseed, 24% hungry at death, 12 of 16 deep-rewind deaths were hunger | Matches NLD/Challenge evidence; matches the owner's anti-whack-a-mole rule |
| Death-moment replay as the fix validator | Use `scripts/rewind.py` to replay the last N turns of a death with the candidate change over many reseeds; accept the change only if saved-rate rises and the funnel does not drop | Same method Astra used on prompts; here applied to rules (it is a test tool, never counted as a clean game) |
| Staged starts for late abilities | Wizard-mode staged runs per ability (Medusa crossing, Castle, Gehennom, invocation), each reported separately | Exactly BotHack's path (wizard-mode win Oct 2014 before the non-wizard win); `ASCENSION-PLAN-NH5.md` Track B |
| Telepathy + blindfold + levitation/cold/dry-dig + reflection as the Medusa stage requirement | From `MEDUSA-NH5.md`: 95% of 199 human NH5 ascenders were telepathic, 96% carried a blindfold/towel, 85% a levitation item, 83% reflection | Largest known ability gap; floating-eye kill rule is a system-level item, not a per-monster patch |

Confidence that Tier 1 improves the funnel: HIGH. That Tier 1 alone reaches ascension within this milestone: LOW (~5-10%).

### Tier 2 (build after the funnel is measured): LLM late-game pilot with record/replay

Design (proposed, not copied from a published system; MEDIUM-LOW confidence in the details):

- **Trigger:** the scripted bot hands over when a readiness predicate fires (e.g. Dlvl >= Medusa's level minus 1 AND kit checks), or when a stuck/no-progress detector fires on a deep level. Hand back when a handover goal completes (e.g. "reach Castle", "reach Valley"). Triggers are plain code.
- **Interface:** Astra-style `act` tool (<= 8 keys, stop on change), guard predicates in code, bot-supplied structured observation (inventory with identified properties from the bot's own tracker, coordinates, monster list), a size-capped notebook, wiki/source reference cards injected as text. Reuse the bot's pathing as a `route` tool; do not make the LLM read ASCII for navigation (this was the largest LLM failure in Jan 2026 and in BALROG).
- **Determinism and proof:** a game is (seed, lgen, input log). Record every LLM call and its raw response keyed by (game turn, state hash). Replay serves cached responses, so any LLM game becomes a deterministic, reproducible-from-seed run. Gate regression tests on replays, never on live LLM calls.
- **Cost model:** ~1% of games reach the handover; Astra-class spend was up to ~$100-200 per full late game. Expect $10^3 to $10^4 total for tens of attempts. Run it on staged starts first (cheap to reach), measure pass rates per stage with CIs, and only then wire it into natural play. Needs an owner budget decision.
- **Why not whole-game LLM:** NetPlay Dlvl 2.6 vs AutoAscend 4.0; Jan 2026 models Dlvl 1-3.5; Creus mean progress 18% at ~$95/game. The scripted early game is free and better.
- **Fallback if LLM cost or quality disappoints:** the same staged tests tell you which late-game abilities to script, so the work is not wasted. Use the LLM runs as demonstrations ("how did it cross Medusa on map 2") to write the rule-based version.

Confidence that an LLM pilot can pass Medusa on staged runs: MEDIUM (Astra: 8 of 10 best games). That it raises natural ascension odds enough: LOW-MEDIUM (no hybrid measurements exist).

### Tier 3 (only after the funnel is >= ~1e-3 end to end): search as amplifier

- Cheap, do early: A/B race/alignment on the natural funnel (human neutral vs dwarvish lawful) and record per-role pass rates. A one-day experiment.
- Later: expand to N thousands of seeds with the final bot; optionally screen `lgen` dungeons (owner decides purity).
- Stop rule: if the per-stage CI on any late stage still includes zero after ~2k games reaching it, search is not the answer for that stage; go back to capability.

### Tier 0: LLM as offline analyst (use throughout, low cost)

- Feed it death dumplogs, rewind outcomes and funnel leaks; ask for ranked **system** causes with evidence rows, not patches. Enforce "each proposed change must name the funnel stage it targets and the metric that proves it".
- Use it to draft reference cards (floating eye, Elbereth rules in NH5, Medusa map table) from the local wiki/source mirrors in `reference/`.
- Consider running the dunnolab-style loop (coding agent proposes a change, isolated bench scores it, keep lineages) only behind the regression gate and with the funnel as fitness, never on score/depth alone (score gaming).

---

## 4. Alternatives considered (do NOT do)

| Category | Option | Why not | Evidence |
|---|---|---|---|
| Learning | Behaviour cloning / HiHack on AutoAscend or NLD-NAO | Plateaus at ~1/8 of the teacher's score; teaches nothing about Medusa | HiHack Table 2 (HIGH) |
| Learning | Online RL / Motif / MaestroMotif for the late game | Sparse reward, no run reaches Medusa-kill; huge compute | HiHack, Motif (MEDIUM) |
| LLM | Pure-LLM game from turn 1 as the main path | $10^2/game, human supervision, 1 ascension in 3 well-resourced runs, and ~$10.7k for 113 games with 0 ascensions | Creus + Kenny (MEDIUM-HIGH) |
| LLM | Live LLM calls inside the deterministic bench | Breaks A/A determinism and the regression gate | project constraint |
| Exploit | Pudding farming / BotHack's crutch | Patched in 3.6.0; irrelevant on NH5 | NetHackWiki (HIGH) |
| Method | Per-monster special-case fixes as the main method | Owner's stated failure mode; the Challenge shows deaths are spread over dozens of monsters | LADDER-NH5.md, REWIND-20.md |
| Method | In-game fork/lookahead on NLE (AutoAscend's `env_wrapper` forking) | Uses future information; counts as a rewind, so it breaks "clean game" | PROJECT.md constraint |
| Method | Counting staged, rewound or reseeded games as results | Hid the Medusa wall before | PROJECT.md |
| Search | Brute-force seeds on the current bot | 0 / 146,743 past Medusa; bound ~2e-5 | arithmetic above |
| Scope | New wrapper frameworks (LuckyMera/MiniHack) | Adds a layer, no capability | |

---

## 5. Illustrative funnel targets (assumptions, not measurements)

Used only to size the search question. Baseline `72ca0b6`: Mines 76%, Dlvl 15+/Quest portal 8%, Medusa level 1.1%, pass Medusa 0.

| Stage | Today | Milestone target (assumed) | Note |
|---|---|---|---|
| Reach Medusa's level | 1.1% | >= 10% | system fixes: food, escape, XP, AC |
| Pass Medusa (with telepathy+blindfold+levitation/dig+reflection) | 0 | >= 30% | staged-tested first |
| Castle entry, wand, Valley | 0 | >= 30% | passtune Mastermind is deterministic and bot-friendly |
| Gehennom to Sanctum and climb | 0 | >= 10% | no prayer/Elbereth in Gehennom; humans: Valkyries who killed Medusa ascended ~41% |
| Product | ~0 | ~1e-3 | = ~1,000 games, about a day of bench time |

If any stage target proves out of reach, the product falls below 1e-4 and the plan needs the LLM pilot or a different stage design.

---

## 6. Implications for the roadmap

Suggested phase order (for SUMMARY/roadmap):

1. **Baseline and proof harness:** fresh `main` baseline, funnel report with CIs, deterministic regression gate, fix `reference/nle-src` ignore so a clean clone builds. (Prerequisite; avoids repeating "claimed started, was idle".)
2. **Early-wall system fixes:** food, stuck/unsticker, escape/HP, mines-branch glyph, peaceful handling, validated by death-moment replay. Include the cheap race/alignment A/B.
3. **Late-ability staged tests (Track B):** Medusa crossing first, then Castle, Gehennom navigation, Vlad/Wizard, invocation. Telepathy/blindfold/levitation prerequisites go in Phase 2/3 as system rules.
4. **LLM pilot spike on staged starts:** harness + record/replay + cost accounting; compare pass rate to the scripted ability from Phase 3.
5. **Integration and search:** wire the better of scripted/LLM per stage into natural play; run thousands of seeds; one clean ascension recorded (seed, lgen, commit, dumplog, LLM log if used).

Research flags:

- Phase 4 (LLM pilot): needs its own research (harness API, budget, handover predicate, record/replay format; which model; open-book vs closed-book policy).
- Phase 3 Medusa and Castle: needs phase research per ability (already partly in MEDUSA-NH5, ASCENSION-PLAN-NH5); verify against the NH5 source.
- Phase 2 (food, stuck): standard patterns plus project data; low research need.
- Phase 5 purity question (lgen screening): owner decision, not research.

---

## 7. Gaps and low-confidence items

- Exact BotHack ascension count, roles and game version are not on the primary page (README lists wizard-mode 2014, one non-wizard Jan 2015, Samurai and Knight at Junethack 2015). "3.4.3" is unconfirmed there; acehack.de is a variant. (MEDIUM)
- BALROG's current NetHack-specific leaderboard numbers conflict across aggregators; Astra's own figure is 13.2 +/- 2.7% averaged over 5 games on BALROG's default agent, which is progress, not win rate. (MEDIUM)
- Astra's ascension used wishes, genocide and bones on a public server and an open-book harness; the notes do not say how it crossed Medusa or the Castle. Do not assume that route is available to a closed-book, bones-free local NLE game. (HIGH that this is a caveat)
- Motif/MaestroMotif/LuckyMera numbers are from abstracts or secondary summaries. (MEDIUM-LOW)
- No data on whether the dunnolab/nethackers coding-agent-over-AutoAscend loop produces anything past AutoAscend; its published AutoAscend baseline number is not shown. (LOW)
- The 1% / 41% / 1e-3 figures in sections 2.6 and 5 mix project data with assumptions; the targets in section 5 are planning guesses to be replaced by the first funnel measurements.
- Not checked: whether NH5 changes make Elbereth, prayer or Sokoban prizes behave differently from 3.6 in ways that matter for the LLM reference cards; the local source in `reference/nethack-5.0.0` is the authority.

---

## Sources

HIGH (primary papers, repos, source code):
- Insights From the NeurIPS 2021 NetHack Challenge (Hambro et al.): https://arxiv.org/abs/2203.11889 , https://ar5iv.labs.arxiv.org/html/2203.11889 , report https://nethackchallenge.com/report.html
- NetHack is Hard to Hack (HiHack, Piterbarg et al., NeurIPS 2023): https://arxiv.org/abs/2305.19240 , https://ar5iv.labs.arxiv.org/html/2305.19240
- Dungeons and Data: A Large-Scale NetHack Dataset (NLD): https://arxiv.org/abs/2211.00539
- Playing NetHack with LLMs: Potential & Limitations as Zero-Shot Agents (NetPlay): https://arxiv.org/abs/2403.00690 , https://arxiv.org/html/2403.00690v1
- BALROG: https://arxiv.org/abs/2411.13543
- BotHack README and changelog: https://github.com/krajj7/BotHack , https://raw.githubusercontent.com/krajj7/BotHack/master/README.md
- NetHackWiki Bot: https://nethackwiki.com/wiki/Bot ; Pudding farming: https://nethackwiki.com/wiki/Pudding_farming
- AutoAscend repo: https://github.com/maciej-sypetkowski/autoascend
- NLE source: `reference/nle-src/nle/env/base.py` (lgen seed), `nle/tests/test_envs.py::test_seed_lgen`
- Local project data: `.planning/research/REWIND-20.md`, `LADDER-NH5.md`, `MEDUSA-NH5.md`, `ASCENSION-PLAN-NH5.md`, `ONLINE-2026-10-29.md`; `nethack_screensaver/game.py:40`

MEDIUM (self-reported but detailed or cross-confirmed):
- An LLM Beat NetHack (Kenny, 2026-09-21): https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/
- nethack_astra harness repo: https://github.com/kenforthewin/nethack_astra
- dunnolab/nethackers PR #114 (third-party verification against server dump): https://github.com/dunnolab/nethackers/pull/114 ; project: https://github.com/dunnolab/nethackers , https://pypi.org/project/nethackers/
- Creus, "I let GPT-6 Astra run its own research. It beat Craftax and reached the bottom of NetHack.": https://roger-creus.github.io/blog/astra-craftax-nethack/
- It's 2026. Can LLMs Play Nethack Yet? (Jan 2026): https://kenforthewin.github.io/blog/posts/nethack-agent/
- It Does What Now? summary: https://itdoeswhatnow.com/m/2026-09-21-gpt-6-astra-becomes-the-first-ai-agent-to-win-nethack/
- Motif: https://arxiv.org/abs/2310.00166 ; MaestroMotif: https://arxiv.org/abs/2412.08542 ; LuckyMera: https://arxiv.org/abs/2307.08532 (abstracts and secondary summaries only)
- NetHackWiki role difficulty (2011 data): https://nethackwiki.com/wiki/Role_difficulty

LOW:
- Usenet bot-difficulty post: https://www.chiark.greenend.org.uk/~damerell/games/nhbot.txt
- Aggregator BALROG leaderboard pages (conflicting; not used for decisions)
- korben.info article returned HTTP 403; not read.
- Henaff, "First NetHack ascension, and insights into the AI capabilities it requires" is a human ascension essay (not a bot): https://mikaelhenaff.substack.com/p/first-nethack-ascension-and-insights ; used only for the capability list (credit assignment, in-context item inference, wiki use, hierarchy).
