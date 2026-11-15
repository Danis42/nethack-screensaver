"""Commit labels (CODE-02, D-14): one rule for the git hooks and the log test (standard library only).

Every commit carries a `Kind:` trailer:
- `Kind: docs` - documentation only (every path under .planning/ or ending in .md); added automatically.
- `Kind: refactor` - does not change how the bot plays. If it touches bot code (autoascend/, nethack_screensaver/)
  it names a passing refactor-gate job: `Gate: job <N>`.
- `Kind: behavior` - changes how the bot plays. If it touches bot code it names `Stage:` (the funnel stage it is
  meant to move), `Metric:` (a bench metric) and `Experiment: job <N>` (or `Experiment: pending` until the run).
"""
import re
import sys

KINDS = ("refactor", "behavior", "docs")
BOT_CODE = ("autoascend/", "nethack_screensaver/")
TRAILER = re.compile(r"^(Kind|Gate|Stage|Metric|Experiment):[ \t]*(.*?)[ \t]*$", re.M)
JOB = re.compile(r"^job \d+$")


def is_docs(path):
    return path.startswith(".planning/") or path.endswith(".md")


def trailers(message):
    return {key: value for key, value in TRAILER.findall(message)}


def _metrics():
    """Bench metric names, or None when bench is not importable (plain python3 in a hook)."""
    try:
        from bench.metrics import METRICS
    except Exception:  # bench, numpy or the repo path missing: accept any metric word
        return None
    return set(METRICS)


def check(message, paths):
    """List of errors; empty when the message labels this change correctly."""
    if message.startswith(("fixup! ", "squash! ", "Merge ")):
        return []
    t = trailers(message)
    kind = t.get("Kind")
    if kind not in KINDS:
        return [f"Kind: missing or not one of {', '.join(KINDS)} (got {kind!r})"]
    if kind == "docs":
        other = [p for p in paths if not is_docs(p)]
        return [f"Kind: docs only for documentation; not docs: {', '.join(other[:5])}"] if other else []
    if not any(p.startswith(BOT_CODE) for p in paths):
        return []
    errors = []
    if kind == "refactor" and not JOB.match(t.get("Gate", "")):
        errors.append("Gate: a refactor of bot code names its passing gate job ('Gate: job <N>')")
    if kind == "behavior":
        if not t.get("Stage"):
            errors.append("Stage: a behaviour change names the funnel stage it should move")
        metrics = _metrics()
        metric = t.get("Metric", "")
        if not metric or (metrics is not None and metric not in metrics):
            errors.append(f"Metric: name a bench metric (got {metric!r})")
        experiment = t.get("Experiment", "")
        if not (JOB.match(experiment) or experiment == "pending"):
            errors.append("Experiment: 'job <N>' or 'pending'")
    return errors


def with_docs_label(message, paths):
    """The message with 'Kind: docs' appended when it has no Kind and every path is documentation."""
    if "Kind" in trailers(message) or not paths or not all(is_docs(p) for p in paths):
        return message
    body = message.rstrip("\n")
    last = body.rsplit("\n\n", 1)[-1]
    joiner = "\n" if body and all(re.match(r"^[\w-]+: ", line) for line in last.splitlines()) else "\n\n"
    return f"{body}{joiner}Kind: docs\n"


if __name__ == "__main__":
    print("\n".join(check(sys.stdin.read(), sys.argv[1:])))
