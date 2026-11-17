import pytest

from bench_fakes import FakeWorker
from bench.scheduler import Scheduler
from bench.store import Store
from bench.triggers import AUDIT_EVERY, TRIGGERS, View, check, mines_unwanted

SPRT = {"test": "sprt-wald", "rule": "sprt", "mde": 0.1, "psi": 0.3, "alpha": 0.05, "power": 0.8, "block": 96,
        "n_planned": 192, "mcnemar_mde_at_n": 0.08}
LO, HI = 1000, 1192


def visits(*places):
    return {"snapshots": {"visits": {p: {"turn": 1, "milestones": list(m)} for p, m in places}}}


def base_game(seed, triggered):
    places = [("0:1", ["FIND_SOKOBAN"])] + ([("2:3", ["FIND_SOKOBAN"])] if triggered else [])
    return {"max_depth": 3, "turns": 900 + seed, "score": 10, "end_reason": "DEATH: killed by a newt",
            "outcome": "died", "seed": seed, **visits(*places)}


def test_mines_unwanted_fires_only_in_the_mines_under_an_unwanted_milestone():
    assert mines_unwanted(visits(("2:3", ["FIND_SOKOBAN"])))
    assert mines_unwanted(visits(("2:2", ["FIND_MINETOWN", "SOLVE_SOKOBAN"])))
    assert not mines_unwanted(visits(("2:3", ["FIND_MINETOWN", "DIVE"])))
    assert not mines_unwanted(visits(("0:5", ["FIND_SOKOBAN"]), ("4:1", ["SOLVE_SOKOBAN"])))


def test_a_game_without_the_visit_log_raises_key_error():
    with pytest.raises(KeyError):
        mines_unwanted({"snapshots": {"depth": {}}})


class SeedWorker(FakeWorker):
    """Plays the game make(sha, seed) for the asked seed."""

    def play(self, seed=None, lgen=None):
        self.log.append((self.sha, seed))
        self.pending.append({**self.make(self.sha, seed), "seed": seed})


def _setup(tmp_path, triggered, cand_game):
    store = Store(tmp_path / "r.db")
    for seed in range(LO, HI):
        store.add_game("base", None, base_game(seed, triggered(seed)))
    played = []
    sched = Scheduler(store, lambda sha: SeedWorker(sha, cand_game, played), slots=4)
    job = sched.submit("experiment", {"candidate": "cand", "candidate_ref": "b", "baseline": "base",
                                      "baseline_ref": "main", "metric": "dlvl6", "trigger": "mines_unwanted",
                                      "seeds": {"range": "dev", "lo": LO, "hi": HI}, "block": 96, "declared": SPRT})
    return sched, store, job, played


def _run(sched):
    for _ in range(5000):
        sched.tick()
        if sched.job is None and sched.store.next_queued() is None:
            return
    raise AssertionError("job did not finish")


def test_the_candidate_plays_only_triggered_and_audit_seeds_and_wins_on_them(tmp_path):
    triggered = lambda seed: seed % 3 == 0
    def cand_game(sha, seed):
        g = base_game(seed, triggered(seed))
        return {**g, "max_depth": 7} if triggered(seed) else g  # the change helps where it fires
    sched, store, job, played = _setup(tmp_path, triggered, cand_game)
    _run(sched)
    seeds = {s for _sha, s in played}
    expected = {s for s in range(LO, HI) if triggered(s) or s % AUDIT_EVERY == 0}
    assert seeds <= expected and {s for s in range(LO, LO + 96) if triggered(s)} <= seeds
    v = store.job(job)["result"]["verdict"]
    assert v["state"] == "better" and v["c"] == 0 and v["b"] > 0
    assert v["pairs"] == v["n"]  # skipped seeds count in n as concordant pairs


def test_an_audit_seed_that_diverges_fails_the_job(tmp_path):
    triggered = lambda seed: seed % 3 == 0
    def cand_game(sha, seed):  # the change also acts where the trigger says it cannot
        return {**base_game(seed, triggered(seed)), "max_depth": 7, "turns": 5}
    sched, store, job, _ = _setup(tmp_path, triggered, cand_game)
    _run(sched)
    j = store.job(job)
    assert j["state"] == "failed" and "trigger missed a divergence" in j["result"]["error"]


def test_without_a_trigger_the_view_passes_the_store_through(tmp_path):
    store = Store(tmp_path / "r.db")
    store.add_game("cand", None, {**base_game(LO, False)})
    view = View(store, {"spec": {"candidate": "cand", "baseline": "base"}, "key": {}})
    assert view.seeds("cand", LO, HI) == store.seeds("cand", LO, HI)
    assert view.played("cand", LO, HI) == 1
    assert view.games_by_seed("cand", range(LO, HI)) == store.games_by_seed("cand", range(LO, HI))


def test_a_candidate_seed_waits_for_its_baseline_game(tmp_path):
    store = Store(tmp_path / "r.db")
    store.add_game("base", None, base_game(LO + 1, False))
    view = View(store, {"spec": {"candidate": "cand", "baseline": "base", "trigger": "mines_unwanted"}, "key": {}})
    taken = view.seeds("cand", LO, LO + 3)
    assert LO in taken and LO + 2 in taken  # baseline not stored yet: held back
    assert LO + 1 in taken and view.played("cand", LO, LO + 3) == 1  # untriggered, not audited: skipped


def test_check_refuses_unknown_triggers_and_baselines_without_visit_logs(tmp_path):
    store = Store(tmp_path / "r.db")
    store.add_game("old", None, {"max_depth": 1, "end_reason": "x", "seed": LO})
    with pytest.raises(ValueError, match="trigger must be one of"):
        check(store, "old", LO, HI, {}, "nope")
    with pytest.raises(ValueError, match="no visit log"):
        check(store, "old", LO, HI, {}, "mines_unwanted")
    store.add_game("new", None, base_game(LO, False))
    check(store, "new", LO, HI, {}, "mines_unwanted")
    assert set(TRIGGERS) == {"mines_unwanted"}
