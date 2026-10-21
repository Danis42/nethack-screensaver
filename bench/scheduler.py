"""Hands out one game at a time to worker slots for the active job and judges experiments.

Games are seeded: a job needs seeds 0 .. N-1 of each commit, so both sides of an experiment
play the same characters and dungeons and are compared seed by seed."""
import time
from collections import defaultdict, deque

from .metrics import METRICS
from .stats import CHECKPOINTS, judge_paired

MAX_DEATHS_IN_ROW = 3


class _Slot:
    def __init__(self):
        self.sha = None
        self.worker = None
        self.busy = False
        self.job_id = None
        self.seed = None


class Scheduler:
    def __init__(self, store, spawn, slots=11):
        self.store = store
        self.spawn = spawn  # spawn(sha) -> worker with play(), results(), alive(), close()
        self._slots = [_Slot() for _ in range(slots)]
        self._inflight = defaultdict(set)  # sha -> seeds being played
        self._deaths_in_row = 0
        self._finished = deque(maxlen=500)  # finish times, for games per minute
        self.job = None
        self.error = None

    def submit(self, kind, spec):
        return self.store.add_job(kind, spec)

    def stop(self, job_id=None):
        """Stop the active job, or a queued one by id. Stored games stay."""
        if self.job is not None and job_id in (None, self.job["id"]):
            self._end("stopped", self.job["result"])
            return True
        if job_id is not None:
            job = self.store.job(job_id)
            if job is not None and job["state"] == "queued":
                self.store.set_job(job_id, "stopped")
                return True
        return False

    def tick(self):
        self._collect()
        if self.job is None:
            job = self.store.next_queued()
            if job is None:
                return
            job["result"] = {"checkpoints": []} if job["kind"] == "experiment" else {}
            job["checkpoint"] = 0
            self.store.set_job(job["id"], "running", job["result"])
            self.job, self.error, self._deaths_in_row = job, None, 0
        if self._judge():
            return
        self._dispatch()

    def shutdown(self):
        for slot in self._slots:
            if slot.worker is not None:
                slot.worker.close()
            slot.worker, slot.busy, slot.sha = None, False, None

    # internals

    def _collect(self):
        for slot in self._slots:
            if slot.worker is None:
                continue
            dead = not slot.worker.alive()
            for result in slot.worker.results():
                self._inflight[slot.sha].discard(slot.seed)
                slot.busy = False
                if "seed" not in result:
                    if self.job is not None:
                        self.error = f"commit {slot.sha[:7]} cannot play seeded games (its run_game has no seed)"
                        self._end("failed", {**self.job["result"], "error": self.error})
                    return
                self.store.add_game(slot.sha, slot.job_id, result)
                self._finished.append(time.time())
                self._deaths_in_row = 0
            if dead:
                self._worker_died(slot, "worker process died")

    def _worker_died(self, slot, why):
        if slot.busy:
            self._inflight[slot.sha].discard(slot.seed)  # handed out again
        if slot.worker is not None:
            slot.worker.close()
        slot.worker, slot.busy, slot.sha = None, False, None
        self._deaths_in_row += 1
        if self._deaths_in_row >= MAX_DEATHS_IN_ROW and self.job is not None:
            self.error = f"{why}: worker died {MAX_DEATHS_IN_ROW} times in a row; see worker.log"
            self._end("failed", {**self.job["result"], "error": self.error})

    def _end(self, state, result):
        self.store.set_job(self.job["id"], state, result)
        self.job = None
        for slot in self._slots:
            if slot.busy:
                self._inflight[slot.sha].discard(slot.seed)  # a game in progress is dropped
        self.shutdown()

    def _targets(self):
        spec = self.job["spec"]
        if self.job["kind"] == "baseline":
            return [(spec["sha"], spec["games"])]
        need = CHECKPOINTS[self.job["checkpoint"]]
        return [(spec["baseline"], need), (spec["candidate"], need)]  # baseline first

    def _judge(self):
        """True when the active job just ended."""
        spec = self.job["spec"]
        if self.job["kind"] == "baseline":
            stored = self._played(spec["sha"], spec["games"])
            if stored >= spec["games"]:
                self._end("done", {"games": stored})
                return True
            return False
        need = CHECKPOINTS[self.job["checkpoint"]]
        if self._played(spec["candidate"], need) < need or self._played(spec["baseline"], need) < need:
            return False
        fn = METRICS[spec["metric"]].fn
        cand = self.store.games_by_seed(spec["candidate"], range(need))
        base = self.store.games_by_seed(spec["baseline"], range(need))
        pairs = []
        for seed in range(need):
            try:
                pairs.append((bool(fn(cand[seed])), bool(fn(base[seed]))))
            except KeyError:  # a game without the metric's field
                pass
        if not pairs:
            self.error = f"no game has the fields metric {spec['metric']} needs"
            self._end("failed", {**self.job["result"], "error": self.error})
            return True
        verdict = judge_paired(pairs, need).as_dict()
        verdict["pairs"] = len(pairs)
        result = self.job["result"]
        result["checkpoints"].append(verdict)
        result["verdict"] = verdict
        if verdict["state"] != "open":
            self._end("done", result)
            return True
        self.store.set_job(self.job["id"], "running", result)
        self.job["checkpoint"] += 1
        return False

    def _played(self, sha, target):
        """How many of the seeds 0 .. target-1 this commit has played."""
        return len(self.store.seeds(sha) & set(range(target)))

    def _wanted(self):
        """(sha, seed) of the next game to play, or None."""
        for sha, target in self._targets():
            taken = self.store.seeds(sha) | self._inflight[sha]
            for seed in range(target):
                if seed not in taken:
                    return sha, seed
        return None

    def _dispatch(self):
        for slot in self._slots:
            if self.job is None or slot.busy:
                continue
            wanted = self._wanted()
            if wanted is None:
                return
            sha, seed = wanted
            try:
                if slot.sha != sha:
                    if slot.worker is not None:
                        slot.worker.close()
                    slot.worker, slot.sha = None, None
                    slot.worker = self.spawn(sha)
                    slot.sha = sha
                slot.worker.play(seed)
            except (OSError, ValueError) as e:
                self._worker_died(slot, f"cannot start a game: {e!r}")
                return
            slot.busy, slot.job_id, slot.seed = True, self.job["id"], seed
            self._inflight[sha].add(seed)

    def status(self):
        now = time.time()
        recent = [t for t in self._finished if now - t < 300]
        per_minute = len(recent) / ((now - recent[0]) / 60) if len(recent) >= 2 and now > recent[0] else 0.0
        job = None
        if self.job is not None:
            spec = self.job["spec"]
            if self.job["kind"] == "baseline":
                done = self._played(spec["sha"], spec["games"])
                progress = {"games": done, "target": spec["games"]}
                left = max(spec["games"] - done, 0)
            else:
                need = CHECKPOINTS[self.job["checkpoint"]]
                b = self._played(spec["baseline"], need)
                c = self._played(spec["candidate"], need)
                progress = {"baseline": b, "candidate": c, "checkpoint": need}
                left = 2 * need - b - c
            job = {**{k: self.job[k] for k in ("id", "kind", "spec", "result")}, "progress": progress,
                   "eta_seconds": left / per_minute * 60 if per_minute else None}
        return {"job": job, "busy_workers": sum(s.busy for s in self._slots), "slots": len(self._slots),
                "games_per_minute": per_minute, "error": self.error}
