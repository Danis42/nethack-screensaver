"""screens-bench: run the bench server, wait for jobs, prune worktrees, import data."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from . import gitrefs
from .runner import ProcessWorker
from .scheduler import Scheduler
from .server import App, serve
from .store import END_STATES, Store

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("SCREENS_BENCH_DATA", "~/.local/share/screens-bench")).expanduser()
CACHE = Path(os.environ.get("SCREENS_BENCH_CACHE", "~/.cache/screens-bench")).expanduser()
URL = os.environ.get("SCREENS_BENCH_URL", "http://127.0.0.1:8765")
# the Python that plays the games (its NLE decides the NetHack version), e.g. the NetHack 5 venv
WORKER_PYTHON = Path(os.environ.get("SCREENS_BENCH_PYTHON", sys.executable)).expanduser()


def build_app(workers=11, data_dir=DATA, cache_dir=CACHE):
    data_dir, cache_dir = Path(data_dir), Path(cache_dir)
    store = Store(data_dir / "results.db")
    store.interrupt_unfinished()

    def spawn(sha):
        worktree = gitrefs.ensure_worktree(REPO, sha, cache_dir / "worktrees")
        return ProcessWorker(WORKER_PYTHON, worktree, data_dir / "worker.log")

    return App(store, Scheduler(store, spawn, slots=workers), REPO, cache_dir)


def _serve(args):
    app = build_app(args.workers, args.data, args.cache)
    httpd, stop = serve(app, port=args.port)
    print(f"bench server on http://127.0.0.1:{args.port} ({args.workers} workers)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        with app.lock:
            app.scheduler.shutdown()
        httpd.server_close()
    return 0


def _wait(args):
    while True:
        try:
            with urlopen(f"{args.url}/api/jobs/{args.job}", timeout=30) as r:
                job = json.loads(r.read())
        except URLError as e:
            print(f"bench server not reachable at {args.url}: {e}")
            return 2
        if job["state"] in END_STATES:
            print(json.dumps({k: job.get(k) for k in ("id", "kind", "state", "spec", "result")}, indent=1))
            return 1 if job["state"] == "failed" else 0
        time.sleep(args.every)


def _prune(args):
    removed = gitrefs.prune(REPO, Path(args.cache) / "worktrees", max_age_days=args.days)
    print(f"removed {len(removed)} worktrees")
    return 0


def _import(args):
    store = Store(Path(args.data) / "results.db")
    if args.what == "results":
        sha, _ = gitrefs.resolve(REPO, args.ref)
        n = 0
        with open(args.source) as f:
            for line in f:
                if line.strip():
                    store.add_game(sha, None, json.loads(line))
                    n += 1
        print(f"stored {n} games under {sha[:10]}")
        return 0
    from . import importers
    if args.what == "xlog":
        out = importers.import_xlog(store, args.source)
    else:
        out = importers.import_dumplogs(store, Path(args.cache), limit=args.limit)
    print(json.dumps(out))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="screens-bench")
    ap.add_argument("--data", default=str(DATA), help="directory of results.db and logs")
    ap.add_argument("--cache", default=str(CACHE), help="directory of worktrees and downloads")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve", help="run the bench server")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--workers", type=int, default=11)
    p.set_defaults(fn=_serve)

    p = sub.add_parser("wait", help="block until a job ends, then print it")
    p.add_argument("job", type=int)
    p.add_argument("--url", default=URL)
    p.add_argument("--every", type=float, default=5.0)
    p.set_defaults(fn=_wait)

    p = sub.add_parser("prune", help="remove worktrees unused for some days")
    p.add_argument("--days", type=int, default=14)
    p.set_defaults(fn=_prune)

    p = sub.add_parser("import", help="import benchmark files, xlogfiles or dumplogs")
    p.add_argument("what", choices=["results", "xlog", "dumplogs"])
    p.add_argument("source", nargs="?", help="results: a .jsonl file; xlog: a URL")
    p.add_argument("--ref", default="main", help="results: commit the games were played on")
    p.add_argument("--limit", type=int, default=500, help="dumplogs: at most this many downloads")
    p.set_defaults(fn=_import)

    args = ap.parse_args(argv)
    if args.command == "import" and args.what in ("results", "xlog") and not args.source:
        ap.error(f"import {args.what} needs a source")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
