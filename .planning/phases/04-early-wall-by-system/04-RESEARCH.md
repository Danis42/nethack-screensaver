# Phase 4: Early Wall by System: research (2026-11-17)

Inline research (owner preference). Sources: Monk baseline job 23 (partial), the 5.0 source, existing research notes
(FOOD-NH5.md, SURVIVAL-NH5.md, PRAYER-NH5.md, MINES-ENTRY-NH5.md, AC-GAP-NH5.md), the bot code.

## Where Monk games end (first 1,000 seeds of job 23)

`uv run python -m bench.triage b2b2bbe6d1c9341319b02e937aac7f37ec4db14d --lo 1000 --hi 2000` (rules: bench/triage_groups.py):

| Group | Share | Stage gain | Dlvl10 gain | Phase 4 requirement |
|---|---|---|---|---|
| too_deep (melee 4+ levels below XL) | 12.8% | 46.7 | 2.4 | SURV-02 (pace the descent) |
| melee (should handle) | 13.7% | 44.6 | 53.4 | combat kit: Monk shield (04-01) |
| groups | 11.1% | 41.1 | 45.9 | combat kit, safety |
| starvation | 7.8% | 34.4 | 35.1 | SURV-02 food |
| strong (3+ difficulty above XL) | 8.5% | 30.8 | 32.6 | SURV-02 pacing, SURV-05 |
| fast | 9.6% | 29.6 | 31.8 | SURV-05 / Elbereth |
| ranged | 7.8% | 25.6 | 23.3 | SURV-05 ray bounces |
| unicorns | 5.6% | 21.3 | 23.0 | SURV-05 cross-aligned unicorns (04-02) |
| stuck explorer | 8.5% | 15.5 | 23.1 | SURV-03 |
| passive | 3.8% | 13.9 | 18.5 | SURV-05 |

Versus the Valkyrie (job 7): starvation 13.9% -> 7.8%; too_deep and unicorns are new at the top. The ranking is redone
on the full job 23 before each plan's pre-registration.

## Findings (5.0 source)

- **A shield costs a Monk most of martial arts.** `uhitm.c:397-401`: a Monk without weapon and shield gets
  +(XL/3 + 2) to hit (`else if (!uwep && !uarms)`). `uhitm.c:733-752` `double_punch()`: an extra strike at Skilled+
  (20-80%) only with `!uwep && !uarms`. `uhitm.c:1779`: `hmd.unarmed = !uwep && !uarm && !uarms`, the unarmed
  special-hit path (`uhitm.c:1827`). Baseline Monks often wear Uruk-hai, elven or dwarvish shields (job 23 end gear).
  The bot already keeps Monks bare-handed (inventory.py:1165) and out of body armour (inventory.py:1265).
- **Unicorns.** Co-aligned unicorns are generated peaceful (`makemon.c:1340`); cross-aligned ones are hostile and try
  to stay off the hero's lines (`monmove.c:1939-1948`, NOTONL) and teleport when stuck (`monmove.c:2064-2066`).
  The bot "freely engages in melee" with any unicorn at HP >= 15 (combat/movement_priority.py:64-67): the
  deaths come from chasing them.
- **Excalibur dip** still runs (global_logic.py:1281, 1295) for every role: 3.6-era and useless for a Monk (SURV-07).

## Order of work (by triage gain, cheapest first within a tier)

1. 04-01 Monk kit: no shield (melee, groups, strong). Small, sourced, measurable: the Phase 4 tracer.
2. 04-02 Cross-aligned unicorns: do not chase; fight only when cornered (5.6%).
3. 04-03 Descent pacing (too_deep 12.8%, strong 8.5%): research the XL/depth rule first.
4. 04-04 Food system (starvation 7.8%; SURV-02 reserve, shops).
5. 04-05 Stuck explorer root cause and fix (8.5%; SURV-03).
6. 04-06 Remaining class-wide safety, dungeon awareness, 3.6 removals (SURV-05, KIT-04, SURV-07).
CODE-03 extractions ride along as gated refactors in the files each plan touches.

## Measurement template (per behaviour plan)

SPRT on a stage metric next to the change, alpha 0.05, declared power 0.8, a trigger where the change has a clear
firing condition, pilot for psi only, dev then confirm (gate field). Each plan writes its pre-registration before
any candidate game.
