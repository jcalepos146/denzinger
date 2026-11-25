#!/usr/bin/env python3
"""Rank what the collection is missing by how much it matters to the continuity research.

    python3 tools/sources/priorities.py            # -> .sources/priorities.md and .json

The aim of the continuity layer is to test whether apparent conflicts between
magisterial texts are reconciled, so evidence matters most where a verdict is
weakest: an unresolved tension or a low-confidence concord can still fail, and
the item that settles it comes first. A text that binds in faith matters more
than a disciplinary one, and an explicit research gap ("what would settle
this") more than general coverage.

Score = case urgency x kind of item (x 1.5 when a proposition resting on the
text asks the assent of faith or definitive assent, or whose binding force is
disputed). Coverage gaps from `sources.py diff` that no case cites come last.
Reads src/data and, if present, .sources/report.json. Writes only to .sources/.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sources import OUT, data, path, read_json, write_json  # noqa: E402

URGENCY = {  # how likely new evidence is to change the verdict
    ('unresolved_tension', 'low'): 3.0, ('unresolved_tension', 'medium'): 2.8, ('unresolved_tension', 'high'): 2.5,
    ('plausible_concord', 'low'): 2.2, ('plausible_concord', 'medium'): 1.6, ('plausible_concord', 'high'): 1.0,
}
KIND = {'gap': 3.0, 'backlog': 3.0, 'unverified-text': 2.0, 'unresolved-claim': 2.0, 'latin': 1.0, 'coverage': 0.6}
BINDING_ASSENT = {'faith', 'definitive_assent', 'disputed'}


def urgency(case):
    u = URGENCY.get((case['verdict'], case['confidence']), 1.0)
    return u + (0.3 if case.get('hard_gate') or case.get('gate') else 0)


def build():
    cont = data('continuity.json')
    cases = {c['id']: c for c in cont['cases']}
    latin = data('latin.json')
    entries = {e['id']: e for e in data('entries.json')}
    records = data('documents.json')
    rec_of = {eid: r for r in records for eid in r.get('entryIds', [])}
    items = []

    def add(kind, case_ids, title, detail, factor=1.0, **extra):
        cs = [cases[c] for c in case_ids if c in cases]
        u = max((urgency(c) for c in cs), default=1.0)
        items.append(dict(kind=kind, cases=[c['id'] for c in cs], title=title, detail=detail,
                          score=round(u * KIND[kind] * factor + 0.1 * (len(cs) - 1), 2), **extra))

    for c in cont['cases']:
        binding_refs = {p['ref'] for p in c['propositions']
                        if p.get('assent') in BINDING_ASSENT or p.get('binding_status') == 'disputed'}
        for g in c.get('gaps', []):
            add('gap', [c['id']], g['what'], f'Source: {g.get("source", "?")}. Settles: {g.get("settles", "?")}')
        for t in c['texts']:
            if t.get('verified'):
                continue
            weighty = bool(set(t.get('refs', [])) & binding_refs)
            held = {'none': 'not held on the site', 'excerpt': 'site has an excerpt', 'summary': 'site has a summary',
                    'full': 'site has the full text'}.get(t.get('local'), t.get('local'))
            add('unverified-text', [c['id']], t['label'],
                f'Not yet checked against a critical edition; {held}.' + (f' {t["note"]}' if t.get('note') else ''),
                1.5 if weighty else 1.0, binding=weighty, refs=t.get('refs', []))
        for p in c['propositions']:
            if p.get('evidence') == 'U':
                add('unresolved-claim', [c['id']], f'{p["id"]}: {p["says"][:140]}', p.get('note') or 'Evidence not yet in.')
        # the Latin of the texts that bind in faith, none of which has been proofread yet
        ds = sorted({d for p in c['propositions'] if p.get('assent') in BINDING_ASSENT and p.get('ref') in entries
                     for d in entries[p['ref']].get('ds', []) if str(d) in latin})
        if ds:
            add('latin', [c['id']], f'Proofread the Latin of {len(ds)} binding text(s) in {c["id"]}',
                'DS ' + ', '.join(str(d) for d in ds[:12]) + (' ...' if len(ds) > 12 else ''))
    for b in cont.get('backlog', []):
        add('backlog', b.get('cases', []), b['what'], b['need'])

    # coverage: documents with missing articles, raised when a case cites them
    cited = {}
    for c in cont['cases']:
        for t in c['texts']:
            for r in t.get('refs', []):
                if r in rec_of:
                    cited.setdefault(rec_of[r]['id'], set()).add(c['id'])
    for row in read_json(path('report.json'), []) or []:
        if not row.get('missing'):
            continue
        cs = sorted(cited.get(row['id'], []))
        add('coverage', cs, f'{row["title"]}: {len(row["missing"])} articles not on the site',
            f'Drafts in .sources/drafts/{row["id"]}.json' + ('' if cs else '. No continuity case cites it yet.'),
            1.0 if cs else 0.5, record=row['id'])
    items.sort(key=lambda i: (-i['score'], i['kind'], i['title']))
    return items, cases


def tier(score):
    return 'Critical' if score >= 7 else 'High' if score >= 4.5 else 'Medium' if score >= 2.5 else 'Low'


def write(items, cases):
    write_json(path('priorities.json'), items)
    L = ['# What to find first', '',
         'Generated by `tools/sources/priorities.py`. Ranked by how much each item could change a continuity verdict: '
         'unresolved tensions and low-confidence cases first, explicit research gaps before unchecked texts, '
         'texts that bind in faith before others, general coverage last.', '',
         '## Cases by urgency', '', '| Case | Verdict | Confidence | Open items | Title |', '|---|---|---|---:|---|']
    open_by = {}
    for i in items:
        for c in i['cases']:
            open_by[c] = open_by.get(c, 0) + 1
    for c in sorted(cases.values(), key=lambda c: (-urgency(c), c['id'])):
        L.append(f'| {c["id"]} | {c["verdict"].replace("_", " ")} | {c["confidence"]} | {open_by.get(c["id"], 0)} | {c["title"]} |')
    current = None
    n = 0
    for i in items:
        t = tier(i['score'])
        if t != current:
            current = t
            L += ['', f'## {t}', '']
        if i['kind'] == 'coverage' and not i['cases'] and t == 'Low':
            continue  # summarised below
        n += 1
        cs = ', '.join(i['cases']) or '-'
        flag = ' (binds in faith)' if i.get('binding') else ''
        L.append(f'{n}. **{i["title"]}**{flag} [{i["kind"]}; {cs}; {i["score"]}]  ')
        L.append(f'   {i["detail"]}')
    rest = [i for i in items if i['kind'] == 'coverage' and not i['cases']]
    if rest:
        L += ['', f'Plus {len(rest)} documents with articles missing that no case cites '
              f'({sum(int(re.match(r".*: (\d+) articles", i["title"]).group(1)) for i in rest):,} articles); '
              'see `.sources/report.md`.']
    L.append('')
    with open(path('priorities.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    counts = {}
    for i in items:
        counts[tier(i['score'])] = counts.get(tier(i['score']), 0) + 1
    print(f'{len(items)} items ranked -> .sources/priorities.md:',
          ', '.join(f'{counts.get(t, 0)} {t.lower()}' for t in ('Critical', 'High', 'Medium', 'Low')))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    write(*build())
