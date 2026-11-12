"""RED placeholder: every function returns an empty value so the tests fail on their assertions."""
NO_EFFECT = "no detectable effect >= MDE"
PRIOR_A = 1.0


def discordant(pairs):
    return (0, 0)


def mcnemar_exact(b, c):
    return 0.0


def log_mixture_lr(b, c, a=PRIOR_A):
    return 0.0


def anytime_p(max_log_lr):
    return 0.0


class SeqVerdict:
    pass


def judge_sequential(looks, alpha, n_planned, mde, a=PRIOR_A):
    return None


def contiguous_prefix(seeds_done, lo):
    return -1
