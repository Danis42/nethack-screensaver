import json
import socket
import subprocess
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from bench_fakes import game as _game
from conftest import git, run_until_idle
from bench import cli
from bench.server import serve
from bench.store import Store


def _req(url, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except HTTPError as e:
        return e.code, json.loads(e.read())


def test_baseline_job_stores_the_sha_resolved_at_start(bench_app, bench_repo):
    job_id = bench_app.start_baseline("main", games=3)["job_id"]
    sha = bench_app.job(job_id)["spec"]["sha"]
    (bench_repo / "f.txt").write_text("three")
    git(bench_repo, "commit", "-qam", "three")  # main moves on while the job waits
    assert bench_app.job(job_id)["spec"]["sha"] == sha != bench_app._sha("main")[0]


def test_bad_requests_are_explained(bench_app):
    with pytest.raises(ValueError):
        bench_app.start_baseline("no-such-ref")
    with pytest.raises(ValueError, match="same commit"):
        bench_app.start_experiment("main", "main")
    with pytest.raises(ValueError, match="metric"):
        bench_app.start_experiment("feature", "main", metric="depth")
    with pytest.raises(LookupError):
        bench_app.job(999)


def test_api_runs_an_experiment_end_to_end(bench_app, bench_url):
    http = bench_url
    status, body = _req(http + "/api/jobs", "POST",
                        {"kind": "experiment", "candidate": "feature", "baseline": "main"})
    assert status == 200
    job_id = body["job_id"]
    run_until_idle(bench_app)
    status, job = _req(f"{http}/api/jobs/{job_id}")
    assert status == 200 and job["state"] == "done"
    assert job["result"]["verdict"]["state"] == "no measurable difference"
    assert {r["metric"] for r in job["table"]} >= {"dlvl6", "depth"}
    assert _req(http + "/api/experiments")[1][0]["id"] == job_id
    status, dash = _req(http + "/api/dashboard")
    assert dash["games"] == 2304
    status, games = _req(http + "/api/games?ref=feature&where=max_depth>3&limit=2")
    assert games["matches"] == 2304 and len(games["games"]) == 2
    assert _req(http + "/api/results?ref=main&metric=dlvl6")[1]["hits"] == 0


def test_api_errors(bench_url):
    http = bench_url
    assert _req(http + "/api/jobs", "POST", {"kind": "nonsense"})[0] == 400
    assert _req(http + "/api/jobs/12345")[0] == 404
    assert _req(http + "/api/jobs/abc")[0] == 400
    assert _req(http + "/api/games?where=max_depth>>1")[0] == 400
    assert _req(http + "/api/nothing")[0] == 404
    assert _req(http + "/api/jobs", "DELETE")[1] == {"stopped": False}


def test_page_is_served(bench_url):
    with urlopen(bench_url + "/", timeout=10) as r:
        assert r.headers["Content-Type"].startswith("text/html")
        page = r.read()
        assert b"<title>Screens Bench</title>" in page
        for section in (b'id="job"', b'id="experiment"', b'id="dashboard"', b'id="history"', b'id="ascenders"'):
            assert section in page


def test_second_server_on_the_same_port_exits_with_a_message(bench_app):
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen()
    try:
        with pytest.raises(SystemExit, match="already running"):
            serve(bench_app, port=blocker.getsockname()[1])
    finally:
        blocker.close()


def test_build_app_marks_jobs_of_a_stopped_server_interrupted(tmp_path):
    store = Store(tmp_path / "data" / "results.db")
    job = store.add_job("baseline", {"sha": "x", "games": 5})
    store.set_job(job, "running", {})
    del store
    app = cli.build_app(workers=1, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache")
    assert app.store.job(job)["state"] == "interrupted"


def test_import_results_file(tmp_path, bench_repo, monkeypatch):
    repo = bench_repo
    monkeypatch.setattr(cli, "REPO", repo)
    results = tmp_path / "old.jsonl"
    results.write_text("\n".join(json.dumps(_game(d)) for d in (3, 7)) + "\n")
    assert cli.main(["--data", str(tmp_path / "d"), "import", "results", str(results), "--ref", "main"]) == 0
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
    assert Store(tmp_path / "d" / "results.db").count(sha) == 2


def test_requests_a_foreign_web_page_could_send_are_refused(bench_url):
    # a cross-site form or fetch can POST text/plain without a CORS preflight
    req = Request(bench_url + "/api/jobs", data=b'{"kind": "baseline"}', method="POST",
                  headers={"Content-Type": "text/plain"})
    with pytest.raises(HTTPError) as e:
        urlopen(req, timeout=10)
    assert e.value.code == 415
    # DNS rebinding: the page's own host name arrives in the Host header
    req = Request(bench_url + "/api/status", headers={"Host": "evil.example:8765"})
    with pytest.raises(HTTPError) as e:
        urlopen(req, timeout=10)
    assert e.value.code == 403


def test_imports_only_fetch_http_urls(bench_app):
    with pytest.raises(ValueError, match="http"):
        bench_app.start_import("xlog", url="file:///etc/passwd")


def test_results_carry_the_ladder_even_without_reference_ascensions(bench_app):
    assert bench_app.yardstick() == {}
    rows = bench_app.results("main")["ladder"]
    assert [r["rung"] for r in rows] == list(range(1, 18))


def test_stop_all_and_shutdown_over_http(bench_app):
    httpd, stop = serve(bench_app, port=0)
    serving = threading.Thread(target=httpd.serve_forever, daemon=True)
    serving.start()
    http = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        jobs = [_req(http + "/api/jobs", "POST", {"kind": "baseline", "ref": "main", "games": 3})[1]["job_id"]
                for _ in range(2)]
        assert _req(http + "/api/stop-all", "POST", {}) == (200, {"stopped": jobs})
        assert all(bench_app.store.job(j)["state"] == "stopped" for j in jobs)
        late = _req(http + "/api/jobs", "POST", {"kind": "baseline", "ref": "main", "games": 3})[1]["job_id"]
        assert _req(http + "/api/shutdown", "POST", {}) == (200, {"stopped": [late], "shutting_down": True})
        serving.join(timeout=10)
        assert not serving.is_alive() and stop.is_set()
    finally:
        httpd.server_close()


def test_shutdown_needs_a_serving_server(bench_app):
    with pytest.raises(ValueError, match="cannot shut itself down"):
        bench_app.shutdown()
