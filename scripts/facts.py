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
import ast
import json
import re
import sqlite3
import sys
import tokenize
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


_EVIDENCE_RE = re.compile(r"^(?P<path>.+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def _normalise(text):
    return " ".join(text.split())


def check_sources(ledger, repo=REPO, roots=ALLOWED_ROOTS):
    """Errors for 5.0-source facts whose quote is not inside any cited line range."""
    repo = Path(repo)
    errors = []
    for fid, entry in ledger.items():
        if not isinstance(entry, dict) or entry.get("tag") != "5.0-source":
            continue
        quote = _normalise(entry.get("quote") or "")
        found = False
        for item in entry.get("evidence") or []:
            match = _EVIDENCE_RE.match(str(item))
            if not match:
                errors.append(f"{fid}: evidence {item!r} is not path:line or path:start-end")
                continue
            path = match["path"]
            if path.startswith("/") or ".." in Path(path).parts or not path.startswith(roots):
                errors.append(f"{fid}: evidence path {path!r} refused (absolute, '..' or outside {', '.join(roots)})")
                continue
            file = repo / path
            if not file.is_file():
                errors.append(f"{fid}: evidence file {path} is missing")
                continue
            lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
            first, last = int(match["start"]), int(match["end"] or match["start"])
            if first < 1 or last < first or last > len(lines):
                errors.append(f"{fid}: {item} is past the end of {path} ({len(lines)} lines)")
                continue
            if quote and quote in _normalise(" ".join(lines[first - 1:last])):
                found = True
        if quote and not found and not any(e.startswith(f"{fid}:") for e in errors):
            errors.append(f"{fid}: quote not found in any cited line range")
    return errors


def report(ledger, cites):
    """Unverified facts that code or notes cite, with their citation sites (D-16)."""
    return [{"id": fid, "claim": entry.get("claim"), "sites": [f"{p}:{n}" for p, n in cites[fid]]}
            for fid, entry in sorted(ledger.items())
            if isinstance(entry, dict) and entry.get("tag") == "unverified" and cites.get(fid)]


def _literals(path):
    count = 0
    with open(path, "rb") as f:
        try:
            for token in tokenize.tokenize(f.readline):
                if token.type == tokenize.NUMBER:
                    try:
                        value = ast.literal_eval(token.string)
                    except (ValueError, SyntaxError):  # odd literal forms still count
                        value = None
                    if value not in (0, 1, 2) or isinstance(value, complex):
                        count += 1
        except (tokenize.TokenError, SyntaxError):  # unparsable file: count what was read
            pass
    return count


def coverage(repo=REPO):
    """Citation coverage (D-20): game-number literals vs fact citations per bot module, and
    fact citations vs "unverified" marks per research note. This measures citation
    coverage only; it cannot tell which literals are NetHack facts or detect untagged facts."""
    repo = Path(repo)
    files = []
    for path in sorted((repo / "autoascend").rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        cites = sum(len(m.group(1).split(",")) for m in CODE_CITE_RE.finditer(text))
        files.append({"path": path.relative_to(repo).as_posix(), "literals": _literals(path), "citations": cites})
    files.sort(key=lambda f: (-(f["literals"] - f["citations"]), f["path"]))
    notes = []
    for path in sorted(repo.glob(NOTES_GLOB)):
        text = path.read_text(encoding="utf-8", errors="replace")
        notes.append({"path": path.relative_to(repo).as_posix(), "citations": len(NOTE_CITE_RE.findall(text)),
                      "unverified": len(re.findall(r"unverified", text, re.I))})
    totals = {"files": len(files), "literals": sum(f["literals"] for f in files),
              "citations": sum(f["citations"] for f in files)}
    return {"files": files, "notes": notes, "totals": totals}


def _check_measured_jobs(ledger):
    """Notices and errors for measured facts that cite a job (read-only lookup)."""
    db = Path.home() / ".local/share/screens-bench/results.db"
    errors = []
    jobs = [(fid, e["job"]) for fid, e in ledger.items() if isinstance(e, dict) and e.get("tag") == "measured"
            and isinstance(e.get("job"), int)]
    if not jobs:
        return errors
    if not db.exists():
        print(f"notice: {db} not present; measured job ids not checked", file=sys.stderr)
        return errors
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        for fid, job in jobs:
            if con.execute("SELECT 1 FROM jobs WHERE id = ?", (job,)).fetchone() is None:
                errors.append(f"{fid}: job {job} does not exist in {db}")
    finally:
        con.close()
    return errors

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    command = args.pop(0) if args else "check"
    ledger = load()
    cites = citations()
    if command == "check":
        errors = check(ledger, cites) + _check_measured_jobs(ledger)
        if "--source" in args:
            if (REPO / "reference").is_dir():
                errors += check_sources(ledger)
            else:
                print("source check skipped: reference/ not present")
        for error in errors:
            print(json.dumps({"error": error}))
        return 1 if errors else 0
    if command == "report":
        rows = report(ledger, cites)
        for row in rows:
            print(json.dumps(row))
        print(json.dumps({"unverified_cited": len(rows)}))
        return 0
    if command == "coverage":
        result = coverage()
        if "--out" in args:
            Path(args[args.index("--out") + 1]).write_text(json.dumps(result, indent=1) + "\n")
        for row in result["files"] + result["notes"]:
            print(json.dumps(row))
        print(json.dumps(result["totals"]))
        return 0
    print(f"unknown command {command!r}; see the module docstring", file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())
