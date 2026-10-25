"""Pins NetHack's start time for seeded games.

NetHack reads the clock at game start (u.ubirthday) and picks shopkeeper names from it; NLE's
fix_moon_phase does not cover that. Names change messages and screen layout, and through them what
the bot does, so the same seed played at another time could play another game (seen in the
Phase 1 A/A control). A tiny LD_PRELOAD library replaces libc's time() with the value of
NLE_FIXED_TIME when that variable is set; run_game sets it per seed. Python's own clocks are not
touched (they do not call time()), so watchdogs keep real time.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ENV_VAR = "NLE_FIXED_TIME"
_BASE = 1_000_000_000  # 2001-09-09; any fixed value works
_NAME_BUCKET = 257     # NetHack's shopkeeper name seed is ubirthday / 257, so each seed gets its own

SOURCE = r"""
#define _GNU_SOURCE
#include <time.h>
#include <stdlib.h>
#include <dlfcn.h>
time_t time(time_t *t) {
    const char *v = getenv("NLE_FIXED_TIME");
    time_t r;
    if (v) r = (time_t) atoll(v);
    else { static time_t (*real)(time_t *) = 0; if (!real) real = dlsym(RTLD_NEXT, "time"); r = real(0); }
    if (t) *t = r;
    return r;
}
"""


def seed_time(seed: int) -> int:
    """The start time a seeded game sees."""
    return _BASE + int(seed) * _NAME_BUCKET


def shim_path(cache: Path | None = None) -> Path:
    """The compiled library, built once per source version with the system C compiler."""
    cache = cache or Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "screens"
    digest = hashlib.sha1(SOURCE.encode()).hexdigest()[:12]
    lib = cache / f"fixtime-{digest}.so"
    if not lib.exists():
        cache.mkdir(parents=True, exist_ok=True)
        # per-process source and output: workers that start together never read each other's half-written file
        src = cache / f"fixtime-{digest}.{os.getpid()}.c"
        src.write_text(SOURCE)
        tmp = lib.with_suffix(f".{os.getpid()}.tmp")
        try:
            subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", str(tmp), str(src), "-ldl"], check=True)
            tmp.replace(lib)
        finally:
            src.unlink(missing_ok=True)
    return lib


def preload_env(env: dict) -> dict:
    """A copy of env whose processes load the time() shim."""
    lib = str(shim_path())
    preload = [p for p in env.get("LD_PRELOAD", "").split(":") if p and p != lib]
    return {**env, "LD_PRELOAD": ":".join([lib, *preload])}


def preloaded() -> bool:
    return "fixtime-" in os.environ.get("LD_PRELOAD", "")


def ensure_preloaded():
    """Restart this script with the shim loaded (for scripts that play seeded games)."""
    if not preloaded():
        os.execve(sys.executable, [sys.executable, *sys.argv], preload_env(dict(os.environ)))


def pin(seed: int | None):
    """Set (seeded game) or clear (screensaver game) the time NetHack sees from now on."""
    if seed is None:
        os.environ.pop(ENV_VAR, None)
    else:
        os.environ[ENV_VAR] = str(seed_time(seed))
