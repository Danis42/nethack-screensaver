import numpy as np

from nethack_screensaver import snapshots as sn


def obs(turn=1, depth=1, hp=16, hpmax=16, ac=6, xl=1, dnum=0, dlevel=1, message="", inv=()):
    bl = np.zeros(27, dtype=np.int64)
    bl[sn.STR125], bl[sn.DEX], bl[sn.CON] = 18, 14, 17
    bl[sn.HP], bl[sn.HPMAX], bl[sn.DEPTH], bl[sn.AC] = hp, hpmax, depth, ac
    bl[sn.XL], bl[sn.TIME], bl[sn.DNUM], bl[sn.DLEVEL] = xl, turn, dnum, dlevel
    strs = np.zeros((55, 80), dtype=np.uint8)
    letters = np.zeros(55, dtype=np.uint8)
    classes = np.full(55, 18, dtype=np.uint8)
    for i, (letter, oclass, text) in enumerate(inv):
        strs[i, :len(text)] = np.frombuffer(text.encode(), dtype=np.uint8)
        letters[i], classes[i] = ord(letter), oclass
    msg = np.zeros(256, dtype=np.uint8)
    msg[:len(message)] = np.frombuffer(message.encode(), dtype=np.uint8)
    return {"blstats": bl, "inv_strs": strs, "inv_letters": letters, "inv_oclasses": classes, "message": msg}


KIT = (("a", 2, "a +1 long sword (weapon in hand)"),
       ("b", 2, "a +0 dagger (alternate weapon; not wielded)"),
       ("c", 3, "an uncursed +3 small shield (being worn)"),
       ("d", 7, "an uncursed food ration"),
       ("e", 7, "2 uncursed food rations"))


def test_first_arrival_per_depth_is_kept_once():
    rec = sn.Recorder()
    rec.observe(obs(turn=1, depth=1, inv=KIT))
    rec.observe(obs(turn=900, depth=2, ac=4))
    rec.observe(obs(turn=950, depth=1))
    rec.observe(obs(turn=990, depth=2, ac=0))
    out = rec.result()
    assert sorted(out["depth"]) == ["1", "2"]
    assert out["depth"]["2"]["turn"] == 900 and out["depth"]["2"]["ac"] == 4
    first = out["depth"]["1"]
    assert first["gear"] == ["a +1 long sword (weapon in hand)", "a +0 dagger (alternate weapon; not wielded)",
                             "an uncursed +3 small shield (being worn)"]
    assert first["counts"] == {"weapon": 2, "armor": 1, "food": 3}
    assert first["str"] == 18 and first["dex"] == 14 and first["xl"] == 1 and first["hp"] == 16


def test_rung_snapshot_taken_when_a_new_rung_appears():
    rec = sn.Recorder()
    rec.observe(obs(turn=10), rungs=())
    rec.observe(obs(turn=1200, depth=3, dnum=2, dlevel=3), rungs=("mines",))
    rec.observe(obs(turn=1300, depth=4, dnum=2, dlevel=4), rungs=("mines",))
    out = rec.result()
    assert list(out["rung"]) == ["mines"] and out["rung"]["mines"]["turn"] == 1200
    assert out["rung"]["mines"]["dungeon"] == 2


def test_kills_and_damage_taken_are_counted():
    rec = sn.Recorder()
    rec.observe(obs(turn=1, hp=16))
    rec.observe(obs(turn=2, hp=12, message="The jackal bites!"))
    rec.observe(obs(turn=3, hp=12, message="You kill the jackal!"))
    rec.observe(obs(turn=4, hp=20, hpmax=20, message="You hit the newt.  You kill the newt!"))
    rec.observe(obs(turn=5, hp=19, message="You destroy the kobold zombie!"))
    end = rec.result()["end"]
    assert end["kills"] == 3 and end["damage_taken"] == 5


def test_end_ignores_the_all_zero_final_observation():
    rec = sn.Recorder()
    rec.observe(obs(turn=700, hp=3, inv=KIT))
    final = obs()
    final["blstats"][:] = 0
    rec.observe(final)
    end = rec.result()["end"]
    assert end["turn"] == 700 and end["hp"] == 3 and len(end["inventory"]) == 5


def test_before_end_is_the_latest_sample_at_least_200_turns_back():
    rec = sn.Recorder()
    for t in range(1, 1001):
        rec.observe(obs(turn=t, hp=t % 50 + 1))
    out = rec.result()
    assert out["end"]["turn"] == 1000
    assert out["before_end"]["turn"] == 800


def test_short_game_has_no_before_end():
    rec = sn.Recorder()
    for t in range(1, 150):
        rec.observe(obs(turn=t))
    assert rec.result()["before_end"] is None


def test_empty_recorder_gives_empty_result():
    assert sn.Recorder().result() == {"depth": {}, "rung": {}, "end": None, "before_end": None}
