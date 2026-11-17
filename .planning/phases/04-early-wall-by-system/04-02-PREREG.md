# 04-02 pre-registration: keep away from hostile unicorns below XL 10

Written from 04-PREREG-TEMPLATE.md (owner pre-approved 2026-11-17), committed before any candidate game is read. Nothing
here departs from the template, so the owner is not asked.

- **Candidate:** f02e8e8aefc2ee824da5a73a332c2fd45ac9a934 (branch `unicorns`). Its bot code differs from the baseline
  only by this change (`git diff --stat b2b2bbe main -- autoascend nethack_screensaver bench` is empty; the candidate
  adds the rule and the `unicorns` metric).
- **Baseline:** job 23, b2b2bbe6d1c9341319b02e937aac7f37ec4db14d (Monk, seeds 1000-10999).
- **Primary metric:** `unicorns` (killed by a unicorn), lower is better.
- **Guardrail:** `dlvl10`. Worse with exact McNemar p < 0.05 on the dev seeds sends the change to the owner before merge.
- **MDE:** half of job 23's final `unicorns` rate, rounded to the nearest 0.005, at least 0.005. Interim value on the
  finished seeds 1000-5999: 289 of 5,000 = 5.78%, so the MDE will be about 0.03. It is fixed from the final job 23
  rate, before the dev experiment starts, and written below.
- **Test:** SPRT (bench/sprt.py), alpha 0.05, declared power 0.8, one-sided. **No trigger:** no recorded game field
  shows whether a unicorn was ever seen, so every seed is played.
- **Discordance psi:** 960-seed pilot of the candidate on seeds 1000-1959, compared with job 23 on the same seeds on
  `unicorns`; psi = Wilson 95% upper bound of the discordant share, rounded up to 0.005, at least MDE + 0.005.
  Nothing else is read from the pilot.
- **Decision:** dev experiment on seeds from 1000 (lo 1000) against job 23. A dev "better" leads to the confirm run on
  seeds from 100,000 with gate `phase4-unicorns`; a win needs both. "No win" or "worse" ends the change; it is not
  retuned and rerun on the same seeds.

## Values fixed after job 23 and the pilot (filled in before the dev experiment)

- Final job 23 `unicorns` rate: _pending_
- MDE: _pending_
- Pilot job: _pending_; discordant seeds: _pending_; psi: _pending_
- SPRT plan (`screens-bench power --rule sprt`): _pending_
