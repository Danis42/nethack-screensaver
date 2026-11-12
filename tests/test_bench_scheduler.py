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


DECLARED = {"test": "msprt-beta1", "mde": 0.1, "psi": 0.3, "alpha": 0.05, "power": 0.8, "block": 96,
            "n_planned": 384, "mcnemar_mde_at_n": 0.08}


def _experiment(scheduler, metric="dlvl6"):
    return scheduler.submit("experiment", {"candidate": "cand", "candidate_ref": "branch",
                                           "baseline": "base", "baseline_ref": "main", "metric": metric,
                                           "seeds": {"range": "dev", "lo": 1000, "hi": 1384}, "block": 96,
                                           "declared": DECLARED})


def _bspec(sha, games, ref="main", lo=1000, **extra):
    """A baseline spec on the seed window [lo, lo + games)."""
    return {"ref": ref, "sha": sha, "games": games, "seeds": {"range": "dev", "lo": lo, "hi": lo + games}, **extra}


def test_baseline_tops_up_stored_games(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    for seed in range(1000, 1005):
        store.add_game("base", None, {**_game(3), "seed": seed})
    store.add_game("base", None, _game(3))  # unseeded, from before seeding: does not count
    job = s.submit("baseline", _bspec("base", 8, ref="main"))
    _run(s)
    assert len(played) == 3 and store.seeds("base") == set(range(1000, 1008))
    assert store.job(job)["state"] == "done" and store.job(job)["result"] == {"games": 8}


def test_clear_win_is_decided_at_the_first_look(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    job = _experiment(s)
    _run(s)
    result = store.job(job)["result"]
    assert result["verdict"]["state"] == "better" and result["verdict"]["n"] == 96
    assert result["looks"] == [{"n": 96, "b": 96, "c": 0, "log_lr": result["verdict"]["log_lr"]}]
    assert store.count("cand") == 96 and store.count("base") == 96


def test_stored_baseline_games_are_reused(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    for seed in range(1000, 1096):
        store.add_game("base", None, {**_game(1), "seed": seed})
    _experiment(s)
    _run(s)
    assert set(played) == {"cand"} and len(played) == 96


def test_identical_outcomes_run_to_the_planned_size(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3), slots=8)
    job = _experiment(s)
    _run(s, ticks=10000)
    result = store.job(job)["result"]
    assert [look["n"] for look in result["looks"]] == [96, 192, 288, 384]
    assert result["verdict"]["state"] == "no detectable effect >= MDE"
    assert result["verdict"]["n_planned"] == 384 and result["verdict"]["mde"] == 0.1
    assert store.count("cand") == 384 and store.count("base") == 384


def test_a_gap_in_the_prefix_blocks_judging(tmp_path):
    # every seed of two blocks is stored on both sides except candidate seed lo + 5, which never comes back
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    for seed in range(1000, 1192):
        store.add_game("base", None, {**_game(1), "seed": seed})
        if seed != 1005:
            store.add_game("cand", None, {**_game(10), "seed": seed})
    job = _experiment(s)
    for _ in range(50):
        s.tick()
        for w in workers:
            w.pending.clear()  # the worker withholds every result
    assert store.job(job)["state"] == "running"
    assert store.job(job)["result"].get("looks", []) == [] and "verdict" not in store.job(job)["result"]
    assert 1005 in [seed for w in workers if w.sha == "cand" for seed in w.seeds]


def test_a_lower_is_better_metric_flips_the_verdict(tmp_path):
    def make(sha, i):
        if sha == "cand":
            return {**_game(3), "end_reason": "ESCAPED: escaped the dungeon"}
        return _game(3)
    s, store, played, _ = _scheduler(tmp_path, make)
    job = _experiment(s, metric="died")
    _run(s)
    v = store.job(job)["result"]["verdict"]
    assert v["c"] == 96 and v["b"] == 0 and v["state"] == "better"  # fewer deaths is better


def test_an_experiment_without_a_declared_mde_fails(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    job = s.submit("experiment", {"candidate": "cand", "baseline": "base", "metric": "dlvl6",
                                  "seeds": {"range": "dev", "lo": 1000, "hi": 3304}})
    _run(s)
    assert store.job(job)["state"] == "failed" and "declared" in store.job(job)["result"]["error"]
    assert played == []


def test_dead_worker_is_replaced_and_the_game_replayed(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", _bspec("base", 3, ref="main"))
    s.tick()  # starts the job and the first game
    workers[0].pending.clear()
    workers[0].dead = True  # dies mid-game
    _run(s)
    assert store.count("base") == 3 and len(workers) == 2 and workers[0].closed


def test_three_deaths_in_a_row_fail_the_job(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    job = s.submit("baseline", _bspec("base", 3, ref="main"))
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
    first = s.submit("baseline", _bspec("base", 100, ref="main"))
    second = s.submit("baseline", _bspec("other", 2, ref="x"))
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
    s.submit("baseline", _bspec("base", 10, ref="main"))
    for _ in range(3):
        s.tick()
    st = s.status()
    assert st["job"]["progress"]["target"] == 10 and st["slots"] == 2
    assert 0 < st["job"]["progress"]["games"] <= 10


def test_status_reports_the_look_of_an_experiment(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    _experiment(s)
    s.tick()
    p = s.status()["job"]["progress"]
    assert (p["look"], p["prefix"], p["n_planned"]) == (0, 96, 384) and p["baseline"] + p["candidate"] <= 192


def test_both_sides_play_the_same_seeds_once(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    _experiment(s)
    _run(s)
    for sha in ("base", "cand"):
        seeds = [seed for w in workers if w.sha == sha for seed in w.seeds]
        assert sorted(seeds) == list(range(1000, 1096))


def test_a_dead_workers_seed_is_played_again(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", _bspec("base", 3, ref="main"))
    s.tick()
    lost = workers[0].seeds[-1]
    workers[0].pending.clear()
    workers[0].dead = True
    _run(s)
    assert store.seeds("base") == {1000, 1001, 1002} and lost in workers[1].seeds


def test_a_commit_that_cannot_seed_fails_the_job(tmp_path):
    store = Store(tmp_path / "r.db")
    s = Scheduler(store, lambda sha: FakeWorker(sha, lambda _, i: _game(3), [], seeded=False), slots=2)
    job = s.submit("baseline", _bspec("old", 4, ref="old"))
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
    assert v["pairs"] == v["n"] and v["n"] % 96 == 0


def test_stop_all_stops_the_active_job_and_the_queue(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    first = s.submit("baseline", _bspec("base", 100, ref="main"))
    second = s.submit("baseline", _bspec("other", 2, ref="x"))
    for _ in range(3):
        s.tick()
    stored = store.count("base")
    assert s.stop_all() == [first, second]
    assert store.job(first)["state"] == store.job(second)["state"] == "stopped"
    assert all(w.closed for w in workers) and s.job is None
    _run(s)
    assert store.count("base") == stored and store.count("other") == 0
    assert s.stop_all() == []


def test_a_baseline_window_plays_exactly_its_seeds_in_ascending_order(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", _bspec("base", 8, lo=1000, env_id="env1"))
    _run(s)
    assert [seed for w in workers for seed in w.seeds] == list(range(1000, 1008))
    rows = store._all("SELECT seed, env_id, rep FROM games WHERE sha = 'base' ORDER BY id")
    assert [(r["seed"], r["env_id"], r["rep"]) for r in rows] == [(seed, "env1", 0) for seed in range(1000, 1008)]


def test_a_job_spec_without_a_seed_window_fails(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    job = s.submit("baseline", {"ref": "main", "sha": "base", "games": 4})
    _run(s)
    assert store.job(job)["state"] == "failed"
    assert "no seed window" in store.job(job)["result"]["error"] and played == []


# Task 2: game key (lgen mode, replicate)

def _lgen_scheduler(tmp_path, capable=True):
    store = Store(tmp_path / "r.db")
    workers = []

    def spawn(sha):
        w = FakeWorker(sha, lambda s, i: _game(3), [])
        w.lgen_capable = capable
        workers.append(w)
        return w

    return Scheduler(store, spawn, slots=2), store, workers


def test_lgen_on_and_off_games_of_the_same_seeds_are_separate_rows(tmp_path):
    s, store, workers = _lgen_scheduler(tmp_path)
    s.submit("baseline", _bspec("base", 4, lo=1000, lgen="off"))
    _run(s)
    s.submit("baseline", _bspec("base", 4, lo=1000, lgen="seed"))
    _run(s)
    rows = store._all("SELECT seed, lgen FROM games WHERE sha = 'base' ORDER BY id")
    assert len(rows) == 8
    assert [r["lgen"] for r in rows[:4]] == [None] * 4
    assert sorted((r["seed"], r["lgen"]) for r in rows[4:]) == [(s_, s_ + 10_000_000) for s_ in range(1000, 1004)]


def test_the_lgen_passed_to_the_worker_is_seed_plus_offset_never_zero(tmp_path):
    s, store, workers = _lgen_scheduler(tmp_path)
    s.submit("baseline", _bspec("base", 3, lo=1000, lgen="seed"))
    _run(s)
    lgens = sorted(l for w in workers for l in w.lgens)
    assert lgens == [10_001_000, 10_001_001, 10_001_002] and 0 not in lgens


def test_replicate_rows_play_again_and_stay_out_of_reads(tmp_path):
    s, store, workers = _lgen_scheduler(tmp_path)
    s.submit("baseline", _bspec("base", 4, lo=1000))
    _run(s)
    before = (store.games("base"), store.count("base"))
    s.submit("baseline", _bspec("base", 4, lo=1000, replicate=1))
    _run(s)
    assert store.count("base", rep=1) == 4 and (store.games("base"), store.count("base")) == before


def test_a_worker_that_cannot_play_lgen_fails_the_job(tmp_path):
    s, store, workers = _lgen_scheduler(tmp_path, capable=False)
    job = s.submit("baseline", _bspec("old", 4, lo=1000, lgen="seed"))
    _run(s)
    assert store.job(job)["state"] == "failed"
    assert "cannot play lgen games" in store.job(job)["result"]["error"] and "old" in store.job(job)["result"]["error"]
    assert store.count("old") == 0


# seed-range policy at dispatch (plan 01-10)

def test_a_final_range_job_submitted_directly_fails_at_dispatch(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    job = s.submit("baseline", _bspec("base", 4, lo=1_000_000))
    _run(s)
    assert store.job(job)["state"] == "failed" and "final" in store.job(job)["result"]["error"]
    assert played == []


def test_a_natural_job_touching_the_tool_block_fails_at_dispatch(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    job = s.submit("baseline", _bspec("base", 4, lo=998))
    _run(s)
    assert store.job(job)["state"] == "failed" and "tool block" in store.job(job)["result"]["error"]
    assert played == []
