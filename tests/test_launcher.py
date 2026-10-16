import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "nethack-screensaver"


def _spawn(mode, tmp_path):
    master, slave = pty.openpty()
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} {mode}")
    p = subprocess.Popen([str(LAUNCHER)], stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    return p, master


def _read_until(master, needle, timeout=5):
    buf = b""
    end = time.time() + timeout
    while time.time() < end and needle not in buf:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                buf += os.read(master, 4096)
            except OSError:
                break
    return buf


def test_keypress_exits_and_restores(tmp_path):
    p, m = _spawn("run", tmp_path)
    out = _read_until(m, b"FAKEPLAYER")
    assert b"\x1b[?1049h" in out and b"FAKEPLAYER" in out
    os.write(m, b"\x1b[A")  # arrow key: multi-byte
    assert p.wait(timeout=5) == 0
    rest = _read_until(m, b"\x1b[?1049l", timeout=3)
    assert b"\x1b[?1049l" in out + rest
    assert b"\x1b[?25h" in out + rest


def test_player_crash_shows_error_and_restores(tmp_path):
    p, m = _spawn("crash", tmp_path)
    out = _read_until(m, b"\x1b[?1049l", timeout=8)
    assert p.wait(timeout=8) != 0
    assert b"player.log" in out
    assert "boom" in (tmp_path / "nethack-screensaver" / "player.log").read_text()


def test_multibyte_key_not_leaked_to_shell(tmp_path):
    master, slave = pty.openpty()
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} run")
    script = f'"{LAUNCHER}"; IFS= read -r -t 0.5 -n 10 rest; printf "LEFT[%s]" "$rest"'
    p = subprocess.Popen(["bash", "-c", script], stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    _read_until(master, b"FAKEPLAYER")
    os.write(master, b"\x1b[A")
    out = _read_until(master, b"LEFT[", timeout=5) + _read_until(master, b"]", timeout=2)
    p.wait(timeout=5)
    assert b"LEFT[]" in out, out[-80:]


def test_zsh_idle_hook_starts_and_returns_to_prompt(tmp_path):
    hook = ROOT / "zsh" / "nethack-screensaver.zsh"
    master, slave = pty.openpty()
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               NETHACK_SCREENSAVER_IDLE="2",
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} run",
               PS1="PROMPT> ")
    p = subprocess.Popen(["zsh", "-f", "-i"], stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    os.write(master, f"source {hook}\n".encode())
    _read_until(master, b"PROMPT> ")
    os.write(master, b"echo kept")  # unsubmitted line
    out = _read_until(master, b"FAKEPLAYER", timeout=8)
    assert b"FAKEPLAYER" in out
    os.write(master, b"x")
    _read_until(master, b"\x1b[?1049l", timeout=5)
    os.write(master, b"\n")
    out = _read_until(master, b"\r\nkept", timeout=5)
    assert b"\r\nkept" in out  # buffer survived and ran; the 'x' was swallowed
    os.write(master, b"exit\n")
    p.wait(timeout=5)


def test_key_during_crash_message_not_leaked(tmp_path):
    master, slave = pty.openpty()
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} crash")
    script = f'"{LAUNCHER}"; IFS= read -r -t 0.5 -n 10 rest; printf "LEFT[%s]" "$rest"'
    p = subprocess.Popen(["bash", "-c", script], stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    _read_until(master, b"player exited")
    os.write(master, b"\r")
    out = _read_until(master, b"LEFT[", timeout=6) + _read_until(master, b"]", timeout=2)
    p.wait(timeout=5)
    assert b"LEFT[]" in out, out[-80:]


def test_terminal_gone_with_hup_ignored_exits_and_stops_player(tmp_path):
    master, slave = pty.openpty()
    pidfile = tmp_path / "player.pid"
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               FAKE_PLAYER_PIDFILE=str(pidfile),
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} run")
    p = subprocess.Popen(["bash", "-c", f'trap "" HUP; exec "{LAUNCHER}"'],
                         stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True)
    os.close(slave)
    _read_until(master, b"FAKEPLAYER")
    os.close(master)
    try:
        p.wait(timeout=5)
    finally:
        if p.poll() is None:
            p.kill()
    player_pid = int(pidfile.read_text())
    time.sleep(0.5)
    assert not Path(f"/proc/{player_pid}").exists() or "zombie" in Path(f"/proc/{player_pid}/status").read_text().lower()
