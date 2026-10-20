from autoascend.item.item_manager import ItemManager

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
