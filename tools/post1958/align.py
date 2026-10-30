# Match Neuner-Dupuis units to sentences of the official vatican.va text.
import re, json, sys
from vat_paras import paras
STOP = set('the of and to in a that is be as by for with which this it are his he or their from on its an not who has have was all also but so they these them we our us him at shall may can will one those such been were would should must into there what'.split())
def words(t): return re.findall(r"[a-z]+", t.lower().replace('’', "'"))
def content(t): return [w for w in words(t) if w not in STOP and len(w) > 2]
def sentences(P):
    from vat_paras import HEADS
    heads = list(HEADS)
    out = []
    for pi, (art, t) in enumerate(P):
        for s in re.split(r'(?:(?<=[.?!;:])|(?<=[.?!;:]["”’)]))\s+(?=["“‘(]?[A-Z])', t):
            if s.strip(): out.append({'art': art if not isinstance(art, tuple) else None, 'note': art[1] if isinstance(art, tuple) else None, 'p': pi, 's': s.strip(), 'head': heads[pi] if pi < len(heads) else None})
    return out
def nd_clean(lines):
    keep = []
    for l in lines:
        st = l.strip()
        if re.search(r'THE CHRISTIAN\s+FAITH', l): continue
        if re.match(r'^[A-Z][A-Z ,\'’—\-]{2,}[A-Z]\s+\d{1,4}$', st) or re.match(r'^\d{1,4}\s+[A-Z][A-Z ,\'’—\-]{2,}$', st): continue  # running head
        if re.fullmatch(r'[A-Z0-9 ,.\'’—\-()]{4,}', st) and re.search(r'[A-Z]{3}', st) and not re.search(r'[a-z]', st):
            break                                                  # heading of the next document
        if re.match(r'^\d{1,2}\.\s+(Cf\.|See|AAS|DS|PL|PG|Ibid|Ib\.)', st): continue   # footnote
        if re.match(r'^\s{4,}\d{1,2}[.,]\s', l) and len(st) < 100 and re.search(r'\d', st[3:]): continue   # footnote with its citation
        if (re.match(r'^(Chapters?|Part|Section)\s+[IVXL0-9]+\b.{0,80}$', st) or re.fullmatch(r'Article\s+\d+\.?', st)) and not st.endswith('.'):
            break                                                  # editorial summary of the next section follows
        if re.match(r'^\s*\(.*\)\s*$', l): continue             # ND's own subheadings
        if re.search(r'THE CHRISTIAN\s+FAITH', l): continue
        if re.match(r'^\s*[A-Z][A-Z ,\'’—\-]{8,}\s+\d{1,4}\s*$', l): continue  # running head
        l = re.sub(r'^\s*\d{4}\s{2,}', ' ', l)                   # DS margin number
        keep.append(l.strip())
    t = ' '.join(keep)
    t = re.sub(r'(\w)- (\w)', r'\1\2', t)
    return t
def score(sent, ndset):
    c = content(sent)
    if len(c) < 4: return 0
    return sum(w in ndset for w in c) / len(c)
def align(unit_text, S):
    ndw = set(content(unit_text))
    return [score(x['s'], ndw) for x in S]
def bigrams(c): return set(zip(c, c[1:]))
def score2(sent, ndbi, ndset):
    c = content(sent)
    if len(c) < 3: return 0
    b = list(zip(c, c[1:]))
    return 0.5 * sum(x in ndbi for x in b) / len(b) + 0.5 * sum(w in ndset for w in c) / len(c)
DOCS = {}
def doc(k):
    if k not in DOCS:
        import os
        p = f'../vat/docs2/{k}.html' if os.path.exists(f'../vat/docs2/{k}.html') else f'../vat/docs/{k}.html'
        DOCS[k] = sentences(paras(p))
    return DOCS[k]
def match(text, k, th=0.5):
    c = content(text); bi, st = bigrams(c), set(c)
    S = doc(k)
    return [(i, round(score2(x['s'], bi, st), 2)) for i, x in enumerate(S)]
