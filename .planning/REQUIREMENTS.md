# Requirements: NetHack Screensaver: Ascension

**Defined:** 2026-11-12
**Core Value:** The bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds and no reseeding. Every claim of progress toward it can be checked.

## v1 Requirements

Requirements for the first clean ascension. Each maps to roadmap phases.

### Measurement and Proof (MEAS)

- [x] **MEAS-01**: A fresh clone can install and run the bot and bench (`uv sync` works; the NLE build is reproducible, not only from the gitignored `reference/nle-src`)
- [x] **MEAS-02**: The bench reports a natural-game funnel by stage keys (Mines, Minetown, Oracle, Sokoban, Sokoban solved, Mines' End, Dlvl 15+, Quest portal, Medusa, Castle, Gehennom, ... Astral, ascended) with Wilson confidence intervals; the old `rung` metric is no longer used for decisions
- [x] **MEAS-03**: The `sokoban_solved` detector is checked against a known game, and the 0/2304 result is explained (detector bug fixed, or the bot really never solves it)
- [x] **MEAS-04**: The `lgen` level-generation seed is piloted (two commits, about 400 seeds each), its effect on paired comparisons is measured, and the decision whether to use it in the bench is recorded
- [x] **MEAS-05**: A fresh natural baseline of `main` exists in the live bench database, plus an A/A run showing reproducibility
- [x] **MEAS-06**: Experiments use a paired statistical test valid under repeated checking (exact McNemar and an always-valid sequential test), validated by simulation; the minimum detectable effect and sample size are fixed before a run
- [x] **MEAS-07**: Seed ranges are split into dev, confirm and final ranges; confirm seeds are only used at phase gates, final seeds only for clean attempts
- [x] **MEAS-08**: Staged, scenario and rewind runs are stored with job IDs in their own table, separate from natural games, and never shown as natural results
- [x] **MEAS-09**: Every progress claim is backed by a job ID, full commit hash or reproducible query; a check script rejects claims without one; a job counts as "started" only once its first game row exists
- [x] **MEAS-10**: NetHack facts used by the bot or plans are tagged as verified against the 5.0 source, measured, or unverified (fact ledger), so 3.6 or LLM-invented knowledge can't slip in unnoticed

### Code Health (CODE)

- [ ] **CODE-01**: A refactor gate replays a fixed seed set and compares a frame-hash trace; a refactor commit must be bit-identical and the gate reports the first divergence otherwise
- [ ] **CODE-02**: Commits are marked as refactor or behavior change; behavior changes name the funnel stage and metric they are meant to move, and the experiment that proves it
- [ ] **CODE-03**: `agent.py` and `global_logic.py` are split into system modules (perception, actions, navigation, an ordered decision arbiter, survival, food, resources, stages) as the work touches them, each extraction passing the refactor gate
- [ ] **CODE-04**: Automated ratchets stop the code from regressing (file size limits, no new bare `except`, no new dependencies on the agent internals)

### Early Wall: Survival by System (SURV)

- [ ] **SURV-01**: Failure triage replays deaths, extracts features and ranks system-level causes by expected funnel gain, so the next fix is chosen by evidence (no LLM needed for this step)
- [ ] **SURV-02**: Food system: the bot keeps a food reserve, buys food in shops, paces its descent, and starvation drops measurably below the 14.5% baseline
- [ ] **SURV-03**: Getting stuck is fixed by system (explorer completion, digging out with an owned dig tool), and the "never reaches the Mines" share drops measurably
- [ ] **SURV-04**: The bot recognises the Mines branch staircase (NetHack 5 branch-stair glyph) and goes straight to it
- [ ] **SURV-05**: Class-wide safety rules, built and tested together: prayer timeout and lockout, no prayer in Gehennom, passive-damage monsters, cross-aligned unicorns, peacefuls (including while hallucinating), ray bounces
- [ ] **SURV-06**: Research picks the best character for the first ascension (role, race, alignment) from evidence, a bench A/B confirms it, and one `CHARACTER` constant holds the result
- [ ] **SURV-07**: Dead or wrong 3.6-era behaviour is removed (e.g. the Excalibur dip, which is impossible for a neutral hero in 5.0)

### Mid-Game Kit and Strength (KIT)

- [ ] **KIT-01**: AC improves toward human medians at Medusa (cause of the AC gap found first; scroll identification, altar curse testing, enchant armour, worn armour slots)
- [ ] **KIT-02**: The bot reliably owns a levitation source and a dig tool before the late game
- [ ] **KIT-03**: The bot gets and uses reflection, telepathy, a blindfold, and poison and fire resistance (corpse policy) as system rules
- [ ] **KIT-04**: The bot knows which dungeon it is in, including Gehennom, and applies its rules (no prayer, no Elbereth, no sacrifice there)
- [ ] **KIT-05**: Natural arrivals at Medusa are checked against the late-game kit ("needs met" rate), so staged ability results can be turned into a predicted natural rate

### Late-Game Abilities (LATE)

Each ability is built as a contract (needs, procedure, pass check), tested on staged starts, and reported with its staged pass rate next to the natural arrival rate.

- [ ] **LATE-01**: Medusa: cross or dig past Medusa's level (dig-down with dry-square choice and attackers cleared; levitation crossing as fallback), and return upward when needed
- [ ] **LATE-02**: Castle: both routes (back entry, and front entry by passtune with the interior and the wand of wishing) are built as staged tests; the one with the higher pass rate is kept
- [ ] **LATE-03**: Wishes: if the wand is obtained, the bot zaps, wrests and uses its wishes in a fixed priority order (e.g. magic resistance, gain level)
- [ ] **LATE-04**: Gehennom: the bot descends through the Valley and Gehennom mazes to Vlad's Tower and the Wizard's Tower levels
- [ ] **LATE-05**: Quest: the bot reaches XL 14, completes the Quest and gets the Bell of Opening
- [ ] **LATE-06**: Vlad's Tower and the Wizard's Tower: the bot gets the Candelabrum and the Book of the Dead
- [ ] **LATE-07**: Invocation: the bot performs the invocation ritual, enters the Sanctum and takes the Amulet
- [ ] **LATE-08**: Endgame: the bot climbs back with the Amulet, passes the Elemental Planes and offers the Amulet on the Astral Plane

### LLM Pilot (PILOT)

- [ ] **PILOT-01**: An LLM offline analyst labels death dossiers with system-level causes, checked against about 30 hand labels before its output is trusted; a local model (Ollama) is tried first
- [ ] **PILOT-02**: An LLM can play the game through MCP tools (observe, act with a few keys and stop on change, route with the bot's pathing). Two backends: a local model via Ollama on the owner's RTX 4070 Ti (12 GB), and a Claude Code session on the existing subscription. No additional cost of any kind
- [ ] **PILOT-06**: Local models are compared on the analyst and pilot tasks (quality vs speed on 12 GB VRAM), and the choice per task is recorded; Claude Code is used only where the local model isn't good enough
- [ ] **PILOT-03**: The scripted bot hands over to the pilot at defined points (e.g. arriving at Medusa's level, or when stuck) and takes back control afterwards
- [ ] **PILOT-04**: Every pilot decision is recorded so a game can be replayed; pilot runs stay out of the deterministic bench and are reported separately
- [ ] **PILOT-05**: The pilot's staged pass rate per late stage is compared with the scripted ability; per stage, the better one is kept

### Clean Ascension (ASC)

- [ ] **ASC-01**: A clean-run verifier checks a game: one process, no rewind, staged start or hand input, tagged commit, recorded seed and `lgen`, dumplog showing the ascension
- [ ] **ASC-02**: If dungeon screening is used, the selection rule is written down and committed before the attempt
- [ ] **ASC-03**: One fresh, clean ascension is recorded (seed, commit, dumplog) and can be reproduced from the seed

## v2 Requirements

Deferred. Tracked but not in the current roadmap.

### Bonus

- **BONUS-01**: Ascend with other characters (every role as a stretch goal)
- **BONUS-02**: A measurable ascension rate on the bench (not just one game)
- **BONUS-03**: Ascensions happen in the real screensaver, not only in bench runs
- **BONUS-04**: Pet management, protection buying, bag of holding and other "nice to have" kit

## Out of Scope

| Feature | Reason |
|---------|--------|
| Counting a rewound, reseeded or staged game as the ascension | The goal is one clean game; these are test tools only |
| Per-monster special-case fixes as the main method | Caused the last session's whack-a-mole and messy code |
| Imitation learning or reinforcement learning | Research shows they plateau far below AutoAscend (score ~1,000 vs ~8,500) |
| Whole-game LLM play from turn 1 | Weak in the early game (NetPlay Dlvl 2.6) and too slow for 15-25k turn games |
| LLM calls inside the deterministic bench | Breaks paired comparisons; pilot runs are reported separately |
| Any additional cost (paid API tokens, cloud GPUs, services) | Owner wants no extra cost; only local models and the existing Claude subscription |
| Farming or exploits without the owner's approval | Allowed in principle, but each one must be proposed to the owner first so they can judge the behaviour |
| In-game lookahead by forking the game | A rewind in disguise |
| Changing the screensaver experience | Works today; only touched if the bot work needs it |
| NetHack 3.6 support | The target is NetHack 5.0 |
| Heavy session bookkeeping ("state:" commits, hand-kept trackers) | Progress lives in the bench and git |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEAS-01 | Phase 1 | Complete |
| MEAS-02 | Phase 1 | Complete |
| MEAS-03 | Phase 1 | Complete |
| MEAS-04 | Phase 1 | Complete |
| MEAS-05 | Phase 1 | Complete |
| MEAS-06 | Phase 1 | Complete |
| MEAS-07 | Phase 1 | Complete |
| MEAS-08 | Phase 1 | Complete |
| MEAS-09 | Phase 1 | Complete |
| MEAS-10 | Phase 1 | Complete |
| CODE-01 | Phase 2 | Pending |
| CODE-02 | Phase 2 | Pending |
| CODE-03 | Phase 4 | Pending |
| CODE-04 | Phase 2 | Pending |
| SURV-01 | Phase 2 | Pending |
| SURV-02 | Phase 4 | Pending |
| SURV-03 | Phase 4 | Pending |
| SURV-04 | Phase 2 | Pending |
| SURV-05 | Phase 4 | Pending |
| SURV-06 | Phase 2 | Pending |
| SURV-07 | Phase 4 | Pending |
| KIT-01 | Phase 5 | Pending |
| KIT-02 | Phase 5 | Pending |
| KIT-03 | Phase 5 | Pending |
| KIT-04 | Phase 4 | Pending |
| KIT-05 | Phase 5 | Pending |
| LATE-01 | Phase 5 | Pending |
| LATE-02 | Phase 5 | Pending |
| LATE-03 | Phase 5 | Pending |
| LATE-04 | Phase 6 | Pending |
| LATE-05 | Phase 6 | Pending |
| LATE-06 | Phase 6 | Pending |
| LATE-07 | Phase 6 | Pending |
| LATE-08 | Phase 6 | Pending |
| PILOT-01 | Phase 3 | Pending |
| PILOT-02 | Phase 3 | Pending |
| PILOT-03 | Phase 3 | Pending |
| PILOT-04 | Phase 3 | Pending |
| PILOT-05 | Phase 5 | Pending |
| PILOT-06 | Phase 3 | Pending |
| ASC-01 | Phase 7 | Pending |
| ASC-02 | Phase 7 | Pending |
| ASC-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓
