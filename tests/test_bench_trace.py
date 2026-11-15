"""Frame-hash trace (CODE-01): identical frame streams give identical traces; a change shows at its step."""
import numpy as np

from bench.frame_trace import TURN, Trace, first_divergence, read


def _frames(n, change_at=None):
    for i in range(n):
        chars = np.full((24, 80), ord(" "), dtype=np.uint8)
        chars[0, i % 80] = ord("@")
        if i == change_at:
            chars[1, 1] = ord("x")
        blstats = np.zeros(27, dtype=np.int64)
        blstats[TURN] = 1 + i // 2
        yield {"tty_chars": chars, "blstats": blstats, "glyphs": None}


def _trace(path, frames):
    t = Trace(path)
    for f in frames:
        t.frame(f)
    return t.close(), t.steps


def test_identical_streams_have_identical_traces(tmp_path):
    da, na = _trace(tmp_path / "a", _frames(50))
    db, nb = _trace(tmp_path / "b", _frames(50))
    assert (da, na) == (db, nb) == (da, 50)
    assert first_divergence(tmp_path / "a", tmp_path / "b") is None
    assert len(read(tmp_path / "a")) == 50


def test_first_changed_frame_is_reported_with_its_turn(tmp_path):
    da, _ = _trace(tmp_path / "a", _frames(50))
    db, _ = _trace(tmp_path / "b", _frames(50, change_at=17))
    assert da != db
    assert first_divergence(tmp_path / "a", tmp_path / "b") == {"step": 17, "turn_a": 9, "turn_b": 9}


def test_a_shorter_game_differs_where_it_ends(tmp_path):
    _trace(tmp_path / "a", _frames(50))
    _trace(tmp_path / "b", _frames(30))
    assert first_divergence(tmp_path / "a", tmp_path / "b") == {"step": 30, "turn_a": 16, "turn_b": None}
