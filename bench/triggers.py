"""Trigger-gated experiments: the candidate plays only the seeds where its change can fire (owner-approved
2026-11-17, quick task 261117-l4a).

Why it is exact: a commit replays its own seeded games exactly (A/A job 8, 1,999 of 1,999). A candidate's game can
only leave the baseline's once the game reaches a state where the candidate's code acts differently. When a stored
baseline game never reaches the change's trigger, the candidate would play the same game: a concordant pair, which
adds nothing to b or c, the only inputs of both decision rules (bench/sequential.py, bench/sprt.py). The estimate
(b - c) / n keeps every seed in n.

The trigger is a claim about the change, so it is checked: every untriggered seed with seed % AUDIT_EVERY == 0
(and any untriggered seed that already has a candidate game) is played, and one whose candidate game differs from
the baseline game fails the job. A trigger is a pure function of one stored game, like a metric
(bench/metrics.py); it raises KeyError for a game without the visit log (nethack_screensaver/visits.py).
Standard library only."""

AUDIT_EVERY = 10
GNOMISH_MINES = 2  # NetHack's dungeon number of the Mines (autoascend/level.py Level.GNOMISH_MINES)
# Milestones whose plan wants the hero in the Mines: plan 02-05's stairs.MINES_MILESTONES (branch
# mines-follow-plan). DIVE counts: a diver that lands in the Mines dives them.
MINES_WANTED = frozenset({"FIND_GNOMISH_MINES", "FIND_MINETOWN", "EXPLORE_MINETOWN", "FIND_MINES_END", "DIVE"})


def _visits(game):
    return game["snapshots"]["visits"]  # KeyError: a game recorded before the visit log


def mines_unwanted(game):
    """On a Gnomish Mines level under a milestone that does not want the Mines (plan 02-05's _on_wrong_branch)."""
    return any(int(place.split(":")[0]) == GNOMISH_MINES and any(m not in MINES_WANTED for m in v["milestones"])
               for place, v in _visits(game).items())


TRIGGERS = {
    "mines_unwanted": mines_unwanted,
}

SAME = ("turns", "end_reason", "max_depth", "score")  # one seeded game replayed exactly matches on all of these


def check(store, baseline, lo, hi, key, trigger):
    """Refuse an experiment whose trigger is unknown or whose stored baseline games lack the visit log."""
    if trigger not in TRIGGERS:
        raise ValueError(f"trigger must be one of {sorted(TRIGGERS)}, got {trigger!r}")
    games = store.games(baseline, limit=1, lo=lo, hi=hi, **key)
    try:
        if games:
            _visits(games[0])
    except KeyError:
        raise ValueError(f"baseline {baseline[:10]} games have no visit log; play a baseline with a commit that "
                         "records visits (nethack_screensaver/visits.py)") from None


class View:
    """The scheduler's reads of the store for one job. Without a trigger it passes the store through. With one, a
    candidate seed whose stored baseline game is untriggered and not audited counts as played, with the baseline
    game standing in for the candidate's; a seed whose baseline game is not stored yet is held back."""

    def __init__(self, store, job):
        self.store = store
        spec = job["spec"]
        self.trigger = TRIGGERS[spec["trigger"]] if spec.get("trigger") else None
        self.candidate, self.baseline = spec.get("candidate"), spec.get("baseline")
        self.key = job.get("key", {})
        self.skip = {}  # seed -> True (stand-in from the baseline) or False (the candidate plays it)
        self.error = None

    def _known(self, lo, hi):
        """Decide every seed of [lo, hi) whose baseline game is stored; return the seeds still undecided."""
        todo = [s for s in range(lo, hi) if s not in self.skip]
        if todo:
            for game in self.store.games(self.baseline, lo=min(todo), hi=hi, **self.key):
                seed = game.get("seed")
                if seed is not None and seed not in self.skip:
                    try:
                        fires = self.trigger(game)
                    except KeyError:  # no visit log in this game: play it
                        fires = True
                    self.skip[seed] = not fires and seed % AUDIT_EVERY != 0
        return {s for s in range(lo, hi) if s not in self.skip}

    def _gated(self, sha):
        return self.trigger is not None and sha == self.candidate

    def seeds(self, sha, lo, hi, **key):
        real = self.store.seeds(sha, lo, hi, **key)
        if not self._gated(sha):
            return real
        held = self._known(lo, hi)
        return real | held | {s for s in range(lo, hi) if self.skip.get(s)}

    def played(self, sha, lo, hi, **key):
        if not self._gated(sha):
            return self.store.played(sha, lo, hi, **key)
        self._known(lo, hi)
        real = self.store.seeds(sha, lo, hi, **key)
        return len(real | {s for s in range(lo, hi) if self.skip.get(s)})

    def games_by_seed(self, sha, seeds, **key):
        """Stored games, plus baseline stand-ins for skipped candidate seeds. Returns {} and sets self.error when
        an untriggered seed's candidate game differs from its baseline game (the scheduler then fails the job)."""
        out = self.store.games_by_seed(sha, seeds, **key)
        if not self._gated(sha):
            return out
        base = self.store.games_by_seed(self.baseline, seeds, **key)
        for seed in seeds:
            if seed in out and seed in base and self.skip.get(seed) is not None:
                if not self._fires(base[seed]) and any(out[seed].get(f) != base[seed].get(f) for f in SAME):
                    self.error = (f"trigger missed a divergence: seed {seed} is untriggered in the baseline but the "
                                  "candidate played it differently; the trigger does not cover the change")
                    return {}
            elif self.skip.get(seed) and seed in base:
                out[seed] = base[seed]
        return out

    def _fires(self, game):
        try:
            return self.trigger(game)
        except KeyError:
            return True
