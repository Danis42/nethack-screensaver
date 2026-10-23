"""Read-only analysis scripts over the seeded bench store (scripts/seeded_report.py, replay_check.py)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import seeded_report  # noqa: E402
from bench.store import Store  # noqa: E402

CAND = "c" * 40
BASE = "b" * 40
OTHER = "d" * 40


def _verdict(state, checkpoint=1152, diff=0.0, lo=-0.04, hi=0.04):
    return {"state": state, "checkpoint": checkpoint, "diff": diff, "lo": lo, "hi": hi,
            "detectable": (hi - lo) / 2}


def add_experiment(store, candidate=CAND, baseline=BASE, metric="rung2", state="done",
                   verdict_state="no measurable difference", pairs=None, **verdict_kw):
    job = store.add_job("experiment", {"candidate": candidate, "baseline": baseline, "metric": metric})
    result = {"verdict": _verdict(verdict_state, **verdict_kw)}
    if pairs is not None:
        result["verdict"]["pairs"] = pairs
    store.set_job(job, state, result)
    return job


def run(capsys, tmp_path, *argv):
    code = seeded_report.main(["--data", str(tmp_path), *argv])
    return code, capsys.readouterr().out


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "results.db")


# verdict


def test_verdict_prints_one_json_line_per_matching_job(store, tmp_path, capsys):
    first = add_experiment(store, verdict_state="open", checkpoint=192)
    second = add_experiment(store, verdict_state="better", pairs=1152, diff=0.1, lo=0.05, hi=0.15)
    code, out = run(capsys, tmp_path, "verdict", CAND)
    assert code == 0
    lines = [json.loads(line) for line in out.strip().splitlines()]
    assert [line["job"] for line in lines] == [second, first]  # newest first
    assert set(lines[0]) == {"job", "candidate", "baseline", "metric", "state", "checkpoint", "diff",
                             "lo", "hi", "detectable", "pairs"}
    assert lines[0]["state"] == "better" and lines[0]["pairs"] == 1152
    assert lines[0]["candidate"] == CAND and lines[0]["baseline"] == BASE and lines[0]["metric"] == "rung2"
    assert lines[1]["pairs"] is None  # older jobs stored no pair count


def test_verdict_filters_by_baseline_and_metric(store, tmp_path, capsys):
    wanted = add_experiment(store, baseline=BASE, metric="rung2")
    add_experiment(store, baseline=OTHER, metric="rung2")
    add_experiment(store, baseline=BASE, metric="dlvl6")
    code, out = run(capsys, tmp_path, "verdict", CAND, "--baseline", BASE, "--metric", "rung2")
    assert code == 0
    assert [json.loads(line)["job"] for line in out.strip().splitlines()] == [wanted]


def test_verdict_only_counts_done_or_stopped_jobs(store, tmp_path, capsys):
    for state in ("queued", "running", "failed", "interrupted"):
        add_experiment(store, state=state)
    code, out = run(capsys, tmp_path, "verdict", CAND)
    assert code == 3 and "no finished experiment" in out
    stopped = add_experiment(store, state="stopped", verdict_state="worse")
    code, out = run(capsys, tmp_path, "verdict", CAND)
    assert code == 0 and json.loads(out.strip())["job"] == stopped


def test_verdict_without_matching_job_exits_3(store, tmp_path, capsys):
    add_experiment(store, candidate=OTHER)
    code, out = run(capsys, tmp_path, "verdict", CAND)
    assert code == 3 and out.strip() == "no finished experiment"


def test_verdict_expect_and_forbid_look_at_the_newest_job(store, tmp_path, capsys):
    add_experiment(store, verdict_state="better")
    add_experiment(store, verdict_state="no measurable difference")  # newest
    assert run(capsys, tmp_path, "verdict", CAND, "--expect", "no measurable difference")[0] == 0
    assert run(capsys, tmp_path, "verdict", CAND, "--expect", "better")[0] == 4
    assert run(capsys, tmp_path, "verdict", CAND, "--forbid", "no measurable difference")[0] == 4
    assert run(capsys, tmp_path, "verdict", CAND, "--forbid", "worse")[0] == 0
    assert run(capsys, tmp_path, "verdict", CAND, "--expect", "no measurable difference",
               "--forbid", "better")[0] == 0
    assert run(capsys, tmp_path, "verdict", CAND, "--expect", "no measurable difference",
               "--forbid", "no measurable difference")[0] == 4


def test_verdict_expect_without_a_job_is_still_3(store, tmp_path, capsys):
    assert run(capsys, tmp_path, "verdict", CAND, "--expect", "better")[0] == 3


def test_full_sha_refs_need_no_git(store, tmp_path, capsys):
    add_experiment(store)
    code, _ = run(capsys, tmp_path, "--repo", str(tmp_path / "not-a-repo"), "verdict", CAND,
                  "--baseline", BASE)
    assert code == 0


def test_short_refs_go_through_git(tmp_path, capsys, bench_repo):
    from bench import gitrefs
    sha, _ = gitrefs.resolve(bench_repo, "main")
    data = tmp_path / "data"
    store = Store(data / "results.db")
    add_experiment(store, candidate=sha)
    code, out = run(capsys, data, "--repo", str(bench_repo), "verdict", "main")
    assert code == 0 and json.loads(out.strip())["candidate"] == sha


def test_scripts_call_no_store_write_methods():
    root = Path(__file__).resolve().parent.parent / "scripts"
    for name in ("seeded_report.py", "replay_check.py"):
        path = root / name
        if not path.exists():
            continue
        code = [line for line in path.read_text().splitlines() if not line.lstrip().startswith("#")]
        for method in ("add_game", "set_job", "add_job", "add_reference", "set_dumplog"):
            assert not any(method in line for line in code), (name, method)
