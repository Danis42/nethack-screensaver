"""A seed plays the same game: in fresh processes, in a long-lived process, on any calendar day."""
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from nethack_screensaver import game

ROOT = Path(__file__).parent.parent
# result fields that must replay exactly (the rest, e.g. score, follow from the same game)
COMPARED = ["turns", "end_reason", "rung", "last_messages"]

CHILD = """
import hashlib, json, sys
from dataclasses import asdict
from nethack_screensaver import game

h = hashlib.sha1()
frames = [0]

def on_frame(obs):
    h.update(obs["tty_chars"].tobytes())
    frames[0] += 1

result = game.run_game(seed=int(sys.argv[1]), watchdog_seconds=120, on_frame=on_frame)
print(json.dumps({"hash": h.hexdigest(), "frames": frames[0], "result": asdict(result)}))
"""


def _start(seed, hashseed):
    env = {**os.environ, "PYTHONHASHSEED": str(hashseed)}
    return subprocess.Popen([sys.executable, "-c", CHILD, str(seed)], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _finish(proc):
    out, err = proc.communicate(timeout=900)
    assert proc.returncode == 0, err[-2000:]
    return json.loads(out.strip().splitlines()[-1])


@pytest.mark.slow
def test_fresh_processes_replay_the_same_game():
    procs = {(seed, hs): _start(seed, hs) for seed in (3, 10) for hs in (1, 2)}
    runs = {key: _finish(proc) for key, proc in procs.items()}
    for seed in (3, 10):
        a, b = runs[(seed, 1)], runs[(seed, 2)]
        assert a["hash"] == b["hash"], f"seed {seed}: frame hashes differ"
        assert a["frames"] == b["frames"], f"seed {seed}: frame counts differ"
        for name in COMPARED:
            assert a["result"][name] == b["result"][name], f"seed {seed}: {name} differs"
        json.dumps(a["result"])


def _play(seed, max_steps=3000):
    h = hashlib.sha1()
    result = game.run_game(seed=seed, max_steps=max_steps, watchdog_seconds=120,
                           on_frame=lambda obs: h.update(obs["tty_chars"].tobytes()))
    return h.hexdigest(), asdict(result)


@pytest.mark.slow
def test_one_process_replays_seed_a_after_seed_b():
    first = _play(3)
    _play(10)
    again = _play(3)
    assert first[0] == again[0], "seed 3 played differently after seed 10 in the same process"
    for name in COMPARED:
        assert first[1][name] == again[1][name], name


@pytest.mark.slow
def test_the_seed_decides_the_moon():
    def top_lines(seed):
        lines = []
        game.run_game(seed=seed, max_steps=20, watchdog_seconds=120,
                      on_frame=lambda obs: lines.append(bytes(obs["tty_chars"][0]).decode(errors="replace").lower()))
        return " ".join(lines[:20])
    assert "friday the 13th" in top_lines(49)
    assert "full moon" in top_lines(3)
