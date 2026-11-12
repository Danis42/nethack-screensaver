import hashlib
import re
import subprocess
import sys

import pytest

from bench.provenance import ENV_ID_FIELDS, env_fingerprint, env_id, lock_blob, lock_sha256, worker_facts

PINNED_NLE = "cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72"


def _env(**changes):
    env = {"nle_commit": PINNED_NLE, "lock_sha256": "ab" * 32, "python": "3.13.1", "numpy": "2.5.4",
           "numba": "0.68.0", "nle_version": "1.3.1.dev21", "worker_python": "/a/venv/bin/python"}
    env.update(changes)
    return env


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _repo_with_lock(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "f.txt").write_text("no lock yet")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "without lock")
    (repo / "uv.lock").write_text("version = 1\n")
    _git(repo, "add", "uv.lock")
    _git(repo, "commit", "-q", "-m", "with lock")
    return repo


def _sha(repo, ref):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", ref], check=True, capture_output=True,
                          text=True).stdout.strip()


def test_env_id_is_sixteen_hex_and_ignores_the_interpreter_path():
    a = env_id(_env(worker_python="/a/venv/bin/python"))
    b = env_id(_env(worker_python="/fresh/clone/.venv/bin/python", nle_version="other label"))
    assert re.fullmatch(r"[0-9a-f]{16}", a)
    assert a == b


def test_env_id_changes_when_the_nle_commit_changes():
    assert env_id(_env()) != env_id(_env(nle_commit="0" * 40))


def test_env_id_fields_name_what_identifies_an_environment():
    assert ENV_ID_FIELDS == ("nle_commit", "lock_sha256", "python", "numpy", "numba")


def test_lock_blob_is_the_blob_id_where_the_commit_has_a_lock_and_none_where_it_has_none(tmp_path):
    repo = _repo_with_lock(tmp_path)
    with_lock, without_lock = _sha(repo, "HEAD"), _sha(repo, "HEAD~1")
    assert lock_blob(repo, with_lock) == _sha(repo, "HEAD:uv.lock")
    assert re.fullmatch(r"[0-9a-f]{40}", lock_blob(repo, with_lock))
    assert lock_blob(repo, without_lock) is None


@pytest.mark.parametrize("bad", ["--help", "HEAD", "a" * 39, "A" * 40, "a" * 41, ""])
def test_lock_blob_rejects_anything_but_a_full_lowercase_hex_sha(tmp_path, bad):
    repo = _repo_with_lock(tmp_path)
    with pytest.raises(ValueError):
        lock_blob(repo, bad)


def test_lock_sha256_hashes_the_file_bytes(tmp_path):
    (tmp_path / "uv.lock").write_bytes(b"version = 1\nrevision = 3\n")
    assert lock_sha256(tmp_path) == hashlib.sha256(b"version = 1\nrevision = 3\n").hexdigest()


def test_worker_facts_reads_the_nle_commit_and_versions_from_the_interpreter():
    facts = worker_facts(sys.executable)
    assert facts["nle_commit"] == PINNED_NLE
    for key in ("python", "numpy", "numba", "nle_version"):
        assert facts[key]


def test_worker_facts_raises_value_error_carrying_the_stderr_of_a_broken_interpreter(tmp_path):
    broken = tmp_path / "python"
    broken.write_text("#!/bin/sh\necho 'boom from the probe' >&2\nexit 3\n")
    broken.chmod(0o755)
    with pytest.raises(ValueError, match="boom from the probe"):
        worker_facts(broken)


def test_worker_facts_raises_value_error_for_a_path_that_is_not_there(tmp_path):
    with pytest.raises(ValueError):
        worker_facts(tmp_path / "no-such-python")


def test_env_fingerprint_adds_the_lock_hash_and_the_interpreter_path(tmp_path):
    (tmp_path / "uv.lock").write_bytes(b"version = 1\n")
    env = env_fingerprint(sys.executable, tmp_path)
    assert env["lock_sha256"] == lock_sha256(tmp_path)
    assert env["worker_python"] == sys.executable
    assert env["nle_commit"] == PINNED_NLE
