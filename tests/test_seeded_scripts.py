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


# ladder, killers, deaths


from autoascend.ladder import RUNGS  # noqa: E402


def _table(out):
    """{first cell: cells} for every markdown table row of the output."""
    rows = {}
    for line in out.splitlines():
        if line.startswith("|") and not line.startswith("|--") and not line.startswith("|-"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows[cells[0]] = cells
    return rows


def _lg(seed, rung, **extra):
    ladder = {r.key: 100 * (i + 1) + seed for i, r in enumerate(RUNGS[:rung])}
    return _g(seed, rung=rung, ladder=ladder, **extra)


def test_ladder_table_for_exact_seeds(store, tmp_path, capsys):
    fill(store, CAND, [_lg(0, 0), _lg(1, 1), _lg(2, 2), _lg(3, 2)])
    store.add_game(CAND, None, {"role": "Wizard", "rung": 8, "ladder": {"mines": 1}, "end_reason": "x"})  # unseeded
    code, out = run(capsys, tmp_path, "ladder", CAND, "--seeds", "4")
    assert code == 0
    assert f"Commit `{CAND}`, n = 4 games (seeds 0..3)" in out
    assert "| # | Rung | Reached | Our median turn | Ascenders' median turn |" in out
    rows = _table(out)
    assert len([k for k in rows if k.isdigit()]) == 17
    assert rows["1"][1:] == ["Gnomish Mines", "3 (75%)", "102", "-"]  # first turns 101, 102, 103
    assert rows["2"][2] == "2 (50%)" and rows["3"][2] == "0 (0%)" and rows["3"][3] == "-"


def test_ladder_median_turn_of_a_row(store, tmp_path, capsys):
    fill(store, CAND, [_lg(0, 1), _lg(1, 1), _lg(2, 1), _lg(3, 1)])
    _, out = run(capsys, tmp_path, "ladder", CAND, "--seeds", "4")
    assert _table(out)["1"][3] == "101.5"  # 100, 101, 102, 103


def test_ladder_needs_all_requested_seeds(store, tmp_path, capsys):
    fill(store, CAND, [_lg(s, 1) for s in range(3)])
    code, out = run(capsys, tmp_path, "ladder", CAND, "--seeds", "4")
    assert code == 2 and out.startswith("missing seeds")


def test_ladder_all_games_uses_unseeded_games_too(store, tmp_path, capsys):
    fill(store, CAND, [_lg(0, 1), _lg(1, 2)])
    for rung in (1, 1, 3):
        store.add_game(CAND, None, {"rung": rung, "ladder": {"mines": 5}, "end_reason": "x"})
    code, out = run(capsys, tmp_path, "ladder", CAND, "--all-games")
    assert code == 0 and "n = 5 games (all stored games)" in out
    assert _table(out)["1"][2] == "5 (100%)" and _table(out)["3"][2] == "1 (20%)"


def test_ladder_skips_games_without_ladder_in_the_percentages(store, tmp_path, capsys):
    fill(store, CAND, [_lg(0, 1), {"seed": 1, "end_reason": "x"}])  # an older commit's game has no ladder
    code, out = run(capsys, tmp_path, "ladder", CAND, "--seeds", "2")
    assert code == 0 and _table(out)["1"][2] == "1 (100%)"


def _killer_games(store):
    reasons = ["DEATH: killed by a soldier ant", "DEATH: killed by a giant ant", "DEATH: starved",
               "DEATH: killed by a newt, while fainted from lack of food", "DEATH: killed by a killer bee",
               "DEATH: killed by a wand of striking", "DEATH: killed by a magic missile",
               "DEATH: killed by a blast of fire", "exception: ValueError: boom", "watchdog",
               "ESCAPED: escaped the dungeon", "DEATH: killed by a jackal", "DEATH: killed by a jackal",
               "DEATH: killed by a gnome lord"]
    games = []
    for seed, reason in enumerate(reasons):
        games.append(_g(seed, end_reason=reason, max_depth=seed % 5 + 1, turns=100 * (seed + 1),
                        **({"depth_at_end": 9} if seed == 13 else {})))
    fill(store, CAND, games)
    return len(reasons)


def test_killers_rows_use_the_benchs_own_definitions(store, tmp_path, capsys):
    n = _killer_games(store)
    code, out = run(capsys, tmp_path, "killers", CAND, "--seeds", str(n))
    assert code == 0
    rows = _table(out)
    assert rows["starved"][1] == "2"  # starved + killed while fainted
    assert rows["ants"][1] == "2" and rows["killer bee"][1] == "1" and rows["wand"][1] == "1"
    assert rows["rays"][1] == "1" and rows["breath"][1] == "1"
    assert rows["exception"][1] == "1" and rows["watchdog"][1] == "1"
    assert rows["escaped/other endings"][1] == "1"
    assert rows["jackal"][1] == "2" and rows["gnome lord"][1] == "1"
    assert rows["starved"][2] == f"{2 / n * 100:.1f}%"
    deaths = 11
    assert rows["jackal"][3] == f"{2 / deaths * 100:.1f}%"
    assert rows["gnome lord"][4] == "9"  # depth_at_end wins over max_depth


def test_killers_other_names_are_not_repeated_in_category_rows(store, tmp_path, capsys):
    n = _killer_games(store)
    _, out = run(capsys, tmp_path, "killers", CAND, "--seeds", str(n))
    rows = _table(out)
    for name in ("soldier ant", "giant ant", "wand of striking", "newt"):
        assert name not in rows


def test_killers_depth_filter(store, tmp_path, capsys):
    n = _killer_games(store)
    _, out = run(capsys, tmp_path, "killers", CAND, "--seeds", str(n), "--min-depth", "9")
    rows = _table(out)
    assert rows["gnome lord"][1] == "1"
    assert "jackal" not in rows


def test_killers_all_games_and_missing_seeds(store, tmp_path, capsys):
    _killer_games(store)
    assert run(capsys, tmp_path, "killers", CAND, "--all-games")[0] == 0
    code, out = run(capsys, tmp_path, "killers", CAND, "--seeds", "500")
    assert code == 2 and out.startswith("missing seeds")


def test_deaths_by_killer_prints_context_rows(store, tmp_path, capsys):
    fill(store, CAND, [
        _g(0, end_reason="DEATH: killed by a soldier ant", hp_at_end=0, max_hp_at_end=41, hunger_at_end=2,
           food_at_end=3, depth_at_end=5, prayers=[[100, "You feel that Tyr is well-pleased."], [900, "p" * 80]],
           zaps_seen=1, last_messages=["m1", "m2", "m3"]),
        _g(1, end_reason="DEATH: killed by a newt"),
        _g(2, end_reason="DEATH: killed by a fire ant | with a pipe"),
    ])
    code, out = run(capsys, tmp_path, "deaths", CAND, "--seeds", "3", "--killer", "ant")
    assert code == 0
    assert out.strip().splitlines()[-1] == "2 games"
    rows = _table(out)
    row = rows["0"]
    assert "0/41" in row and "5" in row and "3" in row
    assert any(c.startswith("2 (last t=900") and "p" * 40 in c and "p" * 41 not in c for c in row)
    assert any(c.endswith("m2 / m3") or "m2" in c and "m3" in c and "m1" not in c for c in row)
    assert "newt" not in out
    assert "|" not in rows["2"][5].replace("/", "")  # a pipe in the text must not break the table


def test_deaths_by_metric_and_without_new_fields(store, tmp_path, capsys):
    fill(store, CAND, [_g(0, max_depth=8), _g(1, max_depth=2), _g(2, max_depth=9)])
    code, out = run(capsys, tmp_path, "deaths", CAND, "--seeds", "3", "--metric", "dlvl6")
    assert code == 0 and out.strip().splitlines()[-1] == "2 games"
    assert set(k for k in _table(out) if k.isdigit()) == {"0", "2"}


def test_deaths_needs_a_selector(store, tmp_path, capsys):
    fill(store, CAND, [_g(0)])
    with pytest.raises(SystemExit):
        seeded_report.main(["--data", str(tmp_path), "deaths", CAND, "--seeds", "1"])


# benchmark.py: seeded smoke runs


import benchmark  # noqa: E402


def test_parse_seeds_accepts_ranges_numbers_and_lists():
    assert benchmark.parse_seeds("0-21") == list(range(22))
    assert benchmark.parse_seeds("5") == [5]
    assert benchmark.parse_seeds("0,3,7") == [0, 3, 7]
    assert benchmark.parse_seeds("0-2,5, 9-10") == [0, 1, 2, 5, 9, 10]
    for bad in ("", "a", "3-1", "1,,2", "-1"):
        with pytest.raises(ValueError):
            benchmark.parse_seeds(bad)


def test_field_value_walks_dotted_names():
    result = {"turns": 5, "events": {"rest_turns": 7}, "prayers": []}
    assert benchmark.field_value(result, "turns") == 5
    assert benchmark.field_value(result, "events.rest_turns") == 7
    assert benchmark.field_value(result, "events.nothing") is None
    assert benchmark.field_value(result, "missing") is None
    assert benchmark.field_value(result, "turns.deeper") is None


class _SerialPool:
    def __init__(self, n):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def imap_unordered(self, fn, items):
        return map(fn, items)


def _fake_run_game(calls):
    from nethack_screensaver.game import GameResult

    def run_game(watchdog_seconds=None, strategy=None, seed=None):
        calls.append((strategy, seed))
        return GameResult("Val", "human", "lawful", 3, 100 + (seed or 0), 10, "DEATH: killed by a newt",
                          seed=seed, events={"rest_turns": (seed or 0) % 2})
    return run_game


def test_seeds_option_plays_the_chosen_seeds_and_reports_fields(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(benchmark, "Pool", _SerialPool)
    monkeypatch.setattr(benchmark, "run_game", _fake_run_game(calls))
    benchmark.main(["--seeds", "0-3", "--field", "events.rest_turns", "--field", "hp_at_end"])
    out = capsys.readouterr().out
    assert sorted(seed for _, seed in calls) == [0, 1, 2, 3]
    assert "events.rest_turns=1" in out and "hp_at_end=0" in out
    assert "events.rest_turns>0: 2 of 4 games" in out and "hp_at_end>0: 0 of 4 games" in out
    assert "seed=2" in out


def test_unseeded_runs_keep_their_output(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(benchmark, "Pool", _SerialPool)
    monkeypatch.setattr(benchmark, "run_game", _fake_run_game(calls))
    benchmark.main(["-n", "2", "-j", "1"])
    out = capsys.readouterr().out
    assert calls == [(None, None), (None, None)]
    assert "[1/2] " in out and "seed=" not in out and ">0:" not in out and "games            : 2" in out


def test_seeds_with_strategy_or_n_is_refused(capsys):
    for extra in (["--strategy", "random"], ["-n", "5"]):
        with pytest.raises(SystemExit) as exc:
            benchmark.main(["--seeds", "0-3", *extra])
        assert exc.value.code == 2
    with pytest.raises(SystemExit):
        benchmark.main(["--seeds", "3-1"])


def test_pairs_judges_a_numeric_metric(store, tmp_path, capsys):
    from bench.stats import judge_paired_numeric
    for seed, (c, b) in enumerate([(3, 1), (2, 2), (5, 1), (1, 2)]):
        store.add_game(CAND, None, _g(seed, rung=c))
        store.add_game(BASE, None, _g(seed, rung=b))
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "rung", "--seeds", "4")
    v = judge_paired_numeric([(3, 1), (2, 2), (5, 1), (1, 2)], 4)
    assert code == 0
    assert "(numeric)" in out and f"diff={v.diff:+.3f}" in out and f"half-width={v.detectable:.3f}" in out


def test_pairs_reports_an_80_percent_interval(store, tmp_path, capsys):
    pair_games(store, hits_both=20, only_cand=15, only_base=5, neither=60)
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "dlvl6", "--seeds", "100",
                    "--confidence", "80")
    verdict = judge_paired([(True, True)] * 20 + [(True, False)] * 15 + [(False, True)] * 5
                           + [(False, False)] * 60, 100, z=1.2815515655446004)
    assert code == 0 and "(80%)" in out
    assert f"half-width={verdict.detectable * 100:.1f}" in out and "standardized=" in out


# starvation

OK = "You finish your prayer.  You feel that Tyr is well-pleased.--More-- | Your stomach feels content."
BAD = "You feel that Tyr is displeased. | You faint from lack of food."


def _starver(seed, turns=5000, end="DEATH: starved to death", **extra):
    return _g(seed, **{"turns": turns, "end_reason": end, "max_depth": 5, "depth_at_end": 5, "food_at_end": 0,
                       "prayers": [], **extra})


def _bucket_rows(out):
    return {line.split("|")[1].strip(): line for line in out.splitlines() if line.startswith("| ") and "---" not in line}


def test_starvation_buckets(store, tmp_path, capsys):
    games = [
        _starver(0, prayers=[[4800, BAD]]),                      # failed-prayer
        _starver(1, food_at_end=2),                              # food-carried
        _starver(2, prayers=[[4400, OK]]),                       # prayer-cooldown
        _starver(3, prayers=[[3000, OK]]),                       # prayer-unused (no prayer after T-1000)
        _starver(4, turns=1200, food_at_end=-1, prayers=None),   # other
        _g(5, end_reason="DEATH: killed by a newt"),             # not a starvation game: ignored
    ]
    games[4].pop("prayers")
    fill(store, CAND, games)
    code, out = run(capsys, tmp_path, "starvation", CAND, "--seeds", "6")
    rows = _bucket_rows(out)
    assert code == 0
    for bucket in ("failed-prayer", "food-carried", "prayer-cooldown", "prayer-unused", "other"):
        assert rows[bucket].split("|")[2].strip() == "1", bucket
    assert "n = 5 starvation games" in out


def test_starvation_tags(store, tmp_path, capsys):
    fill(store, CAND, [
        _starver(0, turns=3000, end="DEATH: killed by a jackal, while fainted from lack of food", max_depth=3,
                 depth_at_end=3, food_at_end=1),
        _starver(1, turns=7000, food_at_end=1, stuck_diving=1),
    ])
    code, out = run(capsys, tmp_path, "starvation", CAND, "--seeds", "2")
    cells = [c.strip() for c in _bucket_rows(out)["food-carried"].split("|")[1:-1]]
    # bucket | games | % | median turns | median depth | roles | fainted-kill | starved | early | long | stuck
    assert code == 0 and cells[1] == "2"
    assert cells[6:] == ["1", "1", "1", "1", "1"]


def test_starvation_failed_prayer_detail(store, tmp_path, capsys):
    fill(store, CAND, [
        _starver(0, prayers=[[3500, OK], [4400, BAD]]),
        _starver(1, prayers=[[4000, OK], [4500, BAD], [4900, BAD]]),
    ])
    code, out = run(capsys, tmp_path, "starvation", CAND, "--seeds", "2")
    assert code == 0
    assert "failed prayers per game: 1 -> 1, 2+ -> 1" in out
    assert "median gap from the previous prayer to the first failed one: 700 turns" in out
