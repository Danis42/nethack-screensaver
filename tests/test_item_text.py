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
