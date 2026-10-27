"""Triage NetHack's doc/fixesX-Y-Z.txt with a local Ollama model: which entries matter to the bot.

Each entry gets PARSE (changes text, prompts, menus, names or symbols the bot reads), RULE (changes
a game rule the bot's strategy relies on) or NONE. Development-only, platform and cleanup sections
are skipped. Resumable. Usage:
    python3 -I scripts/fixes_triage.py reference/nethack-5.0.0/doc/fixes5-0-0.txt out.jsonl [model]
"""
import json
import os
import re
import sys
import urllib.request

SKIP_SECTIONS = ('Exposed Via git Repository', 'Platform- and/or Interface-Specific', 'Code Cleanup')
BATCH = 12

PROMPT = """You review NetHack 5.0 change-log entries for a bot that plays NetHack. The bot was written
for NetHack 3.6 and reads the tty screen: messages, yes/no prompts, menus, item and monster names,
map symbols. It plays a dwarvish Valkyrie diving for the Gnomish Mines, Sokoban, Oracle and deeper,
prays when in trouble, eats corpses, engraves Elbereth, uses shops.
For each entry answer one category:
- "PARSE": the change alters text, a prompt or question, a menu, an item/monster name or appearance,
  a map symbol, an option default or how a command behaves, so a 3.6 bot could misread or get stuck
- "RULE": the change alters a game rule the bot's survival or route depends on (prayer, food and
  hunger, corpses, Elbereth, Sokoban, shops, stairs and dungeon layout, monster or item strength)
- "NONE": anything else (bug fixes of rare cases, wizard mode, cosmetics, other roles)
Answer only JSON: {"items": [{"id": <id>, "cat": "PARSE"|"RULE"|"NONE", "why": "<8 words>"}]}

ENTRIES:
%s"""


def entries(path):
    out, cur, sec = [], None, None
    lines = open(path).read().split('\n')
    for i, line in enumerate(lines):
        if i + 1 < len(lines) and re.match(r'^-{5,}$', lines[i + 1]):
            sec = line.strip()
            continue
        if re.match(r'^-{5,}$', line) or not line.strip():
            continue
        if line[:1] in ('\t', ' ') and cur is not None:
            cur['text'] += ' ' + line.strip()
        else:
            cur = {'id': len(out), 'sec': sec, 'text': line.strip()}
            out.append(cur)
    return [e for e in out if e['sec'] and not any(s in e['sec'] for s in SKIP_SECTIONS)]


def ask(model, batch):
    body = '\n'.join('%d: %s' % (e['id'], e['text']) for e in batch)
    req = urllib.request.Request('http://localhost:11434/api/generate', data=json.dumps({
        'model': model, 'prompt': PROMPT % body, 'format': 'json', 'stream': False,
        'options': {'temperature': 0, 'num_ctx': 8192}}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.loads(r.read())['response']).get('items', [])


def main():
    src, out = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else 'qwen2.5:14b'
    done = set()
    if os.path.exists(out):
        done = {json.loads(line)['id'] for line in open(out)}
    todo = [e for e in entries(src) if e['id'] not in done]
    print(f'{len(todo)} entries to triage', flush=True)
    with open(out, 'a') as f:
        for k in range(0, len(todo), BATCH):
            batch = todo[k:k + BATCH]
            answers = {a.get('id'): a for a in ask(model, batch) if isinstance(a, dict)}
            for e in batch:
                a = answers.get(e['id'], {})
                f.write(json.dumps({**e, 'cat': a.get('cat', 'UNKNOWN'), 'why': a.get('why', '')}) + '\n')
            f.flush()
            print(f'{k + len(batch)}/{len(todo)}', flush=True)


if __name__ == '__main__':
    main()
