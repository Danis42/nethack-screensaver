"""Local status page: bench job progress and the Ollama wiki sweep, with finishing times.

    python3 -I scripts/status_page.py [port]   ->  http://127.0.0.1:8770
"""
import html, json, os, re, sys, time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = "http://127.0.0.1:8765/api/status"
FACTS = os.path.join(ROOT, ".planning/phases/02-real-descent/sweep/wiki-facts.jsonl")
LOG = os.path.join(ROOT, ".planning/phases/02-real-descent/sweep/ollama.log")
BATCHES = os.path.join(ROOT, "reference/wiki_batches")
_samples = []  # (time, pages done) for the wiki rate


def clock(seconds):
    if seconds is None:
        return "?"
    end = datetime.now() + timedelta(seconds=seconds)
    h, m = divmod(int(seconds) // 60, 60)
    return f"{end:%a %H:%M} (in {h} h {m:02d} min)" if h else f"{end:%H:%M} (in {m} min)"


def bench():
    try:
        with urlopen(BENCH, timeout=5) as r:
            s = json.loads(r.read())
    except Exception as e:
        return "<p class=bad>Bench server not reachable: %s</p>" % html.escape(str(e))
    job = s.get("job")
    if not job:
        return "<p>No bench job running.</p>"
    spec, prog = job["spec"], job.get("progress", {})
    v = (job.get("result") or {}).get("verdict") or {}
    target = prog.get("checkpoint") or 1
    done = min(prog.get("baseline", 0), target) + min(prog.get("candidate", 0), target)
    pct = 100 * done / (2 * target)
    verdict = v.get("state", "open")
    if v.get("pairs"):
        verdict += " at %d pairs: %+.1f [%+.1f, %+.1f] points" % (v["pairs"], 100 * v["diff"], 100 * v["lo"], 100 * v["hi"])
    return f"""<h2>Experiment: job {job['id']}</h2>
<p><b>{html.escape(spec.get('candidate_ref', ''))}</b> vs {html.escape(spec.get('baseline_ref', ''))},
metric <b>{html.escape(spec.get('metric', ''))}</b></p>
<div class=bar><div style="width:{pct:.1f}%"></div></div>
<p>Baseline {prog.get('baseline', 0)} / {target} games, candidate {prog.get('candidate', 0)} / {target} games
({pct:.0f}%), {s.get('games_per_minute', 0):.1f} games/min</p>
<p>Finishes at most by: <b>{clock(job.get('eta_seconds'))}</b> (it can stop early at a checkpoint)</p>
<p>Verdict so far: {html.escape(verdict)}</p>"""


def wiki():
    total = 0
    if os.path.isdir(BATCHES):
        for f in os.listdir(BATCHES):
            if f.endswith(".txt"):
                total += open(os.path.join(BATCHES, f), errors="replace").read().count("######## ")
    done = sum(1 for l in open(FACTS) if l.strip()) if os.path.exists(FACTS) else 0
    now = time.time()
    _samples.append((now, done))
    while len(_samples) > 2 and now - _samples[0][0] > 1800:
        _samples.pop(0)
    t0, d0 = _samples[0]
    eta = (total - done) * (now - t0) / (done - d0) if done > d0 else None
    if eta is None and os.path.exists(LOG):  # fresh page: the runner logs "N/M pages, X.Xs per page"
        rates = re.findall(r"([\d.]+)s per page", open(LOG, errors="replace").read())
        eta = (total - done) * float(rates[-1]) if rates else None
    pct = 100 * done / total if total else 0
    state = "finished" if total and done >= total else ("running" if eta else "starting / measuring")
    return f"""<h2>Wiki sorting (local model)</h2>
<div class=bar><div style="width:{pct:.1f}%"></div></div>
<p>{done} / {total} pages ({pct:.0f}%), {state}</p>
<p>Finishes: <b>{'done' if state == 'finished' else clock(eta)}</b></p>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=30>
<meta name=viewport content="width=device-width, initial-scale=1"><title>Bot status</title>
<style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--mute:#6b6b66;--bar:#e4e4dd;--fill:#3a7d5c;--bad:#b3261e}}
@media (prefers-color-scheme: dark){{:root{{--bg:#161615;--fg:#ececea;--mute:#9a9a94;--bar:#2c2c2a;--fill:#5fb38a;--bad:#f2b8b5}}}}
body{{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:0 auto;padding:16px}}
h1{{font-size:1.4em}} h2{{font-size:1.1em;margin-top:2em}} .bad{{color:var(--bad)}} small{{color:var(--mute)}}
.bar{{background:var(--bar);border-radius:6px;height:14px;overflow:hidden}} .bar div{{background:var(--fill);height:100%}}
</style>
<h1>Bot status</h1><small>Updated {datetime.now():%H:%M:%S}, refreshes every 30 s</small>
{bench()}{wiki()}"""
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
