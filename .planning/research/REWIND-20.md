# Infinite lives on 20 seeds (2026-11-02)

Tool: scripts/rewind.py (commit after 87e0af5 game code; NLE screens-nh5 cb9d6572f). Seeds 0-19, up to 60 lives, per death:
5 reseeds 100 turns back, then 5 at 1000, then 5 at 5000; "saved" = lives 200+ turns past the old death.
Raw: scratchpad rewind20.jsonl (not kept).

- 182 deaths. Saved by a reseed 100 back: 123 (68%); 1000 back: 29 (16%); 5000 back: 16 (9%); never: 14 (8%).
- Hunger at death (starved or fainted): 44 of 182 (24%), but 12 of the 16 deaths that needed 5000 turns. Late fixes
  cannot save a starving game; food is decided thousands of turns earlier.
- Deaths needing 1000+ turns had worse AC at death (median 0 to +1) than deaths saved at 100 (median -2), same XL 10.
- Ceiling with infinite lives: best seed 0 reached Medusa's level (rung 9) at T17317; no seed passed Medusa. Max Dlvl 25.
  Final rungs: 9 x1, 8 x4, 7 x6, 6 x3, 4 x1, 3 x1, 2 x1, 1 x2, 0 x1.
- Why seeds stopped: 8 no rewind saved them, 6 hit 60 lives (seeds 2, 10, 7 stuck in early levels: seed 2 starved on Dlvl 3
  at T98034), 4 ABORTED (no-progress timeout: the bot stops acting), 2 crashed (Cyclic Panic on an assertion).

Read: two thirds of deaths are close calls one reroll avoids; the rest are older (food, armour). Even with infinite lives
the bot does not get past Medusa: crossing her level is a missing ability, not a survival problem. Stuck/abort and
panic endings also cap progress.
