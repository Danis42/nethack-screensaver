"""Identify an NLE built from a folder (vendor/nle) rather than from a git commit.

A folder build has no commit of its own, so the git tree id of the folder stands in for it. Standard library
only, like bench/provenance.py.
"""
import subprocess
import urllib.parse


def folder_tree(path):
    """'tree:<git tree id>' of a committed folder, '+dirty' when it has uncommitted edits; None outside git."""
    def git(*args):
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    tree = git("rev-parse", "--verify", "--quiet", "HEAD:./")
    if tree.returncode != 0:
        return None
    dirty = git("status", "--porcelain", "--", ".").stdout.strip()
    return "tree:" + tree.stdout.strip() + ("+dirty" if dirty else "")


def with_folder_commit(facts):
    """Fill nle_commit from the build folder when the worker probe found no git commit."""
    source = facts.get("nle_source")
    if facts.get("nle_commit") is None and source and source.startswith("file://"):
        facts["nle_commit"] = folder_tree(urllib.parse.unquote(source[len("file://"):]))
    return facts
