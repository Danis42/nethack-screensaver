import subprocess
import threading

import pytest

from bench_fakes import FakeWorker, game
from bench.scheduler import Scheduler
from bench.server import App, serve
from bench.store import Store


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def bench_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    for name in ("one", "two"):
        (repo / "f.txt").write_text(name)
        git(repo, "add", "f.txt")
        git(repo, "commit", "-q", "-m", name)
    git(repo, "branch", "feature", "HEAD~1")
    return repo


@pytest.fixture
def bench_app(tmp_path, bench_repo):
    store = Store(tmp_path / "r.db")
    played = []
    sched = Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=16)
    return App(store, sched, bench_repo, tmp_path / "cache")


@pytest.fixture
def bench_url(bench_app):
    httpd, stop = serve(bench_app, port=0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    stop.set()
    httpd.shutdown()
    httpd.server_close()


def run_until_idle(app, ticks=3000):
    """Tick the scheduler under the app lock (the server loop ticks too) until no job is left."""
    for _ in range(ticks):
        with app.lock:
            app.scheduler.tick()
            if app.scheduler.job is None and app.store.next_queued() is None:
                return
    raise AssertionError("job did not finish")
