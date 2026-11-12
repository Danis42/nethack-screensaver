import asyncio

import pytest

from conftest import run_until_idle
from bench import mcp_server


@pytest.fixture
def url(bench_url, monkeypatch):
    monkeypatch.setattr(mcp_server, "URL", bench_url)
    return bench_url


def test_tools_drive_the_server(url, bench_app):
    assert mcp_server.bench_status()["job"] is None
    job_id = mcp_server.bench_baseline("main", games=3)["job_id"]
    run_until_idle(bench_app)
    assert mcp_server.bench_results("main", metric="dlvl6")["n"] == 3
    assert mcp_server.bench_games("main", where="max_depth>3")["matches"] == 3
    sha = bench_app._sha("main")[0]
    assert mcp_server.bench_experiment("main", "main")["error"].endswith("same commit " + sha[:10])
    assert mcp_server.bench_stop() == {"stopped": False}
    assert mcp_server.bench_experiments() == []
    assert mcp_server.bench_reference()["summary"] == {"ascensions": 0}
    assert job_id > 0


def test_tools_are_registered():
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert names == {"bench_status", "bench_baseline", "bench_experiment", "bench_results", "bench_games",
                     "bench_experiments", "bench_stop", "bench_import", "bench_reference"}


def test_bench_baseline_forwards_window_lgen_and_replicate(url, bench_app):
    job_id = mcp_server.bench_baseline("main", games=3, lo=2000, hi=2004, lgen="seed", replicate=1)["job_id"]
    spec = bench_app.job(job_id)["spec"]
    assert spec["seeds"]["lo"] == 2000 and spec["seeds"]["hi"] == 2004
    assert spec["lgen"] == "seed" and spec["replicate"] == 1


def test_bench_baseline_forwards_the_gate_for_confirm_windows(url, bench_app):
    job_id = mcp_server.bench_baseline("main", lo=100_000, hi=100_004, gate="phase-2-gate")["job_id"]
    assert bench_app.job(job_id)["spec"]["gate"] == "phase-2-gate"
