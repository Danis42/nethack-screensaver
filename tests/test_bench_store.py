import sqlite3

import pytest

from bench.store import Store


def _game(depth=3, **extra):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", **extra}


def test_games_are_stored_per_commit_oldest_first(tmp_path):
    store = Store(tmp_path / "r.db")
    for depth in (1, 2, 3):
        store.add_game("aaa", None, _game(depth))
    store.add_game("bbb", 7, _game(9))
    assert store.count("aaa") == 3 and store.count("bbb") == 1 and store.count("ccc") == 0
    assert [g["max_depth"] for g in store.games("aaa")] == [1, 2, 3]
    assert [g["max_depth"] for g in store.games("aaa", limit=2)] == [1, 2]
    assert [s["sha"] for s in store.shas()] == ["bbb", "aaa"]


def test_store_survives_reopening(tmp_path):
    Store(tmp_path / "r.db").add_game("aaa", None, _game())
    assert Store(tmp_path / "r.db").count("aaa") == 1


def test_job_lifecycle(tmp_path):
    store = Store(tmp_path / "r.db")
    first = store.add_job("baseline", {"sha": "aaa", "games": 5})
    second = store.add_job("experiment", {"candidate": "bbb"})
    assert store.next_queued()["id"] == first
    store.set_job(first, "running", {"games": 0})
    assert store.next_queued()["id"] == second
    store.set_job(first, "done", {"games": 5})
    job = store.job(first)
    assert job["state"] == "done" and job["result"] == {"games": 5} and job["ended_at"] is not None
    assert job["spec"] == {"sha": "aaa", "games": 5}
    assert [j["id"] for j in store.jobs()] == [second, first]
    assert [j["id"] for j in store.jobs("experiment")] == [second]
    assert store.job(999) is None


def test_unfinished_jobs_become_interrupted_and_keep_their_games(tmp_path):
    store = Store(tmp_path / "r.db")
    running = store.add_job("baseline", {"sha": "aaa", "games": 5})
    store.set_job(running, "running", {})
    queued = store.add_job("baseline", {"sha": "bbb", "games": 5})
    store.add_game("aaa", running, _game())
    assert store.interrupt_unfinished() == 2
    assert store.job(running)["state"] == "interrupted"
    assert store.job(queued)["state"] == "interrupted"
    assert store.next_queued() is None
    assert store.count("aaa") == 1


def test_reference_games_are_unique_per_source_name_and_start(tmp_path):
    store = Store(tmp_path / "r.db")
    record = {"name": "player", "starttime": "1777773884", "role": "Bar", "turns": "44867"}
    assert store.add_reference("hardfought", record) is True
    assert store.add_reference("hardfought", record) is False
    assert store.add_reference("other", record) is True
    refs = store.references()
    assert len(refs) == 2 and refs[0]["turns"] == 44867 and refs[0]["dumplog"] is None
    store.set_dumplog(refs[0]["id"], "dump text")
    assert store.references()[0]["dumplog"] == "dump text"


def test_schema_version_mismatch_is_refused(tmp_path):
    Store(tmp_path / "r.db")
    db = sqlite3.connect(tmp_path / "r.db")
    db.execute("UPDATE meta SET value = '99' WHERE key = 'schema'")
    db.commit()
    db.close()
    with pytest.raises(RuntimeError, match="schema"):
        Store(tmp_path / "r.db")


def test_seeded_games_are_found_by_seed(tmp_path):
    store = Store(tmp_path / "r.db")
    store.add_game("aaa", None, _game(1))  # unseeded, from an older commit
    store.add_game("aaa", None, _game(2, seed=0))
    store.add_game("aaa", None, _game(3, seed=5))
    store.add_game("aaa", None, _game(4, seed=5))  # a replay: the first one counts
    store.add_game("bbb", None, _game(9, seed=0))
    assert store.seeds("aaa") == {0, 5} and store.seeds("ccc") == set()
    found = store.games_by_seed("aaa", range(6))
    assert {k: g["max_depth"] for k, g in found.items()} == {0: 2, 5: 3}
