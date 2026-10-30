import json, sys
from align2 import toks, idf, nd_sentences, GAP
from artalign import articles, wsim
B = json.load(open('batch1.json'))
for x in B:
    d = x['doc'] if isinstance(x['doc'], str) else x['doc'][0]
    if d not in sys.argv[1].split(','): continue
    A = articles(d); W = idf(d); at = {a: toks(' '.join(s['s'] for s in A[a])) for a in A}
    segs, cur = [], []
    for s in nd_sentences(x['ndtext']):
        if s == GAP:
            if cur: segs.append(' '.join(cur)); cur = []
        else: cur.append(s)
    if cur: segs.append(' '.join(cur))
    print(f"## {x['nd']}")
    for sg in segs:
        st = toks(sg)
        if len(st) < 5: continue
        sc = sorted(((wsim(st, at[a], W) * 0.6 + wsim(at[a], st, W) * 0.4, a) for a in A), reverse=True)[:4]
        print('  ', ' '.join(sg.split()[:14]), '→', ', '.join(f'{a}:{s:.2f}' for s, a in sc))
