"""Stand-in player for launcher tests. Mode via argv[1]: 'run' or 'crash'."""
import sys
import time

if sys.argv[1] == "crash":
    print("boom", file=sys.stderr)
    sys.exit(3)
sys.stdout.write("\x1b[1;1HFAKEPLAYER")
sys.stdout.flush()
time.sleep(60)
