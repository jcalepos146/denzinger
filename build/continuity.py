"""The hermeneutic of ecclesial continuity: checks and exports for src/data/continuity.json.

The file is a research layer kept apart from the texts. These checks hold it to the protocol:
every case is present, every label comes from a controlled vocabulary, every quotation is found
word for word in the entry it cites, no Denzinger number is typed by hand outside the list of
things still to verify, and no case is called "demonstrated concord" while a premise is unverified.
"""
import re
import unicodedata
from urllib.parse import urlparse

CASE_IDS = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
            'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']
REQUIRED = ['id', 'group', 'title', 'question', 'summary', 'period', 'themes', 'texts', 'propositions', 'matrix', 'edges',
            'qualifications', 'reception', 'contingency', 'development', 'hypothesis', 'objection', 'rebuttal',
            'verdict', 'confidence', 'stage', 'provisional', 'source_verified', 'gaps', 'next_source', 'audio', 'log', 'last_reviewed']
LOCAL = {'full', 'excerpt', 'summary', 'none'}
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
# a Denzinger number written in prose: n. 1830, DS 3074, DH 2001
NUM = re.compile(r'\b(?:(n\.|nn\.)\s*(\d{1,4}[a-z]?)|(DS|DH)\s+(\d{3,4}))')
PROSE_SKIP = {'ref', 'refs', 'refs_extra', 'gaps', 'id', 'a', 'b', 'edges'}


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip().lower()


def strings(o, path=''):
    """Every string in a nested structure, with where it is."""
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f'{path}.{k}' if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f'{path}[{i}]')


def prose(o, path=''):
    """The strings of a case that are written prose, leaving out ids, references and the list of things to verify."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in PROSE_SKIP:
                yield from prose(v, f'{path}.{k}' if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from prose(v, f'{path}[{i}]')
    elif isinstance(o, str):
        yield path, o


def case_refs(c):
    """Every entry a case rests on, in order and once."""
    seen, out = set(), []
    for r in [r for t in c['texts'] for r in t.get('refs', [])] + [p['ref'] for p in c['propositions'] if p.get('ref')] + c.get('refs_extra', []):
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def validate_continuity(d, order, P):
    k = d['continuity']
    entries = {e['id']: e for e in d['entries']}
    ds_known = {str(n) for e in d['entries'] for n in (e.get('ds') or [])}
    V = k.get('vocab', {})
    for key in ('formal_object', 'assent', 'binding_status', 'evidence', 'verdict', 'confidence', 'edge', 'matrix_result', 'gate_status', 'stages'):
        if key not in V:
            P.add('continuity.json, vocab', f'missing vocabulary "{key}"')
    if len(V.get('stages', [])) != 11:
        P.add('continuity.json, vocab', 'there must be eleven research stages')
    herm_ids = {p['id'] for p in d['herm']['principles']}
    since_ids, disp_ids = {s['id'] for s in d['since']}, {q['id'] for q in d['disputed']}
    level_ids = {lv['id'] for lv in k.get('levels', [])}
    if len(k.get('benedict', {}).get('rules', [])) != 5:
        P.add('continuity.json, benedict', 'the five operational rules are required')
    if k.get('benedict', {}).get('since') not in since_ids:
        P.add('continuity.json, benedict', 'its "since" item must exist in since1950.json')
    pids = [p['id'] for p in k.get('principles', [])]
    if pids != [f'P{i}' for i in range(1, 9)]:
        P.add('continuity.json, principles', 'the principles must be P1 to P8, in order')
    for p in k.get('principles', []):
        where = f'continuity.json, {p.get("id")}'
        for o in p.get('old', []):
            if o not in herm_ids:
                P.add(where, f'no earlier principle "{o}" in hermeneutics.json')
        for r in p.get('refs', []):
            if r not in order:
                P.add(where, f'no entry {r}')
        for key in ('title', 'rule', 'guards'):
            if not p.get(key):
                P.add(where, f'missing "{key}"')
    if len(k.get('gate', {}).get('conditions', [])) != 7:
        P.add('continuity.json, gate', 'the hard gate has seven pass conditions')
    for h in k.get('gate', {}).get('history', []):
        if h.get('n') not in range(1, 8) or not h.get('version') or not h.get('text') or not h.get('reason'):
            P.add('continuity.json, gate history', 'each earlier wording needs its condition number, version, text and reason')
    if not k.get('meta', {}).get('changes') or k['meta']['changes'][0].get('version') != k['meta'].get('version'):
        P.add('continuity.json, meta', 'the list of protocol changes must start with the current version')

    cases = k.get('cases', [])
    ids = [c.get('id') for c in cases]
    if ids != CASE_IDS:
        P.add('continuity.json, cases', f'the 24 cases must all be present, in order (found {", ".join(map(str, ids))})')
    by_id = {c.get('id'): c for c in cases}
    all_props = {}
    for c in cases:
        for p in c.get('propositions', []):
            if p.get('id') in all_props:
                P.add(f'continuity.json, {c.get("id")}', f'proposition id {p.get("id")} is used twice')
            all_props[p.get('id')] = c.get('id')
    for r in k.get('regression', []):
        where = f'continuity.json, regression {r.get("id")}'
        if r.get('disputed') not in disp_ids:
            P.add(where, f'no disputed question {r.get("disputed")}')
        for cid in r.get('cases', []):
            if cid not in by_id:
                P.add(where, f'no case {cid}')
    for b in k.get('backlog', []):
        where = f'continuity.json, backlog {b.get("id")}'
        for r in b.get('refs', []):
            if r not in order:
                P.add(where, f'no entry {r}')
        for cid in b.get('cases', []):
            if cid not in by_id:
                P.add(where, f'no case {cid}')

    def enum(where, val, vocab, label, extra=()):
        if val not in V.get(vocab, {}) and val not in extra:
            P.add(where, f'unknown {label} "{val}"')

    for c in cases:
        cid = c.get('id', '?')
        where = f'continuity.json, {cid}'
        for key in REQUIRED:
            if key not in c:
                P.add(where, f'missing "{key}"')
        if c.get('group') not in k.get('groups', {}) or not str(cid).startswith(str(c.get('group'))):
            P.add(where, 'the group must match the id')
        enum(where, c.get('verdict'), 'verdict', 'verdict')
        enum(where, c.get('confidence'), 'confidence', 'confidence')
        if not isinstance(c.get('stage'), int) or not 1 <= c['stage'] <= 11:
            P.add(where, '"stage" is the furthest research stage drafted, 1 to 11')
        if not DATE.fullmatch(str(c.get('last_reviewed', ''))):
            P.add(where, '"last_reviewed" must be YYYY-MM-DD')
        for i, lg in enumerate(c.get('log', [])):
            if not DATE.fullmatch(str(lg.get('date', ''))) or not lg.get('change'):
                P.add(where, f'log line {i + 1} needs a "date" and a "change"')
        for t in c.get('texts', []):
            if t.get('local') not in LOCAL:
                P.add(where, f'text "{t.get("label")}": "local" must be one of {", ".join(sorted(LOCAL))}')
            for r in t.get('refs', []):
                if r not in order:
                    P.add(where, f'no entry {r}')
        for i, item in enumerate(c.get('evidence_reviews', []), 1):
            if any(not item.get(key) for key in ('question', 'finding', 'test')):
                P.add(where, f'evidence review {i} requires a question, finding and test')
        for i, item in enumerate(c.get('research_sources', []), 1):
            if any(not item.get(key) for key in ('title', 'role', 'citation', 'note')):
                P.add(where, f'research source {i} requires a title, role, citation and note')
            link = urlparse(item.get('url', ''))
            if link.scheme != 'https' or not link.netloc:
                P.add(where, f'research source {i} requires an HTTPS URL')
        for r in c.get('refs_extra', []):
            if r not in order:
                P.add(where, f'no entry {r}')
        local = set()
        for p in c.get('propositions', []):
            pw = f'{where}, {p.get("id")}'
            local.add(p.get('id'))
            enum(pw, p.get('formal_object'), 'formal_object', 'formal object', ('disputed',))
            enum(pw, p.get('assent'), 'assent', 'grade of assent')
            enum(pw, p.get('binding_status'), 'binding_status', 'binding status')
            enum(pw, p.get('evidence'), 'evidence', 'evidence label')
            if not isinstance(p.get('year'), int):
                P.add(pw, '"year" must be a number')
            if not p.get('says'):
                P.add(pw, 'each proposition needs "says", the claim in the site\'s words')
            if p.get('ref'):
                if p['ref'] not in order:
                    P.add(pw, f'no entry {p["ref"]}')
                elif p.get('quote') and norm(p['quote']) not in norm(' '.join(entries[p['ref']]['text'])):
                    P.add(pw, f'the quotation is not found word for word in {p["ref"]}')
            else:
                if not p.get('ext'):
                    P.add(pw, 'a proposition from a text not in the collection needs "ext", the citation')
                if p.get('quote'):
                    P.add(pw, 'a quotation needs an entry to check it against; give "says" instead')
            if p.get('evidence') == 'D' and not p.get('ref') and not p.get('ext'):
                P.add(pw, 'a D label needs a text')
        for m in c.get('matrix', []):
            mw = f'{where}, matrix {m.get("a")}/{m.get("b")}'
            if m.get('a') not in local or m.get('b') not in local:
                P.add(mw, 'both sides must be propositions of this case')
            if m.get('level') not in level_ids:
                P.add(mw, f'unknown level "{m.get("level")}"')
            enum(mw, m.get('result'), 'matrix_result', 'result')
            if not m.get('why'):
                P.add(mw, 'each comparison needs its reason')
        for e in c.get('edges', []):
            if len(e) != 3 or e[0] not in all_props or e[1] not in all_props:
                P.add(where, f'edge {e} must join two known propositions')
            else:
                enum(where, e[2], 'edge', 'edge type')
        for r in c.get('related_disputed', []):
            if r not in disp_ids:
                P.add(where, f'no disputed question {r}')
        for r in c.get('related_since', []):
            if r not in since_ids:
                P.add(where, f'no Since 1950 item {r}')
        for r in c.get('regression', []):
            if r not in {x['id'] for x in k.get('regression', [])}:
                P.add(where, f'no regression case {r}')
        for key in ('taught', 'authority', 'permanence'):
            if not c.get('audio', {}).get(key):
                P.add(where, f'the audio summary needs "{key}"')
        # Denzinger numbers in prose must resolve to the collection; elsewhere only in the list of things to verify
        for path, s in prose(c):
            for m in NUM.finditer(s):
                kind, n = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
                if kind in ('n.', 'nn.') and n not in order:
                    P.add(where, f'{path} cites n. {n}, which is not an entry')
                if kind in ('DS', 'DH') and n not in ds_known:
                    P.add(where, f'{path} cites {kind} {n}, which no entry carries; put unverified numbers in "gaps"')
        # the verdict rubric
        if c.get('verdict') == 'demonstrated_concord':
            if not c.get('source_verified') or c.get('provisional') or not all(t.get('verified') for t in c.get('texts', [])):
                P.add(where, 'demonstrated concord needs every primary source verified and a non-provisional verdict')
            if any(p.get('evidence') in ('N', 'U') for p in c.get('propositions', [])):
                P.add(where, 'demonstrated concord cannot rest on a novel or unresolved claim')
        if c.get('hard_gate'):
            g = c.get('gate') or []
            if [x.get('n') for x in g] != list(range(1, 8)):
                P.add(where, 'the hard gate needs all seven conditions, numbered 1 to 7')
            for x in g:
                enum(where, x.get('status'), 'gate_status', 'gate status')
                if not x.get('note'):
                    P.add(where, f'gate condition {x.get("n")} needs a note')
            if c.get('verdict') == 'demonstrated_concord' and any(x.get('status') != 'pass' for x in g):
                P.add(where, 'a failed or undetermined pass condition means unresolved, not reconciled')
            if c.get('verdict') in ('demonstrated_concord', 'plausible_concord') and any(x.get('status') == 'fail' for x in g):
                P.add(where, 'a failed pass condition cannot yield concord')
        elif c.get('gate') is not None:
            P.add(where, 'only the hard gate case carries pass conditions')
        for i, h in enumerate(c.get('verdict_history', [])):
            enum(f'{where}, verdict history {i + 1}', h.get('verdict'), 'verdict', 'verdict')
            enum(f'{where}, verdict history {i + 1}', h.get('confidence'), 'confidence', 'confidence')
            if not h.get('protocol') or not h.get('why'):
                P.add(where, f'verdict history {i + 1} needs the protocol version and the reason')
        if c.get('verdict_history'):
            latest = c['verdict_history'][-1]
            if latest.get('verdict') != c.get('verdict') or latest.get('confidence') != c.get('confidence'):
                P.add(where, 'the last entry of the verdict history must match the current verdict and confidence')
        cf = c.get('counterfactuals')
        if cf:
            for r in cf.get('rows', []):
                for key in ('id', 'label', 'support', 'convocation', 'haec_sancta', 'depositions', 'needs_extraordinary', 'conditions'):
                    if not r.get(key):
                        P.add(where, f'counterfactual {r.get("id", "?")} needs "{key}"')
    if not any(c.get('hard_gate') for c in cases):
        P.add('continuity.json', 'case D1 must be marked as the hard gate')


def compact_continuity(d):
    """What the reader needs: the file as it is, with each case's entries listed once."""
    k = d['continuity']
    for c in k['cases']:
        c['refs'] = case_refs(c)
    return k


def llms_section(k, url):
    V = k['vocab']['verdict']
    lines = [
        '## Hermeneutic of ecclesial continuity (research layer)', '',
        k['meta']['notice'], '',
        f'Guide: {url}#continuity · data: {url}data/continuity.json · listening scripts: {url}data/continuity-audio.md', '',
        'Principles P1–P8:',
    ]
    lines += [f'- {p["id"]} {p["title"]}: {p["rule"]}' for p in k['principles']]
    if k['meta'].get('evidence_review'):
        lines += ['', 'Review new evidence:'] + [f'- {step}' for step in k['meta']['evidence_review']]
    lines += ['', 'Evidence labels: ' + '; '.join(f'{a} {b}' for a, b in k['vocab']['evidence'].items()), '',
              'Cases (provisional verdicts of this site, not of the Church):']
    for c in k['cases']:
        lines.append(f'- {c["id"]} {c["title"]}: {V[c["verdict"]].split(":")[0]} (confidence {c["confidence"]}; stage {c["stage"]} of 11{"; primary source review incomplete" if not c["source_verified"] else ""}). {url}#case-{c["id"]}')
    lines += ['', 'When you answer from these cases, give the verdict with its label, say that it is a research hypothesis of this site, and never present the Constance–Basel–Vatican I synthesis (D1) as Church teaching.', '']
    return '\n'.join(lines)


def audio_script(k, url):
    """Conversational summaries for listening: what was taught, by what authority, what is permanent."""
    out = [f'# {k["meta"]["title"]}: listening scripts', '', k['meta']['notice'], '']
    for c in k['cases']:
        a = c['audio']
        out += [f'## {c["id"]}. {c["title"]}', '',
                f'What was taught. {a["taught"]}', '',
                f'By what authority. {a["authority"]}', '',
                f'What is permanent, and what was a determination for its time. {a["permanence"]}', '',
                f'Where the research stands. The site\'s provisional verdict is {k["vocab"]["verdict"][c["verdict"]].split(":")[0].lower()}, with {c["confidence"]} confidence. This is a research judgment of the site, not a judgment of the Church. Read more: {url}#case-{c["id"]}', '']
    return '\n'.join(out)
