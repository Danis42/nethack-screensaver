commit_a: e5b5a7f525bc51b8008f665173600aba80de466d
spare_commit: e0229dc28b9895f5ec37265cc0b7db4d1968d299
pinned_nle: cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72
jobs: off=1 seed=2

# Walking-skeleton proof (D-19, MEAS-01 success criterion 1)

The skeleton works end to end from a fresh clone on the live database. A fresh clone of commit e5b5a7f525bc51b8008f665173600aba80de466d installed with `uv sync --locked` without the gitignored `reference/` directory, and its tests passed. Its server played the spare commit e0229dc28b9895f5ec37265cc0b7db4d1968d299 (branch `proof/fresh-clone`, an empty commit on top of commit A) on seeds 1000-1009: job 1 with lgen off and job 2 with lgen seed. Both jobs finished with 10 keyed game rows each, carrying env_id a8f58c2fda006264, and the funnel of job 2 returned all 18 stages with Wilson intervals. [query: SELECT COUNT(*) FROM games WHERE job_id = 1 AND env_id IS NOT NULL AND seed BETWEEN 1000 AND 1009 => 10] [query: SELECT COUNT(*) FROM games WHERE job_id = 2 AND env_id IS NOT NULL AND lgen IS NOT NULL AND seed BETWEEN 1000 AND 1009 => 10]

## Evidence

- Fresh-clone check: `{"dest": ".../scratchpad/fresh", "sha": "e5b5a7f525bc51b8008f665173600aba80de466d", "nle_commit": "cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72", "env_id": "a8f58c2fda006264", "tests": "passed"}`.
- Both job specs record `sha` e0229dc28b9895f5ec37265cc0b7db4d1968d299, `env.nle_commit` cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72, `env.lock_sha256` 72bcaf34bc29f9e3fe036256c31bc8ccbd65ba45136efd0c2b9a260ae403435e, `env_id` a8f58c2fda006264 and `lock_blob` d0cb77f0c7c86c927b0e16dc167b3e0af6324514. Both have `started: true`.
- The live server, restarted from the main checkout afterwards, reports the same env_id a8f58c2fda006264. The clone and the main checkout fingerprint identically.
- Funnel of job 2 (n = 10, nothing excluded or flagged): mines 5/10, minetown 1/10, oracle 7/10, sokoban 5/10, sokoban_solved 0/10, mines_end 2/10, the rest 0/10. Ten games only show that the plumbing works; they measure nothing.
