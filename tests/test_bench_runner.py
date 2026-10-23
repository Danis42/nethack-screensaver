import sys
import time

from bench.runner import ProcessWorker

FAKE_GAME = '''
from dataclasses import dataclass

@dataclass
class GameResult:
    role: str
    max_depth: int
    end_reason: str

_n = [0]

def run_game(watchdog_seconds=None):
    _n[0] += 1
    print("Warning: NetHack asked for env variable ROGUEOPTS")  # noise on stdout
    if _n[0] == 3:
        raise SystemExit(1)  # the third game kills the process
    return GameResult("val", _n[0], "DEATH: killed by a newt")
'''


def _fake_worktree(tmp_path):
    pkg = tmp_path / "wt" / "nethack_screensaver"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "game.py").write_text(FAKE_GAME)
    return tmp_path / "wt"


def _wait_for(predicate, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("timed out")


def test_worker_plays_on_request_and_keeps_noise_out_of_results(tmp_path):
    w = ProcessWorker(sys.executable, _fake_worktree(tmp_path), tmp_path / "worker.log", nice=0)
    try:
        w.play()
        w.play()
        got = []
        _wait_for(lambda: got.extend(w.results()) or len(got) == 2)
        assert [r["max_depth"] for r in got] == [1, 2]
        assert w.alive()
    finally:
        w.close()
    assert "ROGUEOPTS" in (tmp_path / "worker.log").read_text()


def test_worker_death_is_visible(tmp_path):
    w = ProcessWorker(sys.executable, _fake_worktree(tmp_path), tmp_path / "worker.log", nice=0)
    try:
        for _ in range(3):
            w.play()
        _wait_for(lambda: not w.alive())
        assert [r["max_depth"] for r in w.results()] == [1, 2]
    finally:
        w.close()


SEEDED_GAME = '''
from dataclasses import dataclass

@dataclass
class GameResult:
    max_depth: int
    seed: object = None

def run_game(watchdog_seconds=None, seed=None):
    return GameResult(3, seed)
'''


def test_worker_passes_the_seed_when_the_commit_can_take_one(tmp_path):
    wt = _fake_worktree(tmp_path)
    (wt / "nethack_screensaver" / "game.py").write_text(SEEDED_GAME)
    w = ProcessWorker(sys.executable, wt, tmp_path / "worker.log", nice=0)
    try:
        w.play(17)
        got = []
        _wait_for(lambda: got.extend(w.results()) or got)
        assert got == [{"max_depth": 3, "seed": 17}]
    finally:
        w.close()


def test_an_old_commit_plays_unseeded_and_says_so_by_leaving_out_the_seed(tmp_path):
    w = ProcessWorker(sys.executable, _fake_worktree(tmp_path), tmp_path / "worker.log", nice=0)
    try:
        w.play(5)
        got = []
        _wait_for(lambda: got.extend(w.results()) or got)
        assert "seed" not in got[0] and got[0]["max_depth"] == 1
    finally:
        w.close()


def test_play_lines_are_parsed():
    from bench.worker import parse
    assert parse("play\n") == (True, None) and parse("play 7\n") == (True, 7)
    assert parse("stop\n") == (False, None) and parse("\n") == (False, None)


HASH_SEED_GAME = '''
import os
from dataclasses import dataclass

@dataclass
class GameResult:
    role: str
    max_depth: int

def run_game(watchdog_seconds=None):
    return GameResult(os.environ.get("PYTHONHASHSEED", "unset"), 1)
'''


def test_worker_runs_with_a_fixed_hash_seed(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "random")  # whatever the server was started with
    wt = _fake_worktree(tmp_path)
    (wt / "nethack_screensaver" / "game.py").write_text(HASH_SEED_GAME)
    w = ProcessWorker(sys.executable, wt, tmp_path / "worker.log", nice=0)
    try:
        w.play()
        got = []
        _wait_for(lambda: got.extend(w.results()) or got)
        assert got[0]["role"] == "0"
    finally:
        w.close()


ENV_GAME = '''
import os
from dataclasses import dataclass

@dataclass
class GameResult:
    role: str
    turns: int

def run_game(**kw):
    keys = ("LD_PRELOAD", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")
    return GameResult("|".join(os.environ.get(k, "unset") for k in keys), 1)
'''


def test_worker_loads_the_clock_shim_and_one_blas_thread(tmp_path):
    wt = _fake_worktree(tmp_path)
    (wt / "nethack_screensaver" / "game.py").write_text(ENV_GAME)
    w = ProcessWorker(sys.executable, wt, tmp_path / "worker.log", nice=0)
    try:
        w.play()
        got = []
        _wait_for(lambda: got.extend(w.results()) or got)
        preload, omp, blas = got[0]["role"].split("|")
        assert "fixtime-" in preload and (omp, blas) == ("1", "1")
    finally:
        w.close()
