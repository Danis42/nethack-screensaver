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
