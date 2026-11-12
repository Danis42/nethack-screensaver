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


SCHEMA_1 = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE games (id INTEGER PRIMARY KEY, sha TEXT NOT NULL, job_id INTEGER,
    finished_at REAL NOT NULL, json TEXT NOT NULL);
CREATE INDEX games_by_sha ON games (sha, id);
INSERT INTO meta VALUES ('schema', '1');
INSERT INTO games (sha, job_id, finished_at, json) VALUES ('aaa', NULL, 1.0, '{"seed": 1005, "max_depth": 3}');
INSERT INTO games (sha, job_id, finished_at, json) VALUES ('aaa', NULL, 2.0, '{"max_depth": 4}');
"""


def test_a_schema_1_database_is_migrated_with_the_seed_backfilled(tmp_path):
    with sqlite3.connect(tmp_path / "r.db") as con:
        con.executescript(SCHEMA_1)
    store = Store(tmp_path / "r.db")
    assert store._one("SELECT value FROM meta WHERE key = 'schema'")["value"] == "2"
    assert store.seeds("aaa") == {1005} and store.count("aaa") == 2
    assert store.played("aaa", 1000, 1010) == 1
    assert store._one("SELECT name FROM sqlite_master WHERE name = 'games_by_key'") is not None
    assert Store(tmp_path / "r.db").count("aaa") == 2  # reopening a migrated file works


def test_keyed_reads_use_the_window_env_and_replicate(tmp_path):
    store = Store(tmp_path / "r.db")
    store.add_game("a", None, {"seed": 1001}, env_id="e1")
    store.add_game("a", None, {"seed": 1002}, env_id="e2")
    store.add_game("a", None, {"seed": 1003}, env_id="e1", rep=1)
    assert store.seeds("a", 1000, 1010, env_id="e1") == {1001}
    assert store.played("a", 1000, 1002) == 1 and store.count("a") == 2 and store.count("a", rep=1) == 1


def test_environments_are_stored_by_id(tmp_path):
    from bench.provenance import env_id
    store = Store(tmp_path / "r.db")
    env = {"nle_commit": "c" * 40, "lock_sha256": "l", "python": "3.13", "numpy": "2", "numba": "0.6"}
    assert store.add_env(env) == env_id(env) and store.add_env(env) == env_id(env)
    assert store.env(env_id(env)) == env and store.env("nope") is None


def test_final_range_games_are_refused_unless_the_job_is_a_clean_attempt(tmp_path):
    import pytest
    store = Store(tmp_path / "r.db")
    with pytest.raises(ValueError, match="final"):
        store.add_game("a", None, {"seed": 1_000_000})
    base = store.add_job("baseline", {})
    with pytest.raises(ValueError, match="final"):
        store.add_game("a", base, {"seed": 1_000_000})
    clean = store.add_job("clean_attempt", {})
    store.add_game("a", clean, {"seed": 1_000_000})
    assert store.count("a") == 1


def test_job_kind(tmp_path):
    store = Store(tmp_path / "r.db")
    assert store.job_kind(store.add_job("baseline", {})) == "baseline" and store.job_kind(99) is None
