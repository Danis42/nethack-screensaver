"""Power, minimum detectable effect (MDE) and sample size for the paired tests of the bench (MEAS-06).

Notation: n = paired seeds, psi = probability that a seed is discordant (candidate and baseline
outcomes differ), delta = P(candidate only) - P(baseline only), theta = (psi + delta) / (2 psi) = the
chance that a discordant pair favours the candidate. ND ~ Binomial(n, psi) discordant pairs, and given
ND the candidate-only count b ~ Binomial(ND, theta).

- exact McNemar (``mcnemar_*``): exact power = sum over ND of P(ND) * P(reject | ND, theta), with the
  two-sided exact binomial test at 1/2. Valid at one pre-declared n.
- sequential test (``sequential_*``): the always-valid mixture test of ``bench.sequential``, looked at
  every ``block`` seeds up to n_max; power is simulated with a fixed seed, so it is deterministic.

psi is not known until the lgen pilot and the baseline exist; callers pass it explicitly.
"""
import math

import numpy as np
from scipy.special import gammaln
from scipy.stats import binom

# Wilson upper 95% bound of psi on dlvl10 with lgen off (b 2, c 0, n 400), rounded up: lgen pilot jobs 3/4/5/6,
# decision in .planning/phases/01-measurement-and-proof-foundation/01-LGEN-PILOT.md. Pitfall 11: this psi comes from
# a small mid-game fight change; pass --discordance for a change expected to diverge games more.
DEFAULT_DISCORDANCE = 0.019

_EXACT_TOL = 1e-5
_SEQ_TOL = 1e-4


def _check(psi=None, n=None, mde=None, delta=None, alpha=None, power=None, block=None):
    if psi is not None and not 0 < psi <= 1:
        raise ValueError(f"psi must be in (0, 1], got {psi}")
    if n is not None and n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    if mde is not None and not 0 < mde <= (psi if psi is not None else 1):
        raise ValueError(f"mde must be in (0, psi], got {mde}")
    if delta is not None and not 0 <= delta <= psi:
        raise ValueError(f"delta must be in [0, psi], got {delta}")
    if alpha is not None and not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if power is not None and not 0 < power < 1:
        raise ValueError(f"power must be in (0, 1), got {power}")
    if block is not None and block < 1:
        raise ValueError(f"block must be at least 1, got {block}")


def mcnemar_power(n, psi, delta, alpha=0.05):
    """Exact power of the two-sided exact McNemar test at n paired seeds."""
    _check(psi=psi, n=n, delta=delta, alpha=alpha)
    nd = np.arange(n + 1)
    weight = binom.pmf(nd, n, psi)
    # largest k with 2 * P(Bin(ND, 1/2) <= k) <= alpha; -1 when even k = 0 is too likely
    k = binom.ppf(alpha / 2, nd, 0.5)
    k = np.where(binom.cdf(k, nd, 0.5) <= alpha / 2 + 1e-12, k, k - 1)
    theta = (psi + delta) / (2 * psi)
    reject = binom.cdf(k, nd, theta) + binom.sf(nd - k - 1, nd, theta)
    return float(np.sum(weight * reject))


def _bisect(func, lo, hi, target, tol):
    """Smallest x in (lo, hi] with func(x) >= target, for a func rising in x; ValueError if hi misses."""
    if func(hi) < target:
        raise ValueError("the target power is not reachable")
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if func(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def mcnemar_mde(n, psi, alpha=0.05, power=0.8):
    """Smallest delta the exact McNemar test finds with the given power, to 1e-5."""
    _check(psi=psi, n=n, alpha=alpha, power=power)
    return _bisect(lambda d: mcnemar_power(n, psi, d, alpha), 0.0, psi, power, _EXACT_TOL)


def sequential_power(n_max, psi, delta, alpha=0.05, block=96, reps=4000, seed=0, a=1.0):
    """Share of simulated experiments the mixture test calls "better" within n_max seeds, looking
    after every block of seeds. Common random numbers across delta (per-block streams and inverse-CDF
    draws), so the result rises with delta and with n_max and is the same float on every call."""
    _check(psi=psi, n=n_max, delta=delta, alpha=alpha, block=block)
    blocks = n_max // block
    if blocks < 1:
        raise ValueError(f"n_max {n_max} is smaller than one block of {block}")
    theta = (psi + delta) / (2 * psi)
    bound = math.log(1 / alpha)
    nd_total = np.zeros(reps)
    b_total = np.zeros(reps)
    alive = np.ones(reps, dtype=bool)   # no crossing yet
    won = np.zeros(reps, dtype=bool)
    const = -(2 * gammaln(a) - gammaln(2 * a))
    for k in range(blocks):
        rng = np.random.default_rng([seed, k])
        nd = rng.binomial(block, psi, reps)
        u = np.clip(rng.random(reps), 1e-12, 1 - 1e-12)
        b = binom.ppf(u, nd, theta)
        nd_total += nd
        b_total += b
        c_total = nd_total - b_total
        log_lr = (gammaln(b_total + a) + gammaln(c_total + a) - gammaln(nd_total + 2 * a)
                  + const + nd_total * math.log(2))
        log_lr = np.where(nd_total == 0, 0.0, log_lr)
        crossed = alive & (log_lr >= bound)
        won |= crossed & (b_total > c_total)
        alive &= ~crossed
        if not alive.any():
            break
    return float(won.mean())


def sequential_mde(n_max, psi, alpha=0.05, power=0.8, block=96, reps=4000, seed=0):
    """Smallest delta the sequential test finds with the given power within n_max seeds, to 1e-4."""
    _check(psi=psi, n=n_max, alpha=alpha, power=power, block=block)
    return _bisect(lambda d: sequential_power(n_max, psi, d, alpha, block, reps, seed), 0.0, psi,
                   power, _SEQ_TOL)


def sequential_sample_size(mde, psi, alpha=0.05, power=0.8, block=96, n_cap=100_000, reps=4000, seed=0):
    """Smallest multiple of block (seeds) at which the sequential test reaches the power for delta = mde."""
    _check(psi=psi, mde=mde, alpha=alpha, power=power, block=block)

    def reaches(blocks):
        return sequential_power(blocks * block, psi, mde, alpha, block, reps, seed) >= power

    cap = n_cap // block
    if cap < 1:
        raise ValueError(f"n_cap {n_cap} is smaller than one block of {block}")
    lo, hi = 0, 1   # lo never reaches the power (zero seeds), hi is the candidate
    while not reaches(hi):
        lo = hi
        if hi >= cap:
            raise ValueError(f"n_cap {n_cap} is not enough for mde {mde} at psi {psi}")
        hi = min(hi * 2, cap)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid
    return hi * block


def plan(mde, psi, alpha=0.05, power=0.8, block=96, reps=4000, seed=0):
    """What to declare before a run: the sequential test, its planned size, and what plain exact
    McNemar could detect at that size."""
    n_planned = sequential_sample_size(mde, psi, alpha, power, block, reps=reps, seed=seed)
    return {"test": "msprt-beta1", "mde": mde, "psi": psi, "alpha": alpha, "power": power,
            "block": block, "n_planned": n_planned,
            "mcnemar_mde_at_n": mcnemar_mde(n_planned, psi, alpha, power)}
