---
quick_id: 261123-svv
type: quick
mode: inline (owner: no subagents)
---

# Vendor the patched NLE as a folder of this repo, with upstream credit

Owner decision (2026-11-23): no separate `nle-screens` repo and no GitHub fork. The patched NLE lives in this
repo as a folder that names its upstream (NetHack-LE/nle, branch NetHack-5-upgrade, commit 2a0e3baf) and holds
the updated files.

## Tasks

1. `vendor/nle/`: the tree of nle-screens `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72`; static version in its
   `pyproject.toml` (setuptools-scm cannot read a version from a subfolder).
2. `vendor/nle/SCREENS.md` + `vendor/nle-screens.patch`: upstream, base commit, licence (NGPL), our 9 changes.
3. `pyproject.toml`: `nle = { path = "vendor/nle" }`; `uv lock`; `uv sync`.
4. `bench/provenance.py`: an NLE installed from a folder is identified by the git tree hash of `vendor/nle`.
5. Docs: README, HANDOFF, LICENSE note, publish review.

## Verify

- `uv run pytest` passes; seed 1001 replays identically to job 23.
