"""Fingerprint of the environment that plays bench games.

The fingerprint says which NLE build (git commit of the fork), which lock file and which interpreter and
library versions produced a result, so a number can be traced back to what made it. The facts about the
worker are read by running a small probe in the worker interpreter itself; the bench server must never
load the game library, so this module is standard library only.
"""
import hashlib
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

# Run by the worker interpreter with -I -c; prints one JSON line.
WORKER_PROBE = """
import importlib.metadata as m, json, platform
try:
    url = json.loads(m.distribution("nle").read_text("direct_url.json"))
except (TypeError, ValueError):  # no direct_url.json
    url = {}
commit = url.get("vcs_info", {}).get("commit_id")
source = url.get("url") if "dir_info" in url else None  # built from a folder (vendor/nle)
print(json.dumps({"nle_commit": commit, "nle_source": source, "nle_version": m.version("nle"),
                  "python": platform.python_version(), "numpy": m.version("numpy"), "numba": m.version("numba")}))
"""

# What identifies an environment. The interpreter path is recorded in the fingerprint but is not part of
# the id: a fresh clone with the same lock and NLE commit must get the same id.
ENV_ID_FIELDS = ("nle_commit", "lock_sha256", "python", "numpy", "numba")


def folder_tree(path):
    """'tree:<git tree id>' of a committed folder, '+dirty' when it has uncommitted changes; None outside git.

    NLE built from the vendored folder has no commit of its own, so the folder's tree id identifies the build.
    """
    def git(*args):
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    tree = git("rev-parse", "--verify", "--quiet", "HEAD:./")
    if tree.returncode != 0:
        return None
    dirty = git("status", "--porcelain", "--", ".").stdout.strip()
    return "tree:" + tree.stdout.strip() + ("+dirty" if dirty else "")


def worker_facts(worker_python):
    """nle_commit, nle_version, python, numpy, numba as seen by the worker interpreter.

    For an NLE built from a folder, nle_commit is that folder's git tree id (folder_tree)."""
    try:
        r = subprocess.run([str(worker_python), "-I", "-c", WORKER_PROBE], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:  # no such interpreter, not executable, or it hung
        raise ValueError(f"cannot run worker interpreter {worker_python}: {e}") from e
    if r.returncode != 0:
        raise ValueError(f"worker interpreter {worker_python} failed: {r.stderr.strip()[-2000:]}")
    try:
        facts = json.loads(r.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError) as e:  # empty or non-JSON output
        raise ValueError(f"worker probe printed no JSON line: {r.stdout.strip()[-500:]!r}") from e
    source = facts.get("nle_source")
    if facts.get("nle_commit") is None and source and source.startswith("file://"):
        facts["nle_commit"] = folder_tree(urllib.parse.unquote(source[len("file://"):]))
    return facts


def lock_sha256(repo):
    return hashlib.sha256((Path(repo) / "uv.lock").read_bytes()).hexdigest()


def lock_blob(repo, sha):
    """Blob id of uv.lock at commit `sha`, or None when that commit has no uv.lock."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):  # no option injection through the argument
        raise ValueError(f"not a full commit sha: {sha!r}")
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{sha}:uv.lock"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def env_fingerprint(worker_python, repo):
    return {**worker_facts(worker_python), "lock_sha256": lock_sha256(repo), "worker_python": str(worker_python)}


def env_id(env):
    picked = json.dumps({k: env.get(k) for k in ENV_ID_FIELDS}, sort_keys=True)
    return hashlib.sha256(picked.encode()).hexdigest()[:16]
