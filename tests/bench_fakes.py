"""Test doubles for the bench server: a worker that plays instantly."""


class FakeWorker:
    """Plays instantly: each play() makes one result from make(sha, index)."""

    def __init__(self, sha, make, log, seeded=True):
        self.sha, self.make, self.log, self.seeded = sha, make, log, seeded
        self.pending, self.dead, self.closed = [], False, False
        self.seeds = []

    def play(self, seed=None):
        if self.dead:
            raise BrokenPipeError
        self.log.append(self.sha)
        self.seeds.append(seed)
        result = dict(self.make(self.sha, len(self.log)))
        if self.seeded and seed is not None:  # a commit from before seeding leaves it out
            result["seed"] = seed
        self.pending.append(result)

    def results(self):
        out, self.pending = self.pending, []
        return out

    def alive(self):
        return not self.dead

    def close(self):
        self.closed = True


def game(depth):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", "outcome": "died"}
