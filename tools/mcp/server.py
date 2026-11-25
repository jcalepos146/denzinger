#!/usr/bin/env python3
"""An MCP server for the collection, so an AI assistant can look up and cite its texts.

    python3 tools/mcp/server.py                 # data from dist/data if built, else the published site
    python3 tools/mcp/server.py --data DIR      # a folder holding entries.json, latin.json, ...
    python3 tools/mcp/server.py --refresh       # download the published data again

It speaks the Model Context Protocol over standard input and output (JSON-RPC,
one message per line), needs only Python's standard library, and only reads:
it never changes the data. Tools: search, get_entry, related, cite, list_cases,
get_case, reading_rules. Resources: the reading rules and the continuity
protocol. Prompts: test two texts for continuity, check a statement.

Without --data it reads dist/data when the site has been built here, otherwise
it downloads the published open data once into a cache folder and refreshes
it after a week, so a change to the site reaches the server by itself.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://jcalepos146.github.io/denzinger1.0/'
FILES = ['entries.json', 'latin.json', 'guides.json', 'continuity.json', 'documents.json']
MAX_AGE = 7 * 24 * 3600
NAME, VERSION = 'eodem-sensu', '1.0.0'
PROTOCOLS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']

# What each kind of document is, and what each hand-checked grade means (as the reader states them).
WEIGHTS = {
    'papal-def': ('Papal definition', 'A pope defining a doctrine of faith or morals for the whole Church, in the form Vatican I describes (ex cathedra).'),
    'conc-def': ('Conciliar definition', "An ecumenical council's creed or defining formula. What is proposed as to be believed is dogma; the reasons given are not themselves defined."),
    'conc-canon': ('Conciliar canon', 'A canon of an ecumenical council, usually with an anathema. Most concern faith; some concern discipline.'),
    'conc-decree': ('Conciliar decree', 'Doctrinal chapters, reform decrees and letters of an ecumenical council. Authoritative; only what is proposed as defined is infallible.'),
    'papal-teaching': ('Papal teaching', 'Encyclicals, bulls and letters of popes. Owed religious assent; infallible only when the conditions of a definition are met or the teaching is otherwise definitive.'),
    'particular': ('Particular council', 'A regional council or synod. Its authority comes from reception and papal approval.'),
    'curia': ('Curial response', 'A reply or decree of a Roman congregation. Doctrinal judgments and changeable disciplinary decisions need different assessments.'),
    'pbc': ('Biblical Commission', 'A response of the Pontifical Biblical Commission (1902 onward); binding as a disciplinary safeguard in its time.'),
    'condemned': ('Condemned proposition', 'A proposition the Church censured, in its condemned sense; its contradictory is not thereby defined, and the weight depends on the censure.'),
    'creed': ('Creed', 'A creed, profession of faith or early formula.'),
    'note': ('Editorial note', 'A note by the editors, not a text of the Magisterium.'),
    'cdf': ('Doctrine of the Faith', 'A doctrinal document of the Congregation or Dicastery for the Doctrine of the Faith, approved by the pope. Ordinary Magisterium, owed religious assent.'),
    'liturgy': ('Liturgical norm', 'A rite or liturgical norm. Binds as law and can be changed by competent authority.'),
    'catechism': ('Catechism', 'The Catechism of the Catholic Church. Each statement keeps the weight of the teaching it presents.'),
    'papal-address': ('Address or homily', "A pope's address, homily or message. Ordinary teaching whose weight depends on the manner of speaking and repetition (Lumen Gentium 25)."),
    'interview': ('Interview', 'An interview, press conference or private book. Not an act of the Magisterium.'),
    'commission': ('Commission or council study', 'A publication of a pontifical council or commission; not magisterial merely because the Vatican publishes it.'),
    'synod': ('Synod of Bishops', 'Consultative unless the pope makes it his own.'),
    'bishops': ("Bishops' conference", 'Authentic conference teaching requires the conditions of Apostolos Suos 22.'),
    'ecumenical': ('Ecumenical agreement', 'Binds the Church only so far as it restates Catholic doctrine.'),
    'supplement': ('Not in Denzinger', 'Added to this site: decrees Denzinger leaves out, with the standing of each stated.'),
}
GRADES = {
    'dogma': 'Defined dogma', 'definitive': 'Definitive', 'authentic': 'Authoritative teaching', 'discipline': 'Discipline',
    'condemned': 'Condemned, graded censures', 'condemned-heresy': 'Condemned as heresy', 'profession': 'Profession of faith',
    'disputed': 'Weight disputed', 'act': 'Juridical act', 'void': 'Without authority', 'prudential': 'Prudential decision',
    'witness': 'Historical witness', 'editorial': 'Editorial note',
}
INSTRUCTIONS = (
    'Eodem Sensu is Denzinger\'s Enchiridion in English (older numbering, to Pius XII) continued with the documents of '
    'the Church to Leo XIV. Quote texts from get_entry rather than from memory, and cite them by number (n. 1839, '
    'DS 3074, LG 25). Say what kind of document each text is and its grade: the weight of a text travels with it. '
    'Grades are an editorial reading aid, not an official classification, and the continuity cases are research, not '
    'Church teaching. Read the reading rules (reading_rules) before weighing or comparing texts.')


# ---------------------------------------------------------------- data

def log(*a):
    print(*a, file=sys.stderr, flush=True)


def cache_dir():
    base = os.environ.get('LOCALAPPDATA') or os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache')
    return os.path.join(base, 'eodem-sensu')


def data_dir(arg, refresh):
    if arg:
        return arg
    built = os.path.join(ROOT, 'dist', 'data')
    if not refresh and all(os.path.exists(os.path.join(built, f)) for f in FILES):
        return built
    d = cache_dir()
    os.makedirs(d, exist_ok=True)
    for f in FILES:
        p = os.path.join(d, f)
        if refresh or not os.path.exists(p) or time.time() - os.path.getmtime(p) > MAX_AGE:
            try:
                req = urllib.request.Request(SITE + 'data/' + f, headers={'User-Agent': f'{NAME}/{VERSION} (MCP server)'})
                body = urllib.request.urlopen(req, timeout=120).read()
                json.loads(body)
                with open(p + '.tmp', 'wb') as out:
                    out.write(body)
                os.replace(p + '.tmp', p)
                log(f'downloaded {f} ({len(body):,} bytes)')
            except Exception as err:
                if not os.path.exists(p):
                    raise RuntimeError(f'cannot get {f}: {err}')
                log(f'kept the cached {f}: {err}')
    return d


def fold(s):
    """Lower case without accents, for matching."""
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s).lower()) if not unicodedata.combining(c))


class Data:
    def __init__(self, folder):
        self.folder = folder
        def load(f):
            with open(os.path.join(folder, f), encoding='utf-8') as fh:
                return json.load(fh)
        self.entries = load('entries.json')
        self.latin = load('latin.json')
        self.guides = load('guides.json')
        self.cont = load('continuity.json')
        docs = load('documents.json')
        self.records = {r['id']: r for r in docs['records']}
        self.relations = docs.get('relations', [])
        self.by_id = {e['id']: e for e in self.entries}
        self.by_ds = {}
        for e in self.entries:
            for d in e['ds']:
                self.by_ds.setdefault(str(d), []).append(e['id'])
        # sealed research is published only encrypted: the server never reads it, not even from private/
        self.sealed = {c['id']: c for c in self.cont['cases'] if c.get('sealed')}
        self.cases = {c['id']: c for c in self.cont['cases'] if not c.get('sealed')}
        self.index = [(e, fold(' '.join([e.get('topic') or '', ' '.join(e['text']), e.get('era') or '', e.get('session') or '',
                                         e.get('source') or '']))) for e in self.entries]

    # ---------- references people cite
    def resolve(self, ref):
        """'1839', 'n. 1839', 'DS 3074', 'LG 25', 'Suppl. S1', 'CCC 2267', 'AD 19641203' -> entry ids."""
        r = str(ref).strip()
        m = re.fullmatch(r'(?i)(?:ds|dh|denz(?:inger)?[- ]schönmetzer)\.?\s*(\d{1,4}[a-z]?)', r)
        if m:
            return self.by_ds.get(m.group(1), [])
        r = re.sub(r'(?i)^(n\.|no\.|nr\.|d|denzinger|suppl\.?|supplement)\s*', '', r).strip()
        for key in (r, r.replace(' ', ''), r.upper().replace(' ', ''), r.replace('_s', '*')):
            if key in self.by_id:
                return [key]
        m = re.fullmatch(r'([A-Za-z]{2,})\s*(\d+)', r)
        if m and m.group(1).upper() + m.group(2) in self.by_id:
            return [m.group(1).upper() + m.group(2)]
        return []

    def label(self, i):
        d = re.sub(r'^([A-Z]{2,})(\d)', r'\1 \2', re.sub(r'-\d+$', '', i))
        if re.match(r'[A-Z]{2}', i):
            return d
        return f'Suppl. {i}' if re.match(r'[A-Z]', i) else f'n. {d}'

    def url(self, i):
        return f'{SITE}n/{i.replace("*", "_s")}/'

    def weight(self, e):
        return WEIGHTS.get('papal-teaching' if e['weight'] == 'papal' else e['weight'], WEIGHTS['papal-teaching'])

    def heading(self, e):
        ds = f' (DS {", ".join(e["ds"])})' if e['ds'] else ''
        return f'{self.label(e["id"])}{ds}: {e.get("topic") or ""}'.rstrip(': ')

    def standing(self, e):
        w = self.weight(e)
        out = [f'Kind of document: {w[0]}. {w[1]}']
        if e.get('grade'):
            out.append(f'Grade: {GRADES.get(e["grade"], e["grade"])} ({e.get("gradeStatus") or "editorial assessment"})'
                       + (f'. {e["gradeNote"]}' if e.get('gradeNote') else ''))
        if e.get('censure'):
            out.append('Censure: ' + ', '.join(e['censure']))
        if e.get('papalDefinition'):
            out.append(f'{e["papalDefinition"]["label"]}: {e["papalDefinition"]["note"]}')
        return out


# ---------------------------------------------------------------- tools

def tool_search(D, query, weight=None, grade=None, year_from=None, year_to=None, limit=10):
    phrases = [fold(p) for p in re.findall(r'"([^"]+)"', query)]
    rest = re.sub(r'"[^"]+"', ' ', query)
    words = [w for w in re.findall(r'\w+', fold(rest)) if len(w) > 1 or w.isdigit()]
    direct = [i for i in D.resolve(query)] if not phrases and len(words) <= 2 else []
    hits = []
    for e, text in D.index:
        if weight and e['weight'] != weight:
            continue
        if grade and e.get('grade') != grade:
            continue
        if year_from and (e.get('year') or 0) < year_from or year_to and (e.get('year') or 9999) > year_to:
            continue
        if any(p not in text for p in phrases) or any(w not in text for w in words):
            continue
        score = sum(text.count(w) for w in words) + 5 * len(phrases)
        score += 3 * sum(w in fold(e.get('topic') or '') for w in words)
        hits.append((score, e))
    hits.sort(key=lambda h: (-h[0], h[1]['year'] or 0))
    seen = set(direct)
    lines = []
    for i in direct:
        lines.append(summary_line(D, D.by_id[i], query, words + phrases))
    for _, e in hits:
        if len(lines) >= limit:
            break
        if e['id'] not in seen:
            seen.add(e['id'])
            lines.append(summary_line(D, e, query, words + phrases))
    if not lines:
        return 'No entries match. Try fewer words, another spelling, or a number (n. 1839, DS 3074, LG 25).'
    total = len(hits) + len([i for i in direct if i not in {h[1]['id'] for h in hits}])
    return f'{total} entries match; the first {len(lines)}:\n\n' + '\n\n'.join(lines) + \
        '\n\nUse get_entry with a number for the full text.'


def summary_line(D, e, query, terms):
    text = ' '.join(e['text'])
    ft = fold(text)
    pos = min([ft.find(t) for t in terms if t and ft.find(t) >= 0] or [0])
    start = max(0, pos - 100)
    snippet = ('...' if start else '') + text[start:start + 260].strip() + ('...' if start + 260 < len(text) else '')
    w = D.weight(e)
    grade = f'; {GRADES.get(e["grade"], e["grade"])}' if e.get('grade') else ''
    return f'- {D.heading(e)}\n  {e.get("era")}, {e.get("year") or "date unknown"}. {w[0]}{grade}.\n  {snippet}'


def entry_text(D, e, latin):
    lines = [f'# {D.heading(e)}', '']
    where = ', '.join(x for x in [e.get('era'), e.get('session'), str(e.get('year') or '')] if x)
    lines.append(where)
    if e.get('source'):
        lines.append(e['source'])
    lines += [''] + D.standing(e) + ['', 'Text:', ''] + e['text']
    if latin:
        lat = [(d, D.latin[d]) for d in e['ds'] if d in D.latin]
        if lat:
            lines += ['', 'Latin (as the source page gives it, not proofread):', '']
            lines += [f'DS {d}: {t}' for d, t in lat]
        else:
            lines += ['', 'No Latin text is held for this entry.']
    rec = D.records.get(e.get('documentId'))
    if rec:
        full = next((l['url'] for l in rec.get('sourceLinks', []) if l.get('scope') == 'full-document'), None)
        lines += ['', f'Source record: {rec["title"]} ({rec.get("coverage")} on this site)' + (f'; full text: {full}' if full else '')]
    if e.get('refersTo'):
        lines.append('Refers to: ' + ', '.join(D.label(i) for i in e['refersTo']))
    if e.get('citedBy'):
        lines.append('Cited by: ' + ', '.join(D.label(i) for i in e['citedBy']))
    lines.append(f'Page: {D.url(e["id"])}')
    return '\n'.join(lines)


def tool_get_entry(D, ref, latin=False):
    ids = D.resolve(ref)
    if not ids:
        return None
    return '\n\n---\n\n'.join(entry_text(D, D.by_id[i], latin) for i in ids)


def tool_related(D, ref):
    ids = D.resolve(ref)
    if not ids:
        return None
    out = []
    for i in ids:
        e = D.by_id[i]
        L = [f'# Related to {D.heading(e)}', '']
        if e.get('refersTo'):
            L.append('Refers to: ' + '; '.join(D.heading(D.by_id[x]) for x in e['refersTo'] if x in D.by_id))
        if e.get('citedBy'):
            L.append('Cited by: ' + '; '.join(D.heading(D.by_id[x]) for x in e['citedBy'] if x in D.by_id))
        for r in D.relations:
            if i in (r['from'], r['to']):
                other = r['to'] if r['from'] == i else r['from']
                L.append(f'Relation ({r["kind"]}, {r.get("status", "")}): {D.label(r["from"])} -> {D.label(r["to"])}. {r.get("note", "")}')
                for ev in r.get('evidence', []):
                    L.append(f'  {D.label(ev["entry"])}: "{ev["quote"]}"')
        for t in D.guides.get('threads', []):
            if any(i in json.dumps(s) for s in t.get('steps', [])):
                L.append(f'Doctrinal thread: {t["title"]} ({t["id"]})')
        for c in D.cases.values():
            if any(i in t.get('refs', []) for t in c['texts']) or any(p.get('ref') == i for p in c['propositions']):
                L.append(f'Continuity case {c["id"]}: {c["title"]} (verdict: {c["verdict"].replace("_", " ")}, confidence {c["confidence"]})')
        if len(L) == 2:
            L.append('Nothing is linked to this entry yet.')
        out.append('\n'.join(L))
    return '\n\n'.join(out)


def tool_cite(D, ref, style='all'):
    ids = D.resolve(ref)
    if not ids:
        return None
    out = []
    acc = time.strftime('%B %d, %Y').replace(' 0', ' ')
    for i in ids:
        e = D.by_id[i]
        where = e.get('era') + (', ' + re.sub(r'\s*\(.*\)$', '', e['session']) if e.get('session') else '')
        ds = f' (DS {", ".join(e["ds"])})' if e['ds'] else ''
        site = (f'"{D.label(i)}{": " + " ".join(e["topic"].split()) if e.get("topic") else ""}," Eodem Sensu: Sources of '
                f'Catholic Dogma (online reader), {where}, accessed {acc}, {D.url(i)}.')
        f = {}
        if re.fullmatch(r'\d+[a-z]?\*?(-\d+)?', i):  # the older Denzinger numbers: Deferrari's translation
            n = D.label(i)[3:]
            f['short'] = f'D {n}{"; DS " + ", ".join(e["ds"]) if e["ds"] else ""}'
            f['chicago-note'] = f'Henry Denzinger, The Sources of Catholic Dogma, trans. Roy J. Deferrari (St. Louis: B. Herder, 1957), no. {n}{ds}.'
            f['chicago-bibliography'] = ('Denzinger, Henry. The Sources of Catholic Dogma. Translated by Roy J. Deferrari from the '
                                         'thirtieth edition of Enchiridion Symbolorum. St. Louis: B. Herder, 1957.')
            f['turabian'] = f'(Denzinger 1957, no. {n})'
        elif re.match(r'[A-Z]{2}', i):  # documents after 1958: by the document and its article
            f['short'] = D.label(i)
            src = (e.get('source') or '').strip('[]')
            f['document'] = f'{src}, {D.label(i)}.' if src else D.label(i)
        else:
            f['short'] = D.label(i)
        f['site'] = site
        keep = f if style in ('all', None) else {k: v for k, v in f.items() if k.startswith(style)} or f
        out.append(f'{D.heading(e)}\n' + '\n'.join(f'{k}: {v}' for k, v in keep.items()))
    return '\n\n'.join(out)


def tool_list_cases(D, group=None, verdict=None):
    L = ['Continuity cases (research, not Church teaching). Verdicts: ' +
         '; '.join(f'{k.replace("_", " ")}: {v.split(": ", 1)[-1].rstrip(".")}' for k, v in D.cont['vocab']['verdict'].items()), '']
    for g, name in D.cont['groups'].items():
        if group and g != group.upper():
            continue
        L.append(f'## {g}: {name}')
        for c in D.cont['cases']:
            if c.get('sealed'):
                if c['group'] == g and not verdict:
                    L.append(f'- {c["id"]} {c["title"]}: sealed (untested research, published encrypted; not available here)')
                continue
            if c['group'] == g and (not verdict or c['verdict'] == verdict):
                L.append(f'- {c["id"]} {c["title"]}: {c["verdict"].replace("_", " ")}, confidence {c["confidence"]}'
                         + ('' if c.get('source_verified') else ' (sources not yet verified)'))
        L.append('')
    return '\n'.join(L)


def tool_get_case(D, case_id, part='summary'):
    if str(case_id).upper() in D.sealed:
        raise LookupError(f'Case {str(case_id).upper()} is sealed: untested research, published only encrypted. '
                          'It is not available to this server; do not describe its contents or guess its verdict.')
    c = D.cases.get(str(case_id).upper())
    if not c:
        return None
    L = [f'# {c["id"]} {c["title"]}', '', 'A research case, not Church teaching.', '',
         f'Question: {c["question"]}',
         f'Verdict: {c["verdict"].replace("_", " ")} (confidence {c["confidence"]}; sources verified: {"yes" if c.get("source_verified") else "no"})',
         '', c['summary'], '']
    if part in ('summary', 'all'):
        L += [f'Hypothesis: {c.get("hypothesis", "")}', f'Strongest objection: {c.get("objection", "")}',
              f'Reply: {c.get("rebuttal", "")}', f'Reception: {c.get("reception", "")}',
              f'Contingency: {c.get("contingency", "")}', f'Development: {c.get("development", "")}', '']
    if part in ('texts', 'all'):
        L.append('## Texts')
        for t in c['texts']:
            refs = ', '.join(D.label(r) if r in D.by_id else r for r in t.get('refs', []))
            L.append(f'- {t["label"]} [{refs}] local: {t.get("local")}; checked against an edition: {"yes" if t.get("verified") else "no"}'
                     + (f'. {t["edition"]}' if t.get('edition') else ''))
        L.append('')
    if part in ('propositions', 'all'):
        L.append('## Propositions')
        for p in c['propositions']:
            ref = D.label(p['ref']) if p.get('ref') in D.by_id else p.get('ref') or p.get('ext') or ''
            L.append(f'- {p["id"]} ({ref}, {p.get("year")}): {p["says"]} [object: {p["formal_object"]}; assent: {p["assent"]}; '
                     f'binding: {p["binding_status"]}; evidence: {p["evidence"]}]')
        L += ['', '## Comparisons']
        for m in c.get('matrix', []):
            L.append(f'- {m["a"]} / {m["b"]} ({m["level"]}): {m["result"].replace("_", " ")}. {m["why"]}')
        L.append('')
    if part in ('gaps', 'summary', 'all'):
        L.append('## Evidence still needed')
        for g in c.get('gaps', []):
            L.append(f'- {g["what"]}. Source: {g.get("source", "?")}. Would settle: {g.get("settles", "?")}')
        if c.get('next_source'):
            L.append(f'Next: {c["next_source"]}')
    return '\n'.join(L)


def rules_text(D, which='all'):
    L = []
    if which in ('all', 'hermeneutics'):
        h = D.guides['hermeneutics']
        L += ['# Reading magisterial texts', '']
        for p in h['principles']:
            L.append(f'- {p["title"]}: {p["rule"]}')
        L.append('')
    if which in ('all', 'continuity'):
        C = D.cont
        L += ['# Testing continuity (research protocol, not Church teaching)', '',
              f'Method: {C["benedict"]["source"]}. {C["benedict"].get("status", "")}', '']
        for p in C['principles']:
            L.append(f'- {p["id"]} {p["title"]}: {p["rule"]}')
        L += ['', 'Levels of continuity: ' + '; '.join(f'{l["id"] if isinstance(l, dict) else l}' + (f' ({l.get("title", "")})' if isinstance(l, dict) else '') for l in C['levels']), '']
        for k in ('formal_object', 'assent', 'binding_status', 'evidence', 'verdict', 'matrix_result'):
            L.append(f'{k}: ' + '; '.join(f'{a} = {b}' for a, b in C['vocab'][k].items()))
    return '\n'.join(L)


TOOLS = [
    {'name': 'search', 'description': 'Search the entries by words, "exact phrases" or a number (1839, DS 3074, LG 25). '
     'Filter by kind of document (weight), hand-checked grade, or years. Returns numbered results with a snippet.',
     'inputSchema': {'type': 'object', 'properties': {
         'query': {'type': 'string', 'description': 'Words, "a phrase", or a number'},
         'weight': {'type': 'string', 'enum': sorted(WEIGHTS), 'description': 'Kind of document'},
         'grade': {'type': 'string', 'enum': sorted(GRADES), 'description': 'Hand-checked grade'},
         'year_from': {'type': 'integer'}, 'year_to': {'type': 'integer'},
         'limit': {'type': 'integer', 'minimum': 1, 'maximum': 50, 'default': 10}}, 'required': ['query']},
     'annotations': {'readOnlyHint': True}},
    {'name': 'get_entry', 'description': 'The full text of an entry with its kind of document, grade and the reason for it, censure, '
     'source record, cross-references and page link. Accepts the numbers people cite: 1839, n. 1839, DS 3074, LG 25, CCC 2267, Suppl. S1.',
     'inputSchema': {'type': 'object', 'properties': {
         'ref': {'type': 'string'}, 'latin': {'type': 'boolean', 'default': False, 'description': 'Add the Latin by DS number'}},
         'required': ['ref']}, 'annotations': {'readOnlyHint': True}},
    {'name': 'related', 'description': 'What an entry is linked to: the entries it refers to and that cite it, documented relations '
     'with quotations, doctrinal threads, and continuity cases that use it.',
     'inputSchema': {'type': 'object', 'properties': {'ref': {'type': 'string'}}, 'required': ['ref']},
     'annotations': {'readOnlyHint': True}},
    {'name': 'cite', 'description': 'Citations for an entry: short form, Chicago note and bibliography and Turabian for the older '
     'Denzinger numbers (Deferrari 1957), the document and article after 1958, and the online reader.',
     'inputSchema': {'type': 'object', 'properties': {'ref': {'type': 'string'},
         'style': {'type': 'string', 'enum': ['all', 'short', 'chicago', 'turabian', 'document', 'site'], 'default': 'all'}},
         'required': ['ref']}, 'annotations': {'readOnlyHint': True}},
    {'name': 'list_cases', 'description': 'The continuity research cases (a research layer, not Church teaching) with their '
     'verdicts and confidence, by group.',
     'inputSchema': {'type': 'object', 'properties': {
         'group': {'type': 'string', 'description': 'A, B, C or D'},
         'verdict': {'type': 'string', 'enum': ['plausible_concord', 'unresolved_tension', 'demonstrated_concord',
                                                'textual_conflict_requires_revision', 'not_comparable']}}},
     'annotations': {'readOnlyHint': True}},
    {'name': 'get_case', 'description': 'One continuity case: question, verdict, hypothesis, strongest objection and reply, and '
     'optionally its texts, its propositions (formal object, assent, binding force, evidence) and comparisons, and the evidence still needed.',
     'inputSchema': {'type': 'object', 'properties': {'case_id': {'type': 'string', 'description': 'For example C3 or D1'},
         'part': {'type': 'string', 'enum': ['summary', 'texts', 'propositions', 'gaps', 'all'], 'default': 'summary'}},
         'required': ['case_id']}, 'annotations': {'readOnlyHint': True}},
    {'name': 'reading_rules', 'description': 'The rules for reading magisterial texts (ten principles of hermeneutics) and the '
     'continuity research protocol (principles P1-P8, levels, and the labels for assent, binding force, evidence and verdicts). '
     'Read before weighing or comparing texts.',
     'inputSchema': {'type': 'object', 'properties': {'which': {'type': 'string', 'enum': ['all', 'hermeneutics', 'continuity'], 'default': 'all'}}},
     'annotations': {'readOnlyHint': True}},
]

PROMPTS = [
    {'name': 'test_continuity', 'description': 'Test whether two texts conflict, following the continuity protocol.',
     'arguments': [{'name': 'first', 'description': 'A number, e.g. 1839 or DS 3074', 'required': True},
                   {'name': 'second', 'description': 'A number, e.g. LG 25', 'required': True}]},
    {'name': 'check_statement', 'description': 'Check a statement about Catholic teaching against the texts.',
     'arguments': [{'name': 'statement', 'description': 'The statement to check', 'required': True}]},
]


def prompt_text(name, args):
    if name == 'test_continuity':
        return (f'Test whether {args.get("first")} and {args.get("second")} conflict, using the Eodem Sensu tools.\n\n'
                '1. Call reading_rules, then get_entry for each text (with latin=true where a DS number exists) and related for each.\n'
                '2. If a continuity case already covers them (related shows it), call get_case with part="all" and build on it.\n'
                '3. Break each text into atomic propositions. For each give subject, predicate, scope, time, formal object, '
                'the assent it asks and its binding force, citing the entry number and quoting the words.\n'
                '4. Compare each pair under principles P1-P8: same subject, same sense, same time? Classify the result '
                '(no conflict, apparent, potential contradiction, contradiction, undetermined) and say why.\n'
                '5. State the strongest objection to your reading, a reply, a provisional verdict with a confidence, and the '
                'evidence that would change it.\n\nQuote only what the tools return; mark anything from memory as such. '
                'This is research, not a judgment of the Church.')
    if name == 'check_statement':
        return (f'Check this statement against the texts, using the Eodem Sensu tools: "{args.get("statement")}"\n\n'
                '1. Call reading_rules (hermeneutics). 2. search for the texts that bear on it; put defining and binding texts first. '
                '3. get_entry for the most relevant (up to eight). 4. Say what each actually teaches, with what authority, '
                'quoting and citing by number. 5. Say whether the statement is supported, needs qualifying, or is contradicted, '
                'and what remains disputed (check list_cases and get_case where a case covers it).')
    return None


# ---------------------------------------------------------------- protocol

class Server:
    def __init__(self, folder_arg=None, refresh=False):
        self.folder_arg, self.refresh, self._data = folder_arg, refresh, None

    @property
    def data(self):
        if self._data is None:
            self._data = Data(data_dir(self.folder_arg, self.refresh))
            log(f'{len(self._data.entries)} entries loaded from {self._data.folder}')
        return self._data

    def call_tool(self, name, a):
        D = self.data
        if name == 'search':
            return tool_search(D, a.get('query', ''), a.get('weight'), a.get('grade'), a.get('year_from'), a.get('year_to'),
                               max(1, min(int(a.get('limit') or 10), 50)))
        if name == 'get_entry':
            r = tool_get_entry(D, a.get('ref', ''), bool(a.get('latin')))
        elif name == 'related':
            r = tool_related(D, a.get('ref', ''))
        elif name == 'cite':
            r = tool_cite(D, a.get('ref', ''), a.get('style', 'all'))
        elif name == 'list_cases':
            return tool_list_cases(D, a.get('group'), a.get('verdict'))
        elif name == 'get_case':
            r = tool_get_case(D, a.get('case_id', ''), a.get('part', 'summary'))
            if r is None:
                raise LookupError(f'No case {a.get("case_id")!r}. Call list_cases for the ids.')
            return r
        elif name == 'reading_rules':
            return rules_text(D, a.get('which', 'all'))
        else:
            raise KeyError(f'unknown tool {name}')
        if r is None:
            raise LookupError(f'No entry for {a.get("ref")!r}. Numbers look like 1839, DS 3074, LG 25, CCC 2267 or S1; '
                              'or use search.')
        return r

    def handle(self, msg):
        method, mid, p = msg.get('method'), msg.get('id'), msg.get('params') or {}
        if mid is None:
            return None  # a notification (initialized, cancelled): nothing to answer
        try:
            if method == 'initialize':
                asked = p.get('protocolVersion')
                result = {'protocolVersion': asked if asked in PROTOCOLS else PROTOCOLS[0],
                          'capabilities': {'tools': {}, 'resources': {}, 'prompts': {}},
                          'serverInfo': {'name': NAME, 'title': 'Eodem Sensu', 'version': VERSION},
                          'instructions': INSTRUCTIONS}
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                result = {'tools': TOOLS}
            elif method == 'tools/call':
                try:
                    text = self.call_tool(p.get('name'), p.get('arguments') or {})
                    result = {'content': [{'type': 'text', 'text': text}], 'isError': False}
                except (LookupError, KeyError, ValueError, TypeError) as err:
                    result = {'content': [{'type': 'text', 'text': str(err).strip('"\'')}], 'isError': True}
            elif method == 'resources/list':
                result = {'resources': [
                    {'uri': 'eodem://rules/hermeneutics', 'name': 'Reading magisterial texts', 'mimeType': 'text/markdown',
                     'description': 'The ten principles of hermeneutics, each stated as a rule.'},
                    {'uri': 'eodem://rules/continuity', 'name': 'Continuity research protocol', 'mimeType': 'text/markdown',
                     'description': 'Principles P1-P8, levels of continuity and the labels used in the cases.'}]}
            elif method == 'resources/read':
                which = {'eodem://rules/hermeneutics': 'hermeneutics', 'eodem://rules/continuity': 'continuity'}.get(p.get('uri'))
                if not which:
                    return error(mid, -32002, f'Resource not found: {p.get("uri")}')
                result = {'contents': [{'uri': p['uri'], 'mimeType': 'text/markdown', 'text': rules_text(self.data, which)}]}
            elif method == 'resources/templates/list':
                result = {'resourceTemplates': []}
            elif method == 'prompts/list':
                result = {'prompts': PROMPTS}
            elif method == 'prompts/get':
                text = prompt_text(p.get('name'), p.get('arguments') or {})
                if text is None:
                    return error(mid, -32602, f'Unknown prompt: {p.get("name")}')
                result = {'description': next(x['description'] for x in PROMPTS if x['name'] == p['name']),
                          'messages': [{'role': 'user', 'content': {'type': 'text', 'text': text}}]}
            else:
                return error(mid, -32601, f'Method not found: {method}')
            return {'jsonrpc': '2.0', 'id': mid, 'result': result}
        except Exception as err:  # never let one request stop the server
            log(f'error in {method}: {err!r}')
            return error(mid, -32603, f'Internal error: {err}')


def error(mid, code, message):
    return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': code, 'message': message}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', help='folder with entries.json, latin.json, guides.json, continuity.json, documents.json')
    ap.add_argument('--refresh', action='store_true', help='download the published data again')
    a = ap.parse_args(argv)
    server = Server(a.data, a.refresh)
    stdin = open(sys.stdin.fileno(), 'r', encoding='utf-8', newline='\n', closefd=False)
    out = open(sys.stdout.fileno(), 'w', encoding='utf-8', newline='\n', closefd=False)
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = error(None, -32700, 'Parse error')
        else:
            reply = [r for r in (server.handle(m) for m in msg) if r] if isinstance(msg, list) else server.handle(msg)
        if reply:
            out.write(json.dumps(reply, ensure_ascii=False) + '\n')
            out.flush()


if __name__ == '__main__':
    main()
