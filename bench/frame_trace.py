"""Frame-hash trace of one game for the refactor gate (CODE-01): standard library only.

The bench worker loads this file by path (it must not import the bench package, which old commits lack) and
passes Trace.frame as run_game's on_frame callback, so tracing changes nothing in how the bot plays. Each env
step appends one 16-byte record (step, game turn, 8-byte blake2b of the screen text and the status numbers);
`digest` chains them, so two games are identical exactly when their digests match.
"""
import hashlib
import struct

RECORD = struct.Struct("<II8s")
TURN = 20  # blstats index of the game turn (NLE_BL_TIME)


class Trace:
    def __init__(self, path):
        self.path = path
        self._file = open(path, "wb")
        self._chain = hashlib.blake2b(digest_size=16)
        self.steps = 0

    def frame(self, obs):
        blstats = obs["blstats"]
        digest = hashlib.blake2b(bytes(obs["tty_chars"]) + bytes(blstats), digest_size=8).digest()
        self._file.write(RECORD.pack(self.steps, int(blstats[TURN]), digest))
        self._chain.update(digest)
        self.steps += 1

    def close(self):
        self._file.close()
        return self._chain.hexdigest()


def read(path):
    with open(path, "rb") as f:
        data = f.read()
    return [RECORD.unpack_from(data, i) for i in range(0, len(data) - len(data) % RECORD.size, RECORD.size)]


def first_divergence(path_a, path_b):
    """None when both traces are identical, else {"step", "turn_a", "turn_b"} of the first differing step
    (a trace that ends early differs at the step where it ends; its turn is None there)."""
    a, b = read(path_a), read(path_b)
    for step in range(max(len(a), len(b))):
        ra = a[step] if step < len(a) else None
        rb = b[step] if step < len(b) else None
        if ra != rb:
            return {"step": step, "turn_a": ra and ra[1], "turn_b": rb and rb[1]}
    return None
