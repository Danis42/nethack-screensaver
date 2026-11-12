import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "facts.py"


def _load():
    spec = importlib.util.spec_from_file_location("facts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


facts = _load()

GOOD = {"claim": "c", "tag": "5.0-source", "evidence": ["reference/nethack-5.0.0/src/x.c:1"], "quote": "q"}


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_repository_ledger_loads_and_checks_clean_against_the_code_tree():
    ledger = facts.load(ROOT / "facts" / "FACTS.toml")
    assert "sokoban-entry-is-bottom-level" in ledger
    assert facts.check(ledger, facts.citations(ROOT)) == []


def test_ladder_cites_the_first_fact():
    sites = facts.citations(ROOT)["sokoban-entry-is-bottom-level"]
    assert any(path.endswith("autoascend/ladder.py") for path, _ in sites)


@pytest.mark.parametrize("missing", ["evidence", "quote"])
def test_source_fact_without_evidence_or_quote_is_an_error(missing):
    entry = {k: v for k, v in GOOD.items() if k != missing}
    errors = facts.check({"some-fact": entry}, {})
    assert errors and all("some-fact" in e for e in errors)


def test_unknown_tag_is_an_error():
    errors = facts.check({"some-fact": {**GOOD, "tag": "folklore"}}, {})
    assert any("some-fact" in e and "tag" in e for e in errors)


@pytest.mark.parametrize("bad_id", ["Some-fact", "some_fact", "-lead"])
def test_badly_formed_ids_are_errors(bad_id):
    assert any(bad_id in e for e in facts.check({bad_id: GOOD}, {}))


def test_citation_of_a_missing_fact_names_file_and_line(tmp_path):
    _write(tmp_path / "autoascend" / "mod.py", "x = 1\ny = 5  # fact:no-such-fact\n")
    errors = facts.check({}, facts.citations(tmp_path))
    assert len(errors) == 1 and "no-such-fact" in errors[0] and "autoascend/mod.py:2" in errors[0]


def test_comment_can_cite_several_facts_and_notes_cite_with_brackets(tmp_path):
    _write(tmp_path / "bench" / "m.py", "z = 3  # fact:a, b\n")
    _write(tmp_path / ".planning" / "research" / "NOTE.md", "Sokoban [fact:a] and more.\n")
    cites = facts.citations(tmp_path)
    assert sorted(cites) == ["a", "b"]
    assert len(cites["a"]) == 2 and len(cites["b"]) == 1


def test_measured_fact_needs_job_or_query():
    base = {"claim": "c", "tag": "measured"}
    assert any("m" in e for e in facts.check({"m": base}, {}))
    assert facts.check({"m": {**base, "job": 12}}, {}) == []
    assert facts.check({"m": {**base, "query": "SELECT 1"}}, {}) == []
    assert facts.check({"m": {**base, "job": "12"}}, {}) != []


def test_unverified_fact_needs_web_list_and_notes_when_empty():
    base = {"claim": "c", "tag": "unverified"}
    assert facts.check({"u": base}, {}) != []
    assert facts.check({"u": {**base, "web": ["https://example.org"]}}, {}) == []
    assert facts.check({"u": {**base, "web": []}}, {}) != []
    assert facts.check({"u": {**base, "web": [], "notes": "nothing found on the wiki"}}, {}) == []
