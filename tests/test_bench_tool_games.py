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
