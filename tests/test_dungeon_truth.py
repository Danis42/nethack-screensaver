import pytest
from nle import nethack

from nethack_screensaver import dungeon_truth


def _env(seed):
    env = nethack.Nethack()
    env.set_initial_seeds(seed, seed, False)
    env.reset()
    return env


def _read(env):
    return dungeon_truth.read(env.get_current_seeds()[:2])


@pytest.mark.parametrize("seed, levels", [(1, 8), (3, 9)])
def test_reads_the_mines_size_and_mines_end(seed, levels):
    env = _env(seed)
    try:
        truth = _read(env)
    finally:
        env.close()
    assert truth.mines_levels == levels
    assert truth.mines_end == (2, levels)
    assert truth.quest_dnum == 3


def test_reads_the_game_with_the_given_seeds_among_several():
    envs = [_env(seed) for seed in (3, 1, 8, 4)]
    try:
        assert [_read(env).mines_levels for env in envs] == [9, 8, 8, 9]
    finally:
        for env in envs:
            env.close()


def test_unknown_seeds_raise():
    env = _env(1)
    try:
        with pytest.raises(dungeon_truth.TruthUnavailable):
            dungeon_truth.read((123456789, 987654321))
    finally:
        env.close()


def test_no_game_loaded_raises(monkeypatch):
    monkeypatch.setattr(dungeon_truth, "MEMFD", "/memfd:no-such-library")
    with pytest.raises(dungeon_truth.TruthUnavailable):
        dungeon_truth.read((1, 1))


def test_missing_nm_raises(monkeypatch):
    dungeon_truth._symbols.cache_clear()

    def no_nm(*args, **kwargs):
        raise FileNotFoundError("nm")

    monkeypatch.setattr(dungeon_truth.subprocess, "run", no_nm)
    try:
        with pytest.raises(dungeon_truth.TruthUnavailable):
            dungeon_truth._symbols()
    finally:
        dungeon_truth._symbols.cache_clear()
