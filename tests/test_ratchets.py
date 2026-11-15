"""Code ratchets (CODE-04, D-15): no file grows, no new bare `except:`, no new imports from autoascend.agent.

Limits are in tests/ratchets.json; `scripts/ratchets.py tighten` lowers them after code shrinks."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ratchets  # noqa: E402

if not (ratchets.REPO / ".git").exists():
    pytest.skip("ratchets read git ls-files", allow_module_level=True)

NOW = ratchets.measure()
LIMITS = ratchets.load()


def test_no_file_grows():
    cap = LIMITS["new_file_cap"]
    over = {p: f"{n} > {LIMITS['lines'].get(p, cap)}" for p, n in NOW["lines"].items()
            if n > LIMITS["lines"].get(p, cap)}
    assert not over, f"files past their line limit (tests/ratchets.json; new files: {cap}): {over}"


def test_no_new_bare_except():
    over = {p: f"{n} > {LIMITS['bare_except'].get(p, 0)}" for p, n in NOW["bare_except"].items()
            if n > LIMITS["bare_except"].get(p, 0)}
    assert not over, f"new bare 'except:' (catch a named exception instead): {over}"


def test_no_new_imports_of_agent_internals():
    new = sorted(set(NOW["agent_imports"]) - set(LIMITS["agent_imports"]))
    assert not new, f"new imports from autoascend.agent outside tests/scripts: {new}"


def test_relative_imports_resolve():
    assert ratchets._resolve("autoascend/combat/fight_heur.py", 2, "agent") == "autoascend.agent"
    assert ratchets._resolve("autoascend/env_wrapper.py", 1, "agent") == "autoascend.agent"
