"""Adapter between NLE 1.3.0 (gymnasium API) and the AutoAscend agent.

The agent only calls step(), debug_tiles() and debug_log() on this object.
"""
import contextlib

import nle.nethack as nh

from autoascend import agent as agent_lib


def _blstats(obs):
    return agent_lib.BLStats(*obs['blstats'][:len(agent_lib.BLStats._fields)])


def _role_matches(obs, role):
    bl = _blstats(obs)
    glyph = obs['glyphs'][bl.y, bl.x]
    return nh.permonst(nh.glyph_to_mon(glyph)).mname.startswith(role)


class EnvWrapper:
    def __init__(self, env, on_step=None, step_limit=None, role=None, agent_args=None, choose_plan=None,
                 prepare=None):
        self.env = env
        self.on_step = on_step
        self.step_limit = step_limit
        self.role = role
        self.agent_args = agent_args or {}
        self.choose_plan = choose_plan  # obs after reset -> milestone plan
        self.prepare = prepare  # (env, obs after reset) -> obs: sets up a staged game before the bot plays
        self.agent = None
        self.last_observation = None
        self.score = 0
        self.step_count = 0
        self.end_reason = ''
        self.is_done = False

    def main(self):
        obs = self.reset()
        if self.choose_plan is not None:
            self.agent_args = {**self.agent_args, 'plan': self.choose_plan(obs)}
        self.agent = agent_lib.Agent(self, **self.agent_args)
        self.agent.main()

    def reset(self):
        while True:
            obs, _info = self.env.reset()
            if self.role is None or _role_matches(obs, self.role):
                break
        if self.prepare is not None:
            obs = self.prepare(self.env, obs)
        self.score = 0
        self.step_count = 0
        self.end_reason = ''
        self.is_done = False
        self.last_observation = obs

        agent_lib.G.assert_map(obs['glyphs'], obs['chars'])
        bl = _blstats(obs)
        assert obs['chars'][bl.y, bl.x] == ord('@')
        if self.on_step is not None:
            self.on_step(obs)
        return obs

    def render(self, force=False):
        pass

    def step(self, agent_action):
        obs, reward, terminated, truncated, info = self.env.step(
            self.env.actions.index(agent_action))
        done = terminated or truncated
        self.score += reward
        self.step_count += 1
        if done:
            self.end_reason = self._parse_end_reason(obs, info)
        if self.step_limit is not None and self.step_count >= self.step_limit and not done:
            self.end_reason = 'steplimit'
            done = True
        self.last_observation = obs
        if done:
            self.is_done = True
        if self.on_step is not None:
            self.on_step(obs)
        return obs, reward, done, info

    def _parse_end_reason(self, obs, info):
        # Final screen: "... <score>  Agent-<char> died in <place> on level N.  Killed by X, while Y.  - [hp]"
        status = info.get('end_status')
        status_name = getattr(status, 'name', str(status))
        try:
            words = bytes(obs['tty_chars'].reshape(-1)).decode(errors='replace') \
                .replace('You made the top ten list!', '').split()
            idx = next(i for i, w in enumerate(words) if w.startswith('Agent'))
            text = ' '.join(words[idx + 1:-2])
            first, _, rest = text.partition('.')
            cause = rest.strip().rstrip('.') or first.split(' in ')[0].strip()
            if cause.startswith('escaped'):
                # NLE reports escapes with end_status DEATH; the text says otherwise.
                return 'ESCAPED: ' + cause.split(' [')[0]
            return f'{status_name}: {cause[:1].lower()}{cause[1:]}'
        except Exception:
            return status_name

    def debug_tiles(self, *args, **kwargs):
        return contextlib.nullcontext()

    def debug_log(self, *args, **kwargs):
        return contextlib.nullcontext()
