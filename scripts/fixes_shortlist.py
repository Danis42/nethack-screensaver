"""Second, strict pass over fixes-triage.jsonl: keep only entries that need a bot code change or that
change early/mid-game survival for a dwarvish Valkyrie a lot. Usage: python3 -I scripts/fixes_shortlist.py in out"""
import json
import sys
import urllib.request

PROMPT = """A bot written for NetHack 3.6 now plays NetHack 5.0 as a dwarvish Valkyrie (Dlvl 1-15: Gnomish
Mines, Minetown, Oracle, Sokoban, Big Room, Quest portal). It reads tty messages, y/n prompts and menus with
exact string matching. Be strict. For each change-log entry decide:
- "code": yes ONLY if a message, prompt, menu or item/monster name the bot would commonly meet on Dlvl 1-15
  now reads differently or a new prompt/menu appears, so string matching breaks
- "survival": yes ONLY if it changes a common situation for a Valkyrie on Dlvl 1-15 enough to change deaths
  or progress (food, prayer, common monsters, common items, Sokoban, shops, stairs, Elbereth)
Answer only JSON: {"items": [{"id": <id>, "code": "yes"|"no", "survival": "yes"|"no", "note": "<12 words>"}]}

ENTRIES:
%s"""


def ask(batch):
    body = '\n'.join('%d: %s' % (e['id'], e['text'][:600]) for e in batch)
    req = urllib.request.Request('http://localhost:11434/api/generate', data=json.dumps({
        'model': 'qwen2.5:14b', 'prompt': PROMPT % body, 'format': 'json', 'stream': False,
        'options': {'temperature': 0, 'num_ctx': 8192}}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.loads(r.read())['response']).get('items', [])


entries = [json.loads(line) for line in open(sys.argv[1])]
entries = [e for e in entries if e['cat'] != 'NONE']
with open(sys.argv[2], 'w') as out:
    for k in range(0, len(entries), 10):
        batch = entries[k:k + 10]
        answers = {a.get('id'): a for a in ask(batch) if isinstance(a, dict)}
        for e in batch:
            a = answers.get(e['id'], {})
            if a.get('code') == 'yes' or a.get('survival') == 'yes':
                out.write(json.dumps({'id': e['id'], 'code': a.get('code'), 'survival': a.get('survival'),
                                      'note': a.get('note', ''), 'text': e['text']}) + '\n')
        out.flush()
        print(f'{k + len(batch)}/{len(entries)}', flush=True)
