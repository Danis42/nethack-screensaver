"""Resolve refs to commits and keep one git worktree per benchmarked commit."""
import os
import subprocess
import time
from pathlib import Path


def _git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError(r.stderr.strip() or f"git {' '.join(args)} failed")
    return r.stdout.strip()


def resolve(repo, ref):
    """(full sha, subject line) of a branch, tag or sha. Refs starting with "-" are refused before git sees them
    (they would be read as options)."""
    if str(ref).startswith("-"):
        raise ValueError("refs may not start with '-'")
    sha = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return sha, _git(repo, "log", "-1", "--format=%s", sha)


def history(repo, ref, limit=200):
    return _git(repo, "rev-list", f"--max-count={limit}", ref).split()


def ensure_worktree(repo, sha, root):
    path = Path(root) / sha
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "worktree", "add", "--detach", str(path), sha)
    os.utime(path)  # last use, for prune()
    return path


def prune(repo, root, max_age_days=14, now=None):
    now = time.time() if now is None else now
    removed = []
    root = Path(root)
    if root.exists():
        for path in sorted(root.iterdir()):
            if now - path.stat().st_mtime > max_age_days * 86400:
                _git(repo, "worktree", "remove", "--force", str(path))
                removed.append(path.name)
    _git(repo, "worktree", "prune")
    return removed
