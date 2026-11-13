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
from autoascend.ladder import RUNGS


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
        bench_app.start_experiment("main", "main", mde=0.3, discordance=0.5)
    with pytest.raises(ValueError, match="metric"):
        bench_app.start_experiment("feature", "main", metric="depth")
    with pytest.raises(LookupError):
        bench_app.job(999)


def test_api_runs_an_experiment_end_to_end(bench_app, bench_url):
    http = bench_url
    status, body = _req(http + "/api/jobs", "POST", {"kind": "baseline", "ref": "main", "lo": 1000, "hi": 1096})
    assert status == 200
    run_until_idle(bench_app)
    status, body = _req(http + "/api/jobs", "POST",
                        {"kind": "experiment", "candidate": "feature", "baseline": "main", "mde": 0.3,
                         "discordance": 0.5})
    assert status == 200
    job_id = body["job_id"]
    run_until_idle(bench_app)
    status, job = _req(f"{http}/api/jobs/{job_id}")
    assert status == 200 and job["state"] == "done"
    assert job["result"]["verdict"]["state"] == "no detectable effect >= MDE"
    assert [look["n"] for look in job["result"]["looks"]] == [96]
    assert {r["metric"] for r in job["table"]} >= {"dlvl6", "depth"}
    assert _req(http + "/api/experiments")[1][0]["id"] == job_id
    status, dash = _req(http + "/api/dashboard")
    assert dash["games"] == 96
    status, games = _req(http + "/api/games?ref=feature&where=max_depth>3&limit=2")
    assert games["matches"] == 96 and len(games["games"]) == 2
    assert _req(http + "/api/results?ref=main&metric=dlvl6")[1]["hits"] == 0


def test_an_experiment_must_declare_its_mde(bench_app, monkeypatch):
    from bench import power
    with pytest.raises(ValueError, match="declare the minimum detectable effect"):
        bench_app.start_experiment("feature", "main", discordance=0.5)
    for bad in (0, 1, -0.1):
        with pytest.raises(ValueError):
            bench_app.start_experiment("feature", "main", mde=bad, discordance=0.5)
    monkeypatch.setattr(power, "DEFAULT_DISCORDANCE", None)
    with pytest.raises(ValueError, match="pass discordance"):
        bench_app.start_experiment("feature", "main", mde=0.3)


def test_a_started_experiment_stores_its_declared_plan(bench_app):
    from bench import power
    sha = bench_app._sha("main")[0]
    for seed in range(1000, 1096):
        bench_app.store.add_game(sha, None, {"max_depth": 1, "end_reason": "x", "seed": seed})
    job_id = bench_app.start_experiment("feature", "main", mde=0.3, discordance=0.5)["job_id"]
    spec = bench_app.job(job_id)["spec"]
    plan = power.plan(0.3, 0.5)
    assert spec["declared"] == plan and spec["block"] == 96
    assert (spec["seeds"]["lo"], spec["seeds"]["hi"]) == (1000, 1000 + plan["n_planned"])


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
    assert [r["key"] for r in rows] == [r.key for r in RUNGS] and [r["order"] for r in rows] == list(range(1, 19))
    assert len(rows) == 18 and rows[7]["key"] == "quest_portal" and rows[8]["key"] == "quest"


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


def test_a_baseline_on_a_window_records_seeds_env_and_lock_blob(tmp_path, bench_repo):
    from bench.provenance import env_id
    from bench.scheduler import Scheduler
    from bench.server import App
    from bench.store import Store
    from bench_fakes import FakeWorker, game
    env = {"nle_commit": "c" * 40, "lock_sha256": "l", "python": "3.13", "numpy": "2", "numba": "0.6"}
    store = Store(tmp_path / "w.db")
    app = App(store, Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), []), slots=2),
              bench_repo, tmp_path / "cache", env=env)
    spec = app.job(app.start_baseline("main", lo=1000, hi=1010)["job_id"])["spec"]
    assert spec["seeds"] == {"range": "dev", "lo": 1000, "hi": 1010} and spec["games"] == 10
    assert spec["env_id"] == env_id(env) == app.env_id and spec["env"] == env
    assert "lock_blob" in spec and store.env(app.env_id) == env


def test_a_default_baseline_starts_at_the_baseline_window(bench_app):
    spec = bench_app.job(bench_app.start_baseline("main", games=3)["job_id"])["spec"]
    assert spec["seeds"]["lo"] == 1000 and spec["seeds"]["hi"] == 1003


@pytest.mark.parametrize("lo, hi", [(5, 5), (9, 3), ("x", 4), (-1, 3)])
def test_empty_or_bad_windows_are_refused(bench_app, lo, hi):
    with pytest.raises(ValueError):
        bench_app.start_baseline("main", lo=lo, hi=hi)


@pytest.mark.parametrize("kwargs", [{"lgen": "on"}, {"lgen": 7}, {"replicate": 2}, {"replicate": -1}])
def test_bad_lgen_or_replicate_values_are_refused(bench_app, kwargs):
    with pytest.raises(ValueError):
        bench_app.start_baseline("main", games=3, **kwargs)


def test_baseline_spec_records_lgen_mode_and_replicate(bench_app):
    spec = bench_app.job(bench_app.start_baseline("main", games=3, lgen="seed", replicate=1)["job_id"])["spec"]
    assert spec["lgen"] == "seed" and spec["replicate"] == 1
    assert bench_app.job(bench_app.start_baseline("main", games=3)["job_id"])["spec"]["lgen"] == "off"


def test_final_range_baselines_are_refused(bench_app):
    with pytest.raises(ValueError, match="final"):
        bench_app.start_baseline("main", lo=1_000_000, hi=1_000_010)


def test_confirm_baselines_need_a_gate(bench_app):
    with pytest.raises(ValueError, match="gate"):
        bench_app.start_baseline("main", lo=100_000, hi=100_010)
    spec = bench_app.job(bench_app.start_baseline("main", lo=100_000, hi=100_010, gate="phase-2-gate")["job_id"])["spec"]
    assert spec["seeds"]["range"] == "confirm" and spec["gate"] == "phase-2-gate"


def test_clean_attempt_jobs_cannot_be_created_over_http(bench_url):
    status, body = _req(bench_url + "/api/jobs", "POST", {"kind": "clean_attempt", "ref": "main"})
    assert status == 400 and "not creatable over HTTP or MCP" in body["error"]


def test_an_interrupted_job_resumes_under_its_id_and_plays_each_seed_once(tmp_path, bench_repo):
    from bench.scheduler import Scheduler
    from bench.server import App
    from bench.store import Store
    from bench_fakes import FakeWorker, game
    played = []
    store = Store(tmp_path / "res.db")
    app = App(store, Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=2),
              bench_repo, tmp_path / "cache")
    job_id = app.start_baseline("main", lo=1000, hi=1010)["job_id"]
    for _ in range(3):
        app.scheduler.tick()
    app.scheduler.shutdown()
    assert 0 < store.count(app.job(job_id)["spec"]["sha"]) < 10
    store2 = Store(tmp_path / "res.db")  # the server restarted
    store2.interrupt_unfinished()
    app2 = App(store2, Scheduler(store2, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=2),
               bench_repo, tmp_path / "cache")
    assert app2.resume(job_id) == {"job_id": job_id, "resumed": True}
    run_until_idle(app2)
    job = app2.job(job_id)
    assert job["id"] == job_id and job["state"] == "done"
    rows = store2._all("SELECT seed, COUNT(*) AS n FROM games GROUP BY seed ORDER BY seed")
    assert [(r["seed"], r["n"]) for r in rows] == [(s, 1) for s in range(1000, 1010)]


def test_only_interrupted_jobs_resume_over_http(bench_app, bench_url):
    job_id = bench_app.start_baseline("main", games=2)["job_id"]
    run_until_idle(bench_app)
    status, body = _req(f"{bench_url}/api/jobs/{job_id}/resume", "POST", {})
    assert status == 400 and "only interrupted jobs" in body["error"]
    status, body = _req(f"{bench_url}/api/jobs/999/resume", "POST", {})
    assert status == 404


def test_a_running_job_is_not_started_until_its_first_game_row(bench_app):
    job_id = bench_app.start_baseline("main", games=3)["job_id"]
    with bench_app.lock:
        bench_app.scheduler.tick()  # picks the job up: running
    job = bench_app.job(job_id)  # results are collected on the next tick: no game row yet
    assert job["state"] == "running" and job["started"] is False and job["first_game_at"] is None


def test_a_fully_reused_baseline_is_done_but_never_started(bench_app):
    first = bench_app.start_baseline("main", games=3)["job_id"]
    run_until_idle(bench_app)
    again = bench_app.start_baseline("main", games=3)["job_id"]
    run_until_idle(bench_app)
    job = bench_app.job(again)
    assert job["state"] == "done" and job["started"] is False
    assert job["games_played"] == 0 and job["games_reused"] == 3
    assert bench_app.job(first)["started"] is True and bench_app.job(first)["games_played"] == 3


def test_power_plans_or_reports_the_mde_at_n(bench_app, bench_url):
    from bench import power
    assert bench_app.power(mde=0.03, discordance=0.2) == power.plan(0.03, 0.2)
    at_n = bench_app.power(n=2000, discordance=0.2)
    assert at_n == {"n": 2000, "psi": 0.2, "mcnemar_mde": power.mcnemar_mde(2000, 0.2),
                    "sequential_mde": power.sequential_mde(2000, 0.2)}
    with pytest.raises(ValueError):
        bench_app.power(discordance=0.2)
    status, api = _req(bench_url + "/api/power?mde=0.03&discordance=0.2")
    assert status == 200 and api == power.plan(0.03, 0.2)
    assert _req(bench_url + "/api/power?mde=abc&discordance=0.2")[0] == 400


def test_power_cli_prints_the_plan(capsys):
    from bench import power
    assert cli.main(["power", "--mde", "0.03", "--discordance", "0.2"]) == 0
    assert json.loads(capsys.readouterr().out) == power.plan(0.03, 0.2)


def test_an_experiment_needs_a_stored_baseline(bench_app):
    sha = bench_app._sha("main")[0]
    with pytest.raises(ValueError, match=f"baseline {sha[:10]} has no stored games.*Pitfall 6"):
        bench_app.start_experiment("feature", "main", mde=0.3, discordance=0.5)
    job_id = bench_app.start_experiment("feature", "main", mde=0.3, discordance=0.5,
                                        allow_new_baseline=True)["job_id"]
    assert bench_app.job(job_id)["state"] == "queued"


def _keyed_app(tmp_path, bench_repo, env=None):
    from bench.scheduler import Scheduler
    from bench.server import App
    from bench.store import Store
    from bench_fakes import FakeWorker, game
    store = Store(tmp_path / "keyed.db")
    app = App(store, Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), []), slots=2),
              bench_repo, tmp_path / "cache", env=env)
    return store, app


def test_results_games_and_dashboard_read_one_game_key(tmp_path, bench_repo):
    # review CR-01: lgen-seed rows of the same seeds were counted next to the lgen-off rows
    from bench import seeds
    env = {"nle_commit": "c" * 40, "lock_sha256": "l", "python": "3.13", "numpy": "2", "numba": "0.6"}
    store, app = _keyed_app(tmp_path, bench_repo, env)
    sha = app.results("main")["sha"]
    for s in range(1000, 1004):
        store.add_game(sha, None, {"seed": s, "max_depth": 4}, env_id=app.env_id)
        store.add_game(sha, None, {"seed": s, "lgen": s + seeds.LGEN_OFFSET, "max_depth": 9}, env_id=app.env_id)
        store.add_game(sha, None, {"seed": s, "max_depth": 9}, env_id="other-env")
    assert seeds.USE_LGEN == "off"
    assert app.results("main")["games"] == 4
    assert app.games("main", limit=100)["matches"] == 4
    assert app.dashboard("main")["games"] == 4
    assert app.funnel("main", lo=1000, hi=1004)["n"] == 4


def test_a_job_from_another_environment_is_not_resumed(tmp_path, bench_repo):
    # review CR-02: a resumed job would store new-interpreter games under the old env_id
    env = {"nle_commit": "c" * 40, "lock_sha256": "l", "python": "3.13", "numpy": "2", "numba": "0.6"}
    store, app = _keyed_app(tmp_path, bench_repo, env)
    job_id = app.start_baseline("main", lo=1000, hi=1004)["job_id"]
    app.scheduler.shutdown()
    store.interrupt_unfinished()
    _, app2 = _keyed_app(tmp_path, bench_repo, dict(env, nle_commit="d" * 40))
    with pytest.raises(ValueError, match="environment"):
        app2.resume(job_id)
    assert app2.job(job_id)["state"] == "interrupted"
    _, app3 = _keyed_app(tmp_path, bench_repo, env)
    assert app3.resume(job_id) == {"job_id": job_id, "resumed": True}
