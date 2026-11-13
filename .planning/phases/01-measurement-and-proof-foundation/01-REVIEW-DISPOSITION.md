---
phase: 01-measurement-and-proof-foundation
review: 01-REVIEW.md
reviewed_commit: ae868d6d7df0454ad2c41acbbd2f22a8a9b16380
updated: 2026-11-14
---

# Code review disposition (phase 01)

Each finding was reproduced in the main session before it was fixed. Every fix has a test that failed first. Full suite after the fixes: 856 passed, 6 skipped, 16 deselected.

| ID | Severity | Disposition | Commit / note |
|----|----------|-------------|---------------|
| CR-01 | Critical | fixed | 79f6c851596d0ff06cbf5ee19a28cb05c246a2b7: `results`, `games` and `dashboard` read one game key (bench lgen mode, this server's env, rep 0). Reproduced: `/api/results` counted 10,400 games for commit A where `/api/funnel` counted 10,000 |
| CR-02 | Critical | fixed | 79f6c851596d0ff06cbf5ee19a28cb05c246a2b7: `App.resume` refuses a job from another env_id; `serve --resume` leaves such jobs interrupted |
| CR-03 | Critical | fixed | 79f6c851596d0ff06cbf5ee19a28cb05c246a2b7: a hedge word exempts only its own clause. Reproduced: "Job 99999 has started; next I'll check the funnel." passed before the fix |
| WR-01 | Warning | fixed | dd023ff6e95ef908501d782b2f397ee187467db2: tool jobs are not resumed |
| WR-02 | Warning | partly fixed | d4f96b2dc7df31003b587e3bd388f1c059351d80: query proofs must read `games`, `jobs` or `tool_games`; began/submitted/spawned are start words. Open: a result claim still passes with any existing job, whatever its state |
| WR-03 | Warning | partly fixed | dd023ff6e95ef908501d782b2f397ee187467db2: comparing a replicate with itself is refused. Open: no `--env-id` option; `--lgen` defaults to any mode (the pre-registered A/A command passes `--lgen off`) |
| WR-04 | Warning | open | `facts.py check` does not run measured facts' queries; deferred to the next fact tranche |
| IN-01 | Info | open | `quest_portal_found` not limited to the Dungeons of Doom |
| IN-02 | Info | open | `--mde 0.03` example errors at the 0.019 default discordance; CLI prints a traceback |
| IN-03 | Info | open | whitespace or one-character source quotes accepted by `facts.py` |
| IN-04 | Info | open | `screens-bench wait` exits 0 for interrupted and stopped jobs |
| IN-05 | Info | open | `lgen_pilot.pair_by_seed` keeps the last duplicate; fails on a seed-less game |

The live bench server still runs the code from before these fixes. CR-01 and CR-02 take effect after it is restarted (`uv run screens-bench serve`); no job is running.
