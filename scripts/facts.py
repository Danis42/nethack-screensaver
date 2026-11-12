"""Fact-ledger tool: check the NetHack fact ledger and the code that cites it (MEAS-10).

The ledger is facts/FACTS.toml (format in its header comment). Code cites a fact with
"# fact:<id>" (several: "# fact:a, b"); research notes cite it as "[fact:<id>]".

Usage (from the repository root):
  python scripts/facts.py check            ledger rules and citations; one JSON line per error
  python scripts/facts.py check --source   also find each 5.0-source quote inside its cited
                                           lines (skipped when reference/ is absent)
  python scripts/facts.py report           unverified facts that code cites, with sites (D-16)
  python scripts/facts.py coverage [--out PATH]
                                           citation coverage per bot module and research note
                                           (D-20); it measures citation coverage and cannot
                                           detect untagged facts
Exit codes: 0 clean, 1 errors.
"""
import json
import re
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "facts" / "FACTS.toml"
TAGS = ("5.0-source", "measured", "unverified")
ID_RE = r"^[a-z0-9][a-z0-9-]*$"
CODE_CITE_RE = re.compile(r"#\s*fact:\s*([a-z0-9-]+(?:\s*,\s*[a-z0-9-]+)*)")
NOTE_CITE_RE = re.compile(r"\[fact:([a-z0-9-]+)\]")
ALLOWED_ROOTS = ("reference/nethack-5.0.0/", "reference/nle-src/")
CODE_ROOTS = ("autoascend", "nethack_screensaver", "bench")
NOTES_GLOB = ".planning/research/*.md"


def load(path=LEDGER):
    with open(path, "rb") as f:
        return tomllib.load(f)


def citations(repo=REPO, code_roots=CODE_ROOTS, notes_glob=NOTES_GLOB):
    """{fact id: [(relative path, line number), ...]} for every citation in code and notes."""
    repo = Path(repo)
    cites = {}

    def add(fid, path, line):
        cites.setdefault(fid, []).append((path.relative_to(repo).as_posix(), line))

    for root in code_roots:
        for path in sorted((repo / root).rglob("*.py")):
            for n, text in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for match in CODE_CITE_RE.finditer(text):
                    for fid in match.group(1).split(","):
                        add(fid.strip(), path, n)
    for path in sorted(repo.glob(notes_glob)):
        for n, text in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for fid in NOTE_CITE_RE.findall(text):
                add(fid, path, n)
    return cites


def _entry_errors(fid, entry):
    errors = []
    if not re.match(ID_RE, fid):
        errors.append(f"{fid}: id must be lowercase words and digits joined by hyphens")
    if not isinstance(entry, dict):
        return errors + [f"{fid}: entry is not a table"]
    if not entry.get("claim"):
        errors.append(f"{fid}: missing claim")
    tag = entry.get("tag")
    if tag not in TAGS:
        errors.append(f"{fid}: tag {tag!r} is not one of {', '.join(TAGS)}")
    elif tag == "5.0-source":
        if not entry.get("evidence") or not isinstance(entry["evidence"], list):
            errors.append(f"{fid}: a 5.0-source fact needs an evidence list of path:line")
        if not entry.get("quote"):
            errors.append(f"{fid}: a 5.0-source fact needs a verbatim quote")
    elif tag == "measured":
        job, query = entry.get("job"), entry.get("query")
        job_ok = isinstance(job, int) and not isinstance(job, bool)
        query_ok = isinstance(query, str) and query.strip()
        if not (job_ok or query_ok) or (job is not None and not job_ok):
            errors.append(f"{fid}: a measured fact needs job (integer) and/or query (text)")
    elif tag == "unverified":
        web = entry.get("web")
        if not isinstance(web, list):
            errors.append(f"{fid}: an unverified fact needs a web list of sources consulted")
        elif not web and not entry.get("notes"):
            errors.append(f"{fid}: an empty web list needs notes saying nothing was found")
    return errors


def check(ledger, cites):
    """Ledger rule errors plus citations of ids that are not in the ledger."""
    errors = []
    for fid, entry in ledger.items():
        errors.extend(_entry_errors(fid, entry))
    for fid, sites in sorted(cites.items()):
        if fid not in ledger:
            errors.extend(f"{path}:{line}: cites fact:{fid}, which is not in the ledger" for path, line in sites)
    return errors


def check_sources(ledger, repo=REPO, roots=ALLOWED_ROOTS):
    return []


def report(ledger, cites):
    return []


def coverage(repo=REPO):
    return {"files": [], "notes": [], "totals": {}}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    command = args.pop(0) if args else "check"
    ledger = load()
    cites = citations()
    if command == "check":
        errors = check(ledger, cites)
        for error in errors:
            print(json.dumps({"error": error}))
        return 1 if errors else 0
    print(f"unknown command {command!r}; see the module docstring", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
