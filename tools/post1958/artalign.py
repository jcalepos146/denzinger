# Paragraph-level alignment for texts whose official English is a different translation.
import re
from align import doc
from align2 import toks, idf, nd_sentences, GAP
def articles(k):
    S = doc(k); A = {}
    for x in S:
        if x['art'] is None: continue
        A.setdefault(x['art'], []).append(x)
    return A
def wsim(a, b, W):
    A, B = set(a), set(b)
    if not A or not B: return 0
    return sum(W.get(w, 3) for w in A & B) / sum(W.get(w, 3) for w in A)
def align_art(text, k, tau=0.32):
    A = articles(k); W = idf(k)
    segs, cur = [], []
    for s in nd_sentences(text):
        if s == GAP:
            if cur: segs.append(' '.join(cur)); cur = []
        else: cur.append(s)
    if cur: segs.append(' '.join(cur))
    segs = [s for s in segs if len(toks(s)) >= 5]
    if not segs: return None
    arts = sorted(A)
    at = {a: toks(' '.join(x['s'] for x in A[a])) for a in arts}
    picked, last = [], 0
    for sg in segs:
        st = toks(sg)
        # a segment may span consecutive short paragraphs: try windows of 1-4
        best = (0, None)
        for i, a in enumerate(arts):
            if a < last: continue
            for w in range(1, 5):
                win = arts[i:i + w]
                if len(win) < w: break
                t = sum((at[x] for x in win), [])
                s = wsim(st, t, W) * min(1, len(st) / max(8, 0.6 * len(set(t))))
                if s > best[0] + 0.02: best = (s, win)
        if best[1] and best[0] >= tau and (not picked or best[1][0] - picked[-1][-1] <= 40):
            picked.append(best[1]); last = best[1][0]
    if not picked: return None
    order = []
    for win in picked:
        for a in win:
            if a not in order: order.append(a)
    text_out, prev = [], None
    for a in order:
        if prev is not None and a != prev + 1: text_out.append('...')
        text_out.append(' '.join(x['s'] for x in A[a])); prev = a
    paras = []
    for p in text_out:
        if p == '...' and paras: paras[-1] += ' ...'
        else: paras.append(p)
    return {'arts': order, 'text': paras, 'segs': len(segs), 'hit': len(picked)}
