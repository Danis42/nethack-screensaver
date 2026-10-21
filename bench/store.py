"""SQLite storage for the bench server: games per commit, jobs and reference games."""
import json
import sqlite3
import threading
import time
from pathlib import Path

SCHEMA_VERSION = 1
END_STATES = ("done", "stopped", "failed", "interrupted")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY, sha TEXT NOT NULL, job_id INTEGER,
    finished_at REAL NOT NULL, json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS games_by_sha ON games (sha, id);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, spec TEXT NOT NULL, state TEXT NOT NULL,
    created_at REAL NOT NULL, ended_at REAL, result TEXT);
CREATE TABLE IF NOT EXISTS reference_games (
    id INTEGER PRIMARY KEY, source TEXT NOT NULL, name TEXT NOT NULL,
    starttime INTEGER NOT NULL, role TEXT, turns INTEGER, json TEXT NOT NULL, dumplog TEXT,
    UNIQUE (source, name, starttime));
"""


def _job(row):
    return {"id": row["id"], "kind": row["kind"], "spec": json.loads(row["spec"]),
            "state": row["state"], "created_at": row["created_at"], "ended_at": row["ended_at"],
            "result": None if row["result"] is None else json.loads(row["result"])}


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(_SCHEMA)
            with self._db:
                row = self._db.execute("SELECT value FROM meta WHERE key = 'schema'").fetchone()
                if row is None:
                    self._db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
                elif int(row["value"]) != SCHEMA_VERSION:
                    raise RuntimeError(f"{path} has schema {row['value']}, this code expects {SCHEMA_VERSION}")

    def _one(self, sql, args=()):
        with self._lock:
            return self._db.execute(sql, args).fetchone()

    def _all(self, sql, args=()):
        with self._lock:
            return self._db.execute(sql, args).fetchall()

    def _write(self, sql, args=()):
        with self._lock, self._db:
            return self._db.execute(sql, args)

    # games

    def add_game(self, sha, job_id, result, finished_at=None):
        return self._write("INSERT INTO games (sha, job_id, finished_at, json) VALUES (?, ?, ?, ?)",
                           (sha, job_id, finished_at or time.time(), json.dumps(result))).lastrowid

    def count(self, sha):
        return self._one("SELECT COUNT(*) AS n FROM games WHERE sha = ?", (sha,))["n"]

    def seeds(self, sha):
        """Seeds of a commit's seeded games (older games have none)."""
        rows = self._all("SELECT DISTINCT json_extract(json, '$.seed') AS seed FROM games "
                         "WHERE sha = ? AND json_extract(json, '$.seed') IS NOT NULL", (sha,))
        return {r["seed"] for r in rows}

    def games_by_seed(self, sha, seeds):
        """{seed: game} for the wanted seeds this commit has played; the first game per seed."""
        wanted, out = set(seeds), {}
        rows = self._all("SELECT json_extract(json, '$.seed') AS seed, json FROM games "
                         "WHERE sha = ? AND json_extract(json, '$.seed') IS NOT NULL ORDER BY id", (sha,))
        for r in rows:
            if r["seed"] in wanted and r["seed"] not in out:
                out[r["seed"]] = json.loads(r["json"])
        return out

    def games(self, sha, limit=None):
        """Results of a commit, oldest first."""
        sql, args = "SELECT json FROM games WHERE sha = ? ORDER BY id", (sha,)
        if limit is not None:
            sql, args = sql + " LIMIT ?", args + (int(limit),)
        return [json.loads(r["json"]) for r in self._all(sql, args)]

    def shas(self):
        rows = self._all("SELECT sha, COUNT(*) AS n, MAX(finished_at) AS last FROM games "
                         "GROUP BY sha ORDER BY last DESC")
        return [{"sha": r["sha"], "games": r["n"], "last": r["last"]} for r in rows]

    # jobs

    def add_job(self, kind, spec):
        return self._write("INSERT INTO jobs (kind, spec, state, created_at) VALUES (?, ?, 'queued', ?)",
                           (kind, json.dumps(spec), time.time())).lastrowid

    def set_job(self, job_id, state, result=None):
        ended = time.time() if state in END_STATES else None
        self._write("UPDATE jobs SET state = ?, ended_at = ?, result = ? WHERE id = ?",
                    (state, ended, None if result is None else json.dumps(result), job_id))

    def job(self, job_id):
        row = self._one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return None if row is None else _job(row)

    def jobs(self, kind=None, limit=50):
        if kind is None:
            rows = self._all("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
        else:
            rows = self._all("SELECT * FROM jobs WHERE kind = ? ORDER BY id DESC LIMIT ?", (kind, limit))
        return [_job(r) for r in rows]

    def next_queued(self):
        row = self._one("SELECT * FROM jobs WHERE state = 'queued' ORDER BY id LIMIT 1")
        return None if row is None else _job(row)

    def interrupt_unfinished(self):
        """Jobs a stopped server left queued or running; returns how many were marked."""
        return self._write("UPDATE jobs SET state = 'interrupted', ended_at = ? "
                           "WHERE state IN ('queued', 'running')", (time.time(),)).rowcount

    # reference games (real ascensions)

    def add_reference(self, source, record):
        cur = self._write(
            "INSERT OR IGNORE INTO reference_games (source, name, starttime, role, turns, json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source, record["name"], int(record["starttime"]), record.get("role"),
             int(record.get("turns", 0)), json.dumps(record)))
        return cur.rowcount == 1

    def references(self):
        return [{"id": r["id"], "source": r["source"], "name": r["name"], "starttime": r["starttime"],
                 "role": r["role"], "turns": r["turns"], "record": json.loads(r["json"]),
                 "dumplog": r["dumplog"]}
                for r in self._all("SELECT * FROM reference_games ORDER BY id")]

    def set_dumplog(self, ref_id, text):
        self._write("UPDATE reference_games SET dumplog = ? WHERE id = ?", (text, ref_id))
