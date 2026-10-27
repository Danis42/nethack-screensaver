"""Generate the `objects = [...]` list of autoascend/objects/data.py from NetHack's include/objects.h.

The list mirrors the object macros (WEAPON(...), ARMOR(...), ...) with NetHack 5's trailing enum-name
argument dropped. Objects that data.py writes by hand (quest items, boulders, blank paper, ...) are copied
from the current data.py by name. Usage:
    python3 -I scripts/gen_objects_data.py reference/nethack-5.0.0/include/objects.h autoascend/objects/data.py
prints the new list; --write replaces it in data.py.
"""
import re
import sys

MACROS = {'WEAPON', 'PROJECTILE', 'BOW', 'ARMOR', 'HELM', 'CLOAK', 'SHIELD', 'GLOVES', 'BOOTS', 'DRGN_ARMR',
          'RING', 'AMULET', 'TOOL', 'CONTAINER', 'EYEWEAR', 'WEPTOOL', 'FOOD', 'POTION', 'SCROLL',
          'XTRA_SCROLL_LABEL', 'SPELL', 'WAND', 'COIN', 'GEM', 'ROCK', 'OBJECT', 'GENERIC'}
LEATHER_BOOKS = {'parchment', 'vellum'}  # objects.h overrides PAPER with LEATHER for these two
NONE_OBJECTS = {'strange object', 'blinding venom', 'acid venom', 'splash of blinding venom',
                'splash of acid venom'}


def strip_source(text):
    text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    out, skip = [], 0
    lines = iter(text.split('\n'))
    for line in lines:
        s = line.strip()
        if skip:
            if s.startswith('#if'):
                skip += 1
            elif s.startswith('#endif'):
                skip -= 1
            continue
        if s.startswith('#if 0'):
            skip = 1
            continue
        if s.startswith('#'):
            while line.rstrip().endswith('\\'):  # multi-line #define
                line = next(lines)
            continue
        out.append(line)
    return '\n'.join(out)


def calls(text):
    """Top-level NAME(args) calls in source order, args split at depth-0 commas."""
    i = 0
    while True:
        m = re.compile(r'\b([A-Z_]+)\s*\(').search(text, i)
        if not m:
            return
        name, j, depth, start = m.group(1), m.end(), 1, m.end()
        while depth:
            c = text[j]
            if c == '"':
                j = text.index('"', j + 1)
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            j += 1
        i = j
        if name in MACROS:
            yield name, split_args(text[start:j - 1])


def split_args(s):
    args, depth, cur, in_str = [], 0, '', False
    for c in s:
        if c == '"':
            in_str = not in_str
        if not in_str:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif c == ',' and depth == 0:
                args.append(cur.strip())
                cur = ''
                continue
        cur += c
    args.append(cur.strip())
    return [' '.join(a.split()) for a in args]


def py(arg):
    return 'None' if arg == 'NoDes' else arg


def hand_written(data_py):
    """name -> line for the Misc(...)/QuestItem(...) entries data.py writes by hand."""
    out = {}
    for m in re.finditer(r'^    ((?:Misc|QuestItem)\("([^"]+)", (?:"([^"]*)"|None), wt=[^)]*\)),', data_py, re.M):
        out[(m.group(2), m.group(3))] = m.group(1)
    return out


def generate(objects_h, data_py):
    special = hand_written(data_py)
    lines = []
    for name, args in calls(strip_source(objects_h)):
        if name == 'GENERIC':
            lines.append('None,  # generic %s' % args[0].strip('"'))
            continue
        if name == 'OBJECT':
            obj = re.match(r'OBJ\("([^"]+)", (?:"([^"]*)"|NoDes)\)', args[0])
            if not obj:  # OBJ(NoDes, NoDes): the terminating entry, not an object
                continue
            oname, desc = obj.group(1), obj.group(2)
            if oname == 'meat ring':  # a raw OBJECT in objects.h; data.py keeps it as food
                lines.append('FOOD("meat ring", 0, 1, 5, 0, FLESH, 5, CLR_BROWN),')
                continue
            if oname in NONE_OBJECTS:
                lines.append('None,  # %s' % oname)
            else:
                lines.append(special[(oname, desc)] + ',')
            continue
        args = args[:-1]  # NetHack 5 enum name (sn)
        if name == 'XTRA_SCROLL_LABEL':
            name, args = 'SCROLL', ['NoDes', args[0], '1', '0', '100']
        oname = args[0].strip('"')
        desc = args[1].strip('"') if name not in ('FOOD', 'COIN', 'DRGN_ARMR') else None
        if oname == 'blank paper':
            lines.append(special[(oname, desc)] + ',')
            continue
        if name == 'SPELL' and desc in LEATHER_BOOKS:
            name = 'SPELL_LEATHER'
        lines.append('%s(%s),' % (name, ', '.join(py(a) for a in args)))
    return 'objects = [\n' + ''.join('    %s\n' % line for line in lines) + ']\n'


def main():
    objects_h, data_path = sys.argv[1], sys.argv[2]
    data_py = open(data_path).read()
    new = generate(open(objects_h).read(), data_py)
    if '--write' not in sys.argv:
        sys.stdout.write(new)
        return
    start = data_py.index('objects = [\n')
    end = data_py.index('\n]\n', start) + len('\n]\n')
    open(data_path, 'w').write(data_py[:start] + new + data_py[end:])


if __name__ == '__main__':
    main()
