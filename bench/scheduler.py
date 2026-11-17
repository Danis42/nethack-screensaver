"""Hands out one game at a time to worker slots for the active job and judges experiments.

Games are seeded: a job names a half-open seed window [lo, hi) in its spec ("seeds"); the scheduler plays its
seeds in ascending order, skipping seeds stored or in flight. Both sides of an experiment play the same window and
are compared seed by seed. Stored games are reused only under the same game key: commit, seed, lgen mode, env_id and
replicate (rep). With a spec "trigger", bench.triggers.View skips candidate seeds the change cannot reach.

Experiments declare their rule, MDE and planned size before the run (spec "declared", from bench.sprt.plan).
Look k covers the contiguous seed prefix [lo, lo + min((k + 1) * block, n_planned)) and is taken only when
every seed of it is stored on both sides; the verdict comes from the declared rule (bench.sprt.judge_declared)."""
import dataclasses
import time
from collections import defaultdict, deque

from . import seeds as seedlib, sprt, triggers
from .metrics import METRICS, orient
from .sequential import NO_EFFECT, discordant

MAX_DEATHS_IN_ROW = 3


class _Slot:
    def __init__(self):
        self.sha = None
        self.worker = None
        self.busy = False
        self.job_id = None
        self.seed = None
        self.env_id = None
        self.rep = 0
        self.lgen = None  # lgen value asked of the worker for the game in flight


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

    def stop_all(self):
        """Stop the active job and every queued one. Stored games stay. Returns the stopped job ids."""
        stopped = []
        if self.job is not None:
            stopped.append(self.job["id"])
            self._end("stopped", self.job["result"])
        while (job := self.store.next_queued()) is not None:
            self.store.set_job(job["id"], "stopped")
            stopped.append(job["id"])
        return stopped

    def tick(self):
        self._collect()
        if self.job is None:
            job = self.store.next_queued()
            if job is None:
                return
            job["result"] = {"looks": []} if job["kind"] == "experiment" else {}
            job["look"] = 0
            if "seeds" not in job["spec"]:
                self.error = "job spec has no seed window (created by an older bench); start a new job"
                self.store.set_job(job["id"], "failed", {**job["result"], "error": self.error})
                return
            if job["kind"] == "experiment" and "declared" not in job["spec"]:
                self.error = "experiment has no declared MDE and planned size (created by an older bench); start a new job"
                self.store.set_job(job["id"], "failed", {**job["result"], "error": self.error})
                return
            spec = job["spec"]
            job["key"] = {"lgen_mode": spec.get("lgen", "off"), "env_id": spec.get("env_id"),
                          "rep": int(spec.get("replicate", 0))}
            self.store.set_job(job["id"], "running", job["result"])
            self.job, self.error, self._deaths_in_row = job, None, 0
            self.view = triggers.View(self.store, job)  # store reads; a trigger skips seeds the change cannot reach
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
                if slot.lgen is not None and result.get("lgen") != slot.lgen:
                    if self.job is not None:
                        self.error = f"commit {slot.sha[:7]} cannot play lgen games (its run_game has no lgen)"
                        self._end("failed", {**self.job["result"], "error": self.error})
                    return
                self.store.add_game(slot.sha, slot.job_id, result, env_id=slot.env_id, rep=slot.rep)
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

    def _window(self):
        seeds = self.job["spec"]["seeds"]
        return int(seeds["lo"]), int(seeds["hi"])

    def _prefix(self, look=None):
        """Length of the seed prefix of a look (default: the current one)."""
        spec = self.job["spec"]
        look = self.job["look"] if look is None else look
        return min((look + 1) * int(spec["block"]), int(spec["declared"]["n_planned"]))

    def _targets(self):
        """[(sha, lo, hi)]: the seed windows still to fill, baseline side first."""
        spec, (lo, hi) = self.job["spec"], self._window()
        if self.job["kind"] == "baseline":
            return [(spec["sha"], lo, hi)]
        need = self._prefix()
        return [(spec["baseline"], lo, lo + need), (spec["candidate"], lo, lo + need)]  # baseline first

    def _judge(self):
        """True when the active job just ended."""
        spec, key = self.job["spec"], self.job["key"]
        lo, hi = self._window()
        if self.job["kind"] == "baseline":
            stored = self._played(spec["sha"], lo, hi)
            if stored >= hi - lo:
                self._end("done", {"games": stored})
                return True
            return False
        need = self._prefix()
        if self._played(spec["candidate"], lo, lo + need) < need or self._played(spec["baseline"], lo, lo + need) < need:
            return False  # a gap anywhere in the prefix: never judge on completion order
        metric, declared = METRICS[spec["metric"]], spec["declared"]
        window = range(lo, lo + need)
        cand = self.view.games_by_seed(spec["candidate"], window, **key)
        base = self.store.games_by_seed(spec["baseline"], window, **key)
        pairs = []  # (seed, candidate outcome, baseline outcome), in seed order
        for seed in window:
            try:
                pairs.append((seed, bool(metric.fn(cand[seed])), bool(metric.fn(base[seed]))))
            except KeyError:  # a game without the metric's field
                pass
        if not pairs:
            self.error = self.view.error or f"no game has the fields metric {spec['metric']} needs"
            self._end("failed", {**self.job["result"], "error": self.error})
            return True
        looks = []
        for k in range(self.job["look"] + 1):
            end = lo + self._prefix(k)
            upto = [(c, b) for seed, c, b in pairs if seed < end]
            looks.append((len(upto), *discordant(upto)))
        v, oriented = sprt.judge_declared(looks, declared, metric)  # no "rule": the mixture test (jobs <= 21)
        if v.state == "open" and need >= declared["n_planned"]:  # skipped games: the plan is used up anyway
            v = dataclasses.replace(v, state=NO_EFFECT)
        verdict = v.as_dict()
        verdict["state"] = verdict["state"] if oriented else orient(verdict["state"], metric)
        verdict["pairs"] = len(pairs)
        result = self.job["result"]
        result["looks"].append({"n": v.n, "b": v.b, "c": v.c, "log_lr": v.log_lr})
        result["verdict"] = verdict
        if verdict["state"] != "open":
            self._end("done", result)
            return True
        self.store.set_job(self.job["id"], "running", result)
        self.job["look"] += 1
        return False

    def _played(self, sha, lo, hi):
        """How many seeds of [lo, hi) this commit has played under the job's game key."""
        return self.view.played(sha, lo, hi, **self.job["key"])

    def _wanted(self):
        """(sha, seed) of the next game to play, lowest seed first, or None."""
        for sha, lo, hi in self._targets():
            taken = self.view.seeds(sha, lo, hi, **self.job["key"]) | self._inflight[sha]
            for seed in range(lo, hi):
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
                seedlib.check_seed(seed, self.job["kind"], self.job["spec"].get("gate"))
            except ValueError as e:  # a job that bypassed the API: refuse before any worker plays
                self.error = str(e)
                self._end("failed", {**self.job["result"], "error": self.error})
                return
            try:
                if slot.sha != sha:
                    if slot.worker is not None:
                        slot.worker.close()
                    slot.worker, slot.sha = None, None
                    slot.worker = self.spawn(sha)
                    slot.sha = sha
                lgen = seedlib.lgen_for(seed, self.job["key"]["lgen_mode"])
                if lgen is None:
                    slot.worker.play(seed)
                else:
                    slot.worker.play(seed, lgen=lgen)
            except (OSError, ValueError) as e:
                self._worker_died(slot, f"cannot start a game: {e!r}")
                return
            slot.busy, slot.job_id, slot.seed = True, self.job["id"], seed
            slot.env_id, slot.rep, slot.lgen = self.job["key"]["env_id"], self.job["key"]["rep"], lgen
            self._inflight[sha].add(seed)

    def status(self):
        now = time.time()
        recent = [t for t in self._finished if now - t < 300]
        per_minute = len(recent) / ((now - recent[0]) / 60) if len(recent) >= 2 and now > recent[0] else 0.0
        job = None
        if self.job is not None:
            spec = self.job["spec"]
            lo, hi = self._window()
            if self.job["kind"] == "baseline":
                done = self._played(spec["sha"], lo, hi)
                progress = {"games": done, "target": hi - lo}
                left = max(hi - lo - done, 0)
            else:
                need = self._prefix()
                b = self._played(spec["baseline"], lo, lo + need)
                c = self._played(spec["candidate"], lo, lo + need)
                progress = {"look": self.job["look"], "prefix": need, "n_planned": spec["declared"]["n_planned"],
                            "baseline": b, "candidate": c}
                left = 2 * need - b - c
            job = {**{k: self.job[k] for k in ("id", "kind", "spec", "result")}, "progress": progress,
                   "eta_seconds": left / per_minute * 60 if per_minute else None}
        return {"job": job, "busy_workers": sum(s.busy for s in self._slots), "slots": len(self._slots),
                "games_per_minute": per_minute, "error": self.error}
