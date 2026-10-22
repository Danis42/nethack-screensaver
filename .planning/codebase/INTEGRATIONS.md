---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
# External Integrations

**Analysis Date:** 2026-10-22

## APIs & External Services

**Public web resources (HTTP GET only, no auth):**
- hardfought.org NetHack xlogfile - real-game ascension/game records used as a benchmark yardstick
  - Client: `urllib.request` in `bench/importers.py` (`fetch`, `import_xlog`), with a custom User-Agent and 60 s timeout
  - Endpoint: `https://www.hardfought.org/xlogfiles/nethack50/xlogfile` (default in `bench/mcp_server.py`; any http(s) URL accepted by `bench/server.py` for `xlog` imports)
  - Dumplogs: `https://www.hardfought.org/userdata/{initial}/{name}/nethack/dumplog/{starttime}.nh.txt` (`bench/importers.py`, `import_dumplogs`)
  - Rate limit: at most one request per second (`min_interval=1.0`)
  - Caching: each URL is downloaded once into `<cache>/downloads/<sha1(url)>` (`SCREENS_BENCH_CACHE`, default `~/.cache/screens-bench`)
  - Auth: none
- Documentation links only (not fetched at runtime): nethackwiki.com, github.com/facebookresearch/nle source files, cited in comments and `autoascend/objects/` and `autoascend/soko_solver/maps.py`

**Upstream game engine (local, not a network service):**
- NetHack Learning Environment `nle==1.3.0` - bundles the NetHack game; NLE's `NetHackChallenge` task (`nethack_screensaver/game.py`) runs it in-process. It has a no-progress timeout that ends stuck games.
- AutoAscend bot code (vendored and ported, `autoascend/`) - no external service

**Anthropic / Claude:**
- Claude Code uses the bench MCP server defined in `.mcp.json` (stdio transport, launched with `uv run`). The server is a local client to the bench HTTP server; it makes no direct third-party API calls.
- The application itself does not call any LLM API. No Anthropic SDK is a dependency.

## Data Storage

**Databases:**
- SQLite (local file, stdlib `sqlite3`)
  - Path: `~/.local/share/screens-bench/results.db` (override: `SCREENS_BENCH_DATA`)
  - Implementation: `bench/store.py` (`Store` class; schema version 1 in `meta` table)
  - Tables: `meta`, `games` (per-commit game JSON, indexed by `games_by_sha`), `jobs` (baseline/experiment jobs and their state), `reference_games` (imported public-server games, unique on `source, name, starttime`)
  - Connection: `check_same_thread=False`, `timeout=30`, guarded by an `RLock`
- No server database, no ORM

**File Storage:**
- Local filesystem only
  - Game history: `~/.local/state/nethack-screensaver/games.jsonl` (`nethack_screensaver/gamelog.py`, path via `nethack_screensaver/paths.py`)
  - Player errors: `~/.local/state/nethack-screensaver/player.log` (`bin/nethack-screensaver`)
  - Bench worker log: `<data>/worker.log` (`bench/cli.py`)
  - Downloaded import cache: `<cache>/downloads/` (`bench/importers.py`)

**Git worktrees (local git used as an integration):**
- `bench/gitrefs.py` shells out to `git -C <repo>` to resolve refs to SHAs (`rev-parse`-style lookups), add detached worktrees under `~/.cache/screens-bench/worktrees/`, remove stale ones, and run `git worktree prune`
- Benchmark workers run inside those worktrees via `subprocess.Popen` with `PYTHONPATH` set to the worktree (`bench/runner.py`)

**Caching:**
- Numba on-disk JIT cache (`cache=True`) in `__pycache__` next to `autoascend/utils.py` and `autoascend/monster_tracker/kernels.py`
- Downloaded-text cache for importers (above)
- No Redis or memcached

## Authentication & Identity

**Auth Provider:**
- None. The bench HTTP API has no authentication; it is restricted to local hosts.
  - Implementation: `bench/server.py` returns HTTP 403 for any request whose Host is not `127.0.0.1` or `localhost` (`LOCAL_HOSTS`), and binds to the configured host (default `127.0.0.1:8765`, from `bench/cli.py`).
- No user accounts, sessions, or tokens

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry or similar)

**Logs:**
- Plain-text and JSON-lines files on disk:
  - `~/.local/state/nethack-screensaver/player.log` (stderr of the player process, via `bin/nethack-screensaver`)
  - `~/.local/state/nethack-screensaver/games.jsonl` (per-game records: `strategy`, `outcome`, last plan `milestone`; `nethack_screensaver/gamelog.py`)
  - `autoascend` stats logging in `autoascend/stats_logger.py`
- Bench status page: `bench/static/index.html`, served by `bench/server.py`, with a JSON API for jobs, dashboards and comparisons

## CI/CD & Deployment

**Hosting:**
- Not applicable. Runs locally as a terminal screensaver from a git clone.

**CI Pipeline:**
- None detected (no `.github/workflows`, no other CI config)

**Install flow:** `uv sync`, then source `zsh/nethack-screensaver.zsh` from `~/.zshrc` (documented in `README.md`).

## Environment Configuration

**Required env vars:**
- None. All variables are optional (see `STACK.md` for the list and defaults).

**Optional env vars:**
- `NETHACK_SCREENSAVER_IDLE` - idle timeout for the zsh hook
- `NETHACK_SCREENSAVER_PLAYER` - replace the player command
- `XDG_CONFIG_HOME`, `XDG_STATE_HOME` - standard XDG base directories
- `SCREENS_BENCH_DATA`, `SCREENS_BENCH_CACHE`, `SCREENS_BENCH_URL` - bench paths and server URL

**Secrets location:**
- No secrets are needed or stored. No `.env` or credential files exist in the repository.

## Webhooks & Callbacks

**Incoming:**
- None. The bench server (`bench/server.py`) is a local HTTP JSON API and status page on `127.0.0.1:8765`; it accepts requests only from localhost hosts and does not expose webhooks.

**Outgoing:**
- None (other than the read-only GETs to hardfought.org listed above)

## Inter-Process Communication

- Bench worker processes: `subprocess.Popen` with stdin/stdout pipes (`bench/runner.py`), one per game slot (default 11 workers, `bench/cli.py`)
- Game process: runs under a pty owned by the launcher `bin/nethack-screensaver`, which discards pending keystrokes on exit and restores `stty` settings
- MCP: stdio transport between Claude Code and `bench.mcp_server`, which calls the bench HTTP server at `SCREENS_BENCH_URL`

---

*Integration audit: 2026-10-22*
