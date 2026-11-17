"""Wald's SPRT on discordant pairs: the bench's default decision rule for new experiments.

Owner-approved 2026-11-17 (quick task 261117-kpa, efficiency research recommendation 2). Same pairing as
``bench.sequential``: per seed the candidate and the baseline succeed or fail at the metric, b = candidate-only
successes, c = baseline-only successes, theta = the chance that a discordant pair favours the candidate.

H0: theta = 1/2. H1: theta1 = 1/2 + s * mde / (2 psi), with psi the declared discordance (share of seeds where
the two commits differ) and s = -1 for a lower-is-better metric, so "better" is always the improvement. This is
how Stockfish's Fishtest decides patches (Fishtest Mathematics wiki), on paired outcomes.

- Upper bound log(1/alpha): stop, "better". Under H0 every discordant pair is a fair coin whatever psi is, so the
  likelihood ratio against any fixed theta1 is a nonnegative martingale, and Ville's inequality keeps
  P(ever a false "better") <= alpha at any number of looks. A wrong psi only costs power.
- Lower bound log((1 - power) / (1 - alpha)) (Wald's B): stop, NO_EFFECT ("no win"). It only ends runs early.
- One-sided: never "worse". The keep rule only needs "better".
- n_planned: the smallest block multiple at which the truncated SPRT reaches the power at the MDE (simulated with
  the common random numbers of ``bench.power.sequential_power``, so a plan repeats exactly).

A plan without ``rule`` (every job declared before this module, e.g. jobs 19-21) keeps the mixture test:
``judge_declared`` and ``plan`` dispatch on it. Validated by scripts/sim_sprt.py.
"""
import math

import numpy as np
from scipy.stats import binom

from . import power as powerlib
from .sequential import NO_EFFECT, SeqVerdict, anytime_p, judge_sequential, mcnemar_exact

RULES = ("sprt", "mixture")


def theta1(mde, psi, lower_is_better=False):
    """theta under H1: the metric moves by mde in the good direction (down for a lower-is-better metric)."""
    if not 0 < mde < psi <= 1:
        raise ValueError(f"need 0 < mde < psi <= 1, got mde {mde}, psi {psi}")
    return 0.5 + (-1 if lower_is_better else 1) * mde / (2 * psi)


def log_lr(b, c, th1):
    """log likelihood ratio of theta1 against 1/2 after b candidate-only and c baseline-only pairs."""
    return b * math.log(2 * th1) + c * math.log(2 * (1 - th1))


def bounds(alpha, power):
    """(lower, upper) on the log LR: Wald's lower bound for the declared power, Ville's upper bound."""
    return math.log((1 - power) / (1 - alpha)), math.log(1 / alpha)


def judge_sprt(looks, alpha, power, n_planned, mde, psi, lower_is_better=False):
    """looks: cumulative (n, b, c) per contiguous-prefix look, in order. Stops at the first look whose log LR
    reaches the upper bound ("better", already oriented for the metric) or the lower bound (NO_EFFECT). No
    crossing: NO_EFFECT once the last look reaches n_planned, otherwise open. anytime_p = exp(-max log LR) is
    valid by the same Ville argument."""
    if not looks:
        raise ValueError("no looks")
    th1 = theta1(mde, psi, lower_is_better)
    lower, upper = bounds(alpha, power)
    max_log_lr, state = 0.0, None
    for n, b, c in looks:
        lr = log_lr(b, c, th1)
        max_log_lr = max(max_log_lr, lr)
        if lr >= upper:
            state = "better"
            break
        if lr <= lower:
            state = NO_EFFECT
            break
    if state is None:
        state = NO_EFFECT if n >= n_planned else "open"
    return SeqVerdict(state, n, b, c, (b - c) / n if n else 0.0, lr, max_log_lr,
                      anytime_p(max_log_lr), mcnemar_exact(b, c), n_planned, mde)


def judge_declared(looks, declared, metric):
    """(verdict, oriented): the declared rule's verdict, and whether its state is already oriented for the metric
    (the SPRT's is; the mixture's still goes through bench.metrics.orient)."""
    if declared.get("rule") == "sprt":
        return judge_sprt(looks, declared["alpha"], declared["power"], declared["n_planned"], declared["mde"],
                          declared["psi"], metric.lower_is_better), True
    return judge_sequential(looks, declared["alpha"], declared["n_planned"], declared["mde"]), False


def run(n_max, psi, delta, mde, alpha=0.05, power=0.8, block=96, reps=4000, seed=0):
    """(share called "better", mean seeds used) for the truncated SPRT planned at mde, when the true effect is
    delta (in the good direction) and the true discordance psi. Same common random numbers as
    bench.power.sequential_power, so the result is the same float on every call and rises with n_max."""
    powerlib._check(psi=psi, n=n_max, delta=delta, alpha=alpha, power=power, block=block)
    th1 = theta1(mde, psi)
    lower, upper = bounds(alpha, power)
    step_w, step_l = math.log(2 * th1), math.log(2 * (1 - th1))
    blocks = n_max // block
    if blocks < 1:
        raise ValueError(f"n_max {n_max} is smaller than one block of {block}")
    theta = (psi + delta) / (2 * psi)
    nd_total, w_total = np.zeros(reps), np.zeros(reps)
    alive, won = np.ones(reps, dtype=bool), np.zeros(reps, dtype=bool)
    used = np.full(reps, float(blocks * block))
    for k in range(blocks):
        rng = np.random.default_rng([seed, k])
        nd = rng.binomial(block, psi, reps)
        u = np.clip(rng.random(reps), 1e-12, 1 - 1e-12)
        nd_total += nd
        w_total += binom.ppf(u, nd, theta)
        lr = w_total * step_w + (nd_total - w_total) * step_l
        up, down = alive & (lr >= upper), alive & (lr <= lower)
        won |= up
        used[up | down] = (k + 1) * block
        alive &= ~(up | down)
        if not alive.any():
            break
    return float(won.mean()), float(used.mean())


def sample_size(mde, psi, alpha=0.05, power=0.8, block=96, n_cap=100_000, reps=4000, seed=0):
    """Smallest multiple of block at which the truncated SPRT reaches the power for delta = mde."""
    powerlib._check(psi=psi, mde=mde, alpha=alpha, power=power, block=block)

    def reaches(blocks):
        return run(blocks * block, psi, mde, mde, alpha, power, block, reps, seed)[0] >= power

    cap = n_cap // block
    if cap < 1:
        raise ValueError(f"n_cap {n_cap} is smaller than one block of {block}")
    lo, hi = 0, 1
    while not reaches(hi):
        lo = hi
        if hi >= cap:
            raise ValueError(f"n_cap {n_cap} is not enough for mde {mde} at psi {psi}: Wald's lower bound stops "
                             "too many runs below the power; raise the MDE or lower the power")
        hi = min(hi * 2, cap)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid
    return hi * block


def plan(mde, psi, alpha=0.05, power=0.8, block=96, rule="sprt", reps=4000, seed=0):
    """What to declare before a run. rule "sprt": the SPRT, its cap, and its power, false-win rate and mean seeds at
    the MDE and at no effect. Those come from a second random stream (seed + 1), not the one that sized the cap,
    so they are honest estimates: Wald's lower bound costs about 1 point of power (0.79 for a declared 0.8 at the
    character A/B settings, scripts/sim_sprt.py); declare a little more power when it matters.
    rule "mixture": bench.power.plan unchanged."""
    if rule == "mixture":
        return powerlib.plan(mde, psi, alpha, power, block, reps=reps, seed=seed)
    if rule != "sprt":
        raise ValueError(f"rule must be one of {RULES}, got {rule!r}")
    n_planned = sample_size(mde, psi, alpha, power, block, reps=reps, seed=seed)
    p_h1, n_h1 = run(n_planned, psi, mde, mde, alpha, power, block, reps, seed + 1)
    p_h0, n_h0 = run(n_planned, psi, 0.0, mde, alpha, power, block, reps, seed + 1)
    return {"test": "sprt-wald", "rule": "sprt", "mde": mde, "psi": psi, "alpha": alpha, "power": power,
            "block": block, "n_planned": n_planned, "theta1": theta1(mde, psi),
            "power_at_mde": p_h1, "mean_seeds_at_mde": n_h1, "false_better_at_0": p_h0, "mean_seeds_at_0": n_h0,
            "mcnemar_mde_at_n": powerlib.mcnemar_mde(n_planned, psi, alpha, power)}


def power_report(mde=None, discordance=None, n=None, alpha=0.05, power=0.8, block=96, rule="sprt"):
    """What an experiment must declare (the server's /api/power and the CLI's `power`): with mde, the plan of the
    rule; with n, the MDE that n seeds can detect with exact McNemar and with the mixture test."""
    psi = powerlib.DEFAULT_DISCORDANCE if discordance is None else float(discordance)
    if psi is None:
        raise ValueError("pass discordance: no pilot value is recorded yet")
    alpha, power, block = float(alpha), float(power), int(block)
    if mde is not None:
        return plan(float(mde), psi, alpha, power, block, rule)
    if n is not None:
        n = int(n)
        return {"n": n, "psi": psi, "mcnemar_mde": powerlib.mcnemar_mde(n, psi, alpha, power),
                "sequential_mde": powerlib.sequential_mde(n, psi, alpha, power, block)}
    raise ValueError("pass mde (to plan a run) or n (to see what n seeds can detect)")
