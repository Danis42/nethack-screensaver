---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
# External Integrations

**Analysis Date:** 2026-11-12

## APIs & External Services

**Game engine (in-process, not a network service):**
- NLE (NetHack Learning Environment) - provides the NetHack 5.0 game and observation/action interface
  - SDK/Client: `nle` (local path `reference/nle-src`, branch `screens-nh5`)
  - Imports: `nle.nethack` in `autoascend/glyph/monster.py`, `autoascend/glyph/screen_symbol_consts.py`, `autoascend/glyph/nh5.py`
  - Wrapper: `autoascend/env_wrapper.py`
  - Auth: Not applicable

**Public NetHack ascension archives (read-only downloads):**
- hardfought.org - source of reference ascension data used as a yardstick
  - Client: `urllib.request` in `bench/importers.py`
  - Endpoints built in code: `HARDFOUGHT_DUMPLOG = "https://www.hardfought.org/userdata/{initial}/{name}/nethack/dumplog/{starttime}.nh.txt"` and xlogfile URLs (`https://www.hardfought.org/xlogfiles/nethack50/xlogfile`, referenced in `bench/mcp_server.py`)
  - Triggered by: `screens-bench import xlog <url>`, `screens-bench import dumplogs`, MCP tool `bench_import` (`bench/mcp_server.py`)
  - Auth: None (public URLs)
  - Stored in: `reference_games` table of the bench SQLite DB (`bench/store.py`)

**Local LLM server (optional, scripts only):**
- Ollama HTTP API on `http://localhost:11434/api/generate`
  - Used by: `scripts/wiki_sweep/ollama_sweep.py` (timeout 900 s), `scripts/fixes_triage.py` (timeout 600 s), `scripts/fixes_shortlist.py` (timeout 600 s)
  - Client: `urllib.request` (no SDK, no API key)
  - Purpose: classify/extract NetHack wiki pages into structured knowledge and triage fix candidates
  - Not used by the running bot or the bench server

**Public NetHack wiki and guides (offline reference only):**
- NetHack wiki pages cleaned into `reference/nethackwiki/` and `reference/wiki_batches/`; Reddit and guide material under `reference/reddit/` and `reference/guides/`
- No runtime fetch; the bot does not call the wiki. Source URLs appear only in comments (e.g., `autoascend/soko_solver/maps.py`, `autoascend/objects/data.py`)

**Claude Code MCP integration:**
- `.mcp.json` registers the bench MCP server (`bench/mcp_server.py`, FastMCP-style `@mcp.tool()` tools) for Claude Code
- The MCP server is a thin HTTP client to the local bench server: `SCREENS_BENCH_URL` default `http://127.0.0.1:8765`; it auto-starts `python -m bench.cli serve` with `start_new_session=True` if the server is down (`bench/mcp_server.py` `_ensure_server`)
- Tools: `bench_status`, `bench_baseline`, `bench_experiment`, `bench_results`, `bench_games`, `bench_experiments`, `bench_stop`, `bench_import`, `bench_reference`
- Auth: None; the bench server rejects non-localhost callers (`bench/server.py`: "only http://localhost or http://127.0.0.1 may use the bench server")

## Data Storage

**Databases:**
- SQLite (local file)
  - Bench database: `SCREENS_BENCH_DATA` (default `~/.local/share/screens-bench`), schema in `bench/store.py`
    - Tables: `meta`, `games` (per-commit game JSON), `jobs` (baseline/experiment work queue), `reference_games` (imported ascensions)
    - Connection: `sqlite3.connect(path, check_same_thread=False, timeout=30)` with `row_factory = sqlite3.Row`
  - Analysis script (read-only): `scripts/nld_study.py` opens NLE Data Set databases with `file:{db}?mode=ro` URI
  - Client: stdlib `sqlite3` (no ORM)

**File Storage:**
- Local filesystem only
  - Game history: `~/.local/state/nethack-screensaver/games.jsonl` (`nethack_screensaver/gamelog.py`, `nethack_screensaver/paths.py`)
  - Error log: `~/.local/state/nethack-screensaver/player.log`
  - Bench worktrees and cache: `~/.cache/screens-bench/`
  - Seeded/staged run outputs: `scripts/staged_run.py`, `scripts/scenario_run.py`, `scripts/seeded_report.py`
  - Test fixtures: `tests/data/` (`.npy` tty-char arrays, JSON Sokoban fixtures, xlog/dumplog samples)
  - Git-stored bench data: `scripts/seeded_report.py` runs `git -C <repo> grep ... main` to look up commit contents

**Caching:**
- None as a service
- Fixed-clock shim build cache: `$XDG_CACHE_HOME/screens` or `~/.cache/screens` (`nethack_screensaver/fixed_clock.py`)

## Version Control

**Git (local subprocess):**
- `bench/gitrefs.py` runs `git -C <repo> ...` to resolve refs, create worktrees per commit, and list commits for baselines/experiments
- `nethack_screensaver/dungeon_truth.py` and `nethack_screensaver/fixed_clock.py` shell out to `nm -D` and `cc` respectively
- Remote: none configured for runtime; the repo is local (`main` branch). The README references `github.com/maciej-sypetkowski/autoascend @ 8527910` as the upstream origin of the vendored bot.

## Authentication & Identity

**Auth Provider:**
- Not applicable - no user accounts, no OAuth, no tokens.
- Bench server and MCP bridge are unauthenticated and bound to localhost only.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry or similar)

**Logs:**
- Local files: `~/.local/state/nethack-screensaver/player.log` (errors), `~/.local/state/nethack-screensaver/games.jsonl` (per-game JSON records with `strategy`, `outcome`, `milestone`)
- Bench server log: started by `bench/mcp_server.py` into a log file via `subprocess.Popen(..., stdout=log, stderr=STDOUT)`
- Dashboard: `bench/static/index.html` served by `bench/server.py`

## CI/CD & Deployment

**Hosting:**
- Not applicable. Runs locally as a terminal screensaver (`bin/nethack-screensaver`, `zsh/nethack-screensaver.zsh`).

**CI Pipeline:**
- None detected (no `.github/workflows`, no CI config files in repository root)

## Environment Configuration

**Required env vars:**
- None strictly required; all have defaults.
- Optional: `NETHACK_SCREENSAVER_IDLE`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`, `SCREENS_BENCH_URL`, `SCREENS_BENCH_DATA`, `SCREENS_BENCH_CACHE`, `SCREENS_BENCH_PYTHON`

**Secrets location:**
- No secrets are used by the code. No API keys, tokens, or credentials are read. No `.env` file exists in the repository. Ollama and hardfought.org access are unauthenticated.

## Webhooks & Callbacks

**Incoming:**
- None. The bench HTTP server (`bench/server.py`, default port 8765) is a local control API (routes for status, baseline/experiment jobs, stop, import), accessible only from 127.0.0.1/localhost.

**Outgoing:**
- None. The only outbound HTTP calls are the hardfought.org imports (user-initiated) and optional local Ollama calls from scripts.

---

*Integration audit: 2026-11-12*
