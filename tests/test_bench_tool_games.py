"""tool_games: staged, scenario and rewind runs, recorded with job IDs but never mixed into natural games."""
import pytest

from bench.store import Store


def test_tool_rows_are_invisible_to_natural_reads(tmp_path):
    store = Store(tmp_path / "r.db")
    job = store.add_job("staged", {})
    store.add_tool_game(job, "staged", "a" * 40, {"seed": 7, "stage": "medusa", "max_depth": 21})
    assert store.tool_games(job)[0]["stage"] == "medusa"
    sha = "a" * 40
    assert store.games(sha) == [] and store.seeds(sha) == set() and store.count(sha) == 0
    assert store.played(sha, 0, 1000) == 0


def test_a_job_with_only_a_tool_row_is_started(tmp_path):
    store = Store(tmp_path / "r.db")
    job = store.add_job("staged", {})
    assert not store.started(job)
    store.add_tool_game(job, "staged", "a" * 40, {"seed": 7}, finished_at=12.5)
    assert store.started(job) and store.first_game_at(job) == 12.5


def test_staged_results_are_refused_by_add_game(tmp_path):
    store = Store(tmp_path / "r.db")
    with pytest.raises(ValueError, match="add_tool_game"):
        store.add_game("a", None, {"seed": 1001, "stage": "medusa"})
    store.add_game("a", None, {"seed": 1001, "stage": None})
    assert store.count("a") == 1


# toolruns: recording staged, scenario and rewind runs (plan 01-11 Task 3)

def test_record_run_refuses_seeds_outside_the_tool_block_and_other_kinds(tmp_path):
    from bench import toolruns
    store = Store(tmp_path / "r.db")
    with pytest.raises(ValueError, match="tool block"):
        toolruns.record_run(store, "staged", "a" * 40, {"seeds": [5, 1500]})
    with pytest.raises(ValueError, match="tool must be"):
        toolruns.record_run(store, "baseline", "a" * 40, {"seeds": [5]})
    with pytest.raises(ValueError, match="40-hex"):
        toolruns.record_run(store, "staged", "abc", {"seeds": [5]})


def test_a_recorded_staged_run_is_a_done_job_with_tool_rows_only(tmp_path):
    from bench import toolruns
    store = Store(tmp_path / "r.db")
    sha = "b" * 40
    job = toolruns.record_run(store, "staged", sha, {"seeds": [1, 2], "args": ["medusa"]})
    for seed in (1, 2):
        toolruns.add_result(store, job, "staged", sha, {"seed": seed, "stage": "medusa"})
    toolruns.finish(store, job, result={"games": 2})
    assert store.job(job)["kind"] == "staged" and store.job(job)["state"] == "done"
    assert len(store.tool_games(job)) == 2 and store.started(job) and store.count(sha) == 0


def test_job_ids_share_one_sequence_with_natural_jobs(tmp_path):
    from bench import toolruns
    store = Store(tmp_path / "r.db")
    natural = store.add_job("baseline", {})
    tool = toolruns.record_run(store, "rewind", "c" * 40, {"seeds": [3]})
    assert tool == natural + 1
