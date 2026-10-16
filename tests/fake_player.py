"""Stand-in player for launcher tests. Mode via argv[1]: 'run' or 'crash'."""
import os
import sys
import time

if sys.argv[1] == "crash":
    print("boom", file=sys.stderr)
    sys.exit(3)
if os.environ.get("FAKE_PLAYER_PIDFILE"):
    open(os.environ["FAKE_PLAYER_PIDFILE"], "w").write(str(os.getpid()))
sys.stdout.write("\x1b[1;1HFAKEPLAYER")
sys.stdout.flush()
time.sleep(60)
