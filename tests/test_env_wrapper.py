from pathlib import Path

import numpy as np

from autoascend.env_wrapper import EnvWrapper
from nle.env.base import NLE

DATA = Path(__file__).parent / "data"


def test_end_reason_includes_cause_of_death():
    obs = {"tty_chars": np.load(DATA / "final_tty_chars.npy")}
    reason = EnvWrapper(env=None)._parse_end_reason(obs, {"end_status": NLE.StepStatus.DEATH})
    assert reason == "DEATH: killed by a werejackal, while fainted from lack of food"


def test_end_reason_falls_back_to_status():
    obs = {"tty_chars": np.zeros((24, 80), dtype=np.uint8)}
    assert EnvWrapper(env=None)._parse_end_reason(obs, {"end_status": NLE.StepStatus.ABORTED}) == "ABORTED"
