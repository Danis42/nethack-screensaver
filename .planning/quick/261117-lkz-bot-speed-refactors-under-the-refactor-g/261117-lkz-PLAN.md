---
quick_id: 261117-lkz
slug: bot-speed-refactors-under-the-refactor-gate
date: 2026-11-17
mode: quick (inline)
branch: speedup
---

# Quick task: bot speed refactors (efficiency recommendation 4, owner-approved 2026-11-17)

Make the bot cheaper per game without changing a single decision. Every change must replay identically:
frame-hash digests on fixed seeds while the bench is busy, then the refactor gate (100 seeds) when it is free.
Ratchets: no pinned file grows.

Batch 1 (leaf functions, from cProfile and a stdlib sampling profile of Monk games):
1. `isin`: memo key from the arguments as given (normalise only unhashable lists/sets); moved with its kernels
   to `autoascend/isin.py` (utils.py 190 -> 144 lines), re-exported from utils.
2. `any_in`: fused numba kernel, early exit, no boolean array.
3. `Item`: corpse/statue/glob objects looked up once; container check `O.Container in map(type, objs)`.
4. `ItemPriority._split.add_item`: unit weight computed once per call.
