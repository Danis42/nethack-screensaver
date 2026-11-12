"""Check that a fresh clone of this repository installs and works without the gitignored reference/ directory.

Usage: uv run python scripts/fresh_clone_check.py [--dest DIR] [--ref REF]

Clones this repository into DEST (default: a new temporary directory), checks out REF (default HEAD),
asserts there is no reference/ directory, runs `uv sync --locked` and a few tests there, then reads the
NLE commit from the clone's interpreter. Prints one JSON line {"dest", "sha", "nle_commit", "env_id", "tests"}.
Exit 0: every step passed. Exit 1: a step failed (its name is printed to stderr).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bench.gitrefs import resolve  # noqa: E402
from bench.provenance import env_fingerprint, env_id, worker_facts  # noqa: E402

TESTS = ["tests/test_imports.py", "tests/test_bench_provenance.py"]


def step(name, cmd, cwd=None, env=None):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"fresh_clone_check: step '{name}' failed (exit {r.returncode})\n{(r.stdout + r.stderr)[-3000:]}",
              file=sys.stderr)
        sys.exit(1)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dest", help="directory for the clone (default: a new temporary directory)")
    ap.add_argument("--ref", help="ref to check out (default: HEAD of this repository)")
    args = ap.parse_args(argv)

    sha, _ = resolve(REPO, args.ref or "HEAD")
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="screens-fresh-"))
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}

    step("git clone", ["git", "clone", "-q", str(REPO), str(dest)])
    step("git checkout", ["git", "-C", str(dest), "checkout", "-q", "--detach", sha])
    if (dest / "reference").exists():
        print("fresh_clone_check: step 'no reference dir' failed: the clone has a reference/ directory",
              file=sys.stderr)
        return 1
    step("uv sync --locked", ["uv", "sync", "--locked"], cwd=dest, env=env)
    step("tests", ["uv", "run", "--locked", "python", "-m", "pytest", "-q", *TESTS], cwd=dest, env=env)
    python = dest / ".venv" / "bin" / "python"
    try:
        facts = worker_facts(python)
        fingerprint = env_fingerprint(python, dest)
    except ValueError as e:  # the clone's interpreter cannot report its NLE build
        print(f"fresh_clone_check: step 'worker_facts' failed: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"dest": str(dest), "sha": sha, "nle_commit": facts["nle_commit"],
                      "env_id": env_id(fingerprint), "tests": "passed"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
