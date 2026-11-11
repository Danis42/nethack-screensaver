from collections import defaultdict

import numpy as np

from . import character


class StatsLogger:
    def __init__(self):
        self._values = {
            "agent_panic": 0,
            "medusa_no_levitation": 0,
            "medusa_no_reflection": 0,
            "medusa_no_target": 0,
            "medusa_levitate": 0,
            "medusa_landed": 0,
            "stair_escape": 0,
            "medusa_interrupted": 0,
            "stair_escape_failed": 0,
            "medusa_landed_at_door": 0,
            "telepathy_attempt": 0,
            "telepathy_eye_killed": 0,
            "telepathy_eye_eaten": 0,
            "telepathy_eye_corpse_gone": 0,
            "telepathy_no_blindfold": 0,
            "stoning_cure_eaten": 0,
            "deadly_trouble_prayer": 0,
            "elbereth_write": 0,
            "container_untrap_success": 0,
            "force_lock_success": 0,
            "force_lock_fail": 0,
            "force_lock_destroyed": 0,
            "force_lock_no_blade": 0,
            "container_untrap_fail": 0,
            "untrap_success": 0,
            "triggered_undetected_trap": 0,
            "allow_walk_traps": 0,
            "allow_attack_all": 0,
            "sokoban_dropped": 0,
            "sokoban_live_solved": 0,
            "drop_to_lighten_load": 0,
            "unstick": 0,
            "stuck_dive": 0,
            "stuck_diving": 0,
            "wait_in_fight": 0,
            "melee_gas_spore": 0,
            "ad_aerarium_below_me": 0,
            "drop_gold": 0,
            "ladder_error": 0,
            "ladder_truth_error": 0,
            "stuck_report_error": 0,
            "shop_door_spared": 0,
            "standoff_ignored": 0,
            "zap_empty_wand": 0,
            "dig_fell": 0,
            "dig_undiggable": 0,
            "dig_stopped": 0,
            "dig_no_tool": 0,
            "dig_no_square": 0,
            "dig_no_prompt": 0,
            "quest_portal_level_seen": 0,
            "quest_portal_entered": 0,
            "quest_portal_left": 0,
            "quest_portal_gave_up": 0,
            "boulder_push_try": 0,
            "boulder_pushed": 0,
            # item skills (Phase 02.2 Part 1a)
            "put_on": 0,
            "remove": 0,
            "read_scroll": 0,
            "read_unknown_scroll": 0,
            "sell_offer_id": 0,  # price-ID step 3: a sell offer narrowed a scroll (shop_sell.py)
            "sell_offer_mismatch": 0,  # an offer no remaining identity fits (formula check)
            "unihorn": 0,
            "wish": 0,
            "levitation_on": 0,
            "levitation_off": 0,
            "play_tune": 0,
            "rise_one_level": 0,
            **{f"cast_{n}": 0 for n in character.ALL_SPELL_NAMES},
            **{f"cast_fail_{n}": 0 for n in character.ALL_SPELL_NAMES},
        }
        self._max_values = {
            "search_diff": -float('inf'),
        }

        self._cumulative_values = {
            "max_turns_on_position": defaultdict(int),
        }

        self.gold_stats = ['mean', 'median', 'std', 'min', 'max', 'first', 'last']
        self._keys = list(self._values) + list(self._max_values) + list(self._cumulative_values) + self.gold_stats

        self.gold = []

    def log_cumulative_value(self, name, key, value):
        self._cumulative_values[name][key] += value

    def log_event(self, name):
        self._values[name] += 1

    def add(self, name, n=1):
        self._values[name] += n

    def counters(self):
        """The non-zero event counters as plain ints."""
        return {name: int(v) for name, v in self._values.items() if v}

    def log_gold(self, amount):
        self.gold.append(amount)

    def log_max_value(self, name, value):
        self._max_values[name] = max(self._max_values[name], value)

    def get_stats_dict(self):
        ret = dict()
        ret.update(self._values)
        ret.update(self._max_values)
        ret.update({k: max(v.values()) for k, v in self._cumulative_values.items()})

        for stat in self.gold_stats:
            try:
                ret['gold_' + stat] = getattr(np, stat)(self.gold)
            except AttributeError:
                if stat == 'first':
                    ret['gold_' + stat] = max(self.gold[:20])
                elif stat == 'last':
                    ret['gold_' + stat] = self.gold[-1]
                else:
                    assert 0, stat
        return ret
