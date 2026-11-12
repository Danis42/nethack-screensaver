"""Tool runs (staged, scenario, rewind games) recorded with job IDs in tool_games, never in games.

Tool runs are research tools: wizard-mode stages, scripted scenarios and rewinds are not natural games, so their
results must never reach the natural rates, the funnel or the dashboard (MEAS-08). Recording them as jobs gives each
run a job ID that a progress claim can cite; job IDs share one sequence with natural jobs. Tool-run seeds must lie in
the reserved tool block 0-999 (D-17).
"""
import re
import subprocess
from pathlib import Path

from . import gitrefs, seeds
from .seeds import TOOL_KINDS
from .store import Store

__all__ = ["TOOL_KINDS", "open_store", "record_run", "add_result", "finish", "clean_sha"]


def open_store(data_dir=None):
    if data_dir is None:
        from .cli import DATA
        data_dir = DATA
    return Store(Path(data_dir) / "results.db")


def clean_sha(tree):
    """Full sha of the checkout at `tree`; ValueError when it has uncommitted changes (results must map to a commit)."""
    status = subprocess.run(["git", "-C", str(tree), "status", "--porcelain", "--untracked-files=no"],
                            capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise ValueError(f"{tree} has uncommitted changes; commit them before recording a tool run")
    return gitrefs.resolve(tree, "HEAD")[0]


def record_run(store, tool, sha, spec):
    """Create a running job of kind `tool` for a tool run; returns its id."""
    if tool not in TOOL_KINDS:
        raise ValueError(f"tool must be one of {TOOL_KINDS}, got {tool!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        raise ValueError(f"sha must be a full 40-hex commit, got {sha!r}")
    for seed in spec.get("seeds", ()):
        seeds.check_seed(seed, tool)
    job_id = store.add_job(tool, {**spec, "tool": tool, "sha": sha})
    store.set_job(job_id, "running")
    return job_id


def add_result(store, job_id, tool, sha, result):
    return store.add_tool_game(job_id, tool, sha, result)


def finish(store, job_id, state="done", result=None):
    store.set_job(job_id, state, result)
