# Order-preserving alignment of a Neuner-Dupuis excerpt to the official sentences.
import re, math
from collections import Counter
from align import content, sentences, nd_clean, doc
GAP = '\x00'
def stem(w):
    for suf in ('ings', 'ing', 'edly', 'ed', 'es', 's', 'ly'):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[:-len(suf)]
    return w
def toks(t): return [stem(w) for w in content(t)]
IDF = {}
def idf(k):
    if k not in IDF:
        S = doc(k); df = Counter()
        for x in S: df.update(set(toks(x['s'])))
        n = len(S); IDF[k] = {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}
    return IDF[k]
def nd_sentences(text):
    text = re.sub(r'\[\s*\.{3,4}\s*\]|\[\.{2,}|\.{2,}\]|_\[\.\.\.\]|\[…\]', ' ' + GAP + ' ', text)
    parts = re.split(r'(?:(?<=[.?!;:])|(?<=[.?!;:]["”’)]))\s+(?=["“‘(\x00]?\s*[A-Z\x00])|\s(?=\x00)|(?<=\x00)\s', text)
    return [p.strip() for p in parts if p.strip()]
def sim(a, b, W):
    A, B = set(a), set(b)
    if not A or not B: return 0
    sh = sum(W.get(w, 3) for w in A & B)
    return sh / min(sum(W.get(w, 3) for w in A), sum(W.get(w, 3) for w in B)) * min(1, len(A & B) / 3)
def align(text, k, tau=0.35, arts=None):
    S = doc(k); W = idf(k)
    nd = nd_sentences(text)
    ot = [toks(x['s']) for x in S]
    EDIT = re.compile(r'\((\d{1,3}(-\d{1,3})?|[A-Z]{2,3} \d+\w*)\)|^(The|This) (Constitution|Decree|Declaration|encyclical|document|Synod) (deals|treats|describes|shows|states|stresses|proceeds|then|first|goes on)\b')
    nd = [s for s in nd if s == GAP or not EDIT.search(s)]          # editorial sentences of Neuner-Dupuis
    rows = [(s, toks(s)) for s in nd if s != GAP]
    gaps_after = []   # for each ND sentence row: is a [...] after it
    gi = 0; flags = []
    for s in nd:
        if s == GAP:
            if flags: flags[-1] = True
            else: gaps_after.append('lead')
        else: flags.append(False)
    lead_gap = bool(gaps_after)
    m, N = len(rows), len(S)
    if not m: return None
    # candidate official sentences per ND sentence (top few) keeps the DP small
    cand = []
    for _, t in rows:
        sc = sorted(((sim(t, ot[j], W), j) for j in range(N) if not arts or S[j]['art'] in arts), reverse=True)[:8]
        cand.append([(s, j) for s, j in sc if s >= tau])
    # DP over ND rows, official index non-decreasing; skipping a row costs nothing
    best = {}  # j -> (score, path)
    for i, cs in enumerate(cand):
        new = dict(best)
        for s, j in cs:
            near = [v for jj, v in best.items() if jj <= j and (j - jj) <= 4]
            far = [v for jj, v in best.items() if jj <= j and 4 < (j - jj) <= 60] if s >= 0.5 else []
            prev = max(near + far or [(0, [])], key=lambda v: v[0])
            if not near and not far and best and s < 0.5: continue    # a weak match far from the rest
            cand_v = (prev[0] + s, prev[1] + [(i, j, s)])
            if j not in new or cand_v[0] > new[j][0]: new[j] = cand_v
        best = new
    if not best: return None
    score, path = max(best.values(), key=lambda v: v[0])
    return {'nd': rows, 'gapflags': flags, 'lead': lead_gap, 'path': path, 'score': score, 'm': m}
def render(res, k):
    """Official text from the first to the last aligned sentence; a [...] in Neuner-Dupuis between two
    aligned sentences becomes '...' in place of the official sentences it skips."""
    S = doc(k); path = res['path']
    if not path: return None
    out, arts = [], []
    j0 = path[0][1]; jl = path[-1][1]
    # sentences of the excerpt before the first match or after the last: extend within the same article
    for _ in range(path[0][0]):
        if j0 > 0 and S[j0 - 1]['p'] == S[j0]['p']: j0 -= 1
    for _ in range(res['m'] - 1 - path[-1][0]):
        if jl + 1 < len(S) and S[jl + 1]['p'] == S[jl]['p']: jl += 1
    skip = set()
    for (i1, j1, _), (i2, j2, _) in zip(path, path[1:]):
        if j2 - j1 > 1 and (any(res['gapflags'][i1:i2]) or j2 - j1 - 1 > max(3, 2 * (i2 - i1 - 1) + 1)):
            skip.update(range(j1 + 1, j2)); skip.add(('gap', j1))
    idx = [j for j in range(j0, jl + 1) if j not in skip]
    paras, cur, curp = [], [], None
    if res['lead'] or path[0][0] > 0 and False: cur.append('...')
    for j in range(j0, jl + 1):
        if j in skip:
            continue
        x = S[j]
        if curp is not None and x['p'] != curp and cur:
            paras.append(' '.join(cur)); cur = []
        cur.append(x['s']); curp = x['p']; arts.append(x['art'])
        if ('gap', j) in skip: cur.append('...')
    if res['gapflags'] and res['gapflags'][path[-1][0]]: cur.append('...')
    if cur: paras.append(' '.join(cur))
    paras = [re.sub(r'\s+\.\.\.$', ' ...', p) for p in paras]
    return {'text': paras, 'arts': sorted({a for a in arts if a is not None}), 'idx': idx}
