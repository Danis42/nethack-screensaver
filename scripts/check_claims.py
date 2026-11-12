"""Stop-hook claim checker: block replies that claim progress without proof (MEAS-09).

Claude Code runs this script as a Stop hook on the final message of every turn
(`.claude/settings.json`). It reads the hook payload as JSON on stdin, finds progress
claims in `last_assistant_message`, checks the proof cited next to them against the live
bench database and git, and prints `{"decision": "block", "reason": ...}` when a claim
lacks valid proof. Commit messages and planning documents are not checked.

What counts as a progress claim (deterministic regular expressions, no LLM):
- a start claim: a sentence saying a job, run, baseline, experiment, A/A, bench or pilot
  started, launched, was kicked off or is running. "Queued" is deliberately not a start
  word, so a handoff can say "job N queued, not started".
- a result claim: a sentence with a result verb (finished, completed, passed, improved,
  reduced, raised, rose, dropped, reached, fixed, significant) and a bench noun or number
  (job, run, baseline, experiment, A/A, games, seeds, funnel, rate, a percentage, an n/N
  fraction, Wilson, McNemar).
Future and conditional sentences ("will start", "would", "should", "next") and questions
are not claims. Text in fenced code blocks and inline code spans is not searched for
claims.

What counts as proof, cited in the same paragraph as the claim:
- `job 123` or `job #123`: the job must exist in results.db; for a start claim it must
  also have at least one row in `games` (or `tool_games`). A job counts as started only
  once its first game row exists.
- a full 40-hex commit hash that resolves to a commit in this repository (abbreviated
  hashes do not count).
- `[query: SELECT ... => value]`: the query is re-run read-only and its first cell must
  equal the value.
A claim passes when its paragraph cites at least one proof and every proof there verifies.

Limits (reported to the owner):
- Only the final message of a turn is seen; text written before tool calls is not.
- After eight blocks in a row Claude Code overrides the next block and ends the turn
  (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises the cap). The audit log still records it.
- If this script crashes, the reply passes (D-18): the crash goes to stderr and to the
  audit log. A failed claim is still blocked.
So this is a tripwire for the common failure, not proof that no unproven claim was made.
Every decision (pass, block, crash) is appended to `.claude/claim-checks.jsonl`.

Standard library only, so it runs under system python3 while `.venv` is being rebuilt.
Environment: SCREENS_BENCH_DATA (database directory), CLAUDE_PROJECT_DIR (repository),
CLAIM_CHECK_AUDIT (audit log path, used by tests).
"""
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import traceback
from collections import namedtuple
from pathlib import Path

QUERY_SECONDS = 2.0

_NOT = r"(?:\bnot|n't|\bnever|\bno longer)\s+(?:yet\s+)?(?:been\s+)?(?:be\s+)?"
START_WORDS = r"started|launched|kicked off|is running|are running|running now|now running"
START_RE = re.compile(rf"\b(?:{START_WORDS})\b", re.I)
START_NOUN_RE = re.compile(r"\b(?:jobs?|runs?|baselines?|experiments?|A/A|bench|pilots?)\b", re.I)
RESULT_VERB_RE = re.compile(r"\b(?:finished|completed|passes|passed|improved|reduced|raised|rose|"
                            r"dropped|reached|fixed|significant(?:ly)?)\b", re.I)
RESULT_NOUN_RE = re.compile(
    r"\b(?:jobs?|runs?|baselines?|experiments?|A/A|games|seeds|funnel|rates?|Wilson|McNemar)\b"
    r"|\d(?:\.\d+)?\s?%"
    r"|\b\d+\s*/\s*\d+\b(?!\s*(?:tasks?|plans?|tests?|steps?|files?|criteria|checks?|waves?)\b)",
    re.I)
NEGATED_RE = re.compile(_NOT + r"(?:" + START_WORDS + r"|running|finished|completed|passed|"
                        r"improved|reduced|raised|reached|fixed|significant)\b", re.I)
FUTURE_RE = re.compile(r"\b(?:will|would|should|could|might|may|can|going to|plan to|about to|"
                       r"next|if|unless|once|until|let me|I'll|we'll)\b", re.I)
JOB_RE = re.compile(r"\bjob\s*#?(\d+)\b", re.I)
COMMIT_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")
QUERY_RE = re.compile(r"\[query:\s*(.+?)\s*=>\s*(.+?)\]", re.S)

_FENCE_RE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")

Claim = namedtuple("Claim", "kind text")
Proofs = namedtuple("Proofs", "jobs commits queries")


def split_paragraphs(text):
    """Split on blank lines after dropping fenced code blocks."""
    text = _FENCE_RE.sub("", text or "")
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _sentences(paragraph):
    return [s.strip() for s in _SENTENCE_RE.split(paragraph) if s.strip()]


def find_claims(paragraph):
    """Progress claims in one paragraph, in order; inline code is not searched."""
    claims = []
    for sentence in _sentences(_INLINE_CODE_RE.sub("", paragraph)):
        if sentence.endswith("?") or FUTURE_RE.search(sentence):
            continue
        plain = NEGATED_RE.sub("", sentence)
        if START_RE.search(plain) and START_NOUN_RE.search(plain):
            claims.append(Claim("start", sentence))
        elif RESULT_VERB_RE.search(plain) and RESULT_NOUN_RE.search(plain):
            claims.append(Claim("result", sentence))
    return claims


def find_proofs(paragraph):
    """Proofs cited in one paragraph; backticks around a proof are allowed."""
    text = paragraph.replace("`", "")
    jobs = list(dict.fromkeys(int(n) for n in JOB_RE.findall(text)))
    commits = list(dict.fromkeys(COMMIT_RE.findall(text)))
    queries = [(sql, expected) for sql, expected in QUERY_RE.findall(text)]
    return Proofs(jobs, commits, queries)


def _connect_ro(db_path):
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)


def verify_job(db_path, job_id, need_started):
    """None when the job exists (and, for a start claim, has a game row); else the reason."""
    try:
        con = _connect_ro(db_path)
    except sqlite3.Error as e:  # missing or unreadable database: the proof cannot be checked
        return f"job {job_id}: cannot open {db_path} read-only ({e})"
    try:
        if con.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone() is None:
            return f"job {job_id} does not exist in results.db"
        if not need_started:
            return None
        tables = ["games"]
        if con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tool_games'").fetchone():
            tables.append("tool_games")
        for table in tables:
            if con.execute(f"SELECT EXISTS (SELECT 1 FROM {table} WHERE job_id = ?)", (job_id,)).fetchone()[0]:
                return None
        return f"job {job_id} has no game row yet, so it has not started"
    except sqlite3.Error as e:  # schema mismatch or locked file: a failed proof, not a crash
        return f"job {job_id}: query failed ({e})"
    finally:
        con.close()


def verify_commit(repo, sha):
    """None when sha is a full 40-hex hash of a commit in repo; else the reason."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        return f"{sha!r} is not a full 40-hex commit hash"
    try:
        proc = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                              capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:  # git missing or hung: the proof cannot be checked
        return f"commit {sha[:10]}: git failed ({e})"
    return None if proc.returncode == 0 else f"commit {sha[:10]} not in this repo"


_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


def _same(cell, expected):
    try:
        return math.isclose(float(cell), float(expected), rel_tol=1e-9)
    except (TypeError, ValueError):  # not numbers: compare as text
        return str(cell).strip() == expected.strip()


def verify_query(db_path, sql, expected):
    """Re-run one read-only SELECT; None when its first cell equals expected, else the reason."""
    body = sql.strip().rstrip(";").strip()
    if ";" in body:
        return "only one statement is allowed"
    try:
        con = _connect_ro(db_path)
    except sqlite3.Error as e:  # missing or unreadable database: the proof cannot be checked
        return f"cannot open {db_path} read-only ({e})"
    try:
        con.execute("PRAGMA query_only = ON")
        con.set_authorizer(lambda action, *args: sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY)
        deadline = time.monotonic() + QUERY_SECONDS
        con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 1000)
        row = con.execute(body).fetchone()
    except sqlite3.Error as e:  # refused, failing or interrupted query: a failed proof, not a crash
        return f"query refused or failed ({e})"
    finally:
        con.close()
    if row is None:
        return "query returned no rows"
    return None if _same(row[0], expected) else f"query returned {row[0]!r}, not {expected.strip()!r}"


def _check_paragraph(paragraph, claims, db_path, repo):
    proofs = find_proofs(paragraph)
    need_started = any(c.kind == "start" for c in claims)
    reasons = []
    for job in proofs.jobs:
        reason = verify_job(db_path, job, need_started)
        if reason:
            reasons.append(reason)
    for sha in proofs.commits:
        reason = verify_commit(repo, sha)
        if reason:
            reasons.append(reason)
    for sql, expected in proofs.queries:
        reason = verify_query(db_path, sql, expected)
        if reason:
            reasons.append(f"[query: {sql} => {expected}]: {reason}")
    failures = []
    for claim in claims:
        own = list(reasons)
        if not (proofs.jobs or proofs.commits or proofs.queries):
            own.append("no proof cited")
        elif claim.kind == "start" and not proofs.jobs:
            own.append("a start claim needs a cited job with a game row")
        if own:
            failures.append(f'"{claim.text}": ' + "; ".join(own))
    return failures


def run(payload, db_path, repo, audit_path):
    """Return (decision dict or None, audit record) for one Stop-hook payload."""
    text = payload.get("last_assistant_message") or ""
    active = bool(payload.get("stop_hook_active"))
    claims, failures = [], []
    for paragraph in split_paragraphs(text):
        found = find_claims(paragraph)
        if found:
            claims.extend(found)
            failures.extend(_check_paragraph(paragraph, found, db_path, repo))
    record = {"ts": time.time(), "session_id": payload.get("session_id"),
              "decision": "block" if failures else "pass", "stop_hook_active": active,
              "claims": [c._asdict() for c in claims], "failures": failures, "error": None}
    if not failures:
        return None, record
    lines = [f"{i}. {f}" for i, f in enumerate(failures, 1)]
    reason = ("Unproven progress claim(s):\n" + "\n".join(lines) +
              "\nCite job N (with a game row for \"started\"), a full 40-hex commit or a "
              "[query: SELECT ... => value], or drop the claim.")
    if active:
        reason = "Still unproven after a previous block: " + reason
    return {"decision": "block", "reason": reason}, record


def _paths():
    repo = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent)
    data = os.environ.get("SCREENS_BENCH_DATA") or Path.home() / ".local/share/screens-bench"
    audit = os.environ.get("CLAIM_CHECK_AUDIT") or repo / ".claude" / "claim-checks.jsonl"
    return Path(data) / "results.db", repo, Path(audit)


def _append(audit_path, record):
    try:
        with open(audit_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as e:  # an unwritable audit log must not hide the decision itself
        print(f"check_claims: cannot write audit log {audit_path}: {e}", file=sys.stderr)


def main():
    db_path, repo, audit_path = _paths()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        decision, record = run(payload, db_path, repo, audit_path)
    except Exception as e:  # D-18: a crash of the checker is not a failed claim
        print(f"check_claims crashed: {e!r}; this reply was NOT checked; see {audit_path}", file=sys.stderr)
        _append(audit_path, {"ts": time.time(), "session_id": None, "decision": "crash",
                             "stop_hook_active": None, "claims": [], "failures": [],
                             "error": repr(e), "traceback": traceback.format_exc()})
        return 0
    _append(audit_path, record)
    if decision:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
