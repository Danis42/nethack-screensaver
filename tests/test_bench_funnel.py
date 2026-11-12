import io
import json
import random
import threading
import tokenize
from pathlib import Path

import pytest

from bench import cli, funnel as funnel_mod, mcp_server, stats
from bench.funnel import STAGES, funnel
from bench.scheduler import Scheduler
from bench.server import App, serve
from bench.store import Store
from bench_fakes import FakeWorker, game
from test_bench_server import _req
from autoascend.ladder import RUNGS


def _g(ladder=None, end_reason="DEATH: killed by a newt", **extra):
    g = {"end_reason": end_reason, **extra}
    if ladder is not None:
        g["ladder"] = ladder
    return g


def _rows(out):
    return {r["key"]: r for r in out["rows"]}


def test_empty_funnel_has_every_stage_and_no_rates():
    out = funnel([])
    assert [r["key"] for r in out["rows"]] == list(STAGES) == [r.key for r in RUNGS]
    assert len(STAGES) == 18 and "quest_portal" in STAGES
    assert STAGES.index("quest_portal") + 1 == STAGES.index("quest")
    for r in out["rows"]:
        assert r["n"] == 0 and r["hits"] == 0
        assert r["rate"] is None and r["lo"] is None and r["hi"] is None
    assert out["n"] == 0


def test_marginal_reach_with_wilson():
    games = [_g({"mines": 10, "minetown": 20}), _g({"mines": 30}), _g({})]
    rows = _rows(funnel(games))
    assert (rows["mines"]["hits"], rows["mines"]["n"]) == (2, 3)
    assert (rows["minetown"]["hits"], rows["minetown"]["n"]) == (1, 3)
    assert (rows["oracle"]["hits"], rows["oracle"]["n"]) == (0, 3)
    for key, k in (("mines", 2), ("minetown", 1), ("oracle", 0)):
        assert (rows[key]["lo"], rows[key]["hi"]) == stats.wilson(k, 3, stats.Z95)
        assert rows[key]["rate"] == k / 3
    assert rows["mines"]["order"] == 1 and rows["ascended"]["order"] == 18


def test_same_turn_stages_count_for_both():
    rows = _rows(funnel([_g({"mines": 500, "sokoban": 500})]))
    assert rows["mines"]["hits"] == 1 and rows["sokoban"]["hits"] == 1


def test_order_of_games_does_not_matter():
    games = [_g({"mines": i, "oracle": i}) if i % 2 else _g({"sokoban": i}) for i in range(20)]
    shuffled = list(games)
    random.Random(4).shuffle(shuffled)
    assert funnel(games) == funnel(shuffled)
    assert [r["key"] for r in funnel(shuffled)["rows"]] == list(STAGES)


def test_nothing_is_dropped_silently():
    games = [_g({"mines": 1}), _g(None), _g({}, ladder_error=1),
             _g({"mines": 2}, end_reason="watchdog"), _g({}, end_reason="exception: boom")]
    out = funnel(games)
    assert out["n"] == 4
    assert out["excluded"] == {"no_ladder": 1}
    assert out["flagged"] == {"ladder_error": 1, "watchdog": 1, "exception": 1}
    assert _rows(out)["mines"]["n"] == 4


def test_conditional_rate_along_the_pipeline():
    games = [_g({"mines": 1, "minetown": 2}), _g({"mines": 1}), _g({"minetown": 5}), _g({})]
    rows = _rows(funnel(games))
    first = rows["mines"]
    assert first["prev"] is None and (first["cond_hits"], first["cond_n"]) == (first["hits"], first["n"])
    town = rows["minetown"]
    assert town["prev"] == "mines" and (town["cond_hits"], town["cond_n"]) == (1, 2) and town["cond_rate"] == 0.5
    assert rows["oracle"]["cond_n"] == 2 and rows["oracle"]["cond_rate"] == 0.0  # reached minetown: 2 games
    assert rows["sokoban"]["cond_n"] == 0 and rows["sokoban"]["cond_rate"] is None


def test_funnel_reuses_the_bench_wilson():
    assert "def wilson" not in Path(funnel_mod.__file__).read_text()


# App, HTTP, MCP and CLI


def _laddered(sha, seed):
    return {**game(4), "seed": seed, "ladder": {"mines": 10} if seed % 2 else {"mines": 10, "minetown": 40}}


@pytest.fixture
def stored(tmp_path, bench_repo):
    """An App over results.db in a data dir, with seeds 1000-1003 of main stored as natural rows."""
    data = tmp_path / "data"
    store = Store(data / "results.db")
    app = App(store, Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), []), slots=4),
              bench_repo, tmp_path / "cache")
    sha = app._sha("main")[0]
    for seed in range(1000, 1004):
        store.add_game(sha, None, _laddered(sha, seed))
    return app, data, sha


def test_app_funnel_reads_the_natural_window(stored):
    app, _, sha = stored
    out = app.funnel("main", lo=1000, hi=1004)
    assert out["sha"] == sha and out["window"] == [1000, 1004] and out["lgen"] == "off"
    rows = _rows(out)
    assert (rows["mines"]["hits"], rows["mines"]["n"]) == (4, 4)
    assert rows["minetown"]["hits"] == 2
    assert app.funnel("main", lo=1000, hi=1002)["rows"][0]["n"] == 2


def test_app_funnel_refuses_tool_seeds(stored):
    app, _, _ = stored
    with pytest.raises(ValueError, match="tool"):
        app.funnel("main", lo=999, hi=1004)
    with pytest.raises(ValueError):
        app.funnel("main", lo=10, hi=5)


def test_replicate_rows_do_not_change_the_funnel(stored):
    app, _, sha = stored
    before = app.funnel("main", lo=1000, hi=1004)
    for seed in range(1000, 1004):
        app.store.add_game(sha, None, {**game(9), "seed": seed, "ladder": {"mines": 1, "oracle": 2}}, rep=1)
    assert app.funnel("main", lo=1000, hi=1004) == before


def test_app_funnel_of_a_baseline_job_uses_its_spec(stored):
    app, _, sha = stored
    job_id = app.start_baseline("main", lo=1000, hi=1004)["job_id"]
    out = app.funnel(job=job_id)
    assert out["sha"] == sha and out["window"] == [1000, 1004] and out["lgen"] == "off"


def test_api_mcp_and_cli_agree(stored, monkeypatch, capsys):
    app, data, sha = stored
    httpd, stop = serve(app, port=0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        status, api = _req(url + "/api/funnel?ref=main&lo=1000&hi=1004")
        assert status == 200
        assert _req(url + "/api/funnel?lo=abc")[0] == 400
        assert _req(url + "/api/funnel?lo=10&hi=20")[0] == 400
        assert _req(url + "/api/funnel?lo=1000&hi=1004&lgen=bogus")[0] == 400
        monkeypatch.setattr(mcp_server, "URL", url)
        mcp = mcp_server.bench_funnel("main", lo=1000, hi=1004)
    finally:
        stop.set()
        httpd.shutdown()
        httpd.server_close()
    assert mcp == api
    assert cli.main(["--data", str(data), "funnel", sha, "--lo", "1000", "--hi", "1004",
                     "--repo", str(app.repo)]) == 0
    assert json.loads(capsys.readouterr().out) == api


# the old rung number decides nothing


def _string_tokens(path):
    """(STRING token, previous token, the one before) in code order; comments are dropped by the tokenizer
    filter, and a docstring is never preceded by '[' or 'get(', so it can never match below."""
    toks = [t for t in tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
            if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT)]
    for i, t in enumerate(toks):
        if t.type == tokenize.STRING and i > 1:
            yield t, toks[i - 1], toks[i - 2]


def test_no_decision_path_reads_rung():
    bench = Path(funnel_mod.__file__).parent
    offenders = []
    for path in sorted(bench.glob("*.py")):
        for t, prev, before in _string_tokens(path):
            if t.string.strip("'\"") != "rung":
                continue
            subscript = prev.string == "["
            get_call = prev.string == "(" and before.string == "get"
            if subscript or get_call:
                offenders.append(f"{path.name}:{t.start[0]}")
    assert offenders == []
