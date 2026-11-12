"""The decision test of the bench: paired outcomes in, a verdict out (MEAS-06).

Per seed the candidate and the baseline each succeed or fail at the declared metric. Only the
discordant seeds carry information: b = candidate-only successes, c = baseline-only successes.
Everything below depends on (b, c) alone.

- ``mcnemar_exact``: exact conditional McNemar (binomial test of b against b + c at 1/2). Valid at
  one pre-declared sample size only; peeking inflates its false-positive rate.
- ``log_mixture_lr`` / ``judge_sequential``: an always-valid test. A Beta(a, a) mixture over the
  chance that a discordant pair favours the candidate is tested against 1/2. Its likelihood ratio is
  a nonnegative martingale under the null, so by Ville's inequality the chance that it ever reaches
  1/alpha is at most alpha, however often the owner looks (Johari, Pekelis, Walsh, "Always valid
  inference", arXiv 1512.04922). Validated by scripts/sim_sequential.py (committed report
  01-SIM-SEQUENTIAL.json), not only by citation.

Looks must be contiguous seed prefixes: every seed lo .. lo+n-1 finished on both sides. Never look at
"the games finished so far": long games finish later, so completion order depends on the outcome and
breaks the martingale argument (``contiguous_prefix`` finds the prefix).

Standard library and scipy only.
"""
import math
from dataclasses import asdict, dataclass

from scipy.stats import binomtest

NO_EFFECT = "no detectable effect >= MDE"
PRIOR_A = 1.0


def discordant(pairs):
    """(b, c) from (candidate, baseline) outcomes per seed."""
    b = sum(1 for cand, base in pairs if cand and not base)
    c = sum(1 for cand, base in pairs if base and not cand)
    return b, c


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value; 1.0 without discordant pairs."""
    if b + c == 0:
        return 1.0
    return float(binomtest(b, b + c, 0.5).pvalue)


def log_mixture_lr(b, c, a=PRIOR_A):
    """log of the Beta(a, a) mixture likelihood ratio against theta = 1/2, in log space."""
    if b + c == 0:
        return 0.0
    return (math.lgamma(b + a) + math.lgamma(c + a) - math.lgamma(b + c + 2 * a)
            - (2 * math.lgamma(a) - math.lgamma(2 * a)) + (b + c) * math.log(2))


def anytime_p(max_log_lr):
    """Always-valid p-value from the running maximum of the log likelihood ratio."""
    return min(1.0, math.exp(-max_log_lr))


@dataclass(frozen=True)
class SeqVerdict:
    state: str  # better | worse | NO_EFFECT | open
    n: int
    b: int
    c: int
    estimate: float  # (b - c) / n
    log_lr: float
    max_log_lr: float
    anytime_p: float
    mcnemar_p: float  # descriptive when earlier looks were taken
    n_planned: int
    mde: float

    def as_dict(self):
        return asdict(self)


def judge_sequential(looks, alpha, n_planned, mde, a=PRIOR_A):
    """looks: cumulative (n, b, c) per contiguous-prefix look, in order. Stops at the first look whose
    log LR reaches log(1/alpha): better if b > c, else worse. No crossing: NO_EFFECT once the last look
    reaches n_planned, otherwise open."""
    if not looks:
        raise ValueError("no looks")
    bound = math.log(1 / alpha)
    max_log_lr = 0.0
    state = None
    for n, b, c in looks:
        log_lr = log_mixture_lr(b, c, a)
        max_log_lr = max(max_log_lr, log_lr)
        if log_lr >= bound:
            state = "better" if b > c else "worse"
            break
    if state is None:
        state = NO_EFFECT if n >= n_planned else "open"
    return SeqVerdict(state, n, b, c, (b - c) / n if n else 0.0, log_lr, max_log_lr,
                      anytime_p(max_log_lr), mcnemar_exact(b, c), n_planned, mde)


def contiguous_prefix(seeds_done, lo):
    """How many consecutive seeds lo, lo + 1, ... are in seeds_done."""
    n = 0
    while lo + n in seeds_done:
        n += 1
    return n
