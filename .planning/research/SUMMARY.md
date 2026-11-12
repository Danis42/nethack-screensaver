# Project Research Summary

**Project:** NetHack Screensaver: Ascension (AutoAscend bot, NetHack 5.0 via NLE 1.3.0)
**Domain:** Rule-based NetHack bot (AutoAscend lineage), goal of one clean ascension, developed against a deterministic headless bench
**Researched:** 2026-11-12
**Confidence:** MEDIUM

**Adapted dimensions:** The four files are approaches (STACK), ability gap per stage (FEATURES), development and test method (ARCHITECTURE), and pitfalls (PITFALLS), not the usual library split.

---

## Executive Summary

This is a hand-written rule and strategy bot (AutoAscend lineage) played through a local NLE build and measured by a deterministic headless bench. No scripted bot has ever ascended NetHack 3.6 or later. The only 3.6.7 ascension in the research is an LLM agent (open-book, human-supervised, third of three runs, dwarvish lawful Valkyrie), which is not a clean game by this project's definition. The measured position (baseline `72ca0b6`, 2304 natural games): 58% reach the Gnomish Mines, 1.1% reach Medusa's level, and 0 of 146,743 stored natural games have passed Medusa. There are two walls: an early wall (survival, food, stuck levels; about half of game endings occur before the Mines, Oracle or Sokoban) and a late wall (abilities never exercised in a natural game: Medusa crossing, Castle, Gehennom, Quest, invocation, Planes).

Recommended approach: fix measurement first (key-based funnel instead of `rung`, an `lgen` decision, fresh `main` baseline with A/A, claim layer, one `CHARACTER` constant). Then fix the early wall by system (food supply, class-wide safety rules, explorer completion, Mines branch detection), validated by death-moment replay and the natural funnel. Then build late abilities as staged contracts, each with a measured natural supply rate beside its staged pass rate. Seed search is a final multiplier that pays only near a natural per-game probability of about 1e-3. Rejected: imitation and RL (HiHack plateaus near score 1,000 vs AutoAscend about 8,500), pudding farming, per-monster patches, in-game lookahead.

Risks: capability (every stage after Medusa assumes magic resistance, reflection, levitation and a dig tool, which the bot rarely owns); statistics (0 ascensions in 146,743 games gives a rule-of-three bound of about 2e-5, so only funnel stages can be optimised); proof (the last session claimed unverified work, so every progress statement needs a job ID, commit or query). Odds are judgement, not measurement: STACK estimates about 5-10% for the scripted core alone and 15-30% with an LLM late pilot (LOW).

---

## Key Findings

### 1. Recommended approach (STACK.md)
- **Tier 1 (now):** keep the scripted core; fix by system (food, prayer, escape, HP, stuck, items) before monster rules; validate fixes with `scripts/rewind.py` death-moment replay (a test tool, never a clean game); staged starts per late ability reported separately; Medusa requirements (telepathy, blindfold, levitation or dig, reflection) as system rules. Rewind study: 68% of deaths saved by a 100-turn reseed; 24% hungry at death; 12 of 16 deep-rewind deaths involved hunger.
- **Tier 2 (after funnel is measured):** LLM late-game pilot with record and replay. Proposed design, MEDIUM-LOW confidence. Plain-code handover predicates; act tool (at most 8 keys, stop on change); code guard predicates; bot pathing as a route tool; size-capped notebook; every call recorded keyed by (turn, state hash).
- **Tier 3 (only at or above about 1e-3 end to end):** search as amplifier. A/B race and alignment early (cheap). `lgen` screening later.
- **Tier 0 (throughout):** LLM as offline analyst. Ranked system causes with evidence; each change must name its funnel stage and proving metric.
- **Do not do:** behaviour cloning or HiHack; online RL or Motif for late game; whole-game LLM from turn 1 (NetPlay Dlvl 2.6 vs AutoAscend 4.0; Creus 113 games about $10.7k, zero ascensions); pudding farming; in-game lookahead; per-monster fixes; staged or rewound results as results; brute-force seeds on the current bot.

### 2. Measured baseline (ARCHITECTURE.md, PROJECT.md; `72ca0b6`, n = 2304)

| Stage (ladder key) | Reach | Notes |
|---|---|---|
| Start | 100% | |
| Dlvl 3+ / Dlvl 5+ | 94.5% / 84.7% | not yet ladder keys |
| Gnomish Mines | 58.3% (56.3-60.3), 1343 | **not 76%** (see Conflicts) |
| Minetown | 20.2% (18.6-21.9) | |
| Sokoban | 24.7% (23.0-26.5), 570 | |
| Sokoban solved | 0 / 2304 | detector or solver suspect |
| Mines' End | 11.1% (9.9-12.4), 255 | |
| Dlvl 15+ | 7.7% (6.7-8.8) | |
| Quest portal level | 5.2% (4.4-6.2) | |
| Medusa's level | 1.1% (0.7-1.6), 25 | |
| Castle and beyond | 0% | not measurable naturally |

Starvation: 334 of 2304 (14.5%). Throughput about 25 games per minute on 10 slots.

### 3. Ability gap (FEATURES.md)
Status verified by code reading on `main` (fb5faa2).
- **HAVE:** Sokoban solver and prize, Minetown altar identify and sacrifice, telepathy from eye corpses, unicorn horn, lizard corpse, eel escape, Castle back-entry (staged 8/20, skips interior), Quest portal step-in and out, stair escape from Dlvl 21.
- **PART:** digging when stuck (keeps one identified non-cursed pick-axe), Medusa dig-down (refuses squares near water), Medusa levitation crossing (staged 4/10), reflection (only if identified), AC growth, passtune solver (written, never called), `rise_one_level` (no caller).
- **NONE:** Mines branch glyph (E3), shop buying (E7), food reserve (E8), prayer lockout and no prayer in Gehennom (E9, E10), Gehennom awareness, Valley, Vlad, Wizard, invocation, Planes, Astral, Quest leader and Bell, magic resistance, wand-of-wishing procedure, poison and fire resistance.

**Must have:**
- Food and pace: E7, E8, E2, E4 (stuck is the dominant starvation path).
- Class-wide safety rules as one tested phase: E9, E10, E12 (passive), E13 (unicorns), E14 (peacefuls), E16 (ray bounce), E17.
- Mines branch glyph (E3).
- AC growth toward human medians (AC -14 at Medusa, -17 at Castle per SURVIVAL-NH5 as cited); bot plateaus near -3 or -4. Largest measured strength gap.
- Levitation source and dig tool reliably owned.
- Reflection and magic resistance (MR realistically only via wish or random cloak).
- Wire existing primitives: `play_tune` and `Solver`, `rise_one_level`, wish-prompt order.
- Gehennom awareness (dungeon id; no prayer, Elbereth, sacrifice).
- Medusa dig-down with attacker clearing and dry-square choice; crossing as fallback.
- Late stages: XL 14 and Quest (Bell, cannot be wished), Vlad (Candelabrum), Wizard (Book), invocation, Sanctum, climb, Planes, Astral.

**Should have:** Castle interior to the wand of wishing (VH; only reliable MR source; owner decision); front Castle entry by passtune; wrest and recharge (+1 to +2 wishes); Vlad throne wish; AC via protection and enchant armour; wand of cold for water.

**Defer:** pet management, unicorn horn acquisition, protection racket, stethoscope and bag of holding.

**Anti-features:** Excalibur dip for the neutral Valkyrie (impossible in NH5, fountain.c:404; remove); per-monster special cases; unicorn chasing; Elbereth as main defence (NH5 boxed-in monsters attack; no effect on @, minotaurs, shopkeepers; none in Gehennom); prayer as food; killing the Quest leader to skip XL 14 (Luck -4 permanent; last resort); counting rewound, reseeded or staged games as ascension; LLM in the tactical loop; spellcasting; wishing for a charging scroll.

### 4. Development and test method (ARCHITECTURE.md)
- **One metric:** natural-game funnel with Wilson intervals. Reach a stage iff its key is in `game["ladder"]`. Never `game["rung"]` (F1).
- **Two commit kinds:** `Kind: refactor` must give a bit-identical frame-hash trace on the gate set; `Kind: behavior` is flag-guarded, one system per commit, with a pre-declared paired experiment (primary metric plus guardrails).
- **lgen:** `game.py` seeds only core and display (`set_initial_seeds(core, disp, False)`), so every behaviour change re-rolls later levels. Pilot with two commits, 400 seeds each, measure discordance q (archive: median 0.048 narrow, p75 0.255, max 0.465 over 54 experiments, metric `dlvl6`).
- **Statistics:** always-valid sign e-process on discordant pairs; exact McNemar; power calculator; validate with simulation and archive A/A. Dev and confirm seed ranges; confirm only at phase gates (the same 2304 seeds were reused by 62 experiments).
- **Evidence classes:** natural (N), arrival bank (B), staged (S), scenario (C), rewind (R). Only N and B may support funnel or progress claims. Staged results go to a `tool_games` table with job IDs.
- **Ability contracts:** needs, procedure, pass check, events. Ability rate (staged) times supply rate (natural arrivals meeting `needs`) predicts natural conversion; track the transfer ratio.
- **Triage:** replay with tracer, deterministic features, closed taxonomy (LLM offline, temp 0, kappa against about 30 hand labels), rank system tags by expected gain. `rewind_depth` separates tactical from strategic causes.
- **Refactor gate:** rolling SHA-1 over `tty_chars` and `blstats` (as `tests/test_replay.py`), recorded every 250 turns. Gate: 200 dev seeds plus 16 long or path-exercising seeds; quick gate 20 seeds truncated at 3000 turns.
- **Modules (strangler-fig):** perception, effectors (only key sender), nav, ordered arbiter replacing the `.preempt` chain, systems (survival, food, resources), stages. Extract only what the roadmap touches. Ratchets on size and bare excepts.
- **Proof:** claim = (job ID, full SHA, query). Trailers generated from DB; `check_claims.py`; start confirmation only after the first game row exists; `bench ascension <sha> <seed>` for the final record.
- **Build order:** A (measurement) first; B (gate and structure) after A0 and A5; C (triage) after baseline, C2 usable without LLM; D (late lab) after A and B.

### 5. Critical pitfalls (PITFALLS.md)
1. **Special-case pileup.** 511 commits in 28 days, 53% docs/state/research; 34 subjects say "dropped" or "no difference". Prevention: system classes from monster flags, never species names; each rule needs a scenario test, trace line and class-level metric; delete rules that never fire in 1000 games.
2. **Early wall forever, late wall ignored.** Prevention: two tracks; Track B has standalone ability tests and is not done on staged rates alone.
3. **Staged mistaken for natural ("castle 8/20").** Only 1.1% reach Medusa's level, so a perfect Castle skill yields about 1%. Prevention: kits from natural arrival snapshots; arrival rate reported beside every staged rate.
4. **Small samples and multiplicity.** "5/20 vs 8/20" Fisher p = 0.50; 0/20 vs 10/20 at Medusa p = 0.0004. At n = 1152 per arm, MDE at Medusa reach about 1.2 points. Prevention: MDE and n fixed before running; one primary metric; family-wise control; re-baseline every K merges.
5. **Determinism is not variance reduction.** Prevention: `lgen` pilot before baseline; A/A for reproducibility only.
6. **Seed overfitting and Goodhart.** Seeds 0-19 reused across rewind, staged and scenario work. Diving past Medusa raises depth without strength. Prevention: reserved dev, confirm and final ranges; depth paired with XL, AC, HP at arrival.
7. **Stale baseline and unverifiable claims.** Live DB empty; last session claimed work while idle. Prevention: fresh `main` baseline plus A/A at 2304; store NLE commit, lock hash, bot SHA; claim grammar requires job, hash or query.
8. **Crashes and timeouts miscounted.** Prevention: exactly one terminal state per game; denominator is all started games; narrow exception handlers.
9. **LLM in the loop.** Temperature 0 is not deterministic on typical serving stacks. Prevention: bench LLM-free; LLM calls recorded; outputs validated before actions.
10. **Hallucinated or version-wrong facts.** Cross-checks found wrong facts from several LLMs. Prevention: fact ledger with `SOURCE(file:line, 5.0)`, `MEASURED`, or `UNVERIFIED`.
11. **Inherited 3.6 data.** Prevention: version assertion at startup; table-vs-source diff tests.

**NH5 traps that change plans:** N1 monsters no longer death-drop food; N2 no long sword, Excalibur unavailable; N3 falling damage scales with height (gate dig on HP); N4 dig-down at Medusa fills with water next to water (dig.c:606; dry squares map 1 32/67, map 2 46/53, map 3 0/16, map 4 6/51); N5 eels drown levitating heroes (uhitm.c:3389); N6 Elbereth ignored by @, minotaurs, shopkeepers, uniques; no effect in Gehennom; erased by attacking; N7 prayer never works in Gehennom, Hungry is minor trouble; N10 branch stairs share a glyph with plain stairs in the bot's map (`S_brdnstair`); N12 Amulet pickup gives a wish (verify).

---

## Conflicts Between Sources

1. **Mines rate.** STACK.md uses 76% (sections 1, 2.2, 5). ARCHITECTURE.md F1 shows 76% was a `rung >= 1` artifact; key-based is 58.3% (1343/2304). PROJECT.md says 58%. **Use 58%.**
2. **Starvation.** FEATURES, ARCHITECTURE and PROJECT give 14.5% (334/2304). PITFALLS says 25% (Pitfall 2, N1); FEATURES says 25% was pre-exp-37. **Use 14.5%.**
3. **LLM role.** STACK recommends an in-game LLM pilot (Tier 2). FEATURES, ARCHITECTURE and PITFALLS say offline analyst only; FEATURES lists in-game LLM as an anti-feature. **Recommendation:** offline analyst now; Tier 2 pilot as a late gated phase, only after a staged late contract exists and a budget is approved; out of the regression path; never reported as natural rates. Owner decision.
4. **Character.** game.py:40 is `val-hum-fem-neu`; ASCENSION-PLAN-NH5 and Astra used dwarvish lawful. FEATURES says code is truth; STACK recommends a one-flag A/B. **Recommendation:** A/B in Phase 3, then one `CHARACTER` constant.
5. **Pudding farming.** STACK: removed in 3.6.0 (HIGH). PITFALLS: 5.0 status was unverified; the 5.0 source now shows puddings still split on an iron or metal hit [fact:pudding-splits-on-iron-hit] but clones drop no death items [fact:cloned-monsters-drop-no-items]. Both agree it is out of the plan.
6. **Medusa sample.** PROJECT: 25 of 2304. PITFALLS: 13 of about 1152. Same 1.1%. **Use 25/2304.**
7. **Dlvl 15+.** STACK and FEATURES: about 8%. ARCHITECTURE: 7.7%. **Use 7.7%.**
8. **Sokoban solver.** FEATURES: HAVE, 25% reach. ARCHITECTURE: 0/2304 solved, possible detector bug. **Unresolved; verify the detector.**
9. **Lgen.** ARCHITECTURE: natural games do not pass `lgen`. STACK: rewind sets `lgen` 0. Both true.
10. **Phase order** differs across files; reconciled below.
11. **Confidence.** STACK overall MEDIUM (ranking MEDIUM-LOW); others MEDIUM to MEDIUM-HIGH. Overall MEDIUM here.

---

## Implications for Roadmap

### Phase 1: Measurement foundation and proof
**Rationale:** The `lgen` decision changes every result; the funnel metric is mis-specified.
**Delivers:** reproducible install (NLE from gitignored `reference/nle-src` is the blocker); startup version assertion and one `CHARACTER` constant; key-based funnel chain with `funnel_version`; verify `sokoban_solved`; `lgen` pilot (two commits, 400 seeds each, measure q, decide); fresh `main` baseline at 2304 dev seeds plus A/A; stats engine (exact McNemar, e-process, power); claim layer (job-ID trailers, `check_claims.py`, start confirmation, `tool_games`, dev and confirm ranges); route decision with each claim tagged verified-on-5.0 or inherited.
**Addresses:** Pitfalls 5, 6, 7, 9, 14, 15, 16, 18, 20.
**Research flag:** Needs pilot and simulation (q and e-process unmeasured).

### Phase 2: Refactor gate and structure
**Rationale:** No `agent.py` (2142 lines) or `global_logic.py` (1362) extraction without a bit-exact gate.
**Delivers:** frame-hash trace in `GameResult`; `gate` job kind; `gate_quick.py`; first-divergence report; decision-source tags via ordered arbiter; ratchets in `tests/test_structure.py`; `Kind:` trailer; `premerge.sh`; Gehennom awareness as a behaviour-neutral enabler.
**Addresses:** Pitfalls 1, 10, 17.
**Research flag:** None.

### Phase 3: Early wall by system
**Rationale:** About half of endings precede Mines, Oracle and Sokoban; starvation is a system; close calls are about 2/3 of deaths. Triage features and ranking (C2) need no LLM and can pick the order.
**Delivers:** food (E7 shop buying, E8 reserve, E2 pace, E4 explorer, E5 dig when stuck with pick-axe acquisition); safety rules as one phase (E9, E10, E11 with the Elbereth emergency-path question resolved against N6, E12, E13, E14, E16, E17); Mines branch glyph (E3); Excalibur removed; character A/B; death-moment replay as validator; extract `survival` and `food` when touched.
**Addresses:** Pitfalls 1, 8, 10, 20; N1, N3, N6, N7, N10.
**Research flag:** Yes for E4 explorer stuck causes (root cause not found). Standard otherwise.

### Phase 4: Mid-game strength and kit supply
**Rationale:** AC is the measured strength gap; late stages need levitation, a dig tool, reflection, blindfold; the bot rarely owns them.
**Delivers:** AC growth (scroll ID, altar BUC test, enchant armour, gloves and body armour: E18, E19); levitation source (ring ID, Perseus); dig tool ownership (mattock, dwarf pick-axes); reflection, telepathy and blindfold as system rules; poison and fire resistance corpse policy; healing reserve; `needs_met` supply check on arrival snapshots; Medusa reach bar set from first measurement.
**Addresses:** Pitfall 2 (Track B starts); N13.
**Research flag:** Yes for the AC cause (AC-GAP left it open).

### Phase 5: Late abilities as staged contracts
**Rationale:** The late wall is the ability gap; order by measured gap and dependency.
1. **Medusa:** dig-down with attacker clearing and dry-square choice; levitation fallback; `rise_one_level` wired; ravens and crowds with telepathy and blindfold.
2. **Castle:** decide back-entry (exists, forfeits wand) vs front entry with interior (VH, only MR source); wire passtune; wand zap, wrest, recharge; wish order blessed gain level, cursed gain level, MR.
3. **Gehennom:** no prayer, Elbereth or sacrifice (G1 from Phase 2); dig-down loop; Valley walk; new hellfill styles: 7 in 5.0, not 6 [fact:hellfill-has-seven-styles].
4. **Quest:** XL 14 plan, leader, filler levels (fire resistance, lava), Surtur, Bell.
5. **Vlad and Wizard:** Candelabrum with seven candles; Book.
6. **Invocation,** Sanctum, Amulet (wish on pickup), climb past Wizard harassment, Planes (per-plane movement), Astral offer.
**Method per contract:** needs, procedure, pass check, events; staged ability rate with MDE (at least 40 paired seeds); realism check; natural supply rate; arrival bank by replay (fork spike unverified); transfer ratio.
**Addresses:** Pitfalls 2, 3, 4, 19; N4, N5, N7, N8.
**Research flags:** Yes for each: Medusa attack-clearing untested; Castle interior never tried; Quest no code (XL 14 largest unmeasured step); Gehennom and beyond no code, hellfill new, monster table gap unchecked.

### Phase 6: LLM late-game pilot (optional, gated)
**Rationale:** Only plausible source of late improvisation; most expensive and least reproducible. Needs a scripted baseline to beat.
**Delivers (if approved):** code handover predicate; act tool and guards; route tool; cassette record and replay keyed by (turn, state hash, model revision, prompt hash); cost accounting; staged pass rate compared with Phase 5.
**Gate:** drop if it does not match or beat the scripted ability on staged starts; keep transcripts to write rules.
**Budget:** STACK's judgement $10^3 to $10^4 for tens of attempts. Owner decision.
**Research flag:** Yes (harness, record format, model choice, open-book policy).

### Phase 7: Integration, search, clean attempts
**Rationale:** Search multiplies capability and does not create it.
**Delivers:** best scripted or LLM ability per stage in natural play; seed search only past the stop rule (natural per-game about 1e-3); `lgen` screening only for the final attempt, rule published first, headline stays the unscreened funnel (owner decision); clean-run verifier (no rewind, staged or handplay import; one process; no stdin; tagged commit; seed, `lgen`, NLE hash; dumplog shows ascension); final attempts on unused seeds; `bench ascension` replay.
**Research flag:** None for mechanics.

### Phase ordering rationale
- Measurement first (A1 before A3; A2 before experiments).
- Gate before extraction (B1 before B4).
- Early wall before late wall (late stages unreachable naturally until survival and food improve; supply needs Phase 4).
- Staged contracts after the natural funnel is trusted (D after A).
- LLM after scripted contracts; never in the regression path.
- Search last.

### Research flags summary

| Phase | Needs research | Why |
|---|---|---|
| 1 | Pilot and simulation | q and e-process unmeasured |
| 2 | No | standard refactor under a gate |
| 3 | Yes, E4 only | explorer stuck root cause |
| 3 | No, for food, safety, glyph | data exists |
| 4 | Yes, AC cause | open |
| 5 | Yes, each stage | staged only or no code |
| 6 | Yes | harness, budget, record |
| 7 | No | lgen screening is an owner decision |

---

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack (approaches) | MEDIUM | History HIGH; ranking for NH5 MEDIUM-LOW; odds LOW (judgement) |
| Features | MEDIUM-HIGH | code read on `main`; rates from archive, not re-measured; difficulty estimates |
| Architecture | MEDIUM-HIGH | repo and archive computed; statistical parameters need Phase 1 measurement |
| Pitfalls | MEDIUM-HIGH | local evidence HIGH; external single-source LOW or MEDIUM |

**Overall: MEDIUM.** Baseline numbers are solid. Whether any approach reaches a clean ascension has no direct evidence.

### Gaps to address
- No natural data past Medusa's level; staged results are ability evidence only (Phase 5 contracts and supply).
- `lgen` effect on q unknown (Phase 1 pilot).
- `sokoban_solved` 0/2304 while 570 enter Sokoban; verify detector against a hand game (`.planning/hand-games`).
- Character: human neutral vs dwarvish lawful (Phase 3 A/B).
- AC cause open (Phase 4).
- Explorer stuck cause open (Phase 3).
- Pudding farming status in 5.0 (check source).
- NH5 monster-table gap (N9, unchecked; add diff test in Phase 1).
- Quest, Gehennom, Vlad, Wizard, Planes: no code (Phase 5 research).
- Hybrid LLM and bot: no measurements (LOW-MEDIUM).
- NLE fork survival: unverified (LOW).
- Discordant-pair e-process: must pass simulation before use.
- Astra's route through Medusa and the Castle is undocumented; it used wishes, genocide and bones, so do not assume that route.
- dunnolab coding-agent loop: no published results (LOW).

**Owner decisions needed:** (1) LLM role (offline now; gated pilot later, recommended); (2) Castle entry (back-entry vs interior); (3) character A/B approval and fixed `CHARACTER`; (4) seed purity rule for `lgen` screening; (5) LLM budget and whether Phase 6 is funded; (6) Medusa reach bar from first measurement (STACK's 10% and 30% targets are assumptions).

---

## Sources

**HIGH:** Hambro et al. NeurIPS 2021 NetHack Challenge (https://arxiv.org/abs/2203.11889; https://nethackchallenge.com/report.html); HiHack (https://arxiv.org/abs/2305.19240); NLD (https://arxiv.org/abs/2211.00539); NetPlay (https://arxiv.org/abs/2403.00690); BALROG (https://arxiv.org/abs/2411.13543); BotHack (https://github.com/krajj7/BotHack); NetHackWiki Bot and Pudding farming; AutoAscend (https://github.com/maciej-sypetkowski/autoascend); NLE `lgen` in `reference/nle-src/nle/env/base.py` (around lines 489-512); `reference/nethack-5.0.0/doc/fixes5-0-0.txt`; archived bench DB (146,743 games, baseline `72ca0b6`); local `.planning/research/` notes (REWIND-20, LADDER-NH5, MEDUSA-NH5, ASCENSION-PLAN-NH5, ASCENSION-PLAYBOOK-NH5, SURVIVAL-NH5, FOOD-NH5, PRAYER-NH5, ONLINE-2026-10-29); `nethack_screensaver/game.py:40, 317`; `bench/stats.py`; `bench/metrics.py`; `autoascend/ladder.py`.

**MEDIUM:** Kenny, LLM ascension (https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/; https://github.com/kenforthewin/nethack_astra); dunnolab/nethackers PR #114 (https://github.com/dunnolab/nethackers/pull/114); Creus Astra study (https://roger-creus.github.io/blog/astra-craftax-nethack/); LLM agent failure modes (https://kenforthewin.github.io/blog/posts/nethack-agent); Motif, MaestroMotif, LuckyMera (abstracts only; https://arxiv.org/abs/2310.00166, https://arxiv.org/abs/2412.08542, https://arxiv.org/abs/2307.08532); NetHackWiki role difficulty (2011); Agarwal et al. (https://arxiv.org/pdf/2108.13264); NetHack 5.0 release (https://nethack.org/v500/release.html).

**LOW:** Damerell pre-bot essay (https://www.chiark.greenend.org.uk/~damerell/games/nhbot.txt); CodeHack (https://arxiv.org/abs/2609.31076, notes only); checkpointed exploration page (https://neurips.cc/virtual/2026/161943); Thinking Machines nondeterminism (https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/); Henaff essay (https://mikaelhenaff.substack.com/p/first-nethack-ascension-and-insights); BALROG aggregator leaderboards (conflicting, not used).

---
*Research completed: 2026-11-12. Ready for roadmap once the six owner decisions above are recorded.*
