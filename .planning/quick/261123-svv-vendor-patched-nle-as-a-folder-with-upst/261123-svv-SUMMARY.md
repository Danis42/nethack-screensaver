---
quick_id: 261123-svv
status: complete
date: 2026-11-23
---

# Summary: patched NLE vendored as vendor/nle

- `vendor/nle/`: tree of nle-screens `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72` (1,420 files, 33 MB), fixed
  version `1.3.0.post21+screens.nh5`; `vendor/nle/SCREENS.md` credits NLE and NetHack and lists our changes;
  `vendor/nle-screens.patch` = `git diff 2a0e3baf cb9d6572` (10 files, +139/-69). Upstream base
  `2a0e3baf10316d3706801ce845d4adb6373ac264` verified on NetHack-LE/nle.
- `pyproject.toml`: `nle = { path = "vendor/nle" }`.
- `bench/nle_build.py`: a folder build is identified by `tree:<git tree id of vendor/nle>` (`+dirty` when edited);
  new env id `154519408e03431e` (jobs 1-25: `a8f58c2fda006264`-style ids from commit cb9d6572).
- Docs: HANDOFF, README, LICENSE, publish review.
- Verify: `uv run pytest` 915 passed, 6 skipped; seed 1001 replays identically to job 23 (turns 4735, score 3464,
  killed by a plains centaur).
