import subprocess
import time

import pytest

from bench import gitrefs


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    for text in ("one", "two"):
        (repo / "f.txt").write_text(text)
        _git(repo, "add", "f.txt")
        _git(repo, "commit", "-q", "-m", f"commit {text}")
    return repo


def test_resolve_gives_full_sha_and_subject(repo):
    sha, subject = gitrefs.resolve(repo, "main")
    assert len(sha) == 40 and subject == "commit two"
    assert gitrefs.resolve(repo, sha[:8])[0] == sha
    with pytest.raises(ValueError):
        gitrefs.resolve(repo, "no-such-branch")


def test_history_is_newest_first(repo):
    shas = gitrefs.history(repo, "main")
    assert len(shas) == 2 and shas[0] == gitrefs.resolve(repo, "main")[0]


def test_worktree_is_created_once_at_the_commit(repo, tmp_path):
    old = gitrefs.resolve(repo, "main~1")[0]
    path = gitrefs.ensure_worktree(repo, old, tmp_path / "wt")
    assert (path / "f.txt").read_text() == "one"
    assert gitrefs.ensure_worktree(repo, old, tmp_path / "wt") == path


def test_prune_removes_only_old_worktrees(repo, tmp_path):
    a = gitrefs.resolve(repo, "main~1")[0]
    b = gitrefs.resolve(repo, "main")[0]
    gitrefs.ensure_worktree(repo, a, tmp_path / "wt")
    gitrefs.ensure_worktree(repo, b, tmp_path / "wt")
    assert gitrefs.prune(repo, tmp_path / "wt", now=time.time()) == []
    assert sorted(gitrefs.prune(repo, tmp_path / "wt", now=time.time() + 15 * 86400)) == sorted([a, b])
    assert not (tmp_path / "wt" / a).exists()


def test_refs_starting_with_a_dash_are_refused_before_git(repo, monkeypatch):
    def no_git(*args, **kwargs):
        raise AssertionError("git ran")
    monkeypatch.setattr(gitrefs, "_git", no_git)
    for ref in ("--output=/tmp/x", "-n1"):
        with pytest.raises(ValueError, match="may not start with '-'"):
            gitrefs.resolve(repo, ref)
