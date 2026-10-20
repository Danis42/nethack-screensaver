"""Intervals for comparing rates, and the checkpoint verdicts of an experiment."""
import math
from dataclasses import asdict, dataclass

CHECKPOINTS = (192, 384, 576, 1152)
Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def wilson(k, n, z):
    """Wilson score interval for k successes out of n."""
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def newcombe(k1, n1, k2, n2, z):
    """Difference p1 - p2 with Newcombe's hybrid score interval (method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    diff = p1 - p2
    return (diff,
            diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def z_for(checkpoint):
    """Stricter early: peeking at several checkpoints would otherwise produce false wins."""
    return Z95 if checkpoint == CHECKPOINTS[-1] else Z99


@dataclass(frozen=True)
class Verdict:
    state: str  # better | worse | no measurable difference | open
    checkpoint: int
    diff: float
    lo: float
    hi: float

    @property
    def detectable(self):
        """Half-width of the interval: smaller real differences could not be seen."""
        return (self.hi - self.lo) / 2

    def as_dict(self):
        return {**asdict(self), "detectable": self.detectable}


def judge(k_cand, n_cand, k_base, n_base, checkpoint):
    if n_cand == 0 or n_base == 0:
        raise ValueError("both sides need games")
    diff, lo, hi = newcombe(k_cand, n_cand, k_base, n_base, z_for(checkpoint))
    if lo > 0:
        state = "better"
    elif hi < 0:
        state = "worse"
    elif checkpoint == CHECKPOINTS[-1]:
        state = "no measurable difference"
    else:
        state = "open"
    return Verdict(state, checkpoint, diff, lo, hi)
