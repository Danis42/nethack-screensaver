"""Sell-offer price identification (Phase 02.2 price-ID step 3).

In a shop that buys scrolls the bot drops one unknown scroll, reads the shopkeeper's offer and answers "n"
(the scroll stays the hero's and is picked up again for free). The offer narrows the scroll's base price:
NetHack 5.0 shk.c set_cost() pays base/2 (base/3 with a dunce cap or a visible shirt), and a quarter of
shopkeepers (m_id % 4 == 0, not visible to the bot) pay 3/4 of that for unidentified items. Offers that are not
the real price are ignored: "offers only" (shopkeeper short of gold) and "in credit" (shopkeeper without gold).
NetHack records both in its price memory too, so the price_quotes "{sell X}" suffix is not used for this."""
import re

# shop types that buy scrolls (5.0 shknam.c shtypes: general store, second-hand bookstore, rare books)
BUYS_SCROLLS = frozenset({1, 3, 10})
# Only shops whose type the bot has read. Type 0 (not read) was tried too until bench job 83: the shop outline
# (agent._update_level_shops) can spill out through the door, so type-0 "shop" squares are often outside the
# shop; every unknown scroll was dropped there for no offer and marked tested (seed 1112).
TRY_SHOPS = BUYS_SCROLLS

# 5.0 shk.c sellobj(): every answer of a shopkeeper who is in the shop and awake. A plain "You drop ..." with none
# of these means the square was not a shop floor the keeper deals on (outline spill, or keeper away/asleep).
_REACTIONS = (' offers ', ' seems uninterested', ' cannot pay you', 'Thank you, scum', ' smirks with satisfaction',
              'Thank you for your contribution')


def shop_reacted(message):
    """True if the drop message carries a shopkeeper's answer (sellobj)."""
    return any(r in message for r in _REACTIONS)

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
