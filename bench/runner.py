"""Worker processes: one per slot, bound to one commit's worktree."""
import json
import os
import queue
import subprocess
import threading
from pathlib import Path

WORKER_SCRIPT = Path(__file__).with_name("worker.py")


class ProcessWorker:
    def __init__(self, python, worktree, log_path, nice=10):
        self._log = open(log_path, "a")
        env = {**os.environ, "PYTHONPATH": str(worktree)}
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

    def play(self, seed=None):
        self._proc.stdin.write("play\n" if seed is None else f"play {int(seed)}\n")
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
