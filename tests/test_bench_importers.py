from pathlib import Path

import pytest

from bench import importers, reference
from bench.store import Store

DATA = Path(__file__).parent / "data"
XLOG = (DATA / "bench_xlog_sample.txt").read_text()
DUMP = (DATA / "bench_dumplog_sample.txt").read_text()


def test_xlog_lines_with_tabs_and_colons():
    first = importers.parse_xlog_line(XLOG.splitlines()[0])
    assert first["name"] == "player1" and first["death"] == "ascended" and first["turns"] == "44867"
    old = importers.parse_xlog_line("version=3.4.3:name=x:death=ascended:turns=50000:starttime=1")
    assert old["turns"] == "50000"
    assert importers.parse_xlog_line("garbage without fields") is None


def test_achievements_from_names_or_3_6_bits():
    lines = [importers.parse_xlog_line(l) for l in XLOG.splitlines()]
    assert "entered_gehennom" in importers.achievements(lines[0])
    bits = importers.achievements(lines[1])  # 0xfff in NetHack 3.6
    assert {"obtained_the_bell_of_opening", "defeated_medusa", "ascended"} <= set(bits)
    assert importers.achievements(lines[2]) == []


def test_import_xlog_keeps_ascensions_once(tmp_path):
    store = Store(tmp_path / "r.db")
    fetch = lambda url, cache_dir=None: XLOG
    url = "https://www.hardfought.org/xlogfiles/nethack50/xlogfile"
    assert importers.import_xlog(store, url, fetcher=fetch) == {"lines": 3, "ascensions": 2, "added": 2}
    assert importers.import_xlog(store, url, fetcher=fetch)["added"] == 0
    refs = store.references()
    assert [r["source"] for r in refs] == ["hardfought", "hardfought"]
    assert "ascended" in refs[0]["record"]["achievements"]


def test_dumplog_url_and_import(tmp_path):
    store = Store(tmp_path / "r.db")
    importers.import_xlog(store, "https://www.hardfought.org/x", fetcher=lambda url, cache_dir=None: XLOG)
    importers.import_xlog(store, "https://example.org/xlogfile", fetcher=lambda url, cache_dir=None: XLOG)
    asked = []

    def fetch(url, cache_dir=None):
        asked.append(url)
        if "player2" in url:
            raise OSError("404")
        return DUMP

    out = importers.import_dumplogs(store, tmp_path / "cache", limit=10, fetcher=fetch)
    assert out == {"fetched": 1, "failed": 1, "unsupported": 2}
    assert asked[0] == "https://www.hardfought.org/userdata/p/player1/nethack/dumplog/1777773884.nh.txt"
    assert sum(r["dumplog"] is not None for r in store.references()) == 1


def test_fetch_caches_and_throttles(tmp_path, monkeypatch):
    calls = []

    class Response:
        def __init__(self, url):
            self.url = url
        def read(self):
            return b"body"
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(importers, "urlopen", lambda req, timeout: calls.append(req.full_url) or Response(req.full_url))
    sleeps = []
    monkeypatch.setattr(importers.time, "sleep", lambda s: sleeps.append(s))
    assert importers.fetch("https://a/1", tmp_path) == "body"
    assert importers.fetch("https://a/1", tmp_path) == "body"  # cached
    assert importers.fetch("https://a/2", tmp_path) == "body"
    assert calls == ["https://a/1", "https://a/2"] and sleeps and sleeps[-1] <= 1.0
    assert importers.fetch("https://a/3") == "body"  # no cache dir: always downloads


def test_parse_dumplog():
    d = importers.parse_dumplog(DUMP)
    assert d["ac"] == -38 and d["xl"] == 25
    assert d["reflection"] and d["magic_resistance"] and d["bag_of_holding"]
    assert d["wands"] == ["death", "digging", "teleportation"]
    assert d["events"][1] == (435, "entered the Gnomish Mines")
    assert d["events"][-1] == (59302, "ascended")
    assert d["vanquished"] == 1840
    assert "You used 2 wishes." in d["conducts"]


def test_reference_summary(tmp_path):
    store = Store(tmp_path / "r.db")
    importers.import_xlog(store, "https://www.hardfought.org/x", fetcher=lambda url, cache_dir=None: XLOG)
    store.set_dumplog(store.references()[0]["id"], DUMP)
    s = reference.summary(store.references())
    assert s["ascensions"] == 2 and s["with_dumplog"] == 1 and s["with_timeline"] == 1
    assert s["turns"]["median"] == pytest.approx((44867 + 37140) / 2)
    assert dict(s["roles"]) == {"Bar": 1, "Val": 1}
    events = [m["event"] for m in s["milestones"]]
    assert events.index("entered the Gnomish Mines") < events.index("entered Sokoban")
    assert "killed Famine" in events and "killed Famine (2nd time)" not in events
    assert s["reflection"] == 1.0 and s["ac"] == -38 and ("death", 1.0) in s["wands"]
    assert reference.summary([]) == {"ascensions": 0}
