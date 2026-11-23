# Before publishing: owner review list

Published 2026-11-23 after owner review.

## Checked (2026-11-23)

- Secrets: no API keys, tokens or private keys in any commit of any branch (`git log --all -p` grep for
  `sk-`, `ghp_`, `AIza`, `xox`, private key headers: no hits). No `.env`, `.db`, `.pem` or credential file was ever
  committed. `.git` is 8.8 MB.
- Tracked Claude files: `.claude/CLAUDE.md` (project instructions), `.claude/settings.json` (Stop hook for
  `check_claims.py`), `.mcp.json` (bench MCP server). Nothing personal in them.
- Not in git (gitignored): `reference/` (699 MB vendored sources), `archive/` (old backups and the 146,743-game
  database), `.worktrees/`, `.venv/`. The live bench database is outside the repo.

## Decided by the owner (2026-11-23) and done

1. **Author email:** rewritten to the GitHub no-reply address in an export clone (`git filter-repo --mailmap`),
   for this repo. The local working repo keeps its original history.
2. **Licence:** MIT for this repo's own code (`LICENSE`); `autoascend/` keeps its own MIT licence.
3. **Personal wording:** owner quotes paraphrased and home paths removed at HEAD and, in the export, in every
   commit (`--replace-text`, `--replace-message`).
4. **NLE:** no separate repository and no GitHub fork (owner, 2026-11-23). The patched NLE is vendored in
   `vendor/nle` with upstream credit (quick task 261123-svv). A standalone `Danis42/nle-screens` was public briefly
   and was deleted by the owner. The main repo is `Danis42/nethack-screensaver` (public).
5. **Hashes:** the rewrite changed every commit hash; `.planning/COMMIT-MAP.tsv` in the published repo maps the
   original hashes that the documents and bench jobs quote to the published ones.
