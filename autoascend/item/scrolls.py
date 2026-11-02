"""Which scroll to read now (Phase 02.2 Part 1a, plan decision D-06).

A scroll whose identity is known is read when its effect is wanted. An unidentified scroll is read when every
identity left for it (after shop price identification narrowed its glyph) is safe to read: enchant armour and
remove curse share the 80 zm group, identify is the only 20 zm scroll. Never while confused (remove curse then
curses at random, enchant armour only rustproofs), stunned, hallucinating or blind, and never an unpaid one."""

from autoascend.item.item import Item

ENCHANT_ARMOR, ENCHANT_WEAPON, REMOVE_CURSE, IDENTIFY = 'enchant armor', 'enchant weapon', 'remove curse', 'identify'
# Unknown scrolls are read only if all their possible identities are here.
SAFE_UNKNOWN = frozenset({ENCHANT_ARMOR, REMOVE_CURSE, IDENTIFY, ENCHANT_WEAPON, 'light', 'magic mapping',
                          'gold detection', 'food detection', 'blank paper'})
ARMOR_LIMIT = 3  # above +3 a worn piece may evaporate when enchanted again (read.c seffect_enchant_armor)
WEAPON_LIMIT = 5  # above +5 the weapon may evaporate (wield.c chwepon)


def scroll_names(item):
    return {o.name for o in item.objs}


def wants(name, *, worn_armor_mods, weapon_mod, cursed_equipped, unidentified):
    """Whether reading a scroll of `name` helps now.

    worn_armor_mods: enchantments of worn armour (None = unknown); weapon_mod: wielded weapon enchantment, or
    None with no weapon wielded; cursed_equipped: a worn or wielded item is known cursed; unidentified: the pack
    holds something worth identifying."""
    if name == ENCHANT_ARMOR:
        return bool(worn_armor_mods) and all((m or 0) <= ARMOR_LIMIT for m in worn_armor_mods)
    if name == ENCHANT_WEAPON:
        return weapon_mod is not None and weapon_mod < WEAPON_LIMIT
    if name == REMOVE_CURSE:
        return cursed_equipped
    if name == IDENTIFY:
        return unidentified
    return False


def should_read(item, *, impaired, **state):
    if impaired or item.category != SCROLL_CLASS or item.status == Item.CURSED or \
            item.shop_status != Item.NOT_SHOP:
        return False
    names = scroll_names(item)
    if len(names) == 1:
        return wants(next(iter(names)), **state)
    if not names <= SAFE_UNKNOWN:
        return False
    # unknown but safe: worth it when at least one possible identity is wanted (armour on for the 80 zm group)
    return any(wants(n, **state) for n in names)


SCROLL_CLASS = 9  # nh.SCROLL_CLASS
# What an identify scroll should name first: menu class headers, best first.
IDENTIFY_ORDER = ('Amulets', 'Rings', 'Wands', 'Armor', 'Scrolls', 'Potions', 'Tools')


def identify_choice(popup):
    """The menu letter to pick in "What would you like to identify first?"; None if the menu shows none."""
    header, best = None, None
    for line in popup:
        stripped = line.strip()
        if stripped in IDENTIFY_ORDER or stripped in ('Weapons', 'Comestibles', 'Gems/Stones', 'Spellbooks',
                                                       'Coins', 'Boulders/Statues', 'Iron balls', 'Chains'):
            header = stripped
            continue
        if len(line) > 4 and line[1:4] == ' - ':
            rank = IDENTIFY_ORDER.index(header) if header in IDENTIFY_ORDER else len(IDENTIFY_ORDER)
            if best is None or rank < best[0]:
                best = (rank, line[0])
    return None if best is None else best[1]
