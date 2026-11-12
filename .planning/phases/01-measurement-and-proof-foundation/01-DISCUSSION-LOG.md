# Phase 1: Measurement and Proof Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-12
**Phase:** 01-measurement-and-proof-foundation
**Areas discussed:** NLE reproducibility, Seed ranges & baseline size, Claim checking, Fact ledger scope

---

## NLE reproducibility

| Option | Description | Selected |
|--------|-------------|----------|
| Own GitHub repo + uv git dep | Push fork to GitHub, pin SHA | |
| Git submodule | Same repo as submodule | |
| Vendor into this repo | Commit 36 MB source | |
| Local bare repo + uv git dep | Middle option raised in clarification | ✓ |

**User's choice:** Local bare repo (after asking about the risks of keeping it local).
**Notes:** Claude verified the fork exists only in `reference/nle-src` (not in archive). Path: `~/git/nle-screens.git` (over inside the repo / Claude decides). Backup: none, risk accepted (over bundle-to-drive / private GitHub mirror).

---

## Seed ranges & baseline size

| Option | Description | Selected |
|--------|-------------|----------|
| 10,000 games (~7 h) | Best late-stage precision | ✓ |
| 5,000 games (~3.5 h) | Medusa ~50 arrivals | |
| 2,304 games (~1.5 h) | Same as old baseline | |

**User's choice:** 10,000 games; A/A on a 2,000-seed subset; seeds dev 0–99,999 · confirm 100,000–199,999 · final 1,000,000+; resumable interrupted jobs: yes.
**Notes:** Owner asked whether the bench runs alone or needs Claude. Answer: the bench server runs jobs unattended; Claude only submits and gets a job ID; a server stop marks jobs interrupted (hence resume).

---

## Claim checking

| Option | Description | Selected |
|--------|-------------|----------|
| Claude's replies (Stop hook) | Scan final message per turn | ✓ |
| Commit messages | commit-msg hook | |
| Planning docs | SUMMARY/VERIFICATION | |

**User's choice:** Claude's replies; IDs verified to exist (over format-only); block on failure (over warn).

---

## Fact ledger scope

| Option | Description | Selected |
|--------|-------------|----------|
| New + code-relied facts | Tag new facts and those code uses | |
| New facts only | | |
| Everything now | Tag all existing facts in Phase 1 | ✓ |

**User's choice:** Everything now; web search for unverified facts only (over web+source for all / web only); one ledger file + IDs in code; unverified facts allowed but reported.
**Notes:** Owner interrupted the first ask to add a requirement: facts are not taken as-is; a light web search for more context/better information. The depth of the research was left to Claude's judgement.

---

## Claude's Discretion

- Depth of web research per fact
- Ledger file format and fact-ID naming
- Claim-detection method in the Stop hook (deterministic)
- Funnel report presentation, `tool_games` schema, stats implementation details

## Deferred Ideas

- Off-disk backup of the NLE fork (declined, risk accepted)
- Claim checks on commit messages and planning docs
