"""Refactor gate (CODE-01): pass on identical traces, fail with the first divergence, watchdog seeds skipped."""
import subprocess

import pytest

from bench import gate
from bench.frame_trace import TURN, Trace
from bench.store import Store

SEEDS = range(900, 905)


class TraceFake:
    """Writes a real trace file per game; `differs(sha, seed)` gives the step where this commit plays otherwise."""

    def __init__(self, sha, differs, watchdog, log):
        self.sha, self.differs, self.watchdog, self.log = sha, differs, watchdog, log
        self.pending, self.closed = [], False

    def trace(self, seed, path):
        self.log.append((self.sha, seed))
        t = Trace(path)
        change = self.differs(self.sha, seed)
        for step in range(20):
            chars = bytearray(b" " * 80)
            chars[step % 80] = ord("x") if step == change else ord("@")
            t.frame({"tty_chars": bytes(chars), "blstats": [0] * TURN + [step // 2]})
        end = "watchdog" if (self.sha, seed) in self.watchdog else "DEATH: killed by a newt"
        self.pending.append({"seed": seed, "end_reason": end, "trace_digest": t.close(), "trace_steps": t.steps})

    def results(self):
        out, self.pending = self.pending, []
        return out

    def alive(self):
        return True

    def close(self):
        self.closed = True


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    run = lambda *a: subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)
    run("init", "-q")
    run("config", "user.email", "t@t")
    run("config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    run("add", ".")
    run("commit", "-qm", "base", "--no-verify")
    run("branch", "base")
    (r / "a.py").write_text("x = 2\n")
    run("commit", "-qam", "cand", "--no-verify")
    return r


def _run(tmp_path, repo, differs=lambda sha, seed: None, watchdog=()):
    store, log = Store(tmp_path / "results.db"), []
    spawn = lambda sha: TraceFake(sha, differs, watchdog, log)
    job_id, verdict = gate.run_gate(store, repo, "HEAD", "base", spawn, tmp_path / "traces", workers=3,
                                    seeds=SEEDS, poll=0)
    return store, job_id, verdict, log


def test_identical_commits_pass(tmp_path, repo):
    store, job_id, verdict, _ = _run(tmp_path, repo)
    assert verdict["verdict"] == "pass" and verdict["compared"] == 5 and verdict["first_divergence"] is None
    job = store.job(job_id)
    assert job["kind"] == "gate" and job["state"] == "done" and job["result"]["verdict"] == "pass"
    tree = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], capture_output=True, text=True).stdout
    assert job["spec"]["candidate_tree"] == tree.strip()
    assert len(store.tool_games(job_id)) == 10


def test_changed_commit_fails_at_first_divergent_seed_and_step(tmp_path, repo):
    base = subprocess.run(["git", "-C", str(repo), "rev-parse", "base"], capture_output=True, text=True).stdout.strip()
    differs = lambda sha, seed: 7 if sha != base and seed >= 902 else None
    _, _, verdict, _ = _run(tmp_path, repo, differs)
    assert verdict["verdict"] == "fail" and verdict["differing_seeds"] == [902, 903, 904]
    assert verdict["first_divergence"] == {"seed": 902, "step": 7, "turn_a": 3, "turn_b": 3}


def test_watchdog_seeds_are_skipped_and_too_many_fail(tmp_path, repo):
    base = subprocess.run(["git", "-C", str(repo), "rev-parse", "base"], capture_output=True, text=True).stdout.strip()
    _, _, verdict, _ = _run(tmp_path, repo, watchdog={(base, 900)})
    assert verdict["verdict"] == "pass" and verdict["skipped_seeds"] == [900] and verdict["compared"] == 4
    (tmp_path / "second").mkdir()  # fresh trace cache: the first run's baseline traces would be reused
    _, _, verdict, _ = _run(tmp_path / "second", repo, watchdog={(base, 900), (base, 901), (base, 902)})
    assert verdict["verdict"] == "fail" and verdict["differing_seeds"] == []


def test_baseline_traces_are_reused(tmp_path, repo):
    _run(tmp_path, repo)
    _, _, verdict, log = _run(tmp_path, repo)
    base = subprocess.run(["git", "-C", str(repo), "rev-parse", "base"], capture_output=True, text=True).stdout.strip()
    assert verdict["baseline_reused"] == 5 and all(sha != base for sha, _ in log[-5:]) and len(log) == 5


def test_same_commit_is_refused(tmp_path, repo):
    with pytest.raises(ValueError, match="same commit"):
        gate.run_gate(Store(tmp_path / "r.db"), repo, "HEAD", "HEAD", None, tmp_path / "t", seeds=SEEDS)
