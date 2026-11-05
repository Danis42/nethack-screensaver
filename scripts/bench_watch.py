"""Watch every bench experiment and stop it as soon as its result is clear (owner rule, 2026-11-05).

Checks the bench every 5 minutes. For the running experiment, at its newest checkpoint:
  decided   the bench's own verdict is no longer open (it stops by itself; reported here)
  worse     hi < 0: the candidate is worse                                        -> stop
  gate job  lo >= -MARGIN: a loss over MARGIN is ruled out (no-harm check passed) -> stop
  other     hi < +MARGIN: a gain of MARGIN or more is ruled out (cannot be a win) -> stop
Gate jobs are the ids given with --gate (no-harm checks for fixes); every other experiment is
judged as an improvement experiment. Exits after it stops a job (or a job is decided) so the
caller is notified; restart it afterwards. Baseline jobs are left alone.

Usage: uv run python scripts/bench_watch.py [--gate 80 81]
"""
import argparse
import json
import time
import urllib.request

URL = "http://127.0.0.1:8765"
MARGIN = 0.02  # 2 points; the bench resolves about 2.8 points at 2304 pairs
PERIOD = 300


def call(method, path):
    req = urllib.request.Request(URL + path, method=method, data=b"{}" if method != "GET" else None,
                                 headers={"Content-Type": "application/json"})  # server refuses writes without it
    return json.load(urllib.request.urlopen(req, timeout=30))


def verdict_reason(v, gate):
    """Why this checkpoint is clear, or None."""
    if v["state"] != "open":
        return "decided"
    if v["hi"] < 0:
        return "worse"
    if gate and v["lo"] >= -MARGIN:
        return "no-harm shown"
    if not gate and v["hi"] < MARGIN:
        return "no gain possible"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=int, nargs="*", default=[], help="job ids that are no-harm checks")
    gates = set(ap.parse_args().gate)
    while True:
        try:
            job = call("GET", "/api/status").get("job")
        except Exception as e:
            print("bench unreachable:", e, flush=True)
            time.sleep(PERIOD)
            continue
        v = (job or {}).get("result", {}) or {}
        v = v.get("verdict") if job and job.get("kind") == "experiment" else None
        if v:
            gate = job["id"] in gates
            reason = verdict_reason(v, gate)
            if reason:
                msg = (f"job {job['id']} ({'gate' if gate else 'experiment'}) {reason} at {v['pairs']} pairs: "
                       f"diff {v['diff'] * 100:+.1f} [{v['lo'] * 100:+.1f}, {v['hi'] * 100:+.1f}]")
                if reason != "decided":
                    call("DELETE", f"/api/jobs/{job['id']}")
                    msg += " -> STOPPED"
                print(msg, flush=True)
                return
        time.sleep(PERIOD)


if __name__ == "__main__":
    main()
