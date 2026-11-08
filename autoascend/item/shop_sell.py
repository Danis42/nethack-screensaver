"""Sell-offer price identification (Phase 02.2 price-ID step 3).

In a shop that buys scrolls the bot drops one unknown scroll, reads the shopkeeper's offer and answers "n"
(the scroll stays the hero's and is picked up again for free). The offer narrows the scroll's base price:
NetHack 5.0 shk.c set_cost() pays base/2 (base/3 with a dunce cap or a visible shirt), and a quarter of
shopkeepers (m_id % 4 == 0, not visible to the bot) pay 3/4 of that for unidentified items. Offers that are not
the real price are ignored: "offers only" (shopkeeper short of gold) and "in credit" (shopkeeper without gold);
both are also why the price_quotes "{sell X}" suffix cannot be trusted for this."""
import re

# shop types that buy scrolls (5.0 shknam.c shtypes: general store, second-hand bookstore, rare books)
BUYS_SCROLLS = frozenset({1, 3, 10})
# a shop whose type the bot has not read yet is tried too: one that does not buy says "seems uninterested"
TRY_SHOPS = BUYS_SCROLLS | {0}

_OFFER = re.compile(r' offers (\d+) gold pieces? for (?:your|the) ')


def parse_sell_offer(message):
    """The full per-stack offer in a "Sell it?" prompt, or None when the message carries no real price."""
    if ' offers only ' in message or ' in credit ' in message:
        return None
    match = _OFFER.search(message)
    return int(match[1]) if match else None


def sell_offer(cost, *, shirt_or_dunce, low_keeper):
    """shk.c set_cost() for one unidentified, non-gem item of base price `cost`."""
    tmp, multiplier, divisor = cost, 1, (3 if shirt_or_dunce else 2)
    if low_keeper and tmp > 1:
        multiplier, divisor = 3, divisor * 4
    if tmp >= 1:
        tmp = (tmp * multiplier * 10 // divisor + 5) // 10
        tmp = max(tmp, 1)
    return tmp


def costs_for_offer(offer, costs, *, shirt_or_dunce):
    """Base prices out of `costs` that either kind of shopkeeper would answer with `offer`."""
    return {c for c in costs
            if offer in (sell_offer(c, shirt_or_dunce=shirt_or_dunce, low_keeper=False),
                         sell_offer(c, shirt_or_dunce=shirt_or_dunce, low_keeper=True))}
