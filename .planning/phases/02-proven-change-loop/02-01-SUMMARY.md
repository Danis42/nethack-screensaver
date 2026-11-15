---
phase: 02-proven-change-loop
plan: 01
status: complete
requirements: [CODE-02, CODE-04]
commits:
  - bb308c7214d1cdc54a3e5cfbe8c8ffc9112cf7a1  # hooks, rule, tests, README
  - bd79cef50a4d097493d7a2fb6f32f283b78a86a2  # PHASE2_START marker
  - 0efb387874802138777049cf0dba01d581aabbde  # ratchets
---

# 02-01 Summary: commit labels and ratchets

- `githooks/commit_kind.py` holds the label rule; `githooks/commit-msg` refuses, `githooks/prepare-commit-msg` adds
  `Kind: docs` for documentation-only commits (owner approved the docs label, 2026-11-15). Installed with
  `bash scripts/install_hooks.sh` (core.hooksPath = githooks).
- Probe in a scratch repo: an unlabelled commit of `autoascend/a.py` was refused ("Kind: missing ..."); a
  `.planning/` commit got `Kind: docs` added.
- `githooks/PHASE2_START` = bb308c7214d1cdc54a3e5cfbe8c8ffc9112cf7a1; `test_log_since_phase2_start_is_labelled`
  checks every commit from there.
- `tests/ratchets.json`: 110 files pinned at their length (agent.py 2142, global_logic.py 1382), one bare except
  (`autoascend/item/item_manager.py`), one agent import (`autoascend/env_wrapper.py`), new-file cap 600.
- Violation probes (each reverted): one extra line in agent.py -> 1 failed; a bare except in castle.py -> 2 failed
  (length and except); a new module with `from .agent import Agent` -> 1 failed.
- Full suite: `uv run pytest -q` -> 870 passed, 6 skipped.

Deviation: the hooks also exempt `fixup!`/`squash!`/`Merge` messages and merge commits.
