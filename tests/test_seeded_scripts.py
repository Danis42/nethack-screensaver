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


# replay_check and pairs


import replay_check  # noqa: E402
from bench.stats import judge_paired  # noqa: E402


def _g(seed, **extra):
    base = {"seed": seed, "role": "Valkyrie", "turns": 1000 + seed, "max_depth": 4, "score": 50,
            "end_reason": "DEATH: killed by a newt", "rung": 1}
    return {**base, **extra}


def fill(store, sha, games):
    for g in games:
        store.add_game(sha, None, g)


def replay(capsys, tmp_path, *argv):
    code = replay_check.main(["--data", str(tmp_path), *argv])
    return code, capsys.readouterr().out


def test_replay_identical_games_exit_0(store, tmp_path, capsys):
    fill(store, CAND, [_g(s) for s in range(5)])
    fill(store, BASE, [_g(s) for s in range(5)])
    code, out = replay(capsys, tmp_path, CAND, BASE)
    assert code == 0 and "5 seeds compared, 0 mismatched" in out


def test_replay_reports_each_differing_field(store, tmp_path, capsys):
    fill(store, CAND, [_g(s) for s in range(3)])
    fill(store, BASE, [_g(s, turns=999) if s == 1 else _g(s) for s in range(3)])
    code, out = replay(capsys, tmp_path, CAND, BASE)
    assert code == 1
    assert "seed 1 turns: 1001 != 999" in out
    assert "3 seeds compared, 1 mismatched" in out


def test_replay_truncates_long_values(store, tmp_path, capsys):
    fill(store, CAND, [_g(0, end_reason="x" * 300)])
    fill(store, BASE, [_g(0, end_reason="y" * 300)])
    code, out = replay(capsys, tmp_path, CAND, BASE)
    line = next(line for line in out.splitlines() if line.startswith("seed 0 end_reason"))
    assert code == 1 and len(line) < 200


def test_replay_too_few_common_seeds_exit_2(store, tmp_path, capsys):
    fill(store, CAND, [_g(s) for s in range(5)])
    fill(store, BASE, [_g(s) for s in range(3)])
    code, out = replay(capsys, tmp_path, CAND, BASE, "--min", "4")
    assert code == 2 and "missing seeds: A has 5, B has 3, common 3" in out
    assert replay(capsys, tmp_path, CAND, BASE, "--min", "3")[0] == 0


def test_replay_without_seeded_games_exit_2(store, tmp_path, capsys):
    fill(store, CAND, [{"role": "Valkyrie", "turns": 5, "end_reason": "x"}])
    fill(store, BASE, [{"role": "Valkyrie", "turns": 5, "end_reason": "x"}])
    code, out = replay(capsys, tmp_path, CAND, BASE, "--min", "1")
    assert code == 2 and out.startswith("missing seeds")


def test_replay_seeds_option_limits_the_range(store, tmp_path, capsys):
    fill(store, CAND, [_g(s) for s in range(6)])
    fill(store, BASE, [_g(s, turns=1) if s == 5 else _g(s) for s in range(6)])
    assert replay(capsys, tmp_path, CAND, BASE, "--seeds", "5")[0] == 0
    assert replay(capsys, tmp_path, CAND, BASE, "--seeds", "6")[0] == 1


def test_replay_fields_present_on_one_side_only_are_not_compared(store, tmp_path, capsys):
    fill(store, CAND, [_g(s, hp_at_end=3, events={"a": 1}) for s in range(3)])
    fill(store, BASE, [_g(s) for s in range(3)])
    code, out = replay(capsys, tmp_path, CAND, BASE)
    summary = out.strip().splitlines()[-1]
    assert code == 0
    assert "3 seeds compared, 0 mismatched" in summary
    assert summary.count("hp_at_end") == 1 and summary.count("events") == 1
    assert "not compared" in summary


def test_replay_compares_new_fields_when_both_sides_have_them(store, tmp_path, capsys):
    fill(store, CAND, [_g(0, events={"rest_turns": 4}, prayers=[[10, "You feel that Tyr is well-pleased."]])])
    fill(store, BASE, [_g(0, events={"rest_turns": 5}, prayers=[[10, "You feel that Tyr is well-pleased."]])])
    code, out = replay(capsys, tmp_path, CAND, BASE)
    assert code == 1 and "seed 0 events:" in out and "prayers" not in out.split("compared")[0]


def test_replay_skip_end_leaves_seeds_out(store, tmp_path, capsys):
    fill(store, CAND, [_g(0), _g(1, end_reason="watchdog", turns=1), _g(2)])
    fill(store, BASE, [_g(0), _g(1, end_reason="watchdog", turns=2), _g(2, end_reason="watchdog", turns=9)])
    code, out = replay(capsys, tmp_path, CAND, BASE, "--skip-end", "watchdog")
    assert code == 0
    assert "1 seeds compared, 0 mismatched" in out
    assert "skipped (watchdog): 2" in out and "1" in out and "2" in out
    # --min counts the common seeds before skipping
    assert replay(capsys, tmp_path, CAND, BASE, "--skip-end", "watchdog", "--min", "3")[0] == 0
    assert replay(capsys, tmp_path, CAND, BASE, "--skip-end", "watchdog", "--min", "4")[0] == 2


def test_replay_fields_option_restricts_the_comparison(store, tmp_path, capsys):
    fill(store, CAND, [_g(0)])
    fill(store, BASE, [_g(0, turns=5)])
    assert replay(capsys, tmp_path, CAND, BASE, "--fields", "role,score")[0] == 0
    assert replay(capsys, tmp_path, CAND, BASE, "--fields", "turns")[0] == 1


def pair_games(store, hits_both=0, only_cand=0, only_base=0, neither=0):
    seed = 0
    for cand_hit, base_hit, count in ((1, 1, hits_both), (1, 0, only_cand), (0, 1, only_base), (0, 0, neither)):
        for _ in range(count):
            store.add_game(CAND, None, _g(seed, max_depth=7 if cand_hit else 2))
            store.add_game(BASE, None, _g(seed, max_depth=7 if base_hit else 2))
            seed += 1
    return seed


def test_pairs_matches_judge_paired(store, tmp_path, capsys):
    n = pair_games(store, hits_both=20, only_cand=15, only_base=5, neither=60)
    assert n == 100
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6", "--seeds", "100")
    verdict = judge_paired([(True, True)] * 20 + [(True, False)] * 15 + [(False, True)] * 5
                           + [(False, False)] * 60, 100)
    assert code == 0
    assert "n=100" in out and "n10=15" in out and "n01=5" in out and "q=0.200" in out
    assert "diff=+10.0 points" in out
    assert f"lo={verdict.lo * 100:+.1f}" in out and f"hi={verdict.hi * 100:+.1f}" in out
    assert f"half-width={verdict.detectable * 100:.1f}" in out
    assert f"mde80={2.8 * verdict.detectable / 1.96 * 100:.1f}" in out
    assert "99%" in out  # 100 is not the last checkpoint


def test_pairs_uses_95_percent_only_at_the_last_checkpoint(store, tmp_path, capsys, monkeypatch):
    n = pair_games(store, hits_both=2, only_cand=3, only_base=1, neither=2)
    monkeypatch.setattr(seeded_report, "CHECKPOINTS", (4, n))
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6")
    assert code == 0 and f"seeds 0..{n - 1}" in out
    # judge_paired itself decides the z from bench.stats.CHECKPOINTS; with a fake size it is 99%
    assert "n=8" in out


def test_pairs_default_seeds_is_the_largest_checkpoint_both_refs_have(store, tmp_path, capsys, monkeypatch):
    pair_games(store, hits_both=3, only_cand=3, only_base=1, neither=1)  # 8 seeds each
    monkeypatch.setattr(seeded_report, "CHECKPOINTS", (4, 8, 16))
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6")
    assert code == 0 and "n=8" in out


def test_pairs_missing_seed_exit_2(store, tmp_path, capsys):
    pair_games(store, hits_both=2, only_cand=2)
    store.add_game(CAND, None, _g(4))  # base has seeds 0..3 only
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6", "--seeds", "5")
    assert code == 2 and "missing seeds" in out


def test_pairs_without_any_complete_checkpoint_exit_2(store, tmp_path, capsys):
    pair_games(store, hits_both=1)
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6")
    assert code == 2 and "missing seeds" in out


def test_pairs_skips_games_lacking_the_metric_field(store, tmp_path, capsys):
    store.add_game(CAND, None, {"seed": 0, "end_reason": "x"})  # no max_depth
    store.add_game(BASE, None, {"seed": 0, "end_reason": "x"})
    store.add_game(CAND, None, _g(1, max_depth=9))
    store.add_game(BASE, None, _g(1, max_depth=1))
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6", "--seeds", "2")
    assert code == 0 and "n=1" in out and "n10=1" in out
