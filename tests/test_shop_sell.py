from autoascend.item import shop_sell
from autoascend.item.shop_sell import costs_for_offer, parse_sell_offer, sell_offer

SCROLL_COSTS = {20, 50, 60, 80, 100, 200, 300}


def test_offer_message_parses():
    msg = 'Asidonhopo offers 40 gold pieces for your scroll labeled FOOBIE BLETCH.  Sell it? [ynaq] (y)'
    assert parse_sell_offer(msg) == 40
    assert parse_sell_offer('Izchak offers 1 gold piece for your scroll labeled ZELGO MER.  Sell it?') == 1


def test_offers_that_are_not_the_price_are_ignored():
    assert parse_sell_offer('Izchak offers only 12 gold pieces for your scroll labeled ZELGO MER.  Sell it?') is None
    assert parse_sell_offer('Izchak cannot pay you at present.  Will you accept 36 zorkmids in credit for your '
                            'scroll labeled ZELGO MER?') is None
    assert parse_sell_offer('Izchak seems uninterested.') is None


def test_set_cost_rounding_matches_shk_c():
    # normal keeper pays half; a low keeper 3/8 rounded half up (shk.c: *10, /divisor, +5, /10)
    assert [sell_offer(c, shirt_or_dunce=False, low_keeper=False) for c in (20, 50, 300)] == [10, 25, 150]
    assert [sell_offer(c, shirt_or_dunce=False, low_keeper=True) for c in (20, 50, 100, 300)] == [8, 19, 38, 113]
    assert sell_offer(20, shirt_or_dunce=True, low_keeper=False) == 7  # 20/3 = 6.67 -> 7
    assert sell_offer(20, shirt_or_dunce=True, low_keeper=True) == 5   # 20/4


def test_offer_narrows_to_price_groups():
    assert costs_for_offer(10, SCROLL_COSTS, shirt_or_dunce=False) == {20}           # identify only
    assert costs_for_offer(40, SCROLL_COSTS, shirt_or_dunce=False) == {80}           # enchant armour / remove curse
    assert costs_for_offer(30, SCROLL_COSTS, shirt_or_dunce=False) == {60, 80}       # 60/2 or 80 * 3/8
    assert costs_for_offer(11, SCROLL_COSTS, shirt_or_dunce=False) == set()          # no scroll costs that


def test_only_shops_of_known_type_are_tried():
    # type 0 (not read yet) squares can lie outside the shop (bench job 83, seed 1112)
    assert 0 not in shop_sell.TRY_SHOPS
    assert shop_sell.TRY_SHOPS == shop_sell.BUYS_SCROLLS


def test_shop_reacted():
    assert shop_sell.shop_reacted('Adjama offers 50 gold pieces for your scroll labeled FOO.  Sell it? [ynaq] (y)')
    assert shop_sell.shop_reacted('Kirikkale seems uninterested.')
    assert shop_sell.shop_reacted('Adjama cannot pay you at present.  Will you accept 50 zorkmids in credit for your scroll? [ynaq] (y)')
    assert not shop_sell.shop_reacted('You drop a scroll labeled HAPAX LEGOMENON.')
