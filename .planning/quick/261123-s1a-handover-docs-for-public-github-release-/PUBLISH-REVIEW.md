# Before publishing: owner review list

Nothing has been pushed. GitHub account `Danis42` is logged in to `gh`; the repo has no remote yet.

## Checked (2026-11-23)

- Secrets: no API keys, tokens or private keys in any commit of any branch (`git log --all -p` grep for
  `sk-`, `ghp_`, `AIza`, `xox`, private key headers: no hits). No `.env`, `.db`, `.pem` or credential file was ever
  committed. `.git` is 8.8 MB.
- Tracked Claude files: `.claude/CLAUDE.md` (project instructions), `.claude/settings.json` (Stop hook for
  `check_claims.py`), `.mcp.json` (bench MCP server). Nothing personal in them.
- Not in git (gitignored): `reference/` (699 MB vendored sources), `archive/` (old backups and the 146,743-game
  database), `.worktrees/`, `.venv/`. The live bench database is outside the repo.

## Decide

1. **Author email.** All 700 commits carry `Danis42 <8244890+Danis42@users.noreply.github.com>`. On a public repo that address is visible
   to everyone. Option: rewrite the author to the GitHub no-reply address (`<id>+Danis42@users.noreply.github.com`)
   in a **separate export clone** with `git filter-repo --mailmap`, leaving this repo untouched. The same applies
   to the NLE repo if any of its commits carry the address (its own new commits do).
2. **Licence for this repo's own code.** There is no top-level LICENSE. AutoAscend is MIT; MIT for the rest would
   match. NetHack's NGPL covers only the NLE repo.
3. **Personal wording in `.planning/`.** The planning files quote the owner ("owner's words", decisions with
   dates) and name the local paths `~/...` (about 15 files). Harmless, but public.
4. **Repo names.** Proposal: `nethack-screensaver` (this repo) and `nle-screens` (patched NLE, branch `screens-nh5`).

## Steps after approval (in this order)

1. Create `Danis42/nle-screens` (public), push branch `screens-nh5` (140 MB repo, NetHack history included).
2. In this repo, change the NLE source in `pyproject.toml` from `file://$HOME/git/nle-screens.git` to
   `https://github.com/Danis42/nle-screens.git` (same `rev`), `uv lock`, check that `uv sync` and
   `scripts/fresh_clone_check.py` pass, commit, move tag `ascension-bot-v1` onto that commit.
3. Create `Danis42/nethack-screensaver` (public), push `main`, the tag and the branches worth keeping
   (proposal: `mines-candidate`, `monk-shield`, `unicorns`, `speedup`; the `char/*` and proof branches are
   referenced by job results, so push them too or drop them from HANDOFF.md).
