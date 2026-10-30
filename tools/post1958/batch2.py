# Paul VI to John Paul II: align the Neuner-Dupuis passages and build entries.
import re, json
from align import nd_clean, doc
from align2 import align, render
from spec import member

from manifest2 import DOCS
M = {d[0]: d for d in DOCS}
U = json.load(open('units.json'))
res = []
for u in U:
    ds = [d[0] for d in DOCS if member(u['id'], d[6])]
    if not ds: continue
    t = nd_clean(u['lines'])
    best = None
    for k in ds:
        S = doc(k); arts = {x['art'] for x in S if x['art']}
        stated = None
        if len(arts) >= 3:
            mx = max(arts)
            stated = {int(a) for a in re.findall(r'(?:^|\s|\])(\d{1,3})\.\s+(?:\[|[A-Z“"‘])', t) if 1 <= int(a) <= mx}
            if stated and not re.match(r'^\s*(\[\.+\]\s*)?\d{1,3}\.', t): stated.add(min(stated) - 1)
        r = align(t, k, arts=stated or None)
        if (not r or not r['path']) and stated: r = align(t, k)
        if r and r['path'] and (best is None or r['score'] > best[1]['score']): best = (k, r)
    if not best:
        res.append({'nd': u['id'], 'doc': ds, 'fail': True, 'ndtext': t}); continue
    k, r = best; o = render(r, k)
    S = doc(k); arts = {x['art'] for x in S if x['art']}
    if len(arts) >= 3:      # an article the passage names but the alignment missed: search it alone, more leniently
        named = {int(a) for a in re.findall(r'(?:^|\s|\])(\d{1,3})\.\s+(?:\[|[A-Z“"‘])', t) if 3 < int(a) <= max(arts)}
        for a in sorted(named - set(o['arts'])):
            r2 = align(t, k, tau=0.2, arts={a})
            if r2 and r2['path']:
                o2 = render(r2, k); o['idx'] = sorted(set(o['idx']) | set(o2['idx'])); o['arts'] = sorted(set(o['arts']) | {a})
    res.append({'nd': u['id'], 'doc': k, 'arts': o['arts'], 'idx': o['idx'], 'cover': round(len(r['path']) / r['m'], 2), 'ndtext': t})
json.dump(res, open('batch2.json', 'w'), ensure_ascii=False, indent=1)
fails = [x for x in res if x.get('fail')]
low = [x for x in res if not x.get('fail') and x['cover'] < 0.5]
print(len(res), 'passages;', len(fails), 'failed;', len(low), 'low coverage')
for x in fails: print('  FAIL', x['nd'], x['doc'], x['ndtext'][:80])
for x in low: print('  low', x['nd'], x['doc'], x['arts'], x['cover'])
