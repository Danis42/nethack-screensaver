"""RED placeholder: every function returns an empty value so the tests fail on their assertions."""
DEFAULT_DISCORDANCE = None


def mcnemar_power(n, psi, delta, alpha=0.05):
    return 1.0


def mcnemar_mde(n, psi, alpha=0.05, power=0.8):
    return 0.0


def sequential_power(n_max, psi, delta, alpha=0.05, block=96, reps=4000, seed=0, a=1.0):
    return 0.0


def sequential_mde(n_max, psi, alpha=0.05, power=0.8, block=96, reps=4000, seed=0):
    return 0.0


def sequential_sample_size(mde, psi, alpha=0.05, power=0.8, block=96, n_cap=100_000, reps=4000, seed=0):
    return 0


def plan(mde, psi, alpha=0.05, power=0.8, block=96, reps=4000, seed=0):
    return {}
