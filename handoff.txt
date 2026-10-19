# Where we are (2026-10-20)

Version 0.2.0 is released; everything below is on local `main` after it (not yet released).
Benchmark numbers and every experiment: `autoascend/PORTING.md`.

## Done since 0.2.0 (kept)

- Never melee a seen floating eye (gaze freezes 6-8 → 0-1 per 192 games).
- Bot errors make the bot replan instead of ending the game (`panic_on_errors=True`);
  doorways that refuse diagonal moves are remembered. Crashes went down; the rest end as
  "Cyclic Panic", which now names the errors behind it.
- Fixed: a live-solved Sokoban level crashed the game (missing stat).
- Hunger: eat carried food when Weak instead of praying.
- A character with no new level or plan step for 2500 turns gives up its route and dives;
  divers inside the Gnomish Mines dive down the Mines.
- Human, elven and orcish pilgrims do Sokoban before the Mines.
- Benchmark extras: `--out file.jsonl`, results carry XP level, Elbereth count, panics,
  stuck-diving count.

## Tried and dropped (kept as git stashes or reverts)

Resting on Elbereth, waiting for peaceful monsters to clear a path, a smarter search for
hidden passages, digging down, pushing boulders. None improved the benchmark.

## How to measure

- Use 576 games per change (`uv run python scripts/benchmark.py -n 576 -j 11 --out x.jsonl`,
  ~15 min). 192-game runs proved too noisy.
- One change per measurement; to measure a commit while working on the next, use a git
  worktree and run it with `PYTHONPATH=<worktree> .venv/bin/python scripts/benchmark.py`.

## Next steps (proposed, pick one)

1. Crashes: run games, read the "Cyclic Panic" messages, fix the most common cause
   (9-18 of 576 games end this way).
2. Fight soldier ants from corridors so they cannot surround the character.
3. Step out of the line of fire of monsters that zap wands (largest group of killers,
   about 12% of deaths; striking hits when d20 < 10 + armour class).

Your preference so far: an exciting deep run that dies beats a boring escape.
