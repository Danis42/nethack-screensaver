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


# Task 2: source quotes, unverified report, coverage

SRC = "line one\n    if (x < 0) {\n        y =\n            z + 1;\n    }\nlast line\n"


@pytest.fixture
def src_repo(tmp_path):
    _write(tmp_path / "reference" / "nethack-5.0.0" / "src" / "f.c", SRC)
    return tmp_path


def _src_fact(evidence, quote="if (x < 0) { y = z + 1;"):
    return {"f": {"claim": "c", "tag": "5.0-source", "evidence": evidence, "quote": quote}}


def test_quote_inside_the_cited_range_passes(src_repo):
    assert facts.check_sources(_src_fact(["reference/nethack-5.0.0/src/f.c:2-4"]), src_repo) == []


def test_quote_outside_the_cited_range_is_an_error(src_repo):
    errors = facts.check_sources(_src_fact(["reference/nethack-5.0.0/src/f.c:5-6"]), src_repo)
    assert errors and "quote" in errors[0]


def test_range_past_the_end_of_file_is_an_error(src_repo):
    errors = facts.check_sources(_src_fact(["reference/nethack-5.0.0/src/f.c:2-40"]), src_repo)
    assert errors and "past the end" in errors[0]


def test_missing_file_is_an_error(src_repo):
    errors = facts.check_sources(_src_fact(["reference/nethack-5.0.0/src/nope.c:1"]), src_repo)
    assert errors and "missing" in errors[0]


def test_quote_found_in_one_of_several_ranges_passes_but_every_range_must_exist(src_repo):
    ok = _src_fact(["reference/nethack-5.0.0/src/f.c:1", "reference/nethack-5.0.0/src/f.c:2-4"])
    assert facts.check_sources(ok, src_repo) == []
    bad = _src_fact(["reference/nethack-5.0.0/src/f.c:2-4", "reference/nethack-5.0.0/src/f.c:99"])
    assert facts.check_sources(bad, src_repo) != []


@pytest.mark.parametrize("evidence", [
    "/etc/passwd:1",
    "reference/nethack-5.0.0/../../etc/passwd:1",
    "autoascend/agent.py:1",
])
def test_paths_outside_the_allowed_roots_are_refused(src_repo, evidence):
    errors = facts.check_sources(_src_fact([evidence]), src_repo)
    assert errors and "refused" in errors[0]


def test_report_lists_only_cited_unverified_facts_with_their_sites():
    ledger = {
        "u-cited": {"claim": "c", "tag": "unverified", "web": ["https://x"]},
        "u-uncited": {"claim": "c", "tag": "unverified", "web": ["https://x"]},
        "s-cited": {"claim": "c", "tag": "5.0-source", "evidence": ["e:1"], "quote": "q"},
    }
    cites = {"u-cited": [("autoascend/a.py", 3)], "s-cited": [("autoascend/b.py", 4)]}
    assert facts.report(ledger, cites) == [
        {"id": "u-cited", "claim": "c", "sites": ["autoascend/a.py:3"]}]


def test_coverage_counts_literals_citations_and_unverified_marks(tmp_path):
    _write(tmp_path / "autoascend" / "a.py", "A = 200\nB = 1\nC = -1  # fact:x\nD = 0.5\nE = 2\n")
    _write(tmp_path / "autoascend" / "b.py", "X = 7\nY = 9\n")
    _write(tmp_path / ".planning" / "research" / "N.md", "UNVERIFIED claim. [fact:x] unverified again.\n")
    result = facts.coverage(tmp_path)
    by_path = {f["path"]: f for f in result["files"]}
    assert by_path["autoascend/a.py"]["literals"] == 2 and by_path["autoascend/a.py"]["citations"] == 1
    assert by_path["autoascend/b.py"] == {"path": "autoascend/b.py", "literals": 2, "citations": 0}
    assert result["files"][0]["path"] == "autoascend/b.py"
    assert result["notes"][0] == {"path": ".planning/research/N.md", "citations": 1, "unverified": 2}
    assert result["totals"] == {"files": 2, "literals": 4, "citations": 1}


@pytest.mark.skipif(not (ROOT / "reference" / "nethack-5.0.0").exists(), reason="reference/ not present")
def test_repository_ledger_quotes_are_found_in_the_5_0_source():
    assert facts.check_sources(facts.load(ROOT / "facts" / "FACTS.toml"), ROOT) == []
