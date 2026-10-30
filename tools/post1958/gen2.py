# Paul VI to John Paul II: entries in the format of src/data/entries.json.
import re, json, sys
from align import doc
from manifest2 import DOCS
MON = ['Jan.', 'Feb.', 'March', 'April', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']
def clean(t):
    t = re.sub(r'\s*\[\d{1,3}\]|\s*\(\d{1,3}\*?\)(?=[\s.,;:]|$)', '', t)      # footnote markers
    t = re.sub(r'\s*\[\s*\]', '', t)
    t = re.sub(r'\s+([,;:?!]|\.(?!\.\.))', r'\1', t)
    return re.sub(r'\s+', ' ', t).strip()
def head(h, title):
    if not h or len(h) < 4 or len(h) > 120 or h.endswith(')') or re.search(r'\d{4}|proclaimed|promulgated|his holiness|encyclical|apostolic|to the bishops|venerable|beloved|dear |brothers|excellency|eminence|greeting', h, re.I):
        return None
    if title and title.lower() in h.lower(): return None
    h = re.sub(r'^(CHAPTER|PART|SECTION|ARTICLE)\s+[IVXL0-9]+[.:]?\s*|^[IVXL]+\.\s+|^[A-Z0-9]\)\s*|^\d+\.\s*', '', h).strip()
    if not h or not re.search(r'[a-z]{3}', h, re.I): return None
    if h.isupper():
        small = {'of', 'the', 'and', 'in', 'on', 'to', 'a', 'an', 'for', 'with', 'its', 'as', 'by', 'or'}
        w = h.lower().split()
        h = ' '.join(x if i and x in small else x.capitalize() for i, x in enumerate(w))
    return h
def date_of(url):
    for v in re.findall(r'_(\d{8})(?=[_.\-])', url):
        if v[:2] in ('19', '20') and 1 <= int(v[4:6]) <= 12: return v[:4], int(v[4:6]), int(v[6:])
        if v[4:6] in ('19', '20'): return v[4:], int(v[2:4]), int(v[:2])
    m = re.search(r'_(\d{4})_', url); return (m.group(1), None, None)
def fmt(d):
    y, m, dd = d
    return f'{MON[m - 1]} {dd}, {y}' if m else y
B = json.load(open('batch2.json'))
M = {d[0]: d for d in DOCS}
sel, refs = {}, {}
for x in B:
    if x.get('fail'): continue
    S = doc(x['doc']); numbered = len({s['art'] for s in S if s['art']}) >= 3 and M[x['doc']][1] not in ('AD', 'JD')   # an address is one entry
    for j in x['idx']:
        a = S[j]['art'] if numbered else 0
        if numbered and a is None: continue
        sel.setdefault((x['doc'], a), set()).add(j)
        if x['nd'] not in refs.setdefault((x['doc'], a), []): refs[(x['doc'], a)].append(x['nd'])
entries = []
for (k, a), js in sel.items():
    key, pre, era, weight, kind, title, spec, url = M[k]
    S = doc(k); d = date_of(url)
    allj = [j for j, s in enumerate(S) if (s['art'] == a if a else True)]
    paras, cur, curp, gap = [], [], None, False
    for j in allj:
        if j not in js:
            gap = bool(cur) or bool(paras); continue
        if gap: (cur if cur else paras)[-1] += ' ...'
        gap = False
        if curp is not None and S[j]['p'] != curp and cur: paras.append(' '.join(cur)); cur = []
        cur.append(S[j]['s']); curp = S[j]['p']
    if cur: paras.append(' '.join(cur))
    if allj[0] not in js: paras[0] = '... ' + paras[0]
    if allj[-1] not in js and not paras[-1].endswith('...'): paras[-1] += ' ...'
    text = [p for p in (clean(p) for p in paras) if p and p != '...']
    hs = None
    for j in range(allj[0], -1, -1):
        hs = head(S[j]['head'], title)
        if hs: break
    eid = pre + (f'{d[0]}{d[1]:02d}{d[2]:02d}' if pre in ('AD', 'JD') else '') + (str(a) if a else '')
    src = f'[From the {kind}, "{title}," {fmt(d)}]' if title else f'[From the {kind}, {fmt(d)}]'
    entries.append({'id': eid, 'era': era, 'topic': hs or title or kind, 'source': src, 'text': text,
                    'weight': weight, 'nd': refs[(k, a)], '_sort': (d[0], d[1] or 0, d[2] or 0, a)})
entries.sort(key=lambda e: e['_sort'])
ids = {}
for e in entries:
    del e['_sort']
    if e['id'] in ids: ids[e['id']] += 1; e['id'] += f'-{ids[e["id"]]}'
    else: ids[e['id']] = 1
json.dump(entries, open('entries2.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(len(entries), 'entries,', sum(len(' '.join(e['text']).split()) for e in entries), 'words;', Counter(e['era'] for e in entries))
print('dup ids', [e['id'] for e in entries if '-' in e['id']])
print(Counter(e['weight'] for e in entries))
