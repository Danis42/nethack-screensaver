import nle.nethack as nh

from autoascend.item.item_manager import ContainerContent, ItemManager

CLOAK = 'an uncursed thoroughly burnt thoroughly rotted +2 cloak of displacement (being worn)'


def test_inventory_text_cut_at_80_chars_still_parses_as_worn():
    full = ItemManager.parse_text(CLOAK)
    cut = ItemManager.parse_text(CLOAK[:80])
    assert cut == full


def test_cut_text_with_unknown_suffix_drops_it():
    text = 'an uncursed thoroughly rusty thoroughly corroded +0 two-handed sword (for sale, 15 zorkmids)'
    cut = text[:80]
    assert ' (for sale' in cut and not cut.endswith(')')
    assert ItemManager.parse_text(cut)[0][0].name == 'two-handed sword'


def _manager():
    from types import SimpleNamespace
    from autoascend.character import Character
    prop = SimpleNamespace(hallu=False, blind=False)
    agent = SimpleNamespace(character=SimpleNamespace(prop=prop, role=Character.VALKYRIE), step_count=0)
    return ItemManager(agent)


def test_container_named_empty_counts_as_already_looted():
    # NetHack marks a container "empty" once it knows; looting it again only loops without game time
    box = _manager().get_item_from_text('an empty unlocked large box', position=(0, 1, 5, 7))
    assert box.is_container() and not box.is_possible_container()
    assert list(box.content) == []


def test_container_without_empty_mark_still_needs_looking_into():
    box = _manager().get_item_from_text('an unlocked large box', position=(0, 1, 5, 7))
    assert box.is_possible_container()


def test_empty_mark_clears_stale_container_content():
    manager = _manager()
    box = manager.get_item_from_text('an unlocked large box', position=(0, 1, 5, 7))
    manager.container_contents[box.container_id] = stale = ContainerContent()
    stale.items.append(manager.get_item_from_text('a dagger', position=None))

    box = manager.get_item_from_text('an empty unlocked large box', position=(0, 1, 5, 7))
    assert list(box.content) == []


def test_worn_ring_parses_as_equipped():
    for hand in ['left', 'right']:
        objs, glyphs, count, status, modifier, equipped, *rest = ItemManager.parse_text(
            f'an uncursed ring of slow digestion (on {hand} hand)')
        assert objs[0].name == 'slow digestion' and equipped


def test_dragon_scales_parse_as_armor():
    # a pick-up menu lists them under Armor as "set of <color> dragon scales" (objnam.c xname)
    for text in ['a set of orange dragon scales', '2 sets of gray dragon scales']:
        objs, *rest = ItemManager.parse_text(text, nh.ARMOR_CLASS)
        assert objs[0].name.endswith('dragon scales')


def test_moist_towel_parses():
    # a towel with 1-2 charges of water is "moist", more is "wet" (objnam.c xname)
    for text in ['a moist towel', 'an uncursed wet towel']:
        objs, *rest = ItemManager.parse_text(text, nh.TOOL_CLASS)
        assert objs[0].name == 'towel'


def test_punishment_ball_and_chain_parse():
    objs, *rest = ItemManager.parse_text('a heavy iron ball (chained to you)', nh.BALL_CLASS)
    assert objs[0].name == 'heavy iron ball'
    objs, *rest = ItemManager.parse_text('an iron chain', nh.CHAIN_CLASS)
    assert objs[0].name == 'iron chain'


def test_orcish_town_fruit_parses_as_slime_mold():
    for text in ['a dwarven root', '2 paddle cacti']:
        objs, *rest = ItemManager.parse_text(text, nh.FOOD_CLASS)
        assert objs[0].name == 'slime mold'


def test_shop_glob_without_for_sale_parses():
    # doname: a glob the shopkeeper gives away shows "(<weight> aum, no charge)"
    objs, *rest = ItemManager.parse_text('a small glob of gray ooze (20 aum, no charge)', nh.FOOD_CLASS)
    assert objs[0].name == 'glob of gray ooze'
    objs, *rest = ItemManager.parse_text('a small glob of gray ooze (for sale, 20 aum, 6 zorkmids)', nh.FOOD_CLASS)
    assert objs[0].name == 'glob of gray ooze'


def test_nethack_5_adjectives_parse():
    for text, name in [('a fireproof +0 pair of leather gloves (being worn)', 'leather gloves'),
                       ('a fireproof elven dagger', 'elven dagger'),
                       ('a cracked +1 crystal plate mail (being worn)', 'crystal plate mail'),
                       ('a trapped large box', 'large box'),
                       ('a trapped chest', 'chest')]:
        assert ItemManager.parse_text(text)[0][0].name == name, text


def test_shop_line_cut_short_of_the_limit():
    assert ItemManager.parse_text('a paperback book named Educated Rodents (for s')[0][0].name == 'novel'


def test_smooth_shield_is_reflection():
    assert ItemManager.parse_text('a smooth shield')[0][0].name == 'shield of reflection'


# NetHack 5 option price_quotes appends the prices seen for an unidentified type (shk.c append_price_quote)
def test_price_quote_suffix_parses():
    for text in ['an uncursed scroll labeled FOOBIE BLETCH {sell 10}',
                 '2 uncursed scrolls labeled FOOBIE BLETCH {buy 26-35 sell 10}',
                 'a scroll labeled FOOBIE BLETCH {buy 133}',
                 'an uncursed scroll labeled FOOBIE BLETCH {sell 20-30}']:
        objs, glyphs, count, status, modifier, equipped, *rest = ItemManager.parse_text(text, nh.SCROLL_CLASS)
        assert all(o.name and isinstance(o.name, str) for o in objs) and len(objs) > 1, text
        assert not equipped


def test_price_quote_after_worn_info_keeps_equipped():
    objs, glyphs, count, status, modifier, equipped, *rest = ItemManager.parse_text(
        'an uncursed +0 pair of combat boots (being worn) {sell 4}')
    assert equipped and all(o.name.endswith('boots') for o in objs)


def test_price_quote_cut_at_the_line_limit_is_dropped():
    text = 'an uncursed thoroughly burnt thoroughly rotted +2 cloak of displacement (being worn) {buy 66 sell 33}'
    assert len(text) > 80
    full = ItemManager.parse_text(text)
    assert ItemManager.parse_text(text[:80]) == full
    assert ItemManager.parse_text(text[:86]) == full  # cut inside "{buy 66"


def test_game_options_turn_price_quotes_on():
    from nethack_screensaver.options import GAME_OPTIONS
    assert 'price_quotes' in GAME_OPTIONS and set(nh.NETHACKOPTIONS) <= set(GAME_OPTIONS)
