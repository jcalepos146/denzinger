# Parse the chronological table (1958 on) into documents with their ND id specs.
import re, json, sys
lines = open(sys.argv[1]).read().split('\n')
start = next(i for i, l in enumerate(lines) if 'Instruction of the S. Congregation of rites on sacred music' in l)
recs, cur, section = [], None, None
for l in lines[start:]:
    if re.search(r'CHRONOLOGICAL|THE CHRISTIAN FAITH|BIBLICAL INDEX', l) or not l.strip():
        continue
    m = re.match(r'^\s*(\S{4})\s{2,}(.*)$', l)
    if m and (re.match(r'\d{4}$', m.group(1)) or m.group(1) in ('Lo75', '19971', 'IE')) and not re.match(r'^\s{6,}', l):
        cur = {'year': m.group(1), 'text': m.group(2).strip()}
        recs.append(cur)
    elif re.match(r'^\s*THE (SECOND|THIRD|FOURTH|FourRTH)', l) or 'SYNOD' in l.upper() and l.strip().isupper():
        cur = {'year': None, 'text': l.strip(), 'group': True}; recs.append(cur)
    elif cur is not None:
        cur['text'] += ' ' + l.strip()
for r in recs:
    r['text'] = re.sub(r'\s+', ' ', r['text'])
json.dump(recs, open('chron.json', 'w'), indent=1, ensure_ascii=False)
for r in recs: print(r['year'], '|', r['text'][:130])
