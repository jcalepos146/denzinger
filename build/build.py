#!/usr/bin/env python3
"""Build the Sources of Catholic Dogma site from the files in src/.

    python3 build/build.py                      # GitHub Pages site, written to dist/
    python3 build/build.py --claude page.html   # the single-page version for Claude

Options for the Pages build (the GitHub Action passes both):
    --repo owner/name                 used for "Suggest a correction" links
    --url  https://owner.github.io/name/   the site's public address

Only the Python standard library is used. The build checks every data file
first and stops with a list of problems if anything does not line up.
"""
import argparse, csv, datetime, html, io, json, os, re, shutil, struct, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
DATA = os.path.join(SRC, 'data')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,500;0,700;1,400'
         '&family=Alegreya+SC:wght@500;700&family=Alegreya+Sans:wght@400;500;700&display=swap">\n')
TITLE = 'Sources of Catholic Dogma'
DESC = ("Denzinger's Enchiridion in English (older numbering), searchable, with DS numbers, the Latin text, "
        "hand-checked weights, the Roman Catechism, doctrinal threads and guides to disputed questions.")
WEIGHT_KEYS = {'papal-def', 'conc-def', 'conc-canon', 'conc-decree', 'papal', 'papal-teaching', 'particular',
               'curia', 'pbc', 'condemned', 'creed', 'note', 'supplement'}
GRADE_KEYS = {'dogma', 'definitive', 'authentic', 'discipline', 'condemned', 'condemned-heresy', 'profession',
              'disputed', 'act', 'void', 'prudential', 'witness', 'editorial'}
# label and colour level of each rule-based weight and each hand-checked grade (mirrors app.js)
WEIGHT_LABEL = {
    'papal-def': ('Papal definition', 'dogma'), 'conc-def': ('Conciliar definition', 'dogma'),
    'conc-canon': ('Conciliar canon', 'definitive'), 'conc-decree': ('Conciliar decree', 'authentic'),
    'papal-teaching': ('Papal teaching', 'authentic'), 'particular': ('Particular council', 'study'),
    'curia': ('Curial response', 'prudential'), 'pbc': ('Biblical Commission', 'prudential'),
    'condemned': ('Condemned proposition', 'definitive'), 'creed': ('Creed', 'dogma'),
    'note': ('Editorial note', 'study'), 'supplement': ('Not in Denzinger', 'study'),
}
GRADE_LABEL = {
    'dogma': ('Defined dogma', 'dogma'), 'definitive': ('Definitive', 'definitive'),
    'authentic': ('Authoritative teaching', 'authentic'), 'discipline': ('Discipline', 'discipline'),
    'condemned': ('Condemned, graded censures', 'definitive'), 'condemned-heresy': ('Condemned as heresy', 'definitive'),
    'profession': ('Profession of faith', 'dogma'), 'disputed': ('Weight disputed', 'prudential'),
    'act': ('Juridical act', 'discipline'), 'void': ('Without authority', 'study'),
    'prudential': ('Prudential decision', 'prudential'), 'witness': ('Historical witness', 'study'),
    'editorial': ('Editorial note', 'study'),
}


def load(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


def esc(s):
    return html.escape(str(s), quote=True)


def enc_id(i):
    """Entry id as used in a page address: 88* -> 88_s."""
    return i.replace('*', '_s')


def disp_id(i):
    return re.sub(r'-\d+$', '', i)


# --------------------------------------------------------------------------- load and check
class Problems(list):
    def add(self, where, msg):
        self.append(f'{where}: {msg}')


def load_all():
    d = {
        'eras': load('eras.json'), 'entries': load('entries.json'), 'weights': load('weights.json'),
        'censures': load('censures.json'), 'books': load('books.json'), 'quality': load('quality.json'),
        'since': load('since1950.json'), 'disputed': load('disputed.json'), 'threads': load('threads.json'),
        'latin': load('latin.json'), 'catechism': load('catechism.json'),
    }
    return d


def expand_refs(refs, order, where, P):
    """Turn ["857", "860–870"] into ids; a range runs in the order of the collection."""
    out = []
    for r in refs:
        m = re.fullmatch(r'(.+?)\s*[–-]{1,2}\s*(.+)', r) if r not in order else None
        if m and m.group(1) in order and m.group(2) in order:
            a, b = order[m.group(1)], order[m.group(2)]
            if a > b:
                P.add(where, f'range {r} runs backwards')
                continue
            out.extend(ID_AT[a:b + 1])
        elif r in order:
            out.append(r)
        else:
            P.add(where, f'no entry {r}')
    return out


ID_AT = []


def check(d):
    P = Problems()
    E, eras = d['entries'], d['eras']
    order = {}
    for k, e in enumerate(E):
        where = f"entries.json, entry {e.get('id', '?')} (line {k + 2})"
        for key in ('id', 'era', 'text', 'weight'):
            if key not in e:
                P.add(where, f'missing "{key}"')
        if 'id' not in e:
            continue
        if e['id'] in order:
            P.add(where, 'the same id is used twice')
        order[e['id']] = k
        if not isinstance(e.get('era'), int) or not 0 <= e['era'] < len(eras):
            P.add(where, f'era {e.get("era")} is not a line of eras.json')
        if e.get('weight') not in WEIGHT_KEYS:
            P.add(where, f'unknown weight "{e.get("weight")}"')
        if not isinstance(e.get('text'), list) or not all(isinstance(p, str) for p in e.get('text', [])):
            P.add(where, '"text" must be a list of paragraphs')
        if 'censure' in e and not 0 <= e['censure'] < len(d['censures']):
            P.add(where, f'censure {e["censure"]} is not a line of censures.json')
        for n in e.get('ds', []):
            if not str(n).isdigit():
                P.add(where, f'DS number "{n}" is not a number')
            elif str(n) not in d['latin']:
                pass  # some DS numbers have no Latin text on the source page; the page says so
        if e.get('dsHow') not in (None, 'series', 'checked'):
            P.add(where, f'unknown dsHow "{e.get("dsHow")}"')
    ID_AT[:] = [e['id'] for e in E]
    for i, w in enumerate(d['weights']):
        where = f'weights.json, line {i + 2}'
        for key in ('from', 'to'):
            if w.get(key) not in order:
                P.add(where, f'"{key}" is {w.get(key)}, which is not an entry')
        if w.get('g') not in GRADE_KEYS:
            P.add(where, f'unknown grade "{w.get("g")}"')
        if w.get('from') in order and w.get('to') in order and order[w['from']] > order[w['to']]:
            P.add(where, 'the range runs backwards')
    for s in d['since']:
        for r in s.get('refs', []):
            if r not in order:
                P.add(f'since1950.json, {s["id"]}', f'no entry {r}')
    for q in d['disputed']:
        for r in q.get('refs', []):
            if r not in order:
                P.add(f'disputed.json, {q["id"]}', f'no entry {r}')
    for t in d['threads']:
        for st in t['steps']:
            if st.get('ref') and st['ref'] not in order:
                P.add(f'threads.json, {t["id"]}', f'no entry {st["ref"]}')
    ids = set()
    for p in d['catechism']['parts']:
        for ch in p['chapters']:
            if ch['id'] in ids:
                P.add('catechism.json', f'chapter id {ch["id"]} is used twice')
            ids.add(ch['id'])
            ch['refs'] = expand_refs(ch.get('refs', []), order, f'catechism.json, {ch["id"]}', P)
    return order, P


# --------------------------------------------------------------------------- derived data
def curated_index(E, weights, order):
    """Each entry takes the first hand-checked range that contains it."""
    h = [None] * len(E)
    for ci, w in enumerate(weights):
        a, b = order[w['from']], order[w['to']]
        for k in range(a, b + 1):
            if h[k] is None:
                h[k] = ci
    return h


REF_RE = re.compile(r'(^|[^A-Za-z])((?:Kch|Kirch|R|H|L|M|EP|RS)\.?\s)?(nn?\.\s?)'
                    r'(\d{1,4}[a-z]?(?:\s?(?:,|and|-|–|f\.|ff\.)\s?\d{1,4}[a-z]?)*)')
NUM_RE = re.compile(r'\d{1,4}[a-z]?\*?')


def resolve(num, by_id, by_base):
    if num in by_id:
        return num
    try:
        return by_base.get(int(re.match(r'\d+', num).group()))
    except (AttributeError, ValueError):
        return None


def cross_refs(E):
    """Numbers an entry's text points to ("see n. 1824"), and the reverse."""
    by_id = {e['id']: e for e in E}
    by_base = {}
    for e in E:
        m = re.match(r'\d+', e['id'])
        if m and int(m.group()) not in by_base:
            by_base[int(m.group())] = e['id']
    cites, cited = {}, {}
    for e in E:
        if e.get('supplement'):
            continue
        found = []
        for m in REF_RE.finditer(' '.join(e['text'])):
            if m.group(2):
                continue  # Kirch, Rouet de Journel etc. use their own numbers
            for n in NUM_RE.findall(m.group(4)):
                t = resolve(n, by_id, by_base)
                if t and t != e['id'] and t not in found:
                    found.append(t)
        if found:
            cites[e['id']] = found
            for t in found:
                cited.setdefault(t, []).append(e['id'])
    return cites, cited, by_base


def era_span(er):
    nums = [int(x) for x in re.findall(r'\d{2,4}', er['dates'] or '')]
    if not nums:
        return er['year'], er['year']
    return min(nums + [er['year']]), max(nums)


def entry_year(e, er):
    """A date for the entry: a year printed in its heading inside the era's span, else the era's first year."""
    lo, hi = era_span(er)
    for text in (e.get('source') or '', e.get('session') or ''):
        for y in re.findall(r'(?<![\d.:])(\d{3,4})(?![\d:])', text):
            y = int(y)
            if lo - 1 <= y <= hi + 1 and y > 90:
                return y, True
    return er['year'], False


# --------------------------------------------------------------------------- compact data for the page
def compact(d, order):
    E, eras = d['entries'], d['eras']
    h = curated_index(E, d['weights'], order)
    cites, cited, _ = cross_refs(E)
    rc = {}
    for p in d['catechism']['parts']:
        for ch in p['chapters']:
            for r in ch['refs']:
                rc.setdefault(r, [])
                if ch['id'] not in rc[r]:
                    rc[r].append(ch['id'])
    rows = []
    for k, e in enumerate(E):
        y, exact = entry_year(e, eras[e['era']])
        f = {'w': e['weight']}
        if e.get('note'): f['n'] = 1
        if e.get('kinds'): f['k'] = e['kinds']
        if e.get('scripture'): f['s'] = e['scripture']
        if 'censure' in e: f['c'] = e['censure']
        if h[k] is not None: f['h'] = h[k]
        if e.get('supplement'): f['sup'] = 1
        if e.get('links'): f['L'] = e['links']
        if e.get('ds'): f['x'] = e['ds']
        if e.get('dsHow'): f['xh'] = e['dsHow']
        f['y'] = y if exact else -y
        if e['id'] in cited: f['cb'] = cited[e['id']]
        if e['id'] in rc: f['rc'] = rc[e['id']]
        rows.append([e['id'], e['era'], e.get('session'), e.get('topic'), e.get('source'), e['text'], f])
    era_rows = []
    for er in eras:
        o = {'n': er['name'], 'd': er['dates'], 's': er['note'], 'y': er['year'], 'a': 1 if er.get('appendix') else 0}
        if er.get('supplement'): o['sup'] = 1
        era_rows.append(o)
    cat = {k: v for k, v in d['catechism'].items()}
    raw = {'eras': era_rows, 'entries': rows, 'books': d['books'], 'censures': d['censures'],
           'curated': d['weights'], 'quality': d['quality'], 'rc': cat}
    return raw, {'h': h, 'cites': cites, 'cited': cited, 'rc': rc}


def dump(o):
    s = json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    return s.replace('</', '<\\/')


# --------------------------------------------------------------------------- the reader page
def read_src(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return f.read()


def reader_body(raw, d, site):
    css = read_src('styles.css')
    shell = read_src('shell.html')
    app = read_src('app.js')
    return ('<style>\n' + css + '</style>\n\n' + shell + '\n'
            f'<script type="application/json" id="site-data">{dump(site)}</script>\n'
            f'<script type="application/json" id="data">{dump(raw)}</script>\n'
            f'<script type="application/json" id="since-data">{dump(d["since"])}</script>\n'
            f'<script type="application/json" id="disputed-data">{dump(d["disputed"])}</script>\n'
            f'<script type="application/json" id="threads-data">{dump(d["threads"])}</script>\n'
            f'<script type="application/json" id="latin-data">{dump(d["latin"])}</script>\n'
            '<script>\n' + app + '</script>\n')


ICON_SVG = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23a11f1d'/%3E"
            "%3Ctext x='32' y='45' font-family='Georgia,serif' font-size='38' font-weight='700' text-anchor='middle' fill='%23fff'%3ED%3C/text%3E%3C/svg%3E")


def head(title, desc, url, prefix, extra=''):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{esc(title)}</title>\n'
            f'<meta name="description" content="{esc(desc)}">\n'
            + (f'<link rel="canonical" href="{esc(url)}">\n<meta property="og:url" content="{esc(url)}">\n' if url else '')
            + f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="{TITLE}">\n'
            f'<meta property="og:title" content="{esc(title)}">\n<meta property="og:description" content="{esc(desc)}">\n'
            '<meta name="twitter:card" content="summary">\n'
            '<meta name="theme-color" content="#a11f1d">\n'
            f'<link rel="icon" href="{ICON_SVG}">\n'
            f'<link rel="apple-touch-icon" href="{prefix}icons/icon-180.png">\n'
            f'<link rel="manifest" href="{prefix}manifest.webmanifest">\n'
            + FONTS + extra + '</head>\n<body>\n')


# --------------------------------------------------------------------------- static entry pages
CITE_RE = re.compile(r'\[([^\[\]]{2,80}?\d+\s?:\s?\d+[^\[\]]{0,40}?)\]')
SUP_RE = re.compile(r'\(((?:[CB]\d{1,2}(?:–[CB]\d{1,2})?)(?:,\s*[CB]\d{1,2}(?:–[CB]\d{1,2})?)*)\)')
MIGNE_RE = re.compile(r'\b(MG|ML)(\s+)(\d{1,3})(\s*,\s*\d{1,4}(?:\s?[A-D]\b)?)')


def static_text(text, by_id, by_base):
    h = esc(text).replace('&#x27;', "'")
    h = CITE_RE.sub(r'<span class="cite">[\1]</span>', h)

    def nums(m):
        if m.group(2):
            return m.group(0)
        def one(n):
            t = resolve(n.group(0), by_id, by_base)
            return f'<a class="xref" href="../{esc(enc_id(t))}/">{n.group(0)}</a>' if t else n.group(0)
        return m.group(1) + m.group(3) + NUM_RE.sub(one, m.group(4))
    h = REF_RE.sub(nums, h)
    h = SUP_RE.sub(lambda m: '(' + re.sub(r'[CB]\d{1,2}', lambda x: f'<a class="xref" href="../{x.group(0)}/">{x.group(0)}</a>'
                                         if x.group(0) in by_id else x.group(0), m.group(1)) + ')', h)
    h = MIGNE_RE.sub(lambda m: f'<a class="xref" href="http://{"graeca" if m.group(1) == "MG" else "latina"}.patristica.net/#t{int(m.group(3)):03d}" '
                               f'rel="noopener">{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}</a>', h)
    return h


def ds_range(lst):
    out, i = [], 0
    while i < len(lst):
        j = i
        while j + 1 < len(lst) and int(lst[j + 1]) == int(lst[j]) + 1:
            j += 1
        out.append(f'{lst[i]}–{lst[j]}' if j > i else str(lst[i]))
        i = j + 1
    return ', '.join(out)


def entry_pages(d, raw, derived, out, url):
    E, eras = d['entries'], d['eras']
    by_id = {e['id']: e for e in E}
    _, _, by_base = cross_refs(E)
    weights = d['weights']
    ch_by = {}
    for p in d['catechism']['parts']:
        for ch in p['chapters']:
            ch_by[ch['id']] = (p, ch)
    disc = {}
    for q in d['disputed']:
        for r in q['refs']:
            disc.setdefault(r, []).append((f'#q-{q["id"]}', q['title']))
    for s in d['since']:
        for r in s['refs']:
            disc.setdefault(r, []).append((f'#since-{s["id"]}', s['title']))
    for t in d['threads']:
        for st in t['steps']:
            if st.get('ref'):
                disc.setdefault(st['ref'], []).append((f'#thread-{t["id"]}', t['title'] + ' (thread)'))
    urls = []
    for k, e in enumerate(E):
        er = eras[e['era']]
        eid = e['id']
        label = f'Supplement {eid}' if e.get('supplement') else f'Denzinger n. {disp_id(eid)}'
        ds = e.get('ds') or []
        ds_txt = (' (cf. DS ' if e.get('dsHow') == 'series' else ' (DS ') + ds_range(ds) + ')' if ds else ''
        topic = e.get('topic') or ''
        title = f'{label}{ds_txt}{": " + topic if topic else ""} · {TITLE}'
        body_text = ' '.join(e['text'])
        desc = re.sub(r'\s+', ' ', body_text).strip()
        desc = (desc[:157].rsplit(' ', 1)[0] + '…') if len(desc) > 160 else desc
        page_url = f'{url}n/{enc_id(eid)}/' if url else ''
        hk = derived['h'][k]
        if hk is not None:
            g = GRADE_LABEL[weights[hk]['g']]
            pill = f'<span class="pill lv-{g[1]}">Checked · {esc(g[0])}</span>'
        else:
            g = WEIGHT_LABEL.get('papal-teaching' if e['weight'] == 'papal' else e['weight'])
            pill = f'<span class="pill lv-{g[1]}">{esc(g[0])}</span>'
        meta_bits = [esc(er['name'])] + ([esc(er['dates'])] if er['dates'] else []) + ([esc(e['session'])] if e.get('session') else [])
        parts = [head(title, desc, page_url, '../../', '<link rel="stylesheet" href="../../assets/entry.css">\n')]
        parts.append(f'''<header class="top"><a class="brand" href="../../"><b>Denzinger</b><span>{TITLE}</span></a>
<form class="search" action="../../" method="get" role="search"><input name="q" type="search" placeholder="Search the collection" aria-label="Search the collection"></form>
<a class="btn" href="../../#n{esc(eid)}">Read in context</a></header>
<main class="col">
<p class="crumbs"><a href="../../#e{e['era']}">{meta_bits[0]}</a>{''.join(' · ' + b for b in meta_bits[1:])}</p>
<h1><span class="num">{esc(label.replace('Denzinger ', ''))}</span>{(' ' + static_text(topic, by_id, by_base)) if topic else ''}</h1>
''')
        if e.get('source'):
            parts.append(f'<p class="src">{static_text(e["source"], by_id, by_base)}</p>\n')
        tags = [pill]
        if ds:
            tags.insert(0, f'<span class="dsno">{"cf. " if e.get("dsHow") == "series" else ""}DS {esc(ds_range(ds))}</span>')
        if 'censure' in e:
            c = d['censures'][e['censure']]
            tags.append(f'<span class="cens">Censured as {esc(", ".join(c["w"]))}{", respectively" if c.get("r") else ""}</span>')
        parts.append(f'<div class="wline">{"".join(tags)}</div>\n<div class="body">')
        parts.extend(f'<p>{static_text(p, by_id, by_base)}</p>' for p in e['text'])
        parts.append('</div>\n')
        if ds:
            lat = ''.join(f'<p><span class="dsn">{esc(n)}</span>{esc(d["latin"][str(n)]) if str(n) in d["latin"] else "<i>The Latin page gives no text under this number.</i>"}</p>' for n in ds)
            parts.append(f'<details class="latin" lang="la"><summary>Latin text · DS {esc(ds_range(ds))}</summary>{lat}</details>\n')
        if hk is not None:
            w = weights[hk]
            rng = f' (n. {esc(w["from"])}–{esc(disp_id(w["to"]))})' if w['to'] != w['from'] else ''
            parts.append(f'<p class="curnote"><b>Checked by hand · {esc(GRADE_LABEL[w["g"]][0])}{rng}.</b> {static_text(w["n"], by_id, by_base)}</p>\n')
        if e.get('links'):
            parts.append('<p class="rel">Full text: ' + ' · '.join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])} ↗</a>' for l in e['links']) + '</p>\n')
        rel = []
        if derived['cites'].get(eid):
            rel.append('<div><b>Refers to</b> ' + ', '.join(f'<a href="../{esc(enc_id(t))}/">n. {esc(disp_id(t))}</a>' for t in derived['cites'][eid]) + '</div>')
        if derived['cited'].get(eid):
            rel.append('<div><b>Cited by</b> ' + ', '.join(f'<a href="../{esc(enc_id(t))}/">n. {esc(disp_id(t))}</a>' for t in derived['cited'][eid]) + '</div>')
        if derived['rc'].get(eid):
            rel.append('<div><b>Roman Catechism</b> ' + ', '.join(f'<a href="../../#rc-{c}">{esc(ch_by[c][0]["title"].split(".")[0])}, {esc(ch_by[c][1]["title"])}</a>' for c in derived['rc'][eid]) + '</div>')
        if disc.get(eid):
            rel.append('<div><b>Discussed in</b> ' + ', '.join(f'<a href="../../{h}">{esc(t)}</a>' for h, t in disc[eid]) + '</div>')
        if rel:
            parts.append('<div class="rel">' + ''.join(rel) + '</div>\n')
        prev_e, next_e = (E[k - 1] if k else None), (E[k + 1] if k + 1 < len(E) else None)
        nav = []
        nav.append(f'<a href="../{esc(enc_id(prev_e["id"]))}/" rel="prev"><small>Previous</small>n. {esc(disp_id(prev_e["id"]))}</a>' if prev_e else '<span></span>')
        nav.append(f'<a class="next" href="../{esc(enc_id(next_e["id"]))}/" rel="next"><small>Next</small>n. {esc(disp_id(next_e["id"]))}</a>' if next_e else '<span></span>')
        parts.append(f'<nav class="pager">{"".join(nav)}</nav>\n')
        parts.append('<p class="colophon">Text: Denzinger, <i>Enchiridion Symbolorum</i>, in the English translation with the older numbering, '
                     'as published on patristica.net. Weights and cross-references are a reading aid made for this site, not an official classification. '
                     '<a href="../../#edition">About this edition</a></p>\n</main>\n'
                     '<script>if("serviceWorker" in navigator)navigator.serviceWorker.register("../../sw.js").catch(function(){});</script>\n'
                     '</body>\n</html>\n')
        dest = os.path.join(out, 'n', enc_id(eid))
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(''.join(parts))
        urls.append(page_url)
    return urls


# --------------------------------------------------------------------------- icons (PNG without any library)
def png(size, path):
    """A red rounded square with a white 'D', drawn pixel by pixel."""
    red, white = (161, 31, 29), (255, 255, 255)
    rows = []
    r = size * 0.19
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            # rounded corners (transparent outside)
            cx = min(max(x + .5, r), size - r)
            cy = min(max(y + .5, r), size - r)
            inside = (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r
            if not inside:
                row += bytes((0, 0, 0, 0))
                continue
            u, v = (x + .5) / size, (y + .5) / size
            # the letter D: a stem and a half-ring
            stem = .30 <= u <= .41 and .22 <= v <= .78
            dx, dy = (u - .43) / .30, (v - .5) / .28
            ring = u >= .41 and dx * dx + dy * dy <= 1 and ((u - .43) / .19) ** 2 + ((v - .5) / .17) ** 2 >= 1
            bar = .41 <= u <= .46 and (.22 <= v <= .33 or .67 <= v <= .78)
            c = white if (stem or ring or bar) else red
            row += bytes(c) + b'\xff'
        rows.append(bytes(row))
    raw = zlib.compress(b''.join(rows), 9)

    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', raw) + chunk(b'IEND', b''))


# --------------------------------------------------------------------------- open data
def open_data(d, raw, derived, out, url, built):
    dd = os.path.join(out, 'data')
    os.makedirs(dd, exist_ok=True)
    E, eras = d['entries'], d['eras']
    rows = []
    for k, e in enumerate(E):
        y = raw['entries'][k][6]['y']
        hk = derived['h'][k]
        o = {'id': e['id'], 'ds': e.get('ds', []), 'dsMatch': e.get('dsHow', 'printed' if e.get('ds') else None),
             'era': eras[e['era']]['name'], 'eraDates': eras[e['era']]['dates'], 'year': abs(y), 'yearExact': y > 0,
             'session': e.get('session'), 'topic': e.get('topic'), 'source': e.get('source'), 'text': e['text'],
             'weight': 'papal-teaching' if e['weight'] == 'papal' else e['weight'],
             'grade': d['weights'][hk]['g'] if hk is not None else None,
             'kinds': e.get('kinds', []), 'supplement': bool(e.get('supplement')),
             'refersTo': derived['cites'].get(e['id'], []), 'citedBy': derived['cited'].get(e['id'], []),
             'romanCatechism': derived['rc'].get(e['id'], []),
             'url': f'{url}n/{enc_id(e["id"])}/' if url else None}
        if 'censure' in e:
            o['censure'] = d['censures'][e['censure']]['w']
        rows.append(o)
    with open(os.path.join(dd, 'entries.json'), 'w', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(o, ensure_ascii=False) for o in rows) + '\n]\n')
    with open(os.path.join(dd, 'crosswalk.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['old_number', 'ds_number', 'match'])
        for e in E:
            if e.get('supplement'):
                continue
            for n in e.get('ds', []) or ['']:
                w.writerow([e['id'], n, e.get('dsHow', 'printed') if n else 'none'])
    with open(os.path.join(dd, 'weights.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['from', 'to', 'grade', 'note'])
        for x in d['weights']:
            w.writerow([x['from'], x['to'], x['g'], x['n']])
    shutil.copy(os.path.join(DATA, 'latin.json'), os.path.join(dd, 'latin.json'))
    cat = json.loads(json.dumps(d['catechism']))
    with open(os.path.join(dd, 'roman-catechism.json'), 'w', encoding='utf-8') as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
    guides = {'since1950': d['since'], 'disputed': d['disputed'], 'threads': d['threads']}
    with open(os.path.join(dd, 'guides.json'), 'w', encoding='utf-8') as f:
        json.dump(guides, f, ensure_ascii=False, indent=1)
    files = [
        ('entries.json', 'Every entry with its text, DS numbers, era, year, weight, hand-checked grade, censure, cross-references and Roman Catechism chapters.'),
        ('crosswalk.csv', 'Old number, DS number and how the pair was matched (printed, series = inferred, checked = by hand, none).'),
        ('weights.csv', 'The hand-checked weight ranges with the note on each.'),
        ('latin.json', 'The Latin text by DS number, as the source page gives it (not proofread).'),
        ('roman-catechism.json', 'The chapters of the Roman Catechism with the entries matched to each.'),
        ('guides.json', 'Since 1950, the disputed questions and the doctrinal threads.'),
    ]
    with open(os.path.join(dd, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'built': built, 'files': [{'file': a, 'url': f'{url}data/{a}' if url else f'data/{a}', 'about': b} for a, b in files]},
                  f, ensure_ascii=False, indent=1)
    return files


# --------------------------------------------------------------------------- service worker, manifest, misc
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def pages_build(args):
    d = load_all()
    order, P = check(d)
    if P:
        print('The data has problems; nothing was built:\n  ' + '\n  '.join(P), file=sys.stderr)
        sys.exit(1)
    built = datetime.date.today().isoformat()
    url = (args.url or '').strip()
    if url in ('/', '//'):
        url = ''
    if url and not url.endswith('/'):
        url += '/'
    raw, derived = compact(d, order)
    site = {'mode': 'pages', 'repo': args.repo or '', 'url': url, 'built': built}
    if args.claude:
        site = {'mode': 'claude', 'repo': args.repo or '', 'url': url, 'built': built}
        page = f'<title>{TITLE}</title>\n' + FONTS + '\n' + reader_body(raw, d, site)
        write(args.claude, page)
        print('Claude page:', args.claude, f'{len(page.encode()) // 1024} KB')
        return
    out = os.path.abspath(args.out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    index = head(TITLE, DESC, url, '') + reader_body(raw, d, site) + '</body>\n</html>\n'
    write(os.path.join(out, 'index.html'), index)
    write(os.path.join(out, 'assets', 'entry.css'), read_src('entry.css'))
    urls = entry_pages(d, raw, derived, out, url)
    files = open_data(d, raw, derived, out, url, built)
    os.makedirs(os.path.join(out, 'icons'), exist_ok=True)
    for s in (180, 192, 512):
        png(s, os.path.join(out, 'icons', f'icon-{s}.png'))
    write(os.path.join(out, 'manifest.webmanifest'), json.dumps({
        'name': TITLE, 'short_name': 'Denzinger', 'description': DESC, 'start_url': './', 'scope': './',
        'display': 'standalone', 'background_color': '#f4f5f6', 'theme_color': '#a11f1d',
        'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                  {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}, indent=1))
    version = f'{built}-{zlib.crc32(index.encode()) & 0xffffffff:08x}'
    write(os.path.join(out, 'sw.js'), read_src('sw.js').replace('__VERSION__', version))
    write(os.path.join(out, '.nojekyll'), '')
    write(os.path.join(out, 'robots.txt'), 'User-agent: *\nAllow: /\n' + (f'Sitemap: {url}sitemap.xml\n' if url else ''))
    if url:
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
              f'<url><loc>{esc(url)}</loc><lastmod>{built}</lastmod></url>']
        sm += [f'<url><loc>{esc(u)}</loc></url>' for u in urls]
        write(os.path.join(out, 'sitemap.xml'), '\n'.join(sm + ['</urlset>', '']))
    write(os.path.join(out, '404.html'), head('Page not found · ' + TITLE, DESC, '', './') +
          '<script>(function(){var m=location.pathname.match(/\\/n\\/([^/]+)\\/?$/);'
          'var base=location.pathname.replace(/\\/n\\/[^/]*\\/?$/,"/").replace(/[^/]*$/,"");'
          'location.replace(base+(m?"#n"+decodeURIComponent(m[1]).replace(/_s/g,"*"):""));})();</script>'
          '<p style="font-family:sans-serif;padding:2rem">Page not found. <a href="./">Open the reader</a>.</p></body></html>\n')
    size = sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(out) for f in fs)
    print(f'Built {len(urls)} entry pages, {len(files)} data files; {size / 1e6:.1f} MB in {out}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=None)
    ap.add_argument('--url', default=None)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    ap.add_argument('--claude', default=None, metavar='FILE', help='write the single-page version for Claude instead')
    a = ap.parse_args()
    cfg_path = os.path.join(ROOT, 'site.json')
    if os.path.exists(cfg_path):
        cfg = json.load(open(cfg_path))
        a.repo = a.repo or cfg.get('repo') or None
        a.url = a.url or cfg.get('url') or None
    pages_build(a)
