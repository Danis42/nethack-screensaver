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
    with sqlite3.connect(db) as con:  # an older database: bench schema without the tool_games table
        con.execute("DROP TABLE IF EXISTS tool_games")
        assert con.execute("SELECT name FROM sqlite_master WHERE name = 'tool_games'").fetchone() is None
    assert cc.verify_job(db, 1, need_started=True) is None
    assert "no game row" in cc.verify_job(db, 2, need_started=True)


def test_tool_games_row_counts_as_started(db, tmp_path):
    import sqlite3
    with sqlite3.connect(db) as con:
        con.execute("INSERT INTO tool_games (job_id, tool, sha, finished_at, json) VALUES (2, 'staged', 'x', 1.0, '{}')")
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


# Task 2: commit and query proofs, crash safety, edges, corpus

@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    git = ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    subprocess.run(git + ["init", "-q"], check=True)
    subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "one"], check=True)
    sha = subprocess.run(git + ["rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return path, sha


def test_full_commit_hash_in_the_repo_verifies(repo):
    path, sha = repo
    assert cc.verify_commit(path, sha) is None
    assert "not in this repo" in cc.verify_commit(path, "0" * 40)


def test_only_exactly_forty_hex_characters_count_as_a_commit(repo):
    _, sha = repo
    assert cc.find_proofs(f"commit {sha}").commits == [sha]
    assert cc.find_proofs(f"commit {sha[:39]}").commits == []
    assert cc.find_proofs(f"commit {sha}a").commits == []
    assert cc.verify_commit(repo[0], "--help" + "0" * 34) is not None


def test_result_claim_with_a_valid_commit_passes(db, repo, tmp_path):
    path, sha = repo
    payload = {"last_assistant_message": f"The fix reduced Mines deaths to 12%, commit {sha}.",
               "stop_hook_active": False}
    decision, _ = cc.run(payload, db, path, tmp_path / "a.jsonl")
    assert decision is None


def test_query_proof_must_return_the_cited_value(db):
    assert cc.verify_query(db, "SELECT COUNT(*) FROM games WHERE job_id = 1", "1") is None
    assert cc.verify_query(db, "SELECT COUNT(*) FROM games WHERE job_id = 1", "1.0") is None
    assert "returned 1" in cc.verify_query(db, "SELECT COUNT(*) FROM games WHERE job_id = 1", "2")


def test_query_proof_is_found_in_the_message(db, tmp_path):
    text = "Job 1 finished with 1 games [query: SELECT COUNT(*) FROM games WHERE job_id = 1 => 1]."
    decision, _ = cc.run({"last_assistant_message": text}, db, ROOT, tmp_path / "a.jsonl")
    assert decision is None


@pytest.mark.parametrize("sql", [
    "DELETE FROM games",
    "INSERT INTO jobs (kind, spec, state, created_at) VALUES ('x', '{}', 'q', 0)",
    "UPDATE jobs SET state = 'x'",
    "DROP TABLE games",
    "ATTACH DATABASE '/tmp/x.db' AS x",
    "PRAGMA journal_mode = DELETE",
    "SELECT 1; DELETE FROM games",
    "CREATE TABLE t (x)",
])
def test_writing_queries_are_refused_and_the_file_is_unchanged(db, sql):
    before = (db.stat().st_mtime_ns, db.stat().st_size, db.read_bytes())
    assert cc.verify_query(db, sql, "1") is not None
    assert (db.stat().st_mtime_ns, db.stat().st_size, db.read_bytes()) == before


def test_slow_query_is_aborted(db, monkeypatch):
    import sqlite3
    with sqlite3.connect(db) as con:
        con.executemany("INSERT INTO games (sha, job_id, finished_at, json) VALUES ('b', 1, 0, '{}')",
                        [()] * 3000)
    monkeypatch.setattr(cc, "QUERY_SECONDS", 0.01)
    reason = cc.verify_query(db, "SELECT COUNT(*) FROM games a, games b, games c", "1")
    assert reason is not None and "interrupt" in reason.lower()


def _call(stdin, tmp_path, extra_env=None):
    audit = tmp_path / "crash.jsonl"
    env = {**os.environ, "SCREENS_BENCH_DATA": str(tmp_path), "CLAIM_CHECK_AUDIT": str(audit), **(extra_env or {})}
    proc = subprocess.run([sys.executable, str(SCRIPT)], input=stdin, env=env, text=True, capture_output=True)
    return proc, [json.loads(line) for line in audit.read_text().splitlines()]


def test_invalid_json_on_stdin_passes_but_is_logged_as_crash(tmp_path):
    proc, records = _call("{not json", tmp_path)
    assert proc.returncode == 0 and proc.stdout == ""
    assert proc.stderr.startswith("check_claims crashed")
    assert records[-1]["decision"] == "crash" and records[-1]["error"]


def test_exception_inside_run_passes_but_is_logged_as_crash(tmp_path, monkeypatch):
    def boom(*args):
        raise RuntimeError("boom")
    monkeypatch.setattr(cc, "run", boom)
    monkeypatch.setenv("CLAIM_CHECK_AUDIT", str(tmp_path / "c.jsonl"))
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO('{"last_assistant_message": "x"}'))
    assert cc.main() == 0
    record = json.loads((tmp_path / "c.jsonl").read_text().splitlines()[-1])
    assert record["decision"] == "crash" and "boom" in record["error"] and "traceback" in record


@pytest.mark.parametrize("payload", [{}, {"last_assistant_message": ""}, {"last_assistant_message": None}])
def test_empty_or_missing_message_passes_and_is_logged(db, tmp_path, payload):
    decision, record = cc.run(payload, db, ROOT, tmp_path / "a.jsonl")
    assert decision is None and record["decision"] == "pass"


def test_several_failures_are_listed_in_message_order(db, tmp_path):
    text = "Job 3 finished: Mines rate 61%.\n\nThe baseline is running now.\n\nBaseline job 2 started."
    decision, _ = cc.run({"last_assistant_message": text}, db, ROOT, tmp_path / "a.jsonl")
    reason = decision["reason"]
    positions = [reason.index(s) for s in ("Job 3 finished", "The baseline is running", "Baseline job 2 started")]
    assert positions == sorted(positions)


def _corpus(name):
    return [line for line in (ROOT / "tests" / "data" / name).read_text().splitlines() if line.strip()]


def test_corpus_has_enough_sentences():
    assert len(_corpus("claims_positive.txt")) >= 20 and len(_corpus("claims_negative.txt")) >= 20


@pytest.mark.parametrize("line", _corpus("claims_positive.txt"))
def test_every_labelled_claim_is_detected_with_its_kind(line):
    kind, sentence = line.split("\t", 1)
    assert [c.kind for c in cc.find_claims(sentence)] == [kind]


@pytest.mark.parametrize("sentence", _corpus("claims_negative.txt"))
def test_no_labelled_non_claim_is_detected(sentence):
    assert cc.find_claims(sentence) == []
