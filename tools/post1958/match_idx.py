import json, re
D2 = json.load(open('docs2.json'))
IDX = {p: json.load(open(f'idx_{p}.json')) for p in ('paul-vi', 'john-paul-ii')}
STOP = set('the of and to in a on at for with by from his holy father pope address letter message homily encyclical apostolic exhortation constitution motu proprio speech discourse'.split())
def words(t): return {w for w in re.findall(r'[a-z]+', t.lower()) if w not in STOP and len(w) > 2}
def year(it):
    u = it['any'] or ''
    for m in re.finditer(r'_(\d{8})(?:_|\.|-)', u):
        v = m.group(1)
        if v[:2] in ('19', '20') and 1 <= int(v[4:6]) <= 12: return int(v[:4])
        if v[4:6] in ('19', '20'): return int(v[4:])
    m = re.search(r'(19|20)\d\d', it['title']); return int(m.group(0)) if m else None
for d in D2:
    if d['author'] == 'other': continue
    W = words(d['title'])
    best = []
    for it in IDX[d['author']]:
        if year(it) not in (d['year'], d['year'] - 1, d['year'] + 1): continue
        tw = words(it['title'] + ' ' + re.sub(r'[_\-./]', ' ', (it['any'] or '').split('/')[-1]))
        s = len(W & tw) / max(1, len(W)) + (0.2 if year(it) == d['year'] else 0)
        best.append((s, it['title'][:90], 'EN' in it['links'], it['any']))
    best.sort(key=lambda x: -x[0])
    d['cands'] = best[:3]
    b = best[0] if best else None
    print(d['year'], '|', d['title'][:60], '=>', f"{b[0]:.2f}" if b else '-', b[1] if b else '', '| EN' if b and b[2] else '| --')
json.dump(D2, open('docs2.json', 'w'), ensure_ascii=False, indent=1)
