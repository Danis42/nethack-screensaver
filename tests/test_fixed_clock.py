import os
import subprocess
import sys

from nethack_screensaver import fixed_clock

PRINT_TIME = "import ctypes; print(ctypes.CDLL(None).time(None))"


def _child_time(env):
    out = subprocess.run([sys.executable, "-c", PRINT_TIME], env=env, capture_output=True, text=True, check=True)
    return int(out.stdout)


def test_shim_returns_the_pinned_time(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    env = fixed_clock.preload_env({**os.environ, fixed_clock.ENV_VAR: "123456"})
    assert _child_time(env) == 123456


def test_shim_falls_through_to_the_real_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    env = fixed_clock.preload_env({k: v for k, v in os.environ.items() if k != fixed_clock.ENV_VAR})
    assert _child_time(env) > 1_700_000_000


def test_each_seed_gets_its_own_shopkeeper_name_bucket():
    assert fixed_clock.seed_time(1) - fixed_clock.seed_time(0) == 257
    assert fixed_clock.seed_time(5) == fixed_clock.seed_time(5)


def test_pin_sets_and_clears(monkeypatch):
    monkeypatch.delenv(fixed_clock.ENV_VAR, raising=False)
    fixed_clock.pin(3)
    assert os.environ[fixed_clock.ENV_VAR] == str(fixed_clock.seed_time(3))
    fixed_clock.pin(None)
    assert fixed_clock.ENV_VAR not in os.environ


def test_preload_env_keeps_other_preloads(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    env = fixed_clock.preload_env({"LD_PRELOAD": "/x/other.so"})
    assert env["LD_PRELOAD"].split(":")[1] == "/x/other.so"
    assert "fixtime-" in env["LD_PRELOAD"].split(":")[0]
