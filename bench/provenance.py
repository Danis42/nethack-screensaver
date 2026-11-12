"""Placeholder so the RED run fails on assertions, not on import."""
ENV_ID_FIELDS = ()


def worker_facts(worker_python):
    return {}


def lock_sha256(repo):
    return ""


def lock_blob(repo, sha):
    return ""


def env_fingerprint(worker_python, repo):
    return {}


def env_id(env):
    return ""
