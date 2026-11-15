"""Refactor gate (CODE-01, D-12, D-13): does a commit play the 100 gate seeds exactly like its baseline?

    uv run python -m bench.gate <candidate> [--baseline main] [--workers 10]

Plays seeds 900-999 (tool block, D-17) for both commits with a frame-hash trace (bench/frame_trace.py) and compares
the traces. Recorded as a tool job of kind "gate" (bench/toolruns.py): every game goes to tool_games, never to
the natural games. Verdict "pass" when every compared seed is identical and at most MAX_SKIPPED seeds were skipped
(a watchdog ending on either side depends on machine load, so it is never counted as identical); otherwise "fail"
with the first divergence: lowest differing seed, its step and game turn. The job spec records the candidate's
tree, so a refactor commit amended after the run (same tree) can cite the job (githooks/commit_kind.py).
It refuses to start next to a running bench job."""
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from . import gitrefs, toolruns
from .frame_trace import first_divergence
from .runner import ProcessWorker

GATE_SEEDS = range(900, 1000)
MAX_SKIPPED = 2


class TraceWorker(ProcessWorker):
    def trace(self, seed, path):
        self._proc.stdin.write(f"trace {int(seed)} {path}\n")
        self._proc.stdin.flush()


def tree_of(repo, sha):
    return gitrefs._git(repo, "rev-parse", f"{sha}^{{tree}}")


def judge(seeds, base, cand, trace_path):
    """Verdict dict from {seed: result} of both sides; trace_path(side, seed) locates a trace file."""
    compared, differing, skipped = 0, [], []
    for seed in seeds:
        b, c = base[seed], cand[seed]
        if "watchdog" in (b.get("end_reason"), c.get("end_reason")):
            skipped.append(seed)
            continue
        compared += 1
        if b["trace_digest"] != c["trace_digest"]:
            differing.append(seed)
    verdict = "pass" if not differing and len(skipped) <= MAX_SKIPPED else "fail"
    out = {"verdict": verdict, "compared": compared, "identical": compared - len(differing),
           "differing_seeds": differing, "skipped_seeds": skipped, "first_divergence": None}
    if differing:
        seed = differing[0]
        out["first_divergence"] = {"seed": seed, **first_divergence(trace_path("baseline", seed),
                                                                    trace_path("candidate", seed))}
    return out


def play_all(tasks, spawn, workers, poll=0.2, retries=2, on_result=None):
    """Plays [(sha, seed, path)] on up to `workers` trace workers; returns {(sha, seed): result}.
    on_result(sha, seed, result) runs as each game finishes, so the job has rows while it runs (started = a row)."""
    pending, done, slots, deaths = list(tasks), {}, [], 0
    while pending or any(s["task"] for s in slots):
        for s in slots:
            for result in s["worker"].results():
                done[s["task"][:2]] = result
                if on_result is not None:
                    on_result(*s["task"][:2], result)
                s["task"] = None
            if s["task"] is not None and not s["worker"].alive():
                deaths += 1
                if deaths > retries:
                    raise RuntimeError(f"gate worker died {deaths} times; see worker.log")
                pending.insert(0, s["task"])
                s["worker"].close()
                s["task"] = None
                s["dead"] = True
        slots = [s for s in slots if not s.get("dead")]
        for s in [s for s in slots if s["task"] is None] + [None] * (workers - len(slots)):
            if not pending:
                break
            sha, seed, path = task = pending.pop(0)
            if s is None or s["sha"] != sha:
                if s is not None:
                    s["worker"].close()
                    slots.remove(s)
                s = {"sha": sha, "worker": spawn(sha), "task": None}
                slots.append(s)
            s["worker"].trace(seed, path)
            s["task"] = task
        time.sleep(poll)
    for s in slots:
        s["worker"].close()
    return done


def run_gate(store, repo, candidate, baseline, spawn, trace_root, workers=10, seeds=GATE_SEEDS, poll=0.2):
    """Plays and judges one gate run; returns (job_id, verdict dict). Baseline traces already on disk are reused."""
    cand, _ = gitrefs.resolve(repo, candidate)
    base, _ = gitrefs.resolve(repo, baseline)
    if cand == base:
        raise ValueError(f"{candidate} and {baseline} are the same commit {cand[:10]}")
    spec = {"candidate": cand, "candidate_ref": candidate, "candidate_tree": tree_of(repo, cand),
            "baseline": base, "baseline_ref": baseline, "seeds": list(seeds)}
    job_id = toolruns.record_run(store, "gate", cand, spec)
    path = {sha: Path(trace_root) / sha for sha in (base, cand)}
    [p.mkdir(parents=True, exist_ok=True) for p in path.values()]
    cached = {(base, s): json.loads((path[base] / f"{s}.json").read_text()) for s in seeds
              if (path[base] / f"{s}.json").exists() and (path[base] / f"{s}.trace").exists()}
    side = lambda sha: "baseline" if sha == base else "candidate"

    def record(sha, seed, result):
        (path[sha] / f"{seed}.json").write_text(json.dumps(result))
        toolruns.add_result(store, job_id, "gate", sha, {**result, "seed": seed, "side": side(sha)})

    for (sha, seed), result in sorted(cached.items(), key=lambda kv: kv[0][1]):
        record(sha, seed, result)
    tasks = [(sha, seed, path[sha] / f"{seed}.trace") for sha in (base, cand) for seed in seeds
             if (sha, seed) not in cached]
    try:
        played = play_all(tasks, spawn, workers, poll=poll, on_result=record)
    except Exception as e:  # recorded on the job, then re-raised for the caller
        toolruns.finish(store, job_id, "failed", {"error": str(e)})
        raise
    results = {**cached, **played}
    verdict = judge(seeds, {s: results[(base, s)] for s in seeds}, {s: results[(cand, s)] for s in seeds},
                    lambda side, s: path[base if side == "baseline" else cand] / f"{s}.trace")
    verdict["baseline_reused"] = len(cached)
    toolruns.finish(store, job_id, "done", verdict)
    return job_id, verdict


def _server_busy(url):
    try:
        with urlopen(url + "/api/status", timeout=2) as r:
            return json.loads(r.read()).get("job") is not None
    except (URLError, OSError, ValueError):  # no server: nothing to collide with
        return False


def main(argv=None):
    from .cli import CACHE, DATA, REPO, URL, WORKER_PYTHON
    p = argparse.ArgumentParser(prog="python -m bench.gate", description=__doc__.split("\n\n")[0])
    p.add_argument("candidate")
    p.add_argument("--baseline", default="main")
    p.add_argument("--workers", type=int, default=10)
    args = p.parse_args(argv)
    if _server_busy(URL):
        print("the bench server is running a job; wait for it or stop it first", file=sys.stderr)
        return 2

    def spawn(sha):
        worktree = gitrefs.ensure_worktree(REPO, sha, CACHE / "worktrees")
        return TraceWorker(WORKER_PYTHON, worktree, DATA / "worker.log")

    job_id, verdict = run_gate(toolruns.open_store(DATA), REPO, args.candidate, args.baseline, spawn,
                               DATA / "traces", workers=args.workers)
    print(json.dumps({"job_id": job_id, **verdict}))
    return 0 if verdict["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
