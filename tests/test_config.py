from nethack_screensaver.config import Config, load_config


def test_missing_file_gives_defaults(tmp_path):
    assert load_config(tmp_path / "nope.toml") == Config()


def test_overrides(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('delay = 0.05\nstatus_line = true\nrole = "val"\nend_pause = 2\n')
    c = load_config(p)
    assert c.delay == 0.05 and c.status_line is True and c.role == "val"
    assert c.end_pause == 2.0


def test_invalid_values_fall_back(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text('delay = "fast"\nrole = "dragon"\nlevel_pause = -1\nbogus = 1\n')
    c = load_config(p)
    assert c == Config()
    err = capsys.readouterr().err
    assert "delay" in err and "role" in err and "level_pause" in err


def test_malformed_toml_gives_defaults(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text("delay = = 1\n")
    assert load_config(p) == Config()
    assert "config" in capsys.readouterr().err


def test_non_finite_and_huge_values_fall_back(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text("delay = inf\nlevel_pause = 120\nend_pause = nan\n")
    assert load_config(p) == Config()
    err = capsys.readouterr().err
    assert "delay" in err and "level_pause" in err and "end_pause" in err


def test_non_utf8_file_gives_defaults(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_bytes(b"delay = 0.2\n\xff\xfe\n")
    assert load_config(p) == Config()
    assert "config" in capsys.readouterr().err


def test_strategy_and_reveal(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text('strategy = "treasure"\nreveal_goal = true\n')
    c = load_config(p)
    assert c.strategy == "treasure" and c.reveal_goal is True
    p.write_text('strategy = "speedrun"\nreveal_goal = "yes"\n')
    assert load_config(p) == Config()
    err = capsys.readouterr().err
    assert "strategy" in err and "reveal_goal" in err


def test_ascension_route_is_the_default_and_random_brings_the_mix_back(tmp_path):
    assert Config().strategy == "pilgrim"
    p = tmp_path / "c.toml"
    p.write_text('strategy = "random"\n')
    assert load_config(p).strategy == "random"


def test_non_string_strategy_falls_back_instead_of_crashing(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text('strategy = ["x"]\n')
    assert load_config(p) == Config()
    assert "strategy" in capsys.readouterr().err
