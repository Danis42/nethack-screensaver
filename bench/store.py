"""SQLite storage for the bench server: games per commit, jobs and reference games."""
import json
import sqlite3
import threading
import time
from pathlib import Path

from .seeds import FINAL_LO

SCHEMA_VERSION = 2
END_STATES = ("done", "stopped", "failed", "interrupted")

# Schema 2: games carry the game key as indexed columns (seed, lgen, env_id, rep) and envs holds the
# full environment fingerprint of every env_id. A game's key is (sha, seed, lgen mode, env_id, rep):
# lgen NULL means lgen off; rep 1 marks an A/A replicate row, which summaries never read.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY, sha TEXT NOT NULL, job_id INTEGER,
    finished_at REAL NOT NULL, json TEXT NOT NULL,
    seed INTEGER, lgen INTEGER, env_id TEXT, rep INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS games_by_sha ON games (sha, id);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, spec TEXT NOT NULL, state TEXT NOT NULL,
    created_at REAL NOT NULL, ended_at REAL, result TEXT);
CREATE TABLE IF NOT EXISTS reference_games (
    id INTEGER PRIMARY KEY, source TEXT NOT NULL, name TEXT NOT NULL,
    starttime INTEGER NOT NULL, role TEXT, turns INTEGER, json TEXT NOT NULL, dumplog TEXT,
    UNIQUE (source, name, starttime));
CREATE TABLE IF NOT EXISTS envs (id TEXT PRIMARY KEY, json TEXT NOT NULL);
"""
_KEY_INDEX = "CREATE INDEX IF NOT EXISTS games_by_key ON games (sha, seed, rep)"
_V2_COLUMNS = (("seed", "INTEGER"), ("lgen", "INTEGER"), ("env_id", "TEXT"), ("rep", "INTEGER NOT NULL DEFAULT 0"))


def _job(row):
    return {"id": row["id"], "kind": row["kind"], "spec": json.loads(row["spec"]),
            "state": row["state"], "created_at": row["created_at"], "ended_at": row["ended_at"],
            "result": None if row["result"] is None else json.loads(row["result"])}


def _key(lgen_mode=None, env_id=None, rep=0):
    """SQL conditions and arguments for one game key; None means no filter for lgen_mode and env_id."""
    clauses, args = ["rep = ?"], [int(rep)]
    if lgen_mode == "off":
        clauses.append("lgen IS NULL")
    elif lgen_mode == "seed":
        clauses.append("lgen IS NOT NULL")
    elif lgen_mode is not None:
        raise ValueError(f"lgen mode must be off or seed, got {lgen_mode!r}")
    if env_id is not None:
        clauses.append("env_id = ?")
        args.append(env_id)
    return clauses, args


def _where(sha, lo=None, hi=None, seeded=False, **key):
    clauses, args = _key(**key)
    clauses, args = ["sha = ?"] + clauses, [sha] + args
    if seeded or lo is not None or hi is not None:
        clauses.append("seed IS NOT NULL")
    if lo is not None:
        clauses.append("seed >= ?")
        args.append(int(lo))
    if hi is not None:
        clauses.append("seed < ?")
        args.append(int(hi))
    return " AND ".join(clauses), args


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(_SCHEMA)  # an existing schema-1 games table keeps its old columns
            with self._db:
                row = self._db.execute("SELECT value FROM meta WHERE key = 'schema'").fetchone()
                if row is None:
                    self._db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
                elif int(row["value"]) == 1:
                    self._migrate_v1()
                elif int(row["value"]) != SCHEMA_VERSION:
                    raise RuntimeError(f"{path} has schema {row['value']}, this code expects {SCHEMA_VERSION}")
                self._db.execute(_KEY_INDEX)  # after the migration: the columns must exist

    def _migrate_v1(self):
        """Schema 1 -> 2: add the key columns, backfill seed and lgen from the game JSON."""
        have = {r["name"] for r in self._db.execute("PRAGMA table_info(games)")}
        for name, decl in _V2_COLUMNS:
            if name not in have:
                self._db.execute(f"ALTER TABLE games ADD COLUMN {name} {decl}")
        self._db.execute("UPDATE games SET seed = json_extract(json, '$.seed'), lgen = json_extract(json, '$.lgen')")
        self._db.execute("UPDATE meta SET value = ? WHERE key = 'schema'", (str(SCHEMA_VERSION),))

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

    def job_kind(self, job_id):
        row = None if job_id is None else self._one("SELECT kind FROM jobs WHERE id = ?", (job_id,))
        return None if row is None else row["kind"]

    def add_game(self, sha, job_id, result, finished_at=None, env_id=None, rep=0):
        seed, lgen = result.get("seed"), result.get("lgen")
        if seed is not None and int(seed) >= FINAL_LO and self.job_kind(job_id) != "clean_attempt":
            raise ValueError(f"seed {seed} is in the final range (>= {FINAL_LO:,}); only clean_attempt jobs store it (D-07)")
        return self._write(
            "INSERT INTO games (sha, job_id, finished_at, json, seed, lgen, env_id, rep) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sha, job_id, finished_at or time.time(), json.dumps(result),
             None if seed is None else int(seed), None if lgen is None else int(lgen), env_id, int(rep))).lastrowid

    def count(self, sha, rep=0):
        return self._one("SELECT COUNT(*) AS n FROM games WHERE sha = ? AND rep = ?", (sha, int(rep)))["n"]

    def seeds(self, sha, lo=None, hi=None, lgen_mode=None, env_id=None, rep=0):
        """Seeds this commit has played under one game key (older unseeded games have none)."""
        where, args = _where(sha, lo, hi, seeded=True, lgen_mode=lgen_mode, env_id=env_id, rep=rep)
        return {r["seed"] for r in self._all(f"SELECT DISTINCT seed FROM games WHERE {where}", args)}

    def played(self, sha, lo, hi, lgen_mode=None, env_id=None, rep=0):
        """How many distinct seeds of [lo, hi) this commit has played under one game key."""
        where, args = _where(sha, lo, hi, lgen_mode=lgen_mode, env_id=env_id, rep=rep)
        return self._one(f"SELECT COUNT(DISTINCT seed) AS n FROM games WHERE {where}", args)["n"]

    def games_by_seed(self, sha, seeds, lgen_mode=None, env_id=None, rep=0):
        """{seed: game} for the wanted seeds this commit has played; the first game per seed."""
        wanted, out = set(seeds), {}
        where, args = _where(sha, seeded=True, lgen_mode=lgen_mode, env_id=env_id, rep=rep)
        for r in self._all(f"SELECT seed, json FROM games WHERE {where} ORDER BY id", args):
            if r["seed"] in wanted and r["seed"] not in out:
                out[r["seed"]] = json.loads(r["json"])
        return out

    def games(self, sha, limit=None, rep=0, lgen_mode=None, env_id=None, lo=None, hi=None):
        """Results of a commit, oldest first (rep 0 rows unless asked otherwise)."""
        where, args = _where(sha, lo, hi, lgen_mode=lgen_mode, env_id=env_id, rep=rep)
        sql = f"SELECT json FROM games WHERE {where} ORDER BY id"
        if limit is not None:
            sql, args = sql + " LIMIT ?", args + [int(limit)]
        return [json.loads(r["json"]) for r in self._all(sql, args)]

    def shas(self):
        rows = self._all("SELECT sha, COUNT(*) AS n, MAX(finished_at) AS last FROM games WHERE rep = 0 "
                         "GROUP BY sha ORDER BY last DESC")
        return [{"sha": r["sha"], "games": r["n"], "last": r["last"]} for r in rows]

    # environments

    def add_env(self, env):
        """Store an environment fingerprint; returns its env_id."""
        from .provenance import env_id as _env_id
        eid = _env_id(env)
        self._write("INSERT OR IGNORE INTO envs (id, json) VALUES (?, ?)", (eid, json.dumps(env, sort_keys=True)))
        return eid

    def env(self, env_id):
        row = self._one("SELECT json FROM envs WHERE id = ?", (env_id,))
        return None if row is None else json.loads(row["json"])

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

    def resume(self, job_id):
        """Queue an interrupted job again under the same id (D-08); True when one row changed."""
        return self._write("UPDATE jobs SET state = 'queued', ended_at = NULL WHERE id = ? AND state = 'interrupted'",
                           (int(job_id),)).rowcount == 1

    def interrupted(self):
        """Ids of interrupted jobs, oldest first."""
        return [r["id"] for r in self._all("SELECT id FROM jobs WHERE state = 'interrupted' ORDER BY id")]

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
