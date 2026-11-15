"""Code ratchets (CODE-04, D-15): measure line counts, bare `except:` and imports from autoascend.agent.

    uv run python scripts/ratchets.py measure   # JSON of today's numbers
    uv run python scripts/ratchets.py tighten   # lower tests/ratchets.json to today's numbers (never raises)

tests/test_ratchets.py fails when a number goes past its limit. Raising a limit is a visible edit of
tests/ratchets.json in a commit the owner sees.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIMITS = REPO / "tests" / "ratchets.json"
SIZE_DIRS = ("autoascend/", "nethack_screensaver/", "bench/", "scripts/")
IMPORT_DIRS = ("autoascend/", "nethack_screensaver/", "bench/")
NEW_FILE_CAP = 600


def tracked_python():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "*.py"], capture_output=True, text=True,
                         check=True).stdout.split()
    return sorted(p for p in out if p.startswith(SIZE_DIRS) and (REPO / p).exists())


def _imports_agent(path, node):
    """Names imported from autoascend.agent by one import node, or None if it is not such an import."""
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        absolute = module if not node.level else _resolve(path, node.level, module)
        if absolute == "autoascend.agent":
            return [a.name for a in node.names]
        if absolute == "autoascend" and any(a.name == "agent" for a in node.names):
            return ["<module>"]
    elif isinstance(node, ast.Import):
        if any(a.name == "autoascend.agent" for a in node.names):
            return ["<module>"]
    return None


def _resolve(path, level, module):
    parts = path[:-3].split("/")[:-1]  # package of the file
    base = parts[:len(parts) - (level - 1)] if level > 1 else parts
    return ".".join(base + ([module] if module else []))


def measure():
    lines, bare, agent = {}, {}, []
    for path in tracked_python():
        text = (REPO / path).read_text()
        lines[path] = len(text.splitlines())
        tree = ast.parse(text, filename=path)
        n = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None)
        if n:
            bare[path] = n
        if path.startswith(IMPORT_DIRS):
            for node in ast.walk(tree):
                names = _imports_agent(path, node)
                for name in names or ():
                    agent.append(f"{path}:{name}")
    return {"lines": lines, "bare_except": bare, "agent_imports": sorted(set(agent))}


def load():
    return json.loads(LIMITS.read_text())


def tighten():
    now, limits = measure(), load()
    # files pinned at the Phase 2 start only go down; files created later keep the new-file cap (D-15)
    limits["lines"] = {p: min(n, limits["lines"][p]) for p, n in now["lines"].items() if p in limits["lines"]}
    limits["bare_except"] = {p: min(n, limits["bare_except"].get(p, n)) for p, n in now["bare_except"].items()
                             if p in limits["bare_except"]}
    limits["agent_imports"] = sorted(set(limits["agent_imports"]) & set(now["agent_imports"]))
    LIMITS.write_text(json.dumps(limits, indent=1, sort_keys=True) + "\n")


def main(argv):
    if argv == ["measure"]:
        print(json.dumps(measure(), indent=1, sort_keys=True))
    elif argv == ["tighten"]:
        tighten()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
