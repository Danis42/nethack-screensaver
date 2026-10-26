import nle.nethack as nh
import numpy as np
from nle.nethack import actions as A

from . import objects as O
from . import boulders
from . import quest_portal
from . import soko_solver
from .soko_solver import search as soko_search
from . import stuck
from . import utils
from .character import Character
from .exceptions import AgentPanic
from .glyph import Hunger, G, MON, SS
from .item import Item, flatten_items
from .item.item_priority_base import ItemPriorityBase
from .ladder import Facts, Ladder
from .level import Level
from .plans import DEFAULT_PLAN, Milestone, Plan, ProgressWatch

from .strategy import Strategy

TOWN_TURNS = 1000  # sightseer: turns to look around Minetown
LOOT_TURNS = 1500  # treasure: turns on the top Sokoban level to clear the zoo and loot
MINETOWN_SEARCH_TURNS = 4000  # Orcish Town has no shopkeeper, so Minetown may never be seen
SOKOBAN_SEARCH_TURNS = 8000  # treasure: give up looking for Sokoban and go home
# Live Sokoban solver budget, no wall clock so the pushes never depend on machine load. Measured 2026-10-23
# on an idle machine, worst board (soko3-2 minus spare boulders): 40,000 states = 8.4 s, 50,000 = 10.6 s.
SOKOBAN_LIVE_MAX_STATES = 40_000
LIVE_SOKOBAN_BLOCKED_TRIES = 20  # times a monster may block a push square before giving up
WATER = frozenset({SS.S_pool, SS.S_water})
DRAWBRIDGE = frozenset({SS.S_vodbridge, SS.S_hodbridge, SS.S_vcdbridge, SS.S_hcdbridge})
MEDUSA = frozenset({MON.fn('Medusa')})
BOULDER_PUSHES_PER_LEVEL = 30
STUCK_TURNS = 2500  # no new level and no new milestone for this long: give up the route and dive
PORTAL_HUNT_TURNS = 1500  # on the Quest portal level, this long to walk every square for the portal
_PRIZES = None


STONING_CURE_CORPSES = ('lizard', 'acid blob')  # eating one stops petrification (eat.c fix_petrification)


def is_stoning_cure(item):
    return item.is_unambiguous() and item.is_corpse() and \
        item.monster_id in [MON.from_name(n) - nh.GLYPH_MON_OFF for n in STONING_CURE_CORPSES]


def _prize_objects():
    """Bag of holding, amulet of reflection; O.from_name scans the table, so look up once."""
    global _PRIZES
    if _PRIZES is None:
        _PRIZES = {O.from_name('bag of holding'), O.from_name('amulet of reflection')}
    return _PRIZES


def sokoban_board(objects, walkable, glyphs):
    """Floor, boulder and trap cells of the current Sokoban level, for the live solver.

    `objects` only records squares seen bare; squares that always had an item or monster
    on them are known only as walkable. Doorways are left out: boulders can't use them."""
    boulders = utils.isin(glyphs, G.BOULDER)
    traps = utils.isin(objects, G.TRAPS)
    floor = ((utils.isin(objects, G.FLOOR | G.STAIR_UP | G.STAIR_DOWN) | walkable)
             & ~utils.isin(objects, G.DOORS | G.WALL)) | traps | boulders
    cells = lambda mask: {(int(y), int(x)) for y, x in zip(*mask.nonzero())}
    return cells(floor), cells(boulders), cells(traps)


def dive_stairs(dungeon_number, objects, stair_destination, bfs, mines=False):
    """Known, reachable downstairs that stay in this dungeon: the main one, or the Gnomish
    Mines while diving there (`mines`); a diver stuck in the Mines used to climb back out."""
    if dungeon_number != Level.DUNGEONS_OF_DOOM and not (mines and dungeon_number == Level.GNOMISH_MINES):
        return []  # the bot also travels up through branches; diving there would loop
    return [(y, x) for y, x in zip(*utils.isin(objects, G.STAIR_DOWN).nonzero())
            if bfs[y, x] != -1 and
            (stair_destination.get((y, x)) is None or
             stair_destination[(y, x)][0][0] == dungeon_number)]


class ItemPriority(ItemPriorityBase):
    MAX_NUMBER_OF_ITEMS = 26 * 2 - 1  # + coin slot, one slot should be left for item arranging
    def __init__(self, agent):
        self.agent = agent
        self._take_sacrificial_corpses = False
        self._drop_gold_till_turn = -float('inf')

    def _split(self, items, forced_items, weight_capacity):
        remaining_weight = weight_capacity
        ret_inv = {}
        for item in forced_items:
            remaining_weight -= item.weight()
            ret_inv[item] = item.count

        ret_bag = {}
        bag = None

        def add_item(item, count=None, to_bag=False):
            nonlocal ret_inv, ret_bag, remaining_weight
            assert isinstance(item, Item)
            if to_bag and bag is not None and item is not bag:
                ret = ret_bag
            else:
                ret = ret_inv

            if remaining_weight < 0 or \
                    (ret is ret_inv and len(ret) >= ItemPriority.MAX_NUMBER_OF_ITEMS):  # TODO: coin slot
                return

            how_many_already_total = ret_inv.get(item, 0) + ret_bag.get(item, 0)
            how_many_already = ret.get(item, 0)
            max_to_add = int(remaining_weight // item.unit_weight(with_content=False))
            if count is not None:
                max_to_add = min(max_to_add, count)
            ret[item] = min(item.count, how_many_already_total + max_to_add) - (how_many_already_total - how_many_already)
            remaining_weight -= item.unit_weight(with_content=False) * (ret[item] - how_many_already)

        for item in self.agent.global_logic.prize_pickups(items):
            add_item(item)

        for item in items:
            if item.is_container() and item.status in [Item.UNCURSED, Item.BLESSED] and item.objs[0].desc == 'bag':
                bag = item  # TODO: select the best
                add_item(bag)

        if self._drop_gold_till_turn < self.agent.blstats.time:
            for item in items:
                if item.category == nh.COIN_CLASS:
                    add_item(item)

        for allow_unknown_status in [False, True]:
            item = self.agent.inventory.get_best_melee_weapon(items=forced_items + items,
                                                              allow_unknown_status=allow_unknown_status)
            if item is not None:
                add_item(item)

            for item in self.agent.inventory.get_best_armorset(items=forced_items + items,
                                                               allow_unknown_status=allow_unknown_status):
                if item is not None:
                    add_item(item)

        for item in items:
            if item.is_unambiguous():
                if item.object in [
                        O.from_name('healing', nh.POTION_CLASS),
                        O.from_name('extra healing', nh.POTION_CLASS),
                        O.from_name('full healing', nh.POTION_CLASS)]:
                    add_item(item)

                if self.agent.character.role in [Character.RANGER, Character.ROGUE,
                                                 Character.SAMURAI, Character.TOURIST] and \
                        (item.is_launcher() or item.is_fired_projectile()):
                    add_item(item)

        if self.agent.character.alignment == Character.LAWFUL:
            for item in sorted(filter(lambda i: i.objs[0].name == 'long sword', items),
                               key=lambda i: -utils.calc_dps(*self.agent.character.get_melee_bonus(i))):
                add_item(item)
                break

        for item in sorted(filter(lambda i: i.is_thrown_projectile(), items),
                           key=lambda i: -utils.calc_dps(*self.agent.character.get_ranged_bonus(None, i))):
            add_item(item)

        for item in sorted(filter(lambda i: i.is_food() and not i.is_corpse(), items),
                           key=lambda x: -x.nutrition_per_weight() - 1000 * (x.objs[0].name == 'sprig of wolfsbane')):
            add_item(item)

        for item in filter(is_stoning_cure, items):  # medicine against petrification; never rots
            add_item(item, count=2)

        if self._take_sacrificial_corpses:
            for item in filter(self.agent.global_logic.can_sacrify, items):
                add_item(item)

        # TODO: take nh.COIN_CLASS once shopping is implemented.
        # You have to drop all coins not to be attacked by a vault guard

        for item in sorted(items, key=lambda i: i.unit_weight(with_content=False)):
            if item.category in [nh.POTION_CLASS, nh.RING_CLASS, nh.AMULET_CLASS, nh.WAND_CLASS, nh.SCROLL_CLASS, nh.TOOL_CLASS]:
                if (not isinstance(item.objs[0], O.Container) or not item.is_chest()) and \
                        not item.is_possible_container():
                    to_bag = O.from_name('cancellation', nh.WAND_CLASS) not in item.objs and \
                             not item.is_offensive_usable_wand()
                    to_bag = False
                    if not item.is_container():  # remove condition to pick up bags
                        add_item(item, to_bag=to_bag)

        categories = [nh.WEAPON_CLASS, nh.ARMOR_CLASS, nh.TOOL_CLASS, nh.FOOD_CLASS, nh.GEM_CLASS, nh.AMULET_CLASS,
                      nh.RING_CLASS, nh.POTION_CLASS, nh.SCROLL_CLASS, nh.SPBOOK_CLASS, nh.WAND_CLASS]
        for item in sorted(items, key=lambda i: i.unit_weight(with_content=False)):
            if item.category in categories and not isinstance(item.objs[0], O.Container) and not item.is_corpse():
                if item.status == Item.UNKNOWN:
                    to_bag = O.from_name('cancellation', nh.WAND_CLASS) not in item.objs and \
                             not item.is_offensive_usable_wand()
                    to_bag = False
                    if not item.is_container():  # remove condition to pick up bags
                        add_item(item, to_bag=to_bag)

        r = {None: [ret_inv.get(item, 0) for item in items]}
        if bag is not None:
            r[bag] = [ret_bag.get(item, 0) for item in items]
        for item in items:
            if item.is_container() and item is not bag and ret_inv.get(item, 0) != 0:
                r[item] = [0 for _ in items]
        return r


class GlobalLogic:
    # The real last Mines level, set from outside by measuring code (the screensaver's layout reader).
    # Only ladder_facts may read it: the bot's own decisions come from the screen (Phase 2 CONTEXT D-04).
    truth_mines_end_level = None

    def __init__(self, agent, plan=None):
        self.agent = agent
        self.plan = Plan(plan or DEFAULT_PLAN)
        self._arrived = {}  # milestone -> turn it first stood on its target level
        self._started = {}  # milestone -> turn it became current
        self._live_blocked = 0
        self._progress = ProgressWatch(STUCK_TURNS)
        self._mines_dive_over = False  # a diver in the Mines heads down them until stuck (Mines' End)
        self.stuck_reports = []  # one row per stuck-watch firing (autoascend/stuck.py), for the results
        self._prize_baseline = None  # possible prizes already held on reaching the top Sokoban level
        self._prize_found = False
        self.step_completion_log = {}  # Milestone -> (step, turn)

        self.item_priority = ItemPriority(self.agent)

        self.oracle_level = None
        self.minetown_level = None
        self.portal_level = None  # level key where the quest leader's call was heard
        self._portal_hunt_since = None  # turn the portal hunt began (inf: given up)
        self._quest_arrival = None  # square the portal put the hero on in the Quest
        self._quest_left = False
        self.ladder = Ladder()
        self._ladder_broken = False

        self._got_artifact = False

    @property
    def milestone(self):
        return self.plan.current

    def _stayed(self, key, turns):
        """True once the bot has been on level `key` for `turns` turns in this milestone."""
        if self.agent.current_level().key() != key:
            return False
        start = self._arrived.setdefault(self.milestone, self.agent.blstats.time)
        return self.agent.blstats.time - start >= turns

    def _elapsed(self, turns):
        start = self._started.setdefault(self.milestone, self.agent.blstats.time)
        return self.agent.blstats.time - start >= turns

    def _should_bail(self):
        """Escape plans head home early when the run turns bad."""
        if not self.plan.can_bail_out():
            return False
        # Out of food and prayer still on cooldown: the next hunger is likely fatal.
        if self.agent.blstats.hunger_state >= Hunger.WEAK and not self.agent.is_safe_to_pray() and \
                not any(item.is_food() for item in flatten_items(self.agent.inventory.items)):
            return True
        return self.milestone == Milestone.FIND_SOKOBAN and self._elapsed(SOKOBAN_SEARCH_TURNS)

    def _diving_in_mines(self):
        return self.agent.current_level().dungeon_number == Level.GNOMISH_MINES and not self._mines_dive_over

    def _stuck(self):
        return self._progress.stuck(self.agent.current_level().key(), self.milestone, self.agent.blstats.time)

    def _report_stuck(self, target):
        """Record the level the stuck watch gave up on; reads state only, so it never changes a game."""
        try:
            level = self.agent.current_level()
            self.stuck_reports.append(stuck.stuck_report(
                turn=self.agent.blstats.time, dungeon=level.dungeon_number, level=level.level_number,
                dlvl=self.agent.blstats.depth, milestone=self.milestone.name, target=target, objects=level.objects,
                seen=level.seen, walkable=level.walkable, dis=self.agent.bfs(), glyphs=self.agent.glyphs))
            del self.stuck_reports[:-stuck.KEEP]
        except Exception:  # measuring must never end a game
            self.agent.stats_logger.log_event('stuck_report_error')

    def _minetown_found(self):
        return self.minetown_level is not None or self._elapsed(MINETOWN_SEARCH_TURNS)

    def _minetown_explored(self):
        return self.minetown_level is None or self._stayed(self.minetown_level, TOWN_TURNS)

    def has_prize(self):
        """A possible Sokoban prize was picked up on the top Sokoban level."""
        return self._prize_found

    def prize_pickups(self, items):
        """While looting the top Sokoban level, take anything that may be the prize.

        ItemPriority normally skips bags whose status and contents are unknown."""
        if self.milestone != Milestone.LOOT_SOKOBAN_PRIZE or \
                self.agent.current_level().key() != (Level.SOKOBAN, 1):
            return []
        return [item for item in items if _prize_objects() & set(item.objs)]

    def _loot_check(self):
        # Unidentified amulets/bags may be the prize, so only count ones gained up here:
        # an amulet found earlier in the dungeon is not loot.
        if self.agent.current_level().key() != (Level.SOKOBAN, 1):
            return False
        held = {str(item) for item in flatten_items(self.agent.inventory.items)
                if _prize_objects() & set(item.objs)}
        if self._prize_baseline is None:
            self._prize_baseline = held
        self._prize_found = self._prize_found or bool(held - self._prize_baseline)
        return self._prize_found

    def update(self):
        if not self.agent.character.prop.hallu:
            if utils.isin(self.agent.glyphs, G.ORACLE).any():
                if self.oracle_level is None:
                    self.oracle_level = self.agent.current_level().key()
                else:
                    assert self.oracle_level == self.agent.current_level().key()

            if self.agent.current_level().dungeon_number == Level.GNOMISH_MINES and \
                    utils.isin(self.agent.glyphs, G.SHOPKEEPER).any():
                if self.minetown_level is None:
                    self.minetown_level = self.agent.current_level().key()
                else:
                    assert self.minetown_level == self.agent.current_level().key()

        self._update_portal()
        self._update_ladder()

    def _update_portal(self):
        level = self.agent.current_level()
        if self.portal_level is None and level.dungeon_number == Level.DUNGEONS_OF_DOOM and \
                quest_portal.is_portal_level_message(self.agent.message):
            self.portal_level = level.key()
            self.agent.stats_logger.log_event('quest_portal_level_seen')
        if level.dungeon_number == Level.QUEST and self._quest_arrival is None:
            self._quest_arrival = (self.agent.blstats.y, self.agent.blstats.x)
            self.agent.stats_logger.log_event('quest_portal_entered')
        if self._quest_arrival is not None and not self._quest_left and level.dungeon_number != Level.QUEST:
            self._quest_left = True
            self.agent.stats_logger.log_event('quest_portal_left')

    def _hunting_portal(self):
        """On the portal level, before the portal was found, within the hunt's turn budget."""
        if self.portal_level is None or self._quest_arrival is not None or \
                self.agent.current_level().key() != self.portal_level or self._portal_hunt_since == float('inf'):
            return False
        if self._portal_hunt_since is None:
            self._portal_hunt_since = self.agent.blstats.time
        if self.agent.blstats.time - self._portal_hunt_since > PORTAL_HUNT_TURNS:
            self._give_up_portal()
            return False
        return True

    def _give_up_portal(self):
        if self._portal_hunt_since != float('inf'):
            self._portal_hunt_since = float('inf')
            self.agent.stats_logger.log_event('quest_portal_gave_up')

    @Strategy.wrap
    def portal_hunt(self):
        """Step on every reachable square of the portal level (the portal fires when stepped on), then search
        its dead ends."""
        if not self._hunting_portal():
            yield False
        yield True
        while self._hunting_portal():
            level = self.agent.current_level()
            pos = (self.agent.blstats.y, self.agent.blstats.x)
            target = quest_portal.next_portal_square(self.agent.bfs() >= 0, level.was_on, level.search_count, pos)
            if target is None:
                self._give_up_portal()
                return
            if target == pos:
                self.agent.search(5)
            else:
                self.agent.go_to(*target)

    def _boulder_pushes(self):
        """Pushes worth a try on this level, best first (none in Sokoban, which has its own solver)"""
        level = self.agent.current_level()
        # a pushed boulder makes new (boulder, beyond) pairs, so cap the tries per level (smoke seed 9 pushed 107)
        if level.dungeon_number == Level.SOKOBAN or len(level.boulder_pushes_tried) >= BOULDER_PUSHES_PER_LEVEL:
            return []
        boulder_map = utils.isin(self.agent.glyphs, G.BOULDER)
        if not boulder_map.any():
            return []
        dis = self.agent.bfs()
        if not boulders.nothing_left(level.seen, level.walkable, dis, utils.isin(level.objects, G.STAIR_DOWN)):
            return []
        doors = utils.isin(level.objects, G.DOORS | {SS.S_ndoor}) | level.no_diagonal
        blocked = boulder_map | utils.isin(self.agent.glyphs, G.MONS)
        return boulders.push_candidates(boulder_map, level.walkable, blocked, doors, level.seen, dis,
                                        level.boulder_pushes_tried)

    @Strategy.wrap
    def push_boulders(self):
        """When the level looks finished, walk into boulders: the way on is often behind one."""
        if not self._boulder_pushes():
            yield False
        yield True
        level = self.agent.current_level()
        while True:
            pushes = self._boulder_pushes()
            if not pushes:
                return
            stand, boulder, beyond = pushes[0]
            level.boulder_pushes_tried.add((boulder, beyond))
            if (self.agent.blstats.y, self.agent.blstats.x) != stand:
                self.agent.go_to(*stand)
                if (self.agent.blstats.y, self.agent.blstats.x) != stand:
                    continue
            if self.agent.glyphs[boulder] not in G.BOULDER:
                continue
            self.agent.stats_logger.log_event('boulder_push_try')
            self.agent.direction(*boulder)
            if (self.agent.blstats.y, self.agent.blstats.x) == boulder:
                self.agent.stats_logger.log_event('boulder_pushed')

    @Strategy.wrap
    def leave_quest(self):
        """Rung 8 needs only the step into the Quest: step off the arrival portal and back onto it."""
        if self._quest_arrival is None or self._quest_left or \
                self.agent.current_level().dungeon_number != Level.QUEST:
            yield False
        yield True
        pos = (self.agent.blstats.y, self.agent.blstats.x)
        try:
            if pos == self._quest_arrival:
                dis = self.agent.bfs()
                steps = [(y, x) for y, x in self.agent.neighbors(*pos) if dis[y, x] == 1]
                if not steps:
                    self.agent.search()
                    return
                self.agent.move(*steps[0])
            elif utils.adjacent(pos, self._quest_arrival):
                self.agent.move(*self._quest_arrival)
            else:
                self.agent.go_to(*self._quest_arrival, stop_one_before=True)
        except AgentPanic:  # the portal moved the hero to another level
            pass

    def _update_ladder(self):
        if not self._ladder_broken:
            try:
                self.ladder.observe(self.ladder_facts())
            except Exception:  # measuring must never end a game
                self._ladder_broken = True
                self.agent.stats_logger.log_event('ladder_error')

    def ladder_facts(self):
        """What the ascension ladder needs to know about this step (see ladder.py)."""
        level = self.agent.current_level()
        hallu = self.agent.character.prop.hallu
        seen = int(level.seen.sum())
        water = int((utils.isin(level.objects, WATER) & level.seen).sum())
        return Facts(
            turn=int(self.agent.blstats.time), dungeon=int(level.dungeon_number), level=int(level.level_number),
            oracle_seen=self.oracle_level is not None, minetown_seen=self.minetown_level is not None,
            sokoban_seen=seen, sokoban_traps=bool(utils.isin(level.objects, G.TRAPS).any()),
            medusa_seen=not hallu and bool(utils.isin(self.agent.glyphs, MEDUSA).any()),
            water_share=0.0 if hallu or not seen else water / seen,
            drawbridge_seen=not hallu and bool(utils.isin(level.objects, DRAWBRIDGE).any()),
            down_stairs_seen=bool(utils.isin(level.objects, G.STAIR_DOWN).any()),
            inventory=tuple(item.text for item in flatten_items(self.agent.inventory.items)),
            message=self.agent.message, mines_end_level=self.truth_mines_end_level)

    @utils.debug_log('solving sokoban')
    @Strategy.wrap
    def solve_sokoban_strategy(self):
        # TODO: refactor
        if not utils.isin(self.agent.current_level().objects, G.TRAPS).any():
            yield False
        yield True

        def push_bolder(ty, tx, dy, dx):
            while 1:
                if self.agent.bfs()[ty, tx] == -1:
                    return False
                self.agent.go_to(ty, tx, debug_tiles_args=dict(color=(255, 255, 255), is_path=True))
                with self.agent.atom_operation():
                    direction = self.agent.calc_direction(ty, tx, ty + dy, tx + dx)
                    self.agent.direction(direction)
                    message = self.agent.message

                if (self.agent.blstats.y, self.agent.blstats.x) == (ty, tx):
                    assert 'You hear a monster behind the boulder.' in message or \
                           'You try to move the boulder, but in vain.' in message, message
                    if self.agent.bfs()[ty + dy, tx + dx] != -1:
                        self.agent.go_to(ty + dy, tx + dx, debug_tiles_args=dict(color=(255, 255, 255), is_path=True))
                        continue
                    else:
                        pickaxe = None
                        for item in flatten_items(self.agent.inventory.items):
                            if item.is_unambiguous() and \
                                    item.object in [O.from_name('pick-axe'), O.from_name('dwarvish mattock')]:
                                pickaxe = item
                                break
                        if pickaxe is not None:
                            with self.agent.atom_operation():
                                pickaxe = self.agent.inventory.move_to_inventory(pickaxe)
                                self.agent.step(A.Command.APPLY)
                                self.agent.type_text(self.agent.inventory.items.get_letter(pickaxe))
                                self.agent.direction(direction)
                            return True
                else:
                    return True

                # TODO: not sure what to do
                self.agent.exploration.explore1(None).run()

        while 1:
            wall_map = utils.isin(self.agent.current_level().objects, G.WALL)
            for smap, answer in soko_solver.maps.items():
                sokomap = soko_solver.convert_map(smap)
                offset = np.array(min(zip(*wall_map.nonzero()))) - \
                         np.array(min(zip(*(sokomap.sokomap == soko_solver.WALL).nonzero())))
                mask = wall_map[offset[0] : offset[0] + sokomap.sokomap.shape[0],
                                offset[1] : offset[1] + sokomap.sokomap.shape[1]]
                if (mask & (sokomap.sokomap == soko_solver.WALL) == mask).all():
                    break
            else:
                assert 0, 'sokomap not found'

            possible_mimics = set()
            last_resort_move = None
            for (y, x), (dy, dx) in answer:
                boulder_map = utils.isin(self.agent.glyphs, G.BOULDER)
                mask = boulder_map[offset[0] : offset[0] + sokomap.sokomap.shape[0],
                                   offset[1] : offset[1] + sokomap.sokomap.shape[1]]
                ty, tx = offset[0] + y - dy, offset[1] + x - dx,
                soko_boulder_mask = sokomap.sokomap == soko_solver.BOULDER
                if self.agent.bfs()[ty, tx] != -1 and \
                        ((soko_boulder_mask | mask) == soko_boulder_mask).all() and \
                        self.agent.glyphs[ty + dy, tx + dx] in G.BOULDER:

                    soko_dis1 = sokomap.bfs()
                    sokomap.move(y, x, dy, dx)
                    soko_dis2 = sokomap.bfs()

                    # see points that will no longer be accessible
                    with self.agent.env.debug_log('checking for monsters'):
                        to_visit_mask = self.agent.bfs() != -1
                        to_visit_mask[offset[0] : offset[0] + sokomap.sokomap.shape[0],
                                      offset[1] : offset[1] + sokomap.sokomap.shape[1]] &= \
                                              (soko_dis1 != -1) & (soko_dis2 == -1)

                        with self.agent.env.debug_tiles(to_visit_mask, color=(255, 0, 0, 128)):
                            while to_visit_mask.any():
                                vy, vx = list(zip(*to_visit_mask.nonzero()))[0]
                                to_visit_mask[vy, vx] = 0

                                def clear_neighbors():
                                    to_visit_mask[self.agent.blstats.y, self.agent.blstats.x] = 0
                                    to_visit_mask[utils.isin(self.agent.glyphs, G.VISIBLE_FLOOR)] = 0
                                    return not to_visit_mask[vy, vx]

                                self.agent.go_to(vy, vx, callback=clear_neighbors)

                    if not push_bolder(ty, tx, dy, dx):
                        continue

                    possible_mimics = set()
                    last_resort_move = None

                    if not utils.isin(self.agent.current_level().objects, G.TRAPS).any():
                        return

                else:
                    sokomap.move(y, x, dy, dx)

                if (~soko_boulder_mask | mask).all():
                    if self.agent.bfs()[ty, tx] != -1 and \
                            self.agent.glyphs[ty + dy, tx + dx] in G.BOULDER and \
                            last_resort_move is None:
                        last_resort_move = (ty, tx, dy, dx)

                    if not possible_mimics:
                        for mim_y, mim_x in zip(*(~soko_boulder_mask & mask).nonzero()):
                            possible_mimics.add((mim_y + offset[0], mim_x + offset[1]))


            # sokoban configuration is not in the list. Check for mimics
            with self.agent.env.debug_log('mimics'):
                with self.agent.env.debug_tiles(possible_mimics, color=(255, 0, 0, 128)):
                    for mim_y, mim_x in sorted(possible_mimics):
                        if (self.agent.bfs()[max(0, mim_y - 1) : mim_y + 2, max(0, mim_x - 1) : mim_x + 2] != -1).any():
                            self.agent.go_to(mim_y, mim_x, stop_one_before=True,
                                             debug_tiles_args=dict(color=(255, 0, 0), is_path=True))
                            for _ in range(3):
                                self.agent.search()

            # last resort move (sometimes we can see a mimic diagonally but cannot reach it)
            with self.agent.env.debug_log('last_resort'):
                if last_resort_move is not None:
                    ty, tx, dy, dx = last_resort_move
                    push_bolder(ty, tx, dy, dx)
                    continue

            # The stored solution no longer fits this board: solve it from what is there now.
            with self.agent.env.debug_log('live solver'):
                if self._solve_live_sokoban(push_bolder):
                    self.agent.stats_logger.log_event('sokoban_live_solved')
                    return

            self.agent.stats_logger.log_event('sokoban_dropped')
            self.plan.drop_sokoban()
            raise AgentPanic('sokomap unsolvable')

    @Strategy.wrap
    def leave_dungeon(self):
        if self.agent.current_level().key() != (Level.DUNGEONS_OF_DOOM, 1):
            yield False
        stairs = [(y, x) for y, x in zip(*utils.isin(self.agent.current_level().objects, G.STAIR_UP).nonzero())
                  if self.agent.bfs()[y, x] != -1]
        if not stairs:
            yield False  # upstairs not known or not reachable yet: keep exploring Dlvl 1
        yield True
        y, x = stairs[0]
        self.agent.go_to(y, x)
        # "Beware, there will be no return! Still climb?" is answered 'y' by Agent.update.
        self.agent.direction('<')
        self._after_failed_climb()  # still here: the game did not end

    @Strategy.wrap
    def dive(self):
        level = self.agent.current_level()
        stairs = dive_stairs(level.dungeon_number, level.objects, level.stair_destination, self.agent.bfs(),
                             mines=self._diving_in_mines())
        if not stairs:
            yield False
        yield True
        y, x = stairs[0]
        self.agent.go_to(y, x)
        self.agent.move('>')

    def _after_failed_climb(self):
        if 'too heavy' not in self.agent.message:
            return  # e.g. held by a monster: fighting has priority and frees us
        droppable = [item for item in self.agent.inventory.items
                     if item.can_be_dropped_from_inventory() and not _prize_objects() & set(item.objs)]
        if droppable:
            self.agent.inventory.drop(max(droppable, key=lambda item: item.weight()))

    def _solve_live_sokoban(self, push_bolder, attempts=5):
        """Fill the remaining traps from the board as it is now; True once none are left."""
        for _ in range(attempts):
            level = self.agent.current_level()
            floor, boulders, traps = sokoban_board(level.objects, level.walkable, self.agent.glyphs)
            if not traps:
                return True
            # The lower levels have pits, which the player may walk through; holes never.
            pits = {(y, x) for y, x in traps if level.objects[y, x] in (SS.S_pit, SS.S_spiked_pit)}
            pushes = soko_search.solve(floor, boulders, traps, (self.agent.blstats.y, self.agent.blstats.x),
                                       max_states=SOKOBAN_LIVE_MAX_STATES, max_seconds=None,
                                       crossable=pits if pits == traps else frozenset())
            if pushes is None:
                return False
            for (by, bx), (dy, dx) in pushes:
                if pits == traps:
                    self.agent._allow_walking_through_traps_turn = self.agent._last_turn
                if self.agent.glyphs[by, bx] not in G.BOULDER:
                    break  # the board changed under us (a mimic, a destroyed boulder): look again
                while self.agent.bfs()[by - dy, bx - dx] == -1:
                    if not self._push_square_blocked():
                        return False
                if not push_bolder(by - dy, bx - dx, dy, dx):
                    break
        solved = not utils.isin(self.agent.current_level().objects, G.TRAPS).any()
        if solved:
            self._live_blocked = 0
        return solved

    def _push_square_blocked(self):
        """A monster stands between the bot and its push square: wait a turn, in which it
        moves on or the fight logic takes over. False once it looks permanent."""
        self._live_blocked += 1
        if self._live_blocked > LIVE_SOKOBAN_BLOCKED_TRIES:
            return False
        self.agent.search()
        return True

    @Strategy.wrap
    def wait_out_unexpected_state_strategy(self):
        yielded = False
        while (
                self.agent.character.prop.blind or
                self.agent.character.prop.confusion or
                self.agent.character.prop.stun or
                self.agent.character.prop.hallu or
                self.agent.character.prop.polymorph):
            if not yielded:
                yield True
                yielded = True

            self.agent.direction('.')

        if not yielded:
            yield False

    @utils.debug_log('identify_items_on_altar')
    @Strategy.wrap
    def identify_items_on_altar(self):
        mask = utils.isin(self.agent.current_level().objects, G.ALTAR)
        if not mask.any():
            yield False

        dis = self.agent.bfs()
        mask &= dis != -1
        if not mask.any():
            yield False

        yield any((item.status == Item.UNKNOWN for item in flatten_items(self.agent.inventory.items)
                   if item.can_be_dropped_from_inventory()))

        (ty, tx), *_ = zip(*(mask & (dis == dis[mask].min())).nonzero())
        self.agent.go_to(ty, tx)
        items_to_drop = [item for item in flatten_items(self.agent.inventory.items)
                         if item.can_be_dropped_from_inventory() and item.status == Item.UNKNOWN]
        if not items_to_drop:
            raise AgentPanic('items to drop on altar vanished')

        # TODO: move chunking to inventory.drop
        items_to_drop = items_to_drop[:self.agent.inventory.items.free_slots()]

        self.agent.inventory.drop(items_to_drop)

    @utils.debug_log('dip_for_excalibur')
    @Strategy.wrap
    def dip_for_excalibur(self):
        if self.agent.character.alignment != Character.LAWFUL or self.agent.blstats.experience_level < 5:
            yield False
        if self.agent.current_level().dungeon_number == Level.GNOMISH_MINES and \
                (self.minetown_level is None or self.agent.current_level().key() == self.minetown_level):
            yield False

        dis = self.agent.bfs()
        mask = utils.isin(self.agent.current_level().objects, G.FOUNTAIN) & (dis != -1)
        if not mask.any():
            yield False

        def excalibur_candidate():
            candidate = None
            for item in flatten_items(self.agent.inventory.items):
                if item.is_unambiguous() and item.object == O.from_name('long sword'):
                    if item.dmg_bonus is not None: # TODO: better condition for excalibur existance
                        return None
                    candidate = item
            return candidate

        if excalibur_candidate() is None:
            yield False
        yield True

        self.agent.go_to(*list(zip(*mask.nonzero()))[0])

        candidate = excalibur_candidate()
        if candidate is None:
            return

        # TODO: refactor
        with self.agent.atom_operation():
            candidate = self.agent.inventory.move_to_inventory(candidate)
            self.agent.step(A.Command.DIP)
            self.agent.type_text(self.agent.inventory.items.get_letter(candidate))
            if 'What do you want to dip ' in self.agent.message and 'into?' in self.agent.message:
                raise AgentPanic('no fountain here')

    def can_sacrify(self, item):
        if not item.is_corpse() or item.comment == 'old':
            return False

        if ord(MON.permonst(item.monster_id + nh.GLYPH_MON_OFF).mlet) == MON.S_COCKATRICE:
            return False  # picking it up bare-handed petrifies (pickup.c)

        mname = MON.permonst(item.monster_id + nh.GLYPH_MON_OFF).mname
        if (mname == 'pony' and self.agent.character.role in [Character.KNIGHT, Character.BARBARIAN]) or \
                (mname == 'kitten' and self.agent.character.role == [Character.BARBARIAN, Character.WIZARD]) or \
                (mname == 'little dog' and item.naming):  # little dogs are always named
            # sufficient condition for being an initial pet
            return False

        if self.agent.character.alignment != Character.CHAOTIC:
            mapping = {
                Character.HUMAN: MON.M2_HUMAN | MON.M2_WERE,
                Character.DWARF: MON.M2_DWARF,
                Character.ELF: MON.M2_ELF,
                Character.GNOME: MON.M2_GNOME,
                Character.ORC: MON.M2_ORC,
            }
            f2 = MON.permonst(item.monster_id + nh.GLYPH_MON_OFF).mflags2
            if (f2 & mapping[self.agent.character.race]) > 0:
                return False

        return True

    @utils.debug_log('offer_corpses')
    @Strategy.wrap
    def offer_corpses(self):
        self.item_priority._take_sacrificial_corpses = False

        if self._got_artifact:
            yield False

        altars = [p for p, alignment in self.agent.current_level().altars.items()
                  if alignment == self.agent.character.alignment]

        if not altars:
            yield False

        dis = self.agent.bfs()
        altars = [(y, x) for y, x in altars if dis[y, x] != -1]

        if not altars:
            yield False

        self.item_priority._take_sacrificial_corpses = True

        if not any((self.can_sacrify(item) for item in flatten_items(self.agent.inventory.items))):
            yield False

        yield True

        y, x = min(altars, key=lambda p: dis[p])
        self.agent.go_to(y, x)
        with self.agent.panic_if_position_changes():
            while 1:
                for item in flatten_items(self.agent.inventory.items):
                    if self.can_sacrify(item):
                        with self.agent.atom_operation():
                            item = self.agent.inventory.move_to_inventory(item)
                            assert self.can_sacrify(item)
                            self.agent.step(A.Command.OFFER)
                            while ('There is ' in self.agent.message or 'There are ' in self.agent.message) and \
                                    ('sacrifice it?' in self.agent.message or 'sacrifice one?' in self.agent.message):
                                self.agent.type_text('n')
                            assert 'What do you want to sacrifice?' in self.agent.message, self.agent.message
                            self.agent.type_text(self.agent.inventory.items.get_letter(item))
                            if 'Nothing happens.' in self.agent.message:
                                self.agent.inventory.call_item(item, 'old')
                                return
                            if 'Use my gift wisely' in self.agent.message:
                                self._got_artifact = True
                                self.agent.inventory.get_items_below_me()
                                return
                            if 'So this is how you repay loyalty?' in self.agent.message:
                                raise AgentPanic('pet sacrified')
                            assert 'Your sacrifice is consumed in a flash of light' in self.agent.message or \
                                'Your sacrifice is consumed in a burst of flame' in self.agent.message or \
                                ('The blood covers the altar!' in self.agent.message and \
                                 'You have summoned ' in self.agent.message), \
                                self.agent.message
                            break
                else:
                    break

    @utils.debug_log('follow_guard')
    @Strategy.wrap
    def follow_guard(self):
        if not utils.isin(self.agent.glyphs, G.GUARD).any():
            yield False

        if any(item.category == nh.COIN_CLASS for item in flatten_items(self.agent.inventory.items)):
            yield True
            # if 'Please drop that gold and follow me.' in self.message:
            self.agent.stats_logger.log_event('drop_gold')
            self.item_priority._drop_gold_till_turn = self.agent.blstats.time + 100
            self.agent.inventory.arrange_items().run()
            return

        ys, xs = utils.isin(self.agent.glyphs, G.GUARD).nonzero()
        y, x = ys[0], xs[0]

        if utils.adjacent((y, x), (self.agent.blstats.y, self.agent.blstats.x)):
            yield False

        yield True

        self.agent.go_to(y, x, stop_one_before=True)

    @Strategy.wrap
    def current_strategy(self):
        yield True
        while 1:
            explore_stairs_condition = lambda: False
            if self.milestone == Milestone.BE_ON_FIRST_LEVEL:
                # Dlvl 1 runs out of food long before XL 8: leave once hungry.
                condition = lambda: self.agent.blstats.experience_level >= 8 or \
                                    self.agent.blstats.hunger_state >= Hunger.HUNGRY
                # explore_stairs_condition = lambda: self.agent.inventory.items.total_nutrition() == 0 and \
                #                                    self.agent.blstats.hunger_state >= Hunger.NOT_HUNGRY
                level = (Level.DUNGEONS_OF_DOOM, 1)

            elif self.milestone == Milestone.FIND_SOKOBAN:
                condition = lambda: self.agent.current_level().dungeon_number == Level.SOKOBAN
                level = (Level.SOKOBAN, 4)

            elif self.milestone == Milestone.FIND_GNOMISH_MINES:
                condition = lambda: self.agent.current_level().dungeon_number == Level.GNOMISH_MINES
                level = (Level.GNOMISH_MINES, 1)

            # elif self.milestone == Milestone.FIND_LIGHT_GNOMISH_MINES:
            #     condition = lambda: self.agent.current_level().dungeon_number == Level.GNOMISH_MINES \
            #             and self.agent.current_level().is_light_level()
            #     level = (Level.GNOMISH_MINES, 9)

            # elif self.milestone == Milestone.FARM_LIGHT_GNOMISH_MINES:
            #     condition = lambda: self.agent.blstats.experience_level >= 11
            #     level = (Level.GNOMISH_MINES, self.agent.current_level().level_number)

            elif self.milestone == Milestone.FIND_MINETOWN:
                condition = self._minetown_found
                level = (Level.GNOMISH_MINES, 4)  # TODO

            elif self.milestone == Milestone.SOLVE_SOKOBAN:
                # TODO: fix the condition, monster can destroy doors
                condition = lambda: self.agent.current_level().key() == (Level.SOKOBAN, 1) and \
                                    not utils.isin(self.agent.current_level().objects, G.DOOR_CLOSED).any()
                level = (Level.SOKOBAN, 1)

            elif self.milestone == Milestone.FIND_MINES_END:
                condition = lambda: self.agent.current_level().key() == (Level.GNOMISH_MINES, 9)  # TODO
                level = (Level.GNOMISH_MINES, 9)  # TODO

            elif self.milestone == Milestone.EXPLORE_MINETOWN:
                condition = self._minetown_explored
                level = self.minetown_level  # unused when None: the condition is already true

            elif self.milestone == Milestone.LOOT_SOKOBAN_PRIZE:
                condition = lambda: self._loot_check() or self._stayed((Level.SOKOBAN, 1), LOOT_TURNS)
                level = (Level.SOKOBAN, 1)

            elif self.milestone in (Milestone.RETURN_TO_SURFACE, Milestone.LEAVE_DUNGEON):
                # LEAVE_DUNGEON never completes here: leave_dungeon() ends the game.
                condition = lambda: self.milestone == Milestone.RETURN_TO_SURFACE and \
                                    self.agent.current_level().key() == (Level.DUNGEONS_OF_DOOM, 1)
                level = (Level.DUNGEONS_OF_DOOM, 1)

            elif self.milestone == Milestone.DIVE and self._diving_in_mines():
                condition = lambda: False
                level = (Level.GNOMISH_MINES, 100)  # explore the deepest known Mines level for its downstairs

            else:
                # TODO
                condition = lambda: False
                level = (Level.DUNGEONS_OF_DOOM, 100)

            if self._should_bail():
                self.plan.bail_out()
                continue
            if self._stuck():
                self.agent.stats_logger.log_event('stuck_dive')
                self._report_stuck(level)
                if self.milestone != Milestone.DIVE:
                    self.plan.dive_instead()
                elif self._diving_in_mines():
                    self._mines_dive_over = True  # bottom of the Mines: back up, dive the main dungeon
                else:
                    self.agent.stats_logger.log_event('stuck_diving')  # no downstairs found
                self._progress.restart(self.agent.blstats.time)
                continue
            if condition():
                self.plan.advance()
                continue


            def exploration_strategy(level, **kwargs):
                return (
                    Strategy(lambda: self.agent.exploration.explore1(level, trap_search_offset=1,
                        kick_doors=self.agent.current_level().dungeon_number != Level.GNOMISH_MINES, **kwargs).strategy())
                    .preempt(self.agent, [
                        self.identify_items_on_altar().every(100),
                        self.identify_items_on_altar().condition(
                            lambda: self.agent.current_level().objects[self.agent.blstats.y,
                                                                       self.agent.blstats.x] in G.ALTAR),
                        self.dip_for_excalibur().condition(
                            lambda: self.agent.blstats.experience_level >= 7).every(10),
                    ])
                )

            # Going home is a retreat: no side trips to explore, gather items or wait for the pet.
            going_home = self.milestone == Milestone.RETURN_TO_SURFACE

            def go_to_strategy(y, x):
                return (
                    exploration_strategy(None)
                    .preempt(self.agent, [
                        self.agent.exploration.go_to_strategy(y, x).preempt(self.agent, [
                            self.agent.inventory.gather_items().condition(lambda: not going_home),
                            self.identify_items_on_altar(),
                            self.dip_for_excalibur().condition(lambda: self.agent.blstats.experience_level >= 7),
                        ])
                        .condition(lambda: self._got_artifact or
                                           not any([alignment == self.agent.character.alignment
                                                    for _, alignment in self.agent.current_level().altars.items()]))
                    ])
                    .until(self.agent, lambda: (self.agent.blstats.y, self.agent.blstats.x) == (y, x))
                )

            (
                self.agent.exploration.go_to_level_strategy(*level, go_to_strategy, exploration_strategy(None),
                                                            wait_for_pet=not going_home)
                .before(exploration_strategy(None))#.before(self.agent.exploration.patrol())
                .preempt(self.agent, [
                    exploration_strategy(0).condition(lambda: not going_home),
                    exploration_strategy(None).until(
                        self.agent, lambda: self.agent.blstats.hitpoints >= 0.8 * self.agent.blstats.max_hitpoints)
                ])
                .preempt(self.agent, [
                    self.agent.exploration.explore_stairs(go_to_strategy, all=True).condition(explore_stairs_condition),
                ])
                .until(self.agent, lambda: condition() or self._should_bail() or self._stuck())
            ).run()

    def global_strategy(self):
        return (
            self.current_strategy().repeat()
            .preempt(self.agent, [
                self.solve_sokoban_strategy()
                .condition(lambda: self.milestone == Milestone.SOLVE_SOKOBAN and
                                   self.agent.current_level().dungeon_number == Level.SOKOBAN)
            ])
            .preempt(self.agent, [
                self.leave_dungeon().condition(lambda: self.milestone == Milestone.LEAVE_DUNGEON)
            ])
            .preempt(self.agent, [
                self.dive().condition(lambda: self.milestone == Milestone.DIVE)
            ])
            .preempt(self.agent, [
                self.leave_quest(),
                self.portal_hunt(),
                self.push_boulders().every(20),
            ])
            .preempt(self.agent, [
                self.offer_corpses().preempt(self.agent, [
                    self.agent.eat_corpses_from_ground().condition(lambda: self.agent.blstats.hunger_state >= Hunger.NOT_HUNGRY),
                ]),
            ])
            .preempt(self.agent, [
                self.wait_out_unexpected_state_strategy(),
            ])
            .preempt(self.agent, [
                self.agent.cure_disease().every(5),
            ])
            .preempt(self.agent, [
                self.agent.eat_corpses_from_ground(only_below_me=True).condition(lambda: self.agent.blstats.hunger_state >= Hunger.NOT_HUNGRY),
                self.agent.eat_corpses_from_ground().every(5).condition(lambda: self.agent.blstats.hunger_state >= Hunger.NOT_HUNGRY),
                self.agent.eat_from_inventory().every(5),
            ])
            .preempt(self.agent, [
                self.follow_guard(),
            ])
            .preempt(self.agent, [
                self.agent.fight2(),
            ])
            .preempt(self.agent, [
                self.agent.engulfed_fight(),
            ])
            .preempt(self.agent, [
                self.agent.emergency_strategy(),
            ])
        )
