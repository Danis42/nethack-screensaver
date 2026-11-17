"""MCP tools for Claude: drive the bench server over its JSON API (started if not running)."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from mcp.server.mcpserver import MCPServer

URL = os.environ.get("SCREENS_BENCH_URL", "http://127.0.0.1:8765")
REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("SCREENS_BENCH_DATA", "~/.local/share/screens-bench")).expanduser()

mcp = MCPServer("screens-bench")


def _up():
    try:
        urlopen(URL + "/api/status", timeout=2).close()
        return True
    except (URLError, OSError):
        return False


def _ensure_server():
    if _up():
        return
    DATA.mkdir(parents=True, exist_ok=True)
    log = open(DATA / "server.log", "a")
    subprocess.Popen([sys.executable, "-m", "bench.cli", "serve"], cwd=REPO, stdout=log,
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(80):
        time.sleep(0.25)
        if _up():
            return
    raise RuntimeError(f"bench server did not start; see {DATA / 'server.log'}")


def _call(method, path, body=None, query=None):
    _ensure_server()
    if query:
        path += "?" + urlencode({k: v for k, v in query.items() if v is not None})
    data = None if body is None else json.dumps(body).encode()
    req = Request(URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except HTTPError as e:
        try:
            return json.loads(e.read())
        except ValueError:
            return {"error": str(e)}


@mcp.tool()
def bench_status() -> dict:
    """Current job with progress and verdict so far, worker load, games per minute, import state."""
    return _call("GET", "/api/status")


@mcp.tool()
def bench_baseline(ref: str = "main", games: int = 576, lo: int | None = None, hi: int | None = None,
                   lgen: str | None = None, replicate: int = 0, gate: str | None = None) -> dict:
    """Play `ref` on the half-open seed window [lo, hi) (default lo 1000, hi lo + games); stored games of
    the same commit, seed, lgen mode, environment and replicate are reused. lgen: "off" (default) or
    "seed" (NLE level-generation seed = seed + 10,000,000). replicate=1 reruns the window into separate
    A/A rows that summaries never read. Seed ranges: dev 1,000-99,999; confirm-range windows (100,000-199,999)
    need `gate`, the phase-gate name; final seeds are refused. Returns job_id; a job counts as started only once its first game
    row exists: `started` true in bench_job / bench_status; report a start only then. Run `uv run screens-bench wait <job_id>` as a background shell command to be notified."""
    body = {"kind": "baseline", "ref": ref, "games": games, "replicate": replicate}
    body.update({k: v for k, v in (("lo", lo), ("hi", hi), ("lgen", lgen), ("gate", gate)) if v is not None})
    return _call("POST", "/api/jobs", body)


@mcp.tool()
def bench_experiment(candidate: str, mde: float, baseline: str = "main", metric: str = "dlvl6",
                     discordance: float | None = None, lo: int | None = None, block: int = 96,
                     lgen: str | None = None, allow_new_baseline: bool = False, alpha: float = 0.05,
                     power: float = 0.8, rule: str = "sprt") -> dict:
    """A/B experiment: candidate vs baseline commit on one rate metric (see bench_power first). Declare the MDE
    (smallest effect worth detecting, e.g. 0.03) before the run; the size follows from it and the discordance (share
    of seeds where the commits differ). rule "sprt" (default): Wald's SPRT, "better" or "no detectable effect",
    fewest games; "mixture": can also say "worse"; both valid however often checked. Commit first; refs resolve to
    a SHA now. A job counts as started only when `started` is true (first game row exists); cite the job ID then.
    Returns job_id (`uv run screens-bench wait <job_id>` waits). Baseline needs stored games or allow_new_baseline."""
    return _call("POST", "/api/jobs", {"kind": "experiment", "candidate": candidate, "baseline": baseline,
                                       "metric": metric, "mde": mde, "discordance": discordance, "lo": lo,
                                       "block": block, "lgen": lgen, "allow_new_baseline": allow_new_baseline,
                                       "alpha": alpha, "power": power, "rule": rule})


@mcp.tool()
def bench_power(mde: float | None = None, discordance: float | None = None, n: int | None = None, rule: str = "sprt",
                alpha: float = 0.05) -> dict:
    """What an experiment must declare. With mde (smallest effect worth detecting, e.g. 0.03): planned seeds per side
    (n_planned) for the rule ("sprt" adds mean seeds at the MDE and at no effect) and what exact McNemar could detect
    there. With n: the MDE that n seeds per side can detect. discordance: share of seeds where two commits differ."""
    return _call("GET", "/api/power", query={"mde": mde, "discordance": discordance, "n": n, "rule": rule,
                                             "alpha": alpha})


@mcp.tool()
def bench_results(ref: str = "main", metric: str | None = None) -> dict:
    """Summary of a commit's stored games (rates, killers, depths, outcomes, crashes), or one metric."""
    return _call("GET", "/api/results", query={"ref": ref, "metric": metric})


@mcp.tool()
def bench_funnel(ref: str = "main", lo: int | None = None, hi: int | None = None, lgen: str | None = None,
                 job_id: int | None = None) -> dict:
    """Natural-game funnel of a commit: per ladder stage (mines .. ascended), how many games in the seed window
    [lo, hi) reached it. Marginal reach: a stage counts when its key is in the game's ladder, whatever came before.
    Each row has hits/n, the rate and its 95% Wilson interval (lo, hi), plus the rate conditional on the previous
    stage. Games without a ladder are excluded and counted; ladder errors, watchdog and exception endings stay in n
    and are counted. Defaults: the baseline window 1000-10999 and the bench's lgen mode; job_id reads a baseline
    job's own commit and window. Windows touching the tool seeds 0-999 are refused."""
    return _call("GET", "/api/funnel", query={"ref": ref, "lo": lo, "hi": hi, "lgen": lgen, "job": job_id})


@mcp.tool()
def bench_games(ref: str = "main", where: str | None = None, limit: int = 50) -> dict:
    """Stored games of a commit matching a filter like 'max_depth>9,end_reason~soldier ant'."""
    return _call("GET", "/api/games", query={"ref": ref, "where": where, "limit": limit})


@mcp.tool()
def bench_experiments() -> list:
    """All experiments, newest first, with their verdicts."""
    return _call("GET", "/api/experiments")


@mcp.tool()
def bench_stop(job_id: int | None = None) -> dict:
    """Stop the active job (or a queued job by id). Stored games stay."""
    return _call("DELETE", "/api/jobs" if job_id is None else f"/api/jobs/{quote(str(job_id))}")


@mcp.tool()
def bench_job(job_id: int) -> dict:
    """One job: state, spec, result, and `started` / `first_game_at`. A job counts as started only when
    `started` is true (its first game row exists); report a start only then."""
    return _call("GET", f"/api/jobs/{int(job_id)}")


@mcp.tool()
def bench_resume(job_id: int) -> dict:
    """Resume an interrupted job (server restart, reboot) under the same job ID; it plays only the seeds not
    yet stored. Only interrupted jobs can be resumed."""
    return _call("POST", f"/api/jobs/{int(job_id)}/resume", {})


@mcp.tool()
def bench_shutdown() -> dict:
    """Stop every job and end the bench server process. The next MCP call starts the server of the main checkout
    again, so during a server swap call no other bench tool until the replacement server answers."""
    return _call("POST", "/api/shutdown", {})


@mcp.tool()
def bench_import(kind: str, url: str | None = None, limit: int = 500) -> dict:
    """Import real ascensions: kind='xlog' with an xlogfile url (e.g.
    https://www.hardfought.org/xlogfiles/nethack50/xlogfile), or kind='dumplogs' to download
    dumplogs of imported ascensions (1 request per second). Runs in the background; see bench_status."""
    return _call("POST", "/api/import", {"kind": kind, "url": url, "limit": limit})


@mcp.tool()
def bench_reference(where: str | None = None, limit: int = 50) -> dict:
    """Summary of imported real ascensions plus the xlog records matching a filter (e.g. 'role=Val')."""
    return {"summary": _call("GET", "/api/reference/summary"),
            "games": _call("GET", "/api/reference/games", query={"where": where, "limit": limit})}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
