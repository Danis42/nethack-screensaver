"""Bench server: application logic, JSON API, status page and the scheduler loop."""
import errno
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import gitrefs, report
from .filters import parse_where
from .metrics import METRICS, evaluate

STATIC = Path(__file__).with_name("static")
LOCAL_HOSTS = ("127.0.0.1", "localhost")


class App:
    def __init__(self, store, scheduler, repo, cache_dir):
        self.store, self.scheduler = store, scheduler
        self._yardstick = (None, {})
        self.repo, self.cache_dir = Path(repo), Path(cache_dir)
        self.lock = threading.RLock()
        self.imports = {"running": False, "last": None}

    def _sha(self, ref):
        return gitrefs.resolve(self.repo, ref)

    def status(self):
        with self.lock:
            return {**self.scheduler.status(), "import": dict(self.imports)}

    def start_baseline(self, ref="main", games=576):
        games = int(games)
        if games < 1:
            raise ValueError("games must be at least 1")
        sha, subject = self._sha(ref)
        with self.lock:
            return {"job_id": self.scheduler.submit(
                "baseline", {"ref": ref, "sha": sha, "subject": subject, "games": games})}

    def start_experiment(self, candidate, baseline="main", metric="dlvl6"):
        rates = [n for n, m in METRICS.items() if m.kind == "rate"]
        if metric not in rates:
            raise ValueError(f"metric must be one of {rates}")
        cand, cand_subject = self._sha(candidate)
        base, base_subject = self._sha(baseline)
        if cand == base:
            raise ValueError(f"{candidate} and {baseline} are the same commit {cand[:10]}")
        spec = {"candidate": cand, "candidate_ref": candidate, "candidate_subject": cand_subject,
                "baseline": base, "baseline_ref": baseline, "baseline_subject": base_subject,
                "metric": metric}
        with self.lock:
            return {"job_id": self.scheduler.submit("experiment", spec)}

    def stop(self, job_id=None):
        with self.lock:
            return {"stopped": self.scheduler.stop(job_id)}

    def job(self, job_id):
        job = self.store.job(int(job_id))
        if job is None:
            raise LookupError(f"no job {job_id}")
        if job["kind"] == "experiment":
            spec = job["spec"]
            n = min(self.store.count(spec["candidate"]), self.store.count(spec["baseline"]))
            job["table"] = report.compare(self.store.games(spec["candidate"], limit=n),
                                          self.store.games(spec["baseline"], limit=n))
            job["games_per_side"] = n
        return job

    def results(self, ref="main", metric=None):
        sha, subject = self._sha(ref)
        games = self.store.games(sha)
        if metric is not None:
            if metric not in METRICS:
                raise ValueError(f"unknown metric {metric!r}; known: {sorted(METRICS)}")
            return {"sha": sha, "metric": metric, **evaluate(METRICS[metric], games)}
        return {"sha": sha, "subject": subject, **report.summary(games, self.yardstick())}

    def games(self, ref="main", where=None, limit=50):
        sha, _ = self._sha(ref)
        match = parse_where(where)
        hits = [g for g in self.store.games(sha) if match(g)]
        return {"sha": sha, "matches": len(hits), "games": hits[:int(limit)]}

    def experiments(self):
        return self.store.jobs("experiment")

    def dashboard(self, ref="main"):
        for sha in gitrefs.history(self.repo, ref):
            if self.store.count(sha):
                return {"sha": sha, "subject": self._sha(sha)[1], **report.summary(self.store.games(sha), self.yardstick())}
        return {"sha": None, "games": 0}

    def yardstick(self):
        """Median first turn of each timeline event in the real ascensions (cached per import state)."""
        refs = self.store.references()
        state = (len(refs), sum(1 for r in refs if r["dumplog"]))
        if self._yardstick[0] != state:
            from . import reference
            milestones = reference.summary(refs).get("milestones", [])
            self._yardstick = (state, {m["event"]: m["median_turn"] for m in milestones})
        return self._yardstick[1]

    def reference_summary(self):
        from . import reference
        return reference.summary(self.store.references())

    def reference_games(self, where=None, limit=50):
        match = parse_where(where)
        hits = [r["record"] for r in self.store.references() if match(r["record"])]
        return {"matches": len(hits), "games": hits[:int(limit)]}

    def start_import(self, kind, url=None, limit=500):
        from . import importers
        if kind not in ("xlog", "dumplogs"):
            raise ValueError("kind must be xlog or dumplogs")
        if kind == "xlog" and not (url or "").startswith(("https://", "http://")):
            raise ValueError("an xlog import needs an http(s) url")
        with self.lock:
            if self.imports["running"]:
                raise ValueError("an import is already running")
            self.imports["running"] = True

        def run():
            try:
                if kind == "xlog":
                    out = importers.import_xlog(self.store, url)
                else:
                    out = importers.import_dumplogs(self.store, self.cache_dir, limit=int(limit))
                self.imports["last"] = {"kind": kind, **out}
            except Exception as e:  # shown on the page; the server keeps running
                self.imports["last"] = {"kind": kind, "error": str(e)}
            finally:
                self.imports["running"] = False

        threading.Thread(target=run, daemon=True).start()
        return {"started": kind}

    def loop(self, stop_event, interval=0.2):
        while not stop_event.is_set():
            with self.lock:
                try:
                    self.scheduler.tick()
                except Exception as e:  # keep serving; the error shows in status
                    self.scheduler.error = f"scheduler: {e!r}"
            stop_event.wait(interval)


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, body, content_type="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
            return body

        def _refused(self, write=False):
            """Keep web pages from other sites out: they can reach localhost from the browser."""
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if host not in LOCAL_HOSTS:
                self._send(403, {"error": "only http://localhost or http://127.0.0.1 may use the bench server"})
                return True
            if write and (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
                self._send(415, {"error": "send Content-Type: application/json"})
                return True
            return False

        def _handle(self, fn):
            try:
                self._send(200, fn())
            except LookupError as e:
                self._send(404, {"error": str(e)})
            except (ValueError, TypeError) as e:
                self._send(400, {"error": str(e)})

        def do_GET(self):
            if self._refused():
                return
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            path = url.path
            if path == "/":
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            routes = {
                "/api/status": app.status,
                "/api/results": lambda: app.results(q.get("ref", "main"), q.get("metric")),
                "/api/games": lambda: app.games(q.get("ref", "main"), q.get("where"), q.get("limit", 50)),
                "/api/experiments": app.experiments,
                "/api/dashboard": lambda: app.dashboard(q.get("ref", "main")),
                "/api/metrics": lambda: {n: {"description": m.description, "kind": m.kind}
                                         for n, m in METRICS.items()},
                "/api/reference/summary": app.reference_summary,
                "/api/reference/games": lambda: app.reference_games(q.get("where"), q.get("limit", 50)),
            }
            if path in routes:
                return self._handle(routes[path])
            if path.startswith("/api/jobs/"):
                return self._handle(lambda: app.job(path.rsplit("/", 1)[1]))
            self._send(404, {"error": f"no route {path}"})

        def do_POST(self):
            if self._refused(write=True):
                return
            path = urlparse(self.path).path
            if path == "/api/jobs":
                def start():
                    body = self._body()
                    kind = body.pop("kind", None)
                    if kind == "baseline":
                        return app.start_baseline(**body)
                    if kind == "experiment":
                        return app.start_experiment(**body)
                    raise ValueError("kind must be baseline or experiment")
                return self._handle(start)
            if path == "/api/import":
                return self._handle(lambda: app.start_import(**self._body()))
            self._send(404, {"error": f"no route {path}"})

        def do_DELETE(self):
            if self._refused(write=True):
                return
            path = urlparse(self.path).path
            if path == "/api/jobs":
                return self._handle(app.stop)
            if path.startswith("/api/jobs/"):
                return self._handle(lambda: app.stop(int(path.rsplit("/", 1)[1])))
            self._send(404, {"error": f"no route {path}"})

    return Handler


def serve(app, port=8765, host="127.0.0.1"):
    """Start listening and the scheduler loop; the caller runs httpd.serve_forever()."""
    try:
        httpd = ThreadingHTTPServer((host, port), make_handler(app))
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            raise SystemExit(f"port {port} is taken: a bench server is probably already running "
                             f"(http://{host}:{port})")
        raise
    stop = threading.Event()
    threading.Thread(target=app.loop, args=(stop,), daemon=True).start()
    return httpd, stop
