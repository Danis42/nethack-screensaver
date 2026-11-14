---
status: testing
phase: 01-measurement-and-proof-foundation
source: [01-VERIFICATION.md]
started: 2026-11-14T00:01:09Z
updated: 2026-11-14T00:01:09Z
---

## Current Test

number: 1
name: Prohibition review (7 judgment-tier prohibitions)
expected: |
  Owner accepts or rejects the verifier's verdict that all seven held: 01-01 no push of the NLE fork or screens repo to a remote and no backup tooling; 01-03 no LLM, network or paid API in claim detection; 01-03 no bypass switch for the claim checker; 01-04 no 5.0-source fact tag without file:line and verbatim quote; 01-10 no Claude-reachable surface creates clean_attempt jobs or plays final-range seeds; 01-15 no dungeon screening in lgen pairing or seed choice; 01-16 no archive games imported or archive numbers shown as current. Evidence: 01-VERIFICATION.md, section Prohibitions.
awaiting: user response

## Tests

### 1. Prohibition review (7 judgment-tier prohibitions)
expected: Owner accepts the verifier's verdict that all seven held (evidence in 01-VERIFICATION.md, section Prohibitions)
result: [pending]

### 2. Bench server restarted onto the review fixes
expected: After `uv run screens-bench serve --resume`, GET /api/results?ref=e5b5a7f525bc51b8008f665173600aba80de466d reports games = 10000, matching /api/funnel?job=7 n = 10000
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
