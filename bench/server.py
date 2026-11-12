"""Bench server: application logic, JSON API, status page and the scheduler loop."""
import errno
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import funnel as funnel_mod, gitrefs, provenance, report, seeds
from .filters import parse_where
from .metrics import METRICS, evaluate
from .stats import CHECKPOINTS

STATIC = Path(__file__).with_name("static")
LOCAL_HOSTS = ("127.0.0.1", "localhost")
KINDS_OVER_HTTP = ("baseline", "experiment")  # clean_attempt jobs (final seeds) are never created here


def funnel_for(store, repo, ref="main", lo=None, hi=None, lgen=None, env_id=None, job=None):
    """Funnel of one commit's natural games (rep 0) in a seed window, lgen mode and env (MEAS-02).

    With `job`, the commit, window, lgen mode and env come from that baseline job's spec. Otherwise the window
    defaults to the baseline window and lgen to seeds.USE_LGEN; env_id None reads every env. Windows that touch
    the tool block 0-999 are refused: tool seeds are never judged (D-17)."""
    if job is not None:
        spec_job = store.job(int(job))
        if spec_job is None:
            raise LookupError(f"no job {job}")
        if spec_job["kind"] != "baseline" or "seeds" not in spec_job["spec"]:
            raise ValueError(f"job {spec_job['id']} is a {spec_job['kind']} job; the funnel reads baseline jobs "
                             "with a seed window, or a commit and window")
        spec = spec_job["spec"]
        sha, lo, hi, lgen, env_id = spec["sha"], spec["seeds"]["lo"], spec["seeds"]["hi"], spec.get("lgen"), \
            spec.get("env_id")
    else:
        sha, _ = gitrefs.resolve(repo, ref)
    lo = seeds.BASELINE_WINDOW[0] if lo is None else lo
    hi = seeds.BASELINE_WINDOW[1] if hi is None else hi
    lo, hi = seeds.window(lo, hi)
    if lo < seeds.TOOL[1]:
        raise ValueError(f"seed window [{lo}, {hi}) touches the tool block {seeds.TOOL[0]}-{seeds.TOOL[1] - 1}; "
                         "tool seeds are never judged (D-17)")
    lgen = seeds.USE_LGEN if lgen is None else lgen
    if lgen not in seeds.LGEN_MODES:
        raise ValueError(f"lgen must be one of {seeds.LGEN_MODES}, got {lgen!r}")
    games = store.games(sha, rep=0, lo=lo, hi=hi, lgen_mode=lgen, env_id=env_id)
    return {"sha": sha, "window": [lo, hi], "lgen": lgen, "env_id": env_id, **funnel_mod.funnel(games)}


class App:
    def __init__(self, store, scheduler, repo, cache_dir, env=None):
        self.store, self.scheduler = store, scheduler
        self.env = env  # fingerprint of the worker interpreter (bench/provenance.py), recorded in every job
        self.env_id = None if env is None else provenance.env_id(env)
        if env is not None:
            store.add_env(env)
        self._yardstick = (None, {})
        self.repo, self.cache_dir = Path(repo), Path(cache_dir)
        self.lock = threading.RLock()
        self.imports = {"running": False, "last": None}
        self.request_exit = None  # set by serve(): ends serve_forever from a request thread

    def _sha(self, ref):
        return gitrefs.resolve(self.repo, ref)

    def status(self):
        with self.lock:
            status = self.scheduler.status()
            if status["job"] is not None:
                status["job"]["started"] = self.store.started(status["job"]["id"])
            return {**status, "import": dict(self.imports)}

    def _env_fields(self):
        return {"env_id": self.env_id, "env": self.env}

    @staticmethod
    def _lgen_mode(lgen):
        mode = seeds.USE_LGEN if lgen is None else lgen
        if mode not in seeds.LGEN_MODES:
            raise ValueError(f"lgen must be one of {seeds.LGEN_MODES}, got {lgen!r}")
        return mode

    def start_baseline(self, ref="main", games=576, lo=None, hi=None, lgen=None, replicate=0, gate=None):
        """Play `ref` on the seed window [lo, hi); lo defaults to the baseline window start, hi to lo + games."""
        lo = seeds.BASELINE_WINDOW[0] if lo is None else lo
        if hi is None:
            games = int(games)
            if games < 1:
                raise ValueError("games must be at least 1")
            hi = int(lo) + games
        lo, hi = seeds.window(lo, hi)
        span = seeds.check_window(lo, hi, "baseline", gate)
        mode = self._lgen_mode(lgen)
        if replicate not in (0, 1, "0", "1"):
            raise ValueError(f"replicate must be 0 or 1, got {replicate!r}")
        sha, subject = self._sha(ref)
        spec = {"ref": ref, "sha": sha, "subject": subject, "games": hi - lo,
                "seeds": {"range": span, "lo": lo, "hi": hi}, "lgen": mode,
                "replicate": int(replicate), "gate": gate, **self._env_fields(),
                "lock_blob": provenance.lock_blob(self.repo, sha)}
        with self.lock:
            return {"job_id": self.scheduler.submit("baseline", spec)}

    def start_experiment(self, candidate, baseline="main", metric="dlvl6", lo=None, lgen=None, gate=None):
        rates = [n for n, m in METRICS.items() if m.kind == "rate"]
        if metric not in rates:
            raise ValueError(f"metric must be one of {rates}")
        lo = seeds.BASELINE_WINDOW[0] if lo is None else lo
        lo, hi = seeds.window(lo, int(lo) + CHECKPOINTS[-1])
        span = seeds.check_window(lo, hi, "experiment", gate)
        mode = self._lgen_mode(lgen)
        cand, cand_subject = self._sha(candidate)
        base, base_subject = self._sha(baseline)
        if cand == base:
            raise ValueError(f"{candidate} and {baseline} are the same commit {cand[:10]}")
        spec = {"candidate": cand, "candidate_ref": candidate, "candidate_subject": cand_subject,
                "baseline": base, "baseline_ref": baseline, "baseline_subject": base_subject,
                "metric": metric, "seeds": {"range": span, "lo": lo, "hi": hi},
                "lgen": mode, "gate": gate, **self._env_fields(),
                "lock_blob_candidate": provenance.lock_blob(self.repo, cand),
                "lock_blob_baseline": provenance.lock_blob(self.repo, base)}
        with self.lock:
            return {"job_id": self.scheduler.submit("experiment", spec)}

    def resume(self, job_id):
        """Queue an interrupted job again; it keeps its id and plays only the seeds not yet stored."""
        job = self.store.job(int(job_id))
        if job is None:
            raise LookupError(f"no job {job_id}")
        with self.lock:
            if not self.store.resume(job["id"]):
                raise ValueError(f"job {job['id']} is {job['state']}, only interrupted jobs can be resumed")
        return {"job_id": job["id"], "resumed": True}

    def stop(self, job_id=None):
        with self.lock:
            return {"stopped": self.scheduler.stop(job_id)}

    def stop_all(self):
        with self.lock:
            return {"stopped": self.scheduler.stop_all()}

    def shutdown(self):
        """Stop every job, close the workers and end the server process (serve() sets request_exit)."""
        if self.request_exit is None:
            raise ValueError("this server cannot shut itself down")
        with self.lock:
            stopped = self.scheduler.stop_all()
            self.scheduler.shutdown()
        self.request_exit()
        return {"stopped": stopped, "shutting_down": True}

    def job(self, job_id):
        job = self.store.job(int(job_id))
        if job is None:
            raise LookupError(f"no job {job_id}")
        job["started"] = self.store.started(job["id"])  # started only once its first game row exists
        job["first_game_at"] = self.store.first_game_at(job["id"])
        job["games_played"] = self.store.job_game_count(job["id"])
        spec = job["spec"]
        if job["kind"] == "baseline" and "seeds" in spec:
            key = {"lgen_mode": spec.get("lgen"), "env_id": spec.get("env_id"), "rep": int(spec.get("replicate", 0))}
            stored = self.store.played(spec["sha"], spec["seeds"]["lo"], spec["seeds"]["hi"], **key)
            job["games_reused"] = max(stored - job["games_played"], 0)
        if job["kind"] == "experiment":
            spec = job["spec"]
            window = spec.get("seeds") or {}
            key = {"lgen_mode": spec.get("lgen"), "env_id": spec.get("env_id"), "rep": 0}
            both = sorted(self.store.seeds(spec["candidate"], window.get("lo"), window.get("hi"), **key)
                          & self.store.seeds(spec["baseline"], window.get("lo"), window.get("hi"), **key))
            job["table"] = report.compare(list(self.store.games_by_seed(spec["candidate"], both, **key).values()),
                                          list(self.store.games_by_seed(spec["baseline"], both, **key).values()))
            job["games_per_side"] = len(both)
        return job

    def results(self, ref="main", metric=None):
        sha, subject = self._sha(ref)
        games = self.store.games(sha)
        if metric is not None:
            if metric not in METRICS:
                raise ValueError(f"unknown metric {metric!r}; known: {sorted(METRICS)}")
            return {"sha": sha, "metric": metric, **evaluate(METRICS[metric], games)}
        return {"sha": sha, "subject": subject, **report.summary(games, self.yardstick())}

    def funnel(self, ref="main", lo=None, hi=None, lgen=None, env_id=None, job=None):
        """Per-stage reach of natural games with Wilson intervals; env defaults to this server's env."""
        return funnel_for(self.store, self.repo, ref, lo, hi, lgen, self.env_id if env_id is None else env_id, job)

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


def _int(value):
    """Query parameter as int, None when absent; ValueError (a 400) for anything else."""
    return None if value is None else int(value)


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
                "/api/funnel": lambda: app.funnel(q.get("ref", "main"), _int(q.get("lo")), _int(q.get("hi")),
                                                  q.get("lgen"), q.get("env_id"), _int(q.get("job"))),
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
                    if kind not in KINDS_OVER_HTTP:
                        raise ValueError("kind must be baseline or experiment; clean_attempt jobs are not creatable "
                                         "over HTTP or MCP")
                    if kind == "baseline":
                        return app.start_baseline(**body)
                    return app.start_experiment(**body)
                return self._handle(start)
            m = re.fullmatch(r"/api/jobs/(\d+)/resume", path)
            if m:
                return self._handle(lambda: app.resume(int(m.group(1))))
            if path == "/api/stop-all":
                return self._handle(app.stop_all)
            if path == "/api/shutdown":
                return self._handle(app.shutdown)
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

    def request_exit():
        stop.set()
        # httpd.shutdown() waits for serve_forever, so it must not run on the request thread
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    app.request_exit = request_exit
    threading.Thread(target=app.loop, args=(stop,), daemon=True).start()
    return httpd, stop
