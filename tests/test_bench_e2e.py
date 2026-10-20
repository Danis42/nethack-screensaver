import sys
import time
from pathlib import Path

import pytest

from bench import gitrefs
from bench.runner import ProcessWorker
from bench.scheduler import Scheduler
from bench.store import Store

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_two_real_games_from_a_worktree(tmp_path):
    sha, _ = gitrefs.resolve(REPO, "HEAD")
    store = Store(tmp_path / "r.db")

    def spawn(s):
        return ProcessWorker(Path(sys.executable), gitrefs.ensure_worktree(REPO, s, tmp_path / "wt"),
                             tmp_path / "worker.log")

    sched = Scheduler(store, spawn, slots=2)
    job = sched.submit("baseline", {"ref": "HEAD", "sha": sha, "games": 2})
    end = time.time() + 900
    while sched.job is not None or store.next_queued() is not None:
        assert time.time() < end, (tmp_path / "worker.log").read_text()[-2000:]
        sched.tick()
        time.sleep(0.2)
    assert store.job(job)["state"] == "done"
    games = store.games(sha)
    assert len(games) == 2 and all("max_depth" in g and "end_reason" in g for g in games)
    gitrefs.prune(REPO, tmp_path / "wt", now=time.time() + 30 * 86400)
