import json
from datetime import datetime, timezone

from nethack_screensaver.game import GameResult
from nethack_screensaver.gamelog import LogStats, append_result, read_stats


def _r(depth):
    return GameResult("val", "hum", "law", depth, 1234, 567, "DEATH: killed by a jackal")


def test_append_and_read(tmp_path):
    p = tmp_path / "games.jsonl"
    append_result(p, _r(3), now=datetime(2026, 10, 16, tzinfo=timezone.utc))
    append_result(p, _r(9))
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["role"] == "val" and rec["max_depth"] == 3
    assert rec["timestamp"].startswith("2026-10-16")
    assert read_stats(p) == LogStats(games=2, best_depth=9)


def test_read_stats_missing_file(tmp_path):
    assert read_stats(tmp_path / "x.jsonl") == LogStats(0, 0)


def test_read_stats_skips_malformed_lines(tmp_path):
    p = tmp_path / "games.jsonl"
    append_result(p, _r(4))
    with p.open("a") as f:
        f.write('{"max_depth": 99, "trunc\n')
        f.write("not json\n")
        f.write('{"max_depth": "x"}\n')
    assert read_stats(p) == LogStats(games=1, best_depth=4)


def test_read_stats_survives_invalid_utf8(tmp_path):
    p = tmp_path / "games.jsonl"
    append_result(p, _r(5))
    with p.open("ab") as f:
        f.write(b"\xff\xfe garbage\n")
    assert read_stats(p) == LogStats(games=1, best_depth=5)


def test_read_stats_survives_unreadable_path(tmp_path):
    d = tmp_path / "games.jsonl"
    d.mkdir()
    assert read_stats(d) == LogStats(0, 0)
