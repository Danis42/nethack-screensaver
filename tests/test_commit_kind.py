"""Commit labels (CODE-02, D-14): the rule shared by the git hooks and the log check."""
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("commit_kind", REPO / "githooks" / "commit_kind.py")
commit_kind = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commit_kind)
check = commit_kind.check

CODE = ["autoascend/agent.py"]
DOCS = [".planning/STATE.md", "README.md"]
TOOLING = ["bench/scheduler.py", "tests/test_x.py"]


def test_missing_label_is_rejected():
    errors = check("fix things\n", CODE)
    assert errors and "Kind:" in errors[0]


def test_unknown_label_is_rejected():
    assert check("x\n\nKind: cleanup\n", TOOLING)


def test_docs_label_only_for_documentation():
    assert check("notes\n\nKind: docs\n", DOCS) == []
    assert check("notes\n\nKind: docs\n", DOCS + TOOLING)


def test_tooling_refactor_needs_no_gate():
    assert check("bench change\n\nKind: refactor\n", TOOLING) == []


def test_bot_refactor_needs_gate_job():
    assert any("Gate:" in e for e in check("move code\n\nKind: refactor\n", CODE))
    assert check("move code\n\nKind: refactor\nGate: job 12\n", CODE) == []


def test_bot_behavior_needs_stage_metric_experiment():
    errors = check("new rule\n\nKind: behavior\n", CODE)
    assert {"Stage:", "Metric:", "Experiment:"} <= {e.split()[0] for e in errors}
    ok = "new rule\n\nKind: behavior\nStage: dlvl10\nMetric: dlvl10\nExperiment: pending\n"
    assert check(ok, CODE) == []
    assert check(ok.replace("pending", "job 31"), CODE) == []
    assert check(ok.replace("pending", "soon"), CODE)


def test_unknown_metric_is_rejected():
    msg = "new rule\n\nKind: behavior\nStage: dlvl10\nMetric: happiness\nExperiment: pending\n"
    assert any("Metric" in e for e in check(msg, CODE))


def test_fixup_is_exempt():
    assert check("fixup! something\n", CODE) == []


def test_docs_label_is_added_for_documentation_commits():
    assert commit_kind.with_docs_label("notes\n", DOCS).rstrip().endswith("Kind: docs")
    assert commit_kind.with_docs_label("notes\n", CODE) == "notes\n"
    labelled = "notes\n\nKind: refactor\n"
    assert commit_kind.with_docs_label(labelled, DOCS) == labelled


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def test_log_since_phase2_start_is_labelled():
    start_file = REPO / "githooks" / "PHASE2_START"
    if not start_file.exists() or not (REPO / ".git").exists():
        pytest.skip("no git checkout or no Phase 2 start marker")
    start = start_file.read_text().strip()
    try:
        commits = _git("rev-list", "--no-merges", f"{start}^..HEAD").split()
    except subprocess.CalledProcessError:
        pytest.skip(f"start commit {start} not in this history")
    bad = {}
    for sha in commits:
        message = _git("log", "-1", "--format=%B", sha)
        paths = _git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha).split()
        errors = check(message, paths) + _gate_errors(sha, message, paths)
        if errors:
            bad[sha[:10]] = errors
    assert not bad, bad


def _gate_errors(sha, message, paths):
    """A bot-code refactor's 'Gate: job N' must be a passing gate run on a commit with the same tree."""
    gate = re.search(r"^Gate: job (\d+)$", message, re.M)
    if commit_kind.trailers(message).get("Kind") != "refactor" or not gate or \
            not any(p.startswith(commit_kind.BOT_CODE) for p in paths):
        return []
    db = os.path.join(os.path.expanduser(os.environ.get("SCREENS_BENCH_DATA", "~/.local/share/screens-bench")),
                      "results.db")
    if not os.path.exists(db):
        return []  # no bench database on this machine: the label format was checked above
    row = sqlite3.connect(db).execute("SELECT kind, spec, result FROM jobs WHERE id = ?", (int(gate[1]),)).fetchone()
    if row is None or row[0] != "gate":
        return [f"Gate: job {gate[1]} is not a gate job"]
    spec, result = json.loads(row[1]), json.loads(row[2] or "{}")
    tree = _git("rev-parse", f"{sha}^{{tree}}").strip()
    if result.get("verdict") != "pass" or spec.get("candidate_tree") != tree:
        return [f"Gate: job {gate[1]} did not pass on this tree ({result.get('verdict')})"]
    return []
