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


def add_experiment(store, candidate=CAND, baseline=BASE, metric="stage_minetown", state="done",
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
    assert lines[0]["candidate"] == CAND and lines[0]["baseline"] == BASE and lines[0]["metric"] == "stage_minetown"
    assert lines[1]["pairs"] is None  # older jobs stored no pair count


def test_verdict_filters_by_baseline_and_metric(store, tmp_path, capsys):
    wanted = add_experiment(store, baseline=BASE, metric="stage_minetown")
    add_experiment(store, baseline=OTHER, metric="stage_minetown")
    add_experiment(store, baseline=BASE, metric="dlvl6")
    code, out = run(capsys, tmp_path, "verdict", CAND, "--baseline", BASE, "--metric", "stage_minetown")
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
    assert len([k for k in rows if k.isdigit()]) == 18
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
        store.add_game(CAND, None, {"rung": rung, "ladder": {r.key: 5 for r in RUNGS[:rung]}, "end_reason": "x"})
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
        store.add_game(CAND, None, _g(seed, max_depth=c))
        store.add_game(BASE, None, _g(seed, max_depth=b))
    code, out = run(capsys, tmp_path, "pairs", CAND, BASE, "--metric", "depth", "--seeds", "4")
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


# insects


def _insect(seed, name="soldier ant", **extra):
    return _g(seed, **{"turns": 5000, "end_reason": f"DEATH: killed by a {name}", "max_depth": 6, "depth_at_end": 6,
                       "xp_level": 6, "prayers": [], "last_messages": [], **extra})


def test_insects_counts_and_fainted_apart(store, tmp_path, capsys):
    fill(store, CAND, [
        _insect(0), _insect(1, name="killer bee"),
        _insect(2, end_reason="DEATH: killed by a soldier ant, while fainted from lack of food"),
        _g(3),
    ])
    code, out = run(capsys, tmp_path, "insects", CAND, "--seeds", "4")
    rows = _bucket_rows(out)
    assert code == 0 and "3 insect deaths, 1 of them killed while fainted" in out
    assert rows["soldier ant"].split("|")[2].strip() == "1"
    assert rows["killer bee"].split("|")[2].strip() == "1"


def test_insects_prayer_unused_rule(store, tmp_path, capsys):
    fill(store, CAND, [_insect(0), _insect(1, prayers=[[4500, OK]]), _insect(2, turns=200)])
    code, out = run(capsys, tmp_path, "insects", CAND, "--seeds", "3")
    # seed 0 unused; seed 1 prayed in the window; seed 2 too early to pray
    assert code == 0 and "A1 prayer unused" in out and "33.3%" in out
    assert "tactic: close-door" in out


def test_insects_pray_earlier_when_prayers_unused(store, tmp_path, capsys):
    fill(store, CAND, [_insect(0), _insect(1)])
    code, out = run(capsys, tmp_path, "insects", CAND, "--seeds", "2")
    assert code == 0 and "tactic: pray-earlier" in out


def test_insects_poison_resistance_rule(store, tmp_path, capsys):
    msgs = ["The soldier ant's sting was poisoned!"]
    fill(store, CAND, [_insect(0, prayers=[[4900, OK]], last_messages=msgs), _insect(1, prayers=[[4900, OK]])])
    code, out = run(capsys, tmp_path, "insects", CAND, "--seeds", "2")
    assert code == 0 and "A2 poison in the last messages: 50.0%" in out
    assert "tactic: poison-resistance" in out


# zappers


def _zapped(seed, name="wand", **extra):
    return _g(seed, **{"turns": 5000, "end_reason": f"DEATH: killed by a {name}", "max_depth": 6, "depth_at_end": 6,
                       "xp_level": 6, "prayers": [], "last_messages": [], "zaps_seen": 0, **extra})


def _class_count(out, cls):
    return _bucket_rows(out)[cls].split("|")[2].strip()


def test_zappers_classes(store, tmp_path, capsys):
    fill(store, CAND, [
        _zapped(0, name="bolt of lightning", prayers=[[4995, BAD]]),               # Z1 divine
        _zapped(1, name="bolt of lightning", prayers=[[4000, BAD]]),               # prayer too early: not Z1
        _zapped(2, name="blast of frost"),                                          # Z3 breath
        _zapped(3, zaps_seen=2),                                                    # Z2 warned by count
        _zapped(4, last_messages=["The gnome lord zaps a wand!", "The wand hits you!"]),  # Z2 by message
        _zapped(5, last_messages=["The wand hits you!", "The gnome zaps a wand!"]),  # last line only: Z4
        _g(6),
    ])
    code, out = run(capsys, tmp_path, "zappers", CAND, "--seeds", "7")
    assert code == 0 and "6 wand and ray deaths" in out
    assert _class_count(out, "Z1 divine") == "1"
    assert _class_count(out, "Z2 warned") == "2"
    assert _class_count(out, "Z3 breath") == "1"
    assert _class_count(out, "Z4 unwarned") == "2"


def test_zappers_rule():
    base = {"Z1 divine": 0.0, "Z2 warned": 0.3, "Z3 breath": 0.2, "Z4 unwarned": 0.5}
    assert seeded_report._zapper_tactic({**base, "Z1 divine": 0.3}, False) == "stop-praying-after-failure"
    assert seeded_report._zapper_tactic({**base, "Z1 divine": 0.3}, True) == "leave-zap-line"
    assert seeded_report._zapper_tactic({**base, "Z3 breath": 0.6}, False) == "leave-breath-line"
    assert seeded_report._zapper_tactic(base, False) == "leave-zap-line"


# stuck


def _report_row(dungeon=0, level=7, dlvl=7, milestone="DIVE", down_seen=False, down_reachable=False, frontier=0,
                closed_doors=0, boulders=0, wants_up=False, up_seen=False, up_reachable=False):
    return {"turn": 5000, "dungeon": dungeon, "level": level, "dlvl": dlvl, "milestone": milestone,
            "target": [0, 100], "wants_up": wants_up, "down_seen": down_seen, "down_reachable": down_reachable,
            "up_seen": up_seen, "up_reachable": up_reachable, "frontier": frontier,
            "closed_doors": closed_doors, "boulders": boulders}


def _stuck_g(seed, reports, depth=7, at=(0, 7), **extra):
    return _g(seed, **{"depth_at_end": depth, "max_depth": depth, "unsticks": 0, "stuck_reports": reports,
                       "dungeon_at_end": at[0], "level_at_end": at[1], "watchdog_stack": [], **extra})


def _stuck_store(store):
    fill(store, CAND, [
        _stuck_g(0, [_report_row(down_seen=True, closed_doors=2)]),            # stairs-unreachable
        _stuck_g(1, [_report_row(down_seen=True, down_reachable=True)]),       # stairs-reachable
        _stuck_g(2, [_report_row(frontier=4, milestone="FIND_MINETOWN")]),     # explore-left
        _stuck_g(3, [_report_row()], end_reason="DEATH: starved to death"),  # no-way-found
        _stuck_g(4, [], end_reason="watchdog", depth=24, at=(0, 24),
                 watchdog_stack=["autoascend/agent.py:10 a", "autoascend/agent.py:20 b", "autoascend/level.py:5 c"]),
        _stuck_g(5, [_report_row(level=6, dlvl=6)]),                           # left that level: free
        _g(6),                                                                 # older commit: not recorded
    ])


def test_stuck_buckets_of_the_stuck_endings(store, tmp_path, capsys):
    _stuck_store(store)
    code, out = run(capsys, tmp_path, "stuck", CAND, "--seeds", "7")
    rows = _bucket_rows(out)
    assert code == 0
    assert "1 not recorded" in out and "free5 16.7% (1 of 6)" in out and "ended stuck at Dlvl 5+: 5" in out
    for bucket in ("stairs-unreachable", "stairs-reachable", "explore-left", "no-way-found", "no-report"):
        assert rows[bucket].split("|")[2].strip() == "1", bucket
    assert rows["stairs-unreachable"].split("|")[5].strip() == "1"  # closed doors seen


def test_stuck_events_by_milestone_and_dungeon(store, tmp_path, capsys):
    _stuck_store(store)
    code, out = run(capsys, tmp_path, "stuck", CAND, "--seeds", "7")
    rows = _bucket_rows(out)
    assert code == 0 and "5 events in 5 games" in out
    assert rows["DIVE"].split("|")[2].strip() == "4" and rows["FIND_MINETOWN"].split("|")[2].strip() == "1"
    assert rows["Doom"].split("|")[2].strip() == "5"
    assert "Stuck endings by end type:" in out and "starved 1" in out and "watchdog 1" in out


def test_stuck_groups_watchdog_games_by_their_innermost_frames(store, tmp_path, capsys):
    _stuck_store(store)
    code, out = run(capsys, tmp_path, "stuck", CAND, "--seeds", "7")
    assert code == 0 and "Watchdog games (1)" in out
    assert "autoascend/agent.py:10 a < autoascend/agent.py:20 b < autoascend/level.py:5 c" in out


def test_stuck_rows_list_one_bucket(store, tmp_path, capsys):
    _stuck_store(store)
    code, out = run(capsys, tmp_path, "stuck", CAND, "--seeds", "7", "--rows", "explore-left")
    assert code == 0
    assert out.strip().splitlines() == [
        "seed=2 dlvl=7 milestone=FIND_MINETOWN bucket=explore-left end=DEATH: killed by a newt"]


def test_stuck_buckets_judge_the_up_staircase_when_the_bot_wanted_to_go_up(store, tmp_path, capsys):
    fill(store, CAND, [
        _stuck_g(0, [_report_row(wants_up=True, down_seen=True, down_reachable=True, up_seen=True)]),
        _stuck_g(1, [_report_row(wants_up=True, up_seen=True, up_reachable=True)]),
    ])
    code, out = run(capsys, tmp_path, "stuck", CAND, "--seeds", "2")
    rows = _bucket_rows(out)
    assert code == 0
    assert rows["stairs-unreachable"].split("|")[2].strip() == "1"
    assert rows["stairs-reachable"].split("|")[2].strip() == "1"
    assert rows["stairs-reachable"].split("|")[7].strip() == "1"  # going up


# replay_check as the A/A comparison (plan 01-15): replicate 1 against replicate 0 of one commit


def _aa(store, seeds, rep1=None, lgen=None):
    """Rows of CAND on rep 0 and rep 1; rep1 maps a seed to the rep-1 game when it differs."""
    rep1 = rep1 or {}
    for s in seeds:
        g = _g(s, **({} if lgen is None else {"lgen": s + lgen}))
        store.add_game(CAND, None, g, rep=0)
        store.add_game(CAND, None, rep1.get(s, g), rep=1)


def _json_tail(out):
    return json.loads(out.strip().splitlines()[-1])


def test_aa_compares_replicate_1_with_replicate_0(store, tmp_path, capsys):
    _aa(store, range(1000, 1004))
    code, out = replay(capsys, tmp_path, CAND, CAND, "--rep-b", "1", "--json")
    r = _json_tail(out)
    assert code == 0 and r["compared"] == 4 and r["identical"] == 4 and r["mismatched"] == 0 and r["common"] == 4


def test_aa_without_new_flags_reads_replicate_0_only(store, tmp_path, capsys):
    _aa(store, range(3), rep1={1: _g(1, turns=7)})
    code, out = replay(capsys, tmp_path, CAND, CAND)
    assert code == 0 and "3 seeds compared, 0 mismatched" in out  # rep 0 against itself


def test_aa_window_and_lgen_mode(store, tmp_path, capsys):
    _aa(store, range(1000, 1006), rep1={1005: _g(1005, turns=1)})
    store.add_game(CAND, None, _g(1001, turns=3, lgen=10_001_001), rep=1)  # lgen-on row: another mode
    code, out = replay(capsys, tmp_path, CAND, CAND, "--rep-b", "1", "--lo", "1000", "--hi", "1005",
                       "--lgen", "off", "--json")
    r = _json_tail(out)
    assert code == 0 and r["compared"] == 5 and r["common"] == 5


def test_aa_watchdog_on_both_replicates_is_skipped(store, tmp_path, capsys):
    _aa(store, range(1000, 1004), rep1={})
    store.add_game(CAND, None, _g(1004, end_reason="watchdog"), rep=0)
    store.add_game(CAND, None, _g(1004, end_reason="watchdog"), rep=1)
    code, out = replay(capsys, tmp_path, CAND, CAND, "--rep-b", "1", "--skip-both", "watchdog", "--json")
    r = _json_tail(out)
    assert code == 0 and r["skipped"] == {"watchdog": [1004]} and r["compared"] == 4 and r["common"] == 5


def test_aa_watchdog_on_one_replicate_is_a_mismatch(store, tmp_path, capsys):
    _aa(store, range(1000, 1004), rep1={1002: _g(1002, end_reason="watchdog")})
    code, out = replay(capsys, tmp_path, CAND, CAND, "--rep-b", "1", "--skip-both", "watchdog", "--json")
    r = _json_tail(out)
    assert code == 1 and r["mismatched_seeds"] == [1002] and r["skipped"] == {"watchdog": []}
    assert r["compared"] == 4 and r["identical"] == 3


def test_aa_too_few_common_seeds_exit_2(store, tmp_path, capsys):
    _aa(store, range(1000, 1010))
    code, out = replay(capsys, tmp_path, CAND, CAND, "--rep-b", "1", "--min", "2000", "--json")
    assert code == 2


def test_replay_refuses_to_compare_a_replicate_with_itself(store, tmp_path, capsys):
    # review WR-03: "replay_check A A" with default replicates reported every game identical to itself
    fill(store, CAND, [_g(s) for s in range(5)])
    code, out = replay(capsys, tmp_path, CAND, CAND)
    assert code == 2 and "same commit and replicate" in out
