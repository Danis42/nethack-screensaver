---
phase: 01-midgame-survival
plan: 04
subsystem: analysis
tags: [nld-nao, ttyrec, prayer, hunger, human-baseline, nle-dataset]

requires: []
provides:
  - "autoascend/prayer.py: PRAYER_START, SUCCESS_MARKERS, FAILURE_MARKERS and prayer_outcome(lines) -> success | failed | unknown (standard library only, strings taken from human games)"
  - "scripts/nld_study.py: prayers (message census, cohorts random / died-praying / wrath) and food (three-cohort table) over NLD-NAO ttyrecs, read-only, fixed sampling seed"
  - "01-HUMAN-STUDY.md: prayer message census and the food/prayer table for Dlvl 4-12 (got through versus starved) with method, commands and findings"
affects: [01-05, 01-06, 01-07, 01-08]

actuals:
  tokens: 14900
  tasks: 2
  commits: 2
plan_head_before: 07e51003ffca3ff5430f9993f20dd7ca36e4a04b
plan_head_after: 8c52c31439a072d4f5833ecae145ba37f3250812
commits: 2

tech-stack:
  added: []
  patterns:
    - "Ttyrec studies stream (gameid, frame) from nle.dataset.TtyrecDataset, feed one GameScanner per game and keep only aggregates; game identifiers never leave scan_games"
    - "Screens are garbled sometimes (windows over the status lines, half-drawn counters, 80-column cuts): readings are validated before use (BandClock) and a game counts only if its status line was followed for 80% of its real length"
    - "Markers in autoascend/prayer.py are god-name-free substrings, so one tuple covers all pantheons"

key-files:
  created:
    - scripts/nld_study.py
    - autoascend/prayer.py
    - tests/test_prayer.py
    - tests/test_nld_study.py
    - .planning/phases/01-midgame-survival/01-HUMAN-STUDY.md
  modified: []

key-decisions:
  - "A prayer that shows no shimmering light and ends with 'You die...' is classified failed: an unsafe prayer leaves the hero helpless and 134 of the 141 human games that ended 'while praying' show monsters hitting then 'You die...'"
  - "A failed prayer with no god-like answer line stays 'unknown', never 'failed': no human string shows it"
  - "Human prayer failure is about 2.8% on Dlvl 4-12 (15 of 542) against the bot's 12%; human starvers die early (median game turn 2,206) while the bot's starvation median is 7,828"
  - "Eating events are counted per meal (taste line + finish line + interruptions merge), so rates are comparable across cohorts"

patterns-established:
  - "One question, one command: the study file lists the exact nld_study.py command and sampling seed that produced each table"

requirements-completed: [SURV-02]

coverage:
  - id: D1
    description: "Prayer message census from human games and a tested pure classifier prayer_outcome using only census strings"
    requirement: SURV-02
    verification:
      - kind: unit
        ref: "tests/test_prayer.py (one case per marker, god-name independence, empty/unrelated unknown)"
        status: pass
      - kind: other
        ref: "uv run python scripts/nld_study.py prayers --games 30 (315 prayers over 400 games in the committed census)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Food and prayer habits of humans who got through Dlvl 4-12 versus humans who starved there, on the same yardsticks"
    requirement: SURV-02
    verification:
      - kind: unit
        ref: "tests/test_nld_study.py (eat_event, band_turns, BandClock guards, summarize, food_table)"
        status: pass
    human_judgment: true
    rationale: "The table is measured, the five findings are interpretation; plan 01-08 decides what the starvation diagnosis takes from it"

duration: 31min
completed: 2026-10-23
status: complete
---

# Phase 1 Plan 04: Human prayer and food study Summary

**NLD-NAO ttyrec study: census-backed prayer_outcome classifier and a three-cohort Dlvl 4-12 food/prayer table showing humans fail 2.8% of prayers (bot 12%) and that human starvers die early, not late like the bot**

## Performance

- **Duration:** 31 min
- **Started:** 2026-10-23T16:46:00Z
- **Completed:** 2026-10-23T17:17:00Z
- **Tasks:** 2
- **Files modified:** 5 (all new)

## Accomplishments

- `scripts/nld_study.py prayers` decodes recorded 3.6 games and censuses the messages after "You begin praying to": 315 prayers over 400 random Dlvl 4+ games, plus the 141 games that ended "while praying" and the 27 killed by an angry god, to see how a bad prayer reads. The table is in 01-HUMAN-STUDY.md.
- `autoascend/prayer.py` (standard library only) classifies the lines after a prayer as success, failed or unknown with markers taken from that census (shimmering light and "starts to attack you, but pulls back" for success, "is displeased.", the angry god's lines and "You die..." for failure). Over the census prayers it gives success 293, failed 7, unknown 15 (random cohort).
- `scripts/nld_study.py food` measures prayers per 1000 turns, gap between prayers, share of prayers while Weak or worse, share failed, eating events per 1000 turns and share of turns Hungry/Weak on Dlvl 4-12 for 292 usable survivor games and two starved cohorts (143 and 117 games). Findings are in 01-HUMAN-STUDY.md: survivors Hungry+ 3.9% of band turns versus about 21% for starvers; both eat 2.8-2.9 times per 1000 turns; survivors pray once per 6,700 turns with a median gap of 2,715 (25th percentile 927) against the bot's 400/500-turn limits; survivors fail 2.8% of prayers, starvers 14.9%.

## Task Commits

1. **Task 1: Prayer messages from human games decoded end to end into a tested classifier** - `abf39e0` (feat)
2. **Task 2: Food and prayer timing of humans who got through Dlvl 4-12 versus humans who starved there** - `8c52c31` (feat)

**Plan metadata:** committed with this SUMMARY (docs: complete plan)

_Note: TDD order was test-first for `nld_study.py` helpers (collection error before the module existed) and for Task 2 helpers (22 failures before the code). `prayer.py` markers can only be written after the census, so its tests were written alongside the markers._

## Files Created/Modified

- `scripts/nld_study.py` - ttyrec readers (`message_line`, `status`, `GameScanner`, `BandClock`, `band_turns`, `eat_event`), `summarize`/`food_table`, `prayers` and `food` subcommands (`--db`, `--games`, `--seed`, `--cohort`, `--jobs`, `--write`)
- `autoascend/prayer.py` - `PRAYER_START`, `SUCCESS_MARKERS`, `FAILURE_MARKERS`, `prayer_outcome`; not used by the bot yet
- `tests/test_prayer.py` - classifier cases, one per marker, god-name independence
- `tests/test_nld_study.py` - helpers on synthetic 24x80 frames, scanner behaviour, band clock guards, summary and table rows
- `.planning/phases/01-midgame-survival/01-HUMAN-STUDY.md` - prayer census, failure-string sources, food/prayer table, method, commands, findings

## Decisions Made

- "You die..." inside the prayer window is a failure marker, and a failed prayer with no answer line is `unknown`, never guessed `failed` (see key-decisions).
- Eating events are counted per meal rather than per message so that a corpse (taste line plus finish line) is not two events.
- The study keeps only aggregates and `<god>`-normalised lines; the `food` and `prayers` outputs never print a game identifier, name or uid.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Extra census cohorts for failure strings**
- **Found during:** Task 1 (census over 30, then 400 random games)
- **Issue:** Humans fail so rarely that the random sample held 7 failed prayers and no angry-god lines, so `FAILURE_MARKERS` could not be taken from the census as the plan requires.
- **Fix:** `prayers --cohort died-praying` (all 141 games ending "while praying") and `--cohort wrath` (all 27 games killed by an angry god); their tables are in 01-HUMAN-STUDY.md and the markers come from them.
- **Files modified:** scripts/nld_study.py, 01-HUMAN-STUDY.md
- **Verification:** identical census re-run with the final code; `tests/test_prayer.py`
- **Committed in:** abf39e0

**2. [Rule 1 - Bug] Garbled screens made band turns up to 100 times too large**
- **Found during:** Task 2 (first full `food` run: 25.9 million band turns for 298 games)
- **Issue:** a window over the status lines leaves attribute-line pieces and stale digits (`T:307219`, `T:1472812`); 13 of 300 survivor games had turn counters far beyond the real game length. Half-drawn counters and covered status lines also hide stretches of a game.
- **Fix:** status read from row 23 only and rejected if it holds `St:`..`Ch:`; `BandClock` ignores readings that go backwards, exceed the game's real `turns`, or jump ahead by over 500 turns without confirmation by the next reading; a game counts only if its status line was followed for 80% of its real length (excluded games are counted in the table).
- **Files modified:** scripts/nld_study.py, tests/test_nld_study.py
- **Verification:** unit tests for each guard; re-run gives 3.7 million band turns for 292 games
- **Committed in:** 8c52c31

**3. [Rule 2 - Missing critical] Third column "starved, and died on Dlvl 4-12"**
- **Found during:** Task 2 (28 of 153 starved games died above Dlvl 4 after a brief visit, with 1-84 band turns)
- **Issue:** the plan's cohort (maxlvl 4-12) includes people who starved on Dlvl 1-3; the human yardstick for "starved there" should also exist for the stricter reading.
- **Fix:** an extra column using `deathlev between 4 and 12` (125 games); the two-cohort table the plan asks for is the first two columns.
- **Files modified:** scripts/nld_study.py, 01-HUMAN-STUDY.md
- **Committed in:** 8c52c31

---

**Total deviations:** 3 auto-fixed (1 bug, 2 missing critical)
**Impact on plan:** all three needed for numbers that can be trusted; no scope beyond the study. Extra table rows (gap quartile, failure after short/long gap) and `--jobs`/`--write` options were added for plan 01-08's comparison.

## Issues Encountered

- The `Dlvl` seen on the status line is a depth, so Mines (Dlvl 3-13) and Sokoban count inside the band for both cohorts; stated in the study file.
- Games where the player did not enable `T:` cannot be timed; 8 of 300 survivor games and 3 of 153 starved games were excluded (or under 80% coverage) and are reported.

## Known Stubs

None. `autoascend/prayer.py` is intentionally not wired into the bot yet (plan: unused until an experiment needs it); `scripts/seeded_report.py` consumption is plan 01-08.

## Threat Flags

None. The scripts only read the NLD-NAO database and ttyrecs; T-01-08 holds (only aggregates and `<god>`-normalised lines are written; `grep -cwE 'gameid|uid'` on the study file prints 0) and T-01-SC holds (`git log abf39e0^..HEAD -- pyproject.toml uv.lock` prints nothing).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-08 can import `autoascend.prayer.prayer_outcome` and compare the bot's starvation timeline with the table in 01-HUMAN-STUDY.md.
- Not measured here: what each human meal was worth (corpse versus ration), and the hunger-prayer gap by role; the study file lists the method limits.

## Self-Check: PASSED

- Created files exist: scripts/nld_study.py, autoascend/prayer.py, tests/test_prayer.py, tests/test_nld_study.py, 01-HUMAN-STUDY.md
- Commits abf39e0 and 8c52c31 are ancestors of HEAD
- `uv run pytest -q -m ""`: 401 passed, 5 skipped, 5 xfailed, 1 xpassed (exit 0)

---
*Phase: 01-midgame-survival*
*Completed: 2026-10-23*
