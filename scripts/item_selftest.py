"""Drive one item primitive directly on a staged start and print what happened (Phase 02.2 Part 1a D-09).

    PYTHONHASHSEED=0 .venv/bin/python scripts/item_selftest.py levitation --seeds 1-6

Primitives that no natural-play rule calls yet (levitation on/off, playing a tune) are tested here: the bot's
own strategy is replaced by the check, which ends the game. Staged games only, never bench data.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoascend.env_wrapper import EnvWrapper  # noqa: E402
from autoascend.exceptions import AgentFinished  # noqa: E402
from nethack_screensaver import fixed_clock, staging  # noqa: E402
from nethack_screensaver.game import AGENT_ARGS, CHARACTER  # noqa: E402


def check_levitation(agent):
    inv = agent.inventory
    out = {"before": inv.levitating()}
    out["on"] = inv.start_levitation()
    out["floating"] = inv.levitating()
    out["off"] = inv.stop_levitation()
    out["msg"] = agent.message
    out["after"] = inv.levitating()
    out["ok"] = out["on"] and out["floating"] and out["off"] and not out["after"]
    return out


def check_tune(agent):
    message = agent.inventory.play_tune("CDEFG")
    tail = (message or "")[-160:]
    return {"message": tail, "ok": message is not None and "CDEFG" in message and not tail.rstrip().endswith("]")}


CHECKS = {"levitation": ("kit-levitation", check_levitation), "tune": ("kit-levitation", check_tune),
          "levitation-boots": ("kit-levitation-boots", check_levitation)}


class _Check:
    def __init__(self, agent, fn, sink):
        self.agent, self.fn, self.sink = agent, fn, sink

    def run(self):
        self.sink.update(self.fn(self.agent))
        raise AgentFinished()


def run(name, seed):
    stage_name, fn = CHECKS[name]
    stage = staging.STAGES[stage_name]
    fixed_clock.pin(seed)
    env = staging.StagedChallenge(no_progress_timeout=1000, fix_moon_phase=True, character=CHARACTER)
    type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False)
    result = {}
    wrapper = EnvWrapper(env, agent_args=dict(AGENT_ARGS), prepare=lambda e, obs: staging.apply_stage(e, stage))
    obs = wrapper.reset()
    import autoascend.agent as agent_lib
    agent = agent_lib.Agent(wrapper, **wrapper.agent_args)
    wrapper.agent = agent
    agent.global_logic.global_strategy = lambda: _Check(agent, fn, result)
    try:
        agent.main()
    except Exception as e:  # report, do not hide
        result.setdefault("error", f"{type(e).__name__}: {e}")
    finally:
        env.close()
    return result


def seeds(text):
    lo, _, hi = text.partition("-")
    return range(int(lo), int(hi or lo) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("check", choices=sorted(CHECKS))
    ap.add_argument("--seeds", default="1-6")
    args = ap.parse_args()
    ok = 0
    for seed in seeds(args.seeds):
        r = run(args.check, seed)
        ok += bool(r.get("ok"))
        print(seed, r)
    print(f"{args.check}: {ok}/{len(seeds(args.seeds))} ok")


if __name__ == "__main__":
    main()
