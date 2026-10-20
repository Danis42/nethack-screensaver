"""Test doubles for the bench server: a worker that plays instantly."""


class FakeWorker:
    """Plays instantly: each play() makes one result from make(sha, index)."""

    def __init__(self, sha, make, log):
        self.sha, self.make, self.log = sha, make, log
        self.pending, self.dead, self.closed = [], False, False

    def play(self):
        if self.dead:
            raise BrokenPipeError
        self.log.append(self.sha)
        self.pending.append(self.make(self.sha, len(self.log)))

    def results(self):
        out, self.pending = self.pending, []
        return out

    def alive(self):
        return not self.dead

    def close(self):
        self.closed = True


def game(depth):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", "outcome": "died"}
