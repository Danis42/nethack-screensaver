---
phase: 02-proven-change-loop
plan: 02
status: complete
requirements: [CODE-01]
commits:
  - a3d1c723d83fcf52be65e229d9d8a323fb4e2bbd  # frame-hash trace in the worker
  - c79d0ef5bd9da8385fbdfc323f47d7d828df2827  # gate tool job
  - 536089e87fe35ef4097af477318bdc38995565ad  # dive_stairs refactor, Gate: job 9
  - f56684e83117f555a5d56a3075007cdddb4e1998  # gate stores rows as games finish
jobs: [9, 10, 11]
---

# 02-02 Summary: refactor gate

- `bench/frame_trace.py` hashes screen text and status numbers per env step; `bench/worker.py` plays
  `trace <seed> <path>` lines through run_game's on_frame, so bot code is untouched. Seed 900 traced twice:
  identical digest over 13,023 steps.
- `python -m bench.gate <candidate> --baseline <ref>` plays seeds 900-999 for both, records a `gate` tool job,
  rows in tool_games (one per game, written as it finishes since f56684e83117f555a5d56a3075007cdddb4e1998),
  verdict pass/fail with first divergence (seed, step, turn); watchdog seeds skipped (at most 2).
- Proof (02-GATE-PROOF.md): job 9 pass (100/100 identical) for the dive_stairs move; job 11 fail (first
  divergence seed 900, step 407, turn 271/272) for a deliberate change; job 10 shows a change that never fires
  passes.
- The commit-label log test checks that a bot-code refactor's `Gate: job N` passed on the same tree.

Deviations:
- The gate is a command (`python -m bench.gate`), not an HTTP/MCP job kind: the "no file may grow" ratchet makes
  the server, scheduler and MCP files expensive to extend, and Phase 1 tool runs work the same way. It refuses to
  start while the bench server runs a job.
- The `gate-negative` branch is kept (not deleted) so its commit d2f4941fc4b09be586bf7e913ed747d6cd8d1a81 stays
  checkable. It is never merged.
- First negative try (job 10) passed because the change never fired; replaced by a stronger change (job 11).
