import re, json
from align import nd_clean, doc
from align2 import align, render
SPEC = {
 'pp': '1132-1135', 'mm': '2113-2123', 'pt': '2026-2042, 2124-2140/2',
 'sc': '668, 1231-1234a, 1258, 1334-1335, 1574-1575, 1663-1666',
 'lg': '716a-718a, 860-882, 1018, 1136, 1439, 1576, 1667, 1738-1741, 1834, 1998-1999, 2043-2047, 2311-2314',
 'oe': '1235-1236', 'ur': '909-914, 1439a', 'na': '424, 1019-1022', 'dv': '149-153, 246-257',
 'aa': '1439f-1440', 'dh': '2048-2050', 'ag': '1023-1026, 1137-1144, 1439c-d, 1741a',
 'po': '1439e, 1576b-c, 1741b-d',
 'gs': '154, 421-423, 668-669a, 1027a-1028, 1145, 1439b, 1576a, 1835-1840, 2051-2061, 2141-2144, 2214-2219, 2315-2316',
}
def k(s):
    m = re.match(r'(\d+)([a-zA-Z]{0,2})(?:/(\d+))?$', s.replace(' ', ''))
    return (int(m.group(1)), m.group(2).lower(), int(m.group(3) or 0))
def member(uid, spec):
    u = k(uid)
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-')
            if re.fullmatch(r'[a-z]', b): b = re.match(r'\d+', a).group(0) + b
            if k(a)[:1] <= u[:1] <= k(b)[:1] and (u[0] != k(a)[0] or u >= k(a)) and (u[0] != k(b)[0] or u[1] <= k(b)[1] or not k(b)[1] and not u[1] and u[2] <= max(k(b)[2], 99)):
                return True
        elif u[:2] == k(part)[:2]:
            return True
    return False
U = json.load(open('units.json'))
out = []
for u in U:
    docs = [d for d, s in SPEC.items() if member(u['id'], s)]
    if not docs: continue
    t = nd_clean(u['lines'])
    best = None
    for d in docs:
        stated = None
        if d not in ('mm', 'pt', 'pp'):
            from align import doc as _doc
            mx = max(x['art'] or 0 for x in _doc(d))
            stated = {int(a) for a in re.findall(r'(?:^|\s|\])(\d{1,3})\.\s+(?:\[|[A-Z“"‘])', t) if 1 < int(a) <= mx or a == '1' and t.lstrip().startswith('1.')}
        if stated and not re.match(r'^\s*(\[\.+\]\s*)?\d{1,3}\.', t): stated.add(min(stated) - 1)   # opens inside the article before
        r = align(t, d, arts=stated or None)
        if r and r['path'] and (best is None or r['score'] > best[1]['score']): best = (d, r)
    if not best:
        out.append({'nd': u['id'], 'doc': docs, 'fail': True, 'ndtext': t}); continue
    d, r = best
    o = render(r, d)
    out.append({'nd': u['id'], 'doc': d, 'arts': o['arts'], 'text': o['text'], 'idx': o['idx'], 'cover': round(len(r['path']) / r['m'], 2),
                'score': round(r['score'], 2), 'ndtext': t})
json.dump(out, open('batch1.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(len(out), 'units;', sum(1 for x in out if x.get('fail')), 'failed')
print(Counter(x['doc'] if isinstance(x['doc'], str) else 'fail' for x in out))
low = [x for x in out if not x.get('fail') and x['cover'] < 0.5]
print('low coverage', len(low)); [print(' ', x['nd'], x['doc'], x['arts'], x['cover']) for x in low]
