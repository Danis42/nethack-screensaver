from bench_fakes import FakeWorker, game as _game
from bench.scheduler import Scheduler
from bench.store import Store


def _scheduler(tmp_path, make, slots=4):
    store = Store(tmp_path / "r.db")
    played, workers = [], []

    def spawn(sha):
        workers.append(FakeWorker(sha, make, played))
        return workers[-1]

    return Scheduler(store, spawn, slots=slots), store, played, workers


def _run(scheduler, ticks=2000):
    for _ in range(ticks):
        scheduler.tick()
        if scheduler.job is None and scheduler.store.next_queued() is None:
            return
    raise AssertionError("job did not finish")


def _experiment(scheduler, metric="dlvl6"):
    return scheduler.submit("experiment", {"candidate": "cand", "candidate_ref": "branch",
                                           "baseline": "base", "baseline_ref": "main", "metric": metric})


def test_baseline_tops_up_stored_games(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    for seed in range(5):
        store.add_game("base", None, {**_game(3), "seed": seed})
    store.add_game("base", None, _game(3))  # unseeded, from before seeding: does not count
    job = s.submit("baseline", {"ref": "main", "sha": "base", "games": 8})
    _run(s)
    assert len(played) == 3 and store.seeds("base") == set(range(8))
    assert store.job(job)["state"] == "done" and store.job(job)["result"] == {"games": 8}


def test_clear_win_is_decided_at_the_first_checkpoint(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    job = _experiment(s)
    _run(s)
    result = store.job(job)["result"]
    assert result["verdict"]["state"] == "better" and result["verdict"]["checkpoint"] == 192
    assert store.count("cand") == 192 and store.count("base") == 192


def test_stored_baseline_games_are_reused(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    for seed in range(192):
        store.add_game("base", None, {**_game(1), "seed": seed})
    _experiment(s)
    _run(s)
    assert set(played) == {"cand"} and len(played) == 192


def test_no_difference_runs_to_the_last_checkpoint(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if i % 2 else 1), slots=8)
    job = _experiment(s)
    _run(s, ticks=10000)
    result = store.job(job)["result"]
    assert [c["checkpoint"] for c in result["checkpoints"]] == [192, 384, 576, 1152, 2304]
    assert result["verdict"]["state"] == "no measurable difference"
    assert store.count("cand") == 2304 and store.count("base") == 2304


def test_dead_worker_is_replaced_and_the_game_replayed(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", {"ref": "main", "sha": "base", "games": 3})
    s.tick()  # starts the job and the first game
    workers[0].pending.clear()
    workers[0].dead = True  # dies mid-game
    _run(s)
    assert store.count("base") == 3 and len(workers) == 2 and workers[0].closed


def test_three_deaths_in_a_row_fail_the_job(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    job = s.submit("baseline", {"ref": "main", "sha": "base", "games": 3})
    for _ in range(10):
        s.tick()
        if workers:
            workers[-1].pending.clear()
            workers[-1].dead = True
    assert store.job(job)["state"] == "failed"
    assert "died 3 times" in store.job(job)["result"]["error"]
    assert s.job is None


def test_stop_keeps_stored_games_and_queued_jobs_run_next(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    first = s.submit("baseline", {"ref": "main", "sha": "base", "games": 100})
    second = s.submit("baseline", {"ref": "x", "sha": "other", "games": 2})
    for _ in range(3):
        s.tick()
    stored = store.count("base")
    assert stored > 0
    assert s.stop() is True
    assert store.job(first)["state"] == "stopped" and all(w.closed for w in workers)
    _run(s)
    assert store.count("base") == stored and store.job(second)["state"] == "done"


def test_status_reports_progress(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    assert s.status()["job"] is None
    s.submit("baseline", {"ref": "main", "sha": "base", "games": 10})
    for _ in range(3):
        s.tick()
    st = s.status()
    assert st["job"]["progress"]["target"] == 10 and st["slots"] == 2
    assert 0 < st["job"]["progress"]["games"] <= 10


def test_both_sides_play_the_same_seeds_once(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    _experiment(s)
    _run(s)
    for sha in ("base", "cand"):
        seeds = [seed for w in workers if w.sha == sha for seed in w.seeds]
        assert sorted(seeds) == list(range(192))


def test_a_dead_workers_seed_is_played_again(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", {"ref": "main", "sha": "base", "games": 3})
    s.tick()
    lost = workers[0].seeds[-1]
    workers[0].pending.clear()
    workers[0].dead = True
    _run(s)
    assert store.seeds("base") == {0, 1, 2} and lost in workers[1].seeds


def test_a_commit_that_cannot_seed_fails_the_job(tmp_path):
    store = Store(tmp_path / "r.db")
    s = Scheduler(store, lambda sha: FakeWorker(sha, lambda _, i: _game(3), [], seeded=False), slots=2)
    job = s.submit("baseline", {"ref": "old", "sha": "old", "games": 4})
    _run(s)
    assert store.job(job)["state"] == "failed"
    assert "cannot play seeded games" in store.job(job)["result"]["error"]
    assert store.count("old") == 0


def test_verdict_pairs_games_by_seed(tmp_path):
    # the candidate wins exactly the seeds the baseline loses: pairs see it at once
    def make(sha, i):
        return _game(10 if (sha == "cand") == (i % 2 == 0) else 1)
    s, store, played, workers = _scheduler(tmp_path, make, slots=1)
    job = _experiment(s)
    _run(s, ticks=20000)
    v = store.job(job)["result"]["verdict"]
    assert v["pairs"] == v["checkpoint"]
