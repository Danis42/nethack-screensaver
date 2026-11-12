import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from bench.store import Store

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_claims.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_claims", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = _load()


@pytest.fixture
def db(tmp_path):
    """results.db with job 1 (one game), job 2 (no game), job 5 (no game); job 3 does not exist."""
    store = Store(tmp_path / "results.db")
    assert store.add_job("baseline", {}) == 1
    store.add_game("a" * 40, 1, {"max_depth": 3})
    assert store.add_job("baseline", {}) == 2
    assert store.add_job("experiment", {}) == 3
    assert store.add_job("experiment", {}) == 4
    assert store.add_job("baseline", {}) == 5
    store._db.execute("DELETE FROM jobs WHERE id IN (3, 4)")
    store._db.commit()
    store._db.close()
    return tmp_path / "results.db"


def _run(db, text, tmp_path, active=False):
    payload = {"session_id": "s", "last_assistant_message": text, "stop_hook_active": active}
    return cc.run(payload, db, ROOT, tmp_path / "audit.jsonl")


def test_start_claim_with_job_that_has_a_game_passes(db, tmp_path):
    decision, record = _run(db, "Baseline job 1 started.", tmp_path)
    assert decision is None
    assert record["decision"] == "pass"
    assert [c["kind"] for c in record["claims"]] == ["start"]


def test_start_claim_with_job_without_game_row_is_blocked(db, tmp_path):
    decision, record = _run(db, "Baseline job 2 started.", tmp_path)
    assert decision["decision"] == "block"
    assert "job 2" in decision["reason"] and "no game row" in decision["reason"]
    assert record["decision"] == "block"


def test_start_claim_without_proof_is_blocked(db, tmp_path):
    decision, _ = _run(db, "The baseline is running now.", tmp_path)
    assert decision["decision"] == "block"


def test_result_claim_naming_a_missing_job_is_blocked(db, tmp_path):
    decision, _ = _run(db, "Job 3 finished: Mines rate 61%.", tmp_path)
    assert decision["decision"] == "block"
    assert "job 3" in decision["reason"]


def test_queued_job_handoff_is_not_a_start_claim(db, tmp_path):
    decision, record = _run(db, "Job 5 queued, not started.", tmp_path)
    assert decision is None
    assert record["claims"] == []


def test_message_without_claims_passes(db, tmp_path):
    decision, record = _run(db, "I read the scheduler and will change _targets next.", tmp_path)
    assert decision is None and record["decision"] == "pass"


def test_database_without_tool_games_table_still_verifies_start_claims(db, tmp_path):
    import sqlite3
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT name FROM sqlite_master WHERE name = 'tool_games'").fetchone() is None
    assert cc.verify_job(db, 1, need_started=True) is None
    assert "no game row" in cc.verify_job(db, 2, need_started=True)


def test_tool_games_row_counts_as_started(db, tmp_path):
    import sqlite3
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE tool_games (id INTEGER PRIMARY KEY, job_id INTEGER)")
        con.execute("INSERT INTO tool_games (job_id) VALUES (2)")
    assert cc.verify_job(db, 2, need_started=True) is None


def test_database_is_opened_read_only(db, tmp_path):
    before = (db.stat().st_mtime_ns, db.stat().st_size)
    _run(db, "Baseline job 1 started. Job 2 started.", tmp_path)
    cc.verify_job(db, 1, need_started=True)
    assert (db.stat().st_mtime_ns, db.stat().st_size) == before


def test_stop_hook_active_prefixes_the_reason(db, tmp_path):
    decision, _ = _run(db, "The baseline is running now.", tmp_path, active=True)
    assert decision["reason"].startswith("Still unproven after a previous block:")


def test_every_decision_is_appended_to_the_audit_log(db, tmp_path):
    audit = tmp_path / "audit.jsonl"
    env = {**os.environ, "SCREENS_BENCH_DATA": str(db.parent), "CLAIM_CHECK_AUDIT": str(audit)}
    for text in ("Baseline job 1 started.", "The baseline is running now."):
        payload = json.dumps({"session_id": "s", "last_assistant_message": text, "stop_hook_active": False})
        subprocess.run([sys.executable, str(SCRIPT)], input=payload, env=env, text=True,
                       capture_output=True, check=True)
    records = [json.loads(line) for line in audit.read_text().splitlines()]
    assert [r["decision"] for r in records] == ["pass", "block"]
    assert all({"ts", "session_id", "decision", "stop_hook_active", "claims", "failures", "error"} <= r.keys()
               for r in records)


def test_end_to_end_through_stdin_and_stdout(db, tmp_path):
    env = {**os.environ, "SCREENS_BENCH_DATA": str(db.parent), "CLAIM_CHECK_AUDIT": str(tmp_path / "a.jsonl")}

    def call(text):
        payload = json.dumps({"session_id": "s", "last_assistant_message": text, "stop_hook_active": False})
        return subprocess.run([sys.executable, str(SCRIPT)], input=payload, env=env, text=True,
                              capture_output=True)

    proven = call("Baseline job 1 started.")
    assert proven.returncode == 0 and proven.stdout == ""
    unproven = call("Baseline job 2 started.")
    assert unproven.returncode == 0
    assert json.loads(unproven.stdout)["decision"] == "block"
