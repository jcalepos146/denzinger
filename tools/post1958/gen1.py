# Batch 1 (John XXIII, Vatican II): entries in the format of src/data/entries.json.
import re, json
from align import doc
from artalign import articles
DOCS = {  # key: (abbrev, era name, kind, title, date, order)
 'pp': ('PP', 'John XXIII', 'Encyclical Letter', 'Princeps Pastorum', 'Nov. 28, 1959'),
 'mm': ('MM', 'John XXIII', 'Encyclical Letter', 'Mater et Magistra', 'May 15, 1961'),
 'pt': ('PT', 'John XXIII', 'Encyclical Letter', 'Pacem in Terris', 'April 11, 1963'),
 'sc': ('SC', 'Vatican II', 'Constitution on the Sacred Liturgy', 'Sacrosanctum Concilium', 'Dec. 4, 1963'),
 'lg': ('LG', 'Vatican II', 'Dogmatic Constitution on the Church', 'Lumen Gentium', 'Nov. 21, 1964'),
 'oe': ('OE', 'Vatican II', 'Decree on the Catholic Eastern Churches', 'Orientalium Ecclesiarum', 'Nov. 21, 1964'),
 'ur': ('UR', 'Vatican II', 'Decree on Ecumenism', 'Unitatis Redintegratio', 'Nov. 21, 1964'),
 'na': ('NA', 'Vatican II', 'Declaration on the Relation of the Church to Non-Christian Religions', 'Nostra Aetate', 'Oct. 28, 1965'),
 'dv': ('DV', 'Vatican II', 'Dogmatic Constitution on Divine Revelation', 'Dei Verbum', 'Nov. 18, 1965'),
 'aa': ('AA', 'Vatican II', 'Decree on the Apostolate of the Laity', 'Apostolicam Actuositatem', 'Nov. 18, 1965'),
 'dh': ('DH', 'Vatican II', 'Declaration on Religious Freedom', 'Dignitatis Humanae', 'Dec. 7, 1965'),
 'ag': ('AG', 'Vatican II', 'Decree on the Mission Activity of the Church', 'Ad Gentes', 'Dec. 7, 1965'),
 'po': ('PO', 'Vatican II', 'Decree on the Ministry and Life of Priests', 'Presbyterorum Ordinis', 'Dec. 7, 1965'),
 'gs': ('GS', 'Vatican II', 'Pastoral Constitution on the Church in the Modern World', 'Gaudium et Spes', 'Dec. 7, 1965'),
}
J23 = {  # ND unit -> official paragraphs, checked by reading both texts
 '1132': [18], '1133': [28, 29, 34], '1134': [44], '1135': [49],
 '2113': [51, 52, 53, 55], '2114': [59, 61, 62, 64], '2115': [71], '2116': [73], '2117/1': [82], '2117/2': [91],
 '2117/3': [97, 99], '2118': [105, 106, 108], '2119': [109], '2120': [113], '2121': [116, 117], '2122': [157, 163],
 '2123': [171, 173, 201, 203, 204, 207],
 '2026': [5], '2027': [9, 10], '2028': [11], '2029': [12], '2030': [13], '2031': [14], '2032': [15, 16, 17],
 '2033': [19], '2034': [20], '2035': [21, 22], '2036': [23, 24], '2037': [25], '2038': [26], '2039': [27],
 '2040': [28, 29, 30], '2041': [31, 33], '2042': [34], '2124': [37, 38], '2125': [46], '2126': [47, 49],
 '2127': [51], '2128': [52], '2129': [54, 56, 57], '2130': [60, 61], '2131': [73], '2132': [80],
 '2133': [86, 91, 98], '2134': [112, 113, 126], '2135': [130, 132, 134, 136], '2136': [137], '2137': [139],
 '2138': [140], '2139': [146, 157], '2140/1': [158], '2140/2': [159],
}
ERA = {'John XXIII': 119, 'Vatican II': 120}
def clean(t):
    t = re.sub(r'\s*\(\d{1,3}\*?\)', '', t)                 # footnote markers
    t = re.sub(r'\s*\[\s*\]', '', t)
    t = re.sub(r'\s+([,;:?!]|\.(?!\.\.))', r'\1', t)            # not before an ellipsis
    return re.sub(r'\s+', ' ', t).strip()
def head(h):
    if not h or len(h) < 4 or re.match(r'^[A-Z]{1,2}$|^(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\b', h) or h.endswith(')') or h.endswith('."'):
        return None
    h = re.sub(r'^(CHAPTER|PART)\s+[IVXL]+\.?\s*', '', h)
    h = re.sub(r'^[IVXL]+\.\s+', '', h)
    if h.isupper():
        small = {'of', 'the', 'and', 'in', 'on', 'to', 'a', 'an', 'for', 'with', 'its', 'as', 'by'}
        w = h.lower().split()
        h = ' '.join(x if i and x in small else x.capitalize() for i, x in enumerate(w))
        h = re.sub(r"'S\b", "'s", h)
    return h
def art_text(d, arts):
    S = doc(d); out, prev, heads = [], None, []
    for a in arts:
        xs = [x for x in S if x['art'] == a]
        if prev is not None and a != prev + 1 and out: out[-1] += ' ...'
        ps = {}
        for x in xs: ps.setdefault(x['p'], []).append(x['s'])
        out += [' '.join(v) for v in ps.values()]
        heads += [x['head'] for x in xs]; prev = a
    return out, heads
units = {u['id']: u for u in json.load(open('units.json'))}
B = json.load(open('batch1.json'))
sel, refs = {}, {}           # (doc, art) -> sentence indices; -> ND numbers
for x in B:
    nd = x['nd']
    if nd in J23:
        d = x['doc'] if isinstance(x['doc'], str) else x['doc'][0]
        idx = [j for j, s in enumerate(doc(d)) if s['art'] in J23[nd]]
    elif x.get('fail'):
        print('skipped', nd); continue
    else:
        d, idx = x['doc'], x['idx']
    for j in idx:
        a = doc(d)[j]['art']
        if a is None: continue
        sel.setdefault((d, a), set()).add(j)
        refs.setdefault((d, a), []).append(nd) if nd not in refs.get((d, a), []) else None
entries = []
for (d, a), js in sorted(sel.items(), key=lambda t: (list(DOCS).index(t[0][0]), t[0][1])):
    S = doc(d); ab, era, kind, title, date = DOCS[d]
    allj = [j for j, s in enumerate(S) if s['art'] == a]
    paras, cur, curp, gap = [], [], None, False
    for j in allj:
        if j not in js:
            gap = bool(cur) or bool(paras); continue
        if gap and cur: cur[-1] += ' ...'
        elif gap and paras: paras[-1] += ' ...'
        gap = False
        if curp is not None and S[j]['p'] != curp and cur: paras.append(' '.join(cur)); cur = []
        cur.append(S[j]['s']); curp = S[j]['p']
    if cur: paras.append(' '.join(cur))
    if allj[0] not in js: paras[0] = '... ' + paras[0]
    if allj[-1] not in js: paras[-1] += ' ...'
    text = [clean(p) for p in paras]
    ds = sorted({int(m) for nd in refs[(d, a)] for l in units[nd]['lines'] for m in re.findall(r'^\s*(39\d\d)\b', l)})
    h = head(S[allj[0]]['head'])
    e = {'id': f'{ab}{a}', 'era': ERA[era], 'topic': h or title,
         'source': f'[From the {kind}, "{title}," {date}]',
         'text': text, 'weight': 'papal' if era == 'John XXIII' else 'conc-decree', 'nd': refs[(d, a)]}
    if ds and d in ('mm', 'pt'): e['dsND'] = [str(n) for n in ds]
    entries.append(e)
json.dump(entries, open('entries1.json', 'w'), ensure_ascii=False, indent=1)
print(len(entries), 'entries,', sum(len(' '.join(e['text']).split()) for e in entries), 'words')
from collections import Counter
print(Counter(re.match(r'[A-Z]+', e['id']).group(0) for e in entries))
