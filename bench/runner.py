"""Worker processes: one per slot, bound to one commit's worktree."""
import json
import os
import queue
import subprocess
import threading
from pathlib import Path

from nethack_screensaver import fixed_clock

WORKER_SCRIPT = Path(__file__).with_name("worker.py")


class ProcessWorker:
    def __init__(self, python, worktree, log_path, nice=10):
        self._log = open(log_path, "a")
        # fixed hash seed, one BLAS thread (workers were oversubscribed), and the fixed_clock shim so a seeded
        # game's start time comes from its seed
        env = fixed_clock.preload_env({**os.environ, "PYTHONPATH": str(worktree), "PYTHONHASHSEED": "0",
                                       "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        cmd = [str(python), str(WORKER_SCRIPT)]
        if nice:
            cmd = ["nice", "-n", str(nice), *cmd]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=self._log, text=True, env=env, cwd=worktree)
        self._out = queue.Queue()
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._out.put(json.loads(line))
            except json.JSONDecodeError:
                self._log.write(f"bench: not a result line: {line[:200]}\n")

    def play(self, seed=None, lgen=None):
        if lgen is not None and seed is None:
            raise ValueError("lgen needs a seed")
        if seed is None:
            line = "play\n"
        elif lgen is None:
            line = f"play {int(seed)}\n"
        else:
            line = f"play {int(seed)} {int(lgen)}\n"
        self._proc.stdin.write(line)
        self._proc.stdin.flush()

    def results(self):
        out = []
        while True:
            try:
                out.append(self._out.get_nowait())
            except queue.Empty:
                return out

    def alive(self):
        if self._proc.poll() is None:
            return True
        self._reader.join(timeout=2)  # collect a result printed just before dying
        return False

    def close(self):
        if self._proc.poll() is None:
            self._proc.kill()
        self._proc.wait()
        self._reader.join(timeout=2)
        self._log.close()
