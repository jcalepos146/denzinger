"""Sealed research: the part of the research layer that is published only encrypted.

The plaintext lives in private/ (ignored by git): private/sealed-research.json and private/docs/*.md.
tools/seal/seal.mjs encrypts it into src/data/sealed.json, which is committed and published.
The public files carry placeholders: a case with "sealed": true, "gate": {"sealed": true}, and
continuity.json's "sealed" list of what is withheld.

When the plaintext is present, the build merges it into a copy of the data and runs every check on
that copy too, then publishes only the public data and the encrypted file. Without it (on GitHub),
the build checks the public data and passes the encrypted file through unchanged.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_DIR = os.path.join(ROOT, 'private')
PRIVATE_FILE = os.path.join(PRIVATE_DIR, 'sealed-research.json')
SEALED_FILE = os.path.join(ROOT, 'src', 'data', 'sealed.json')


def load_private():
    if not os.path.exists(PRIVATE_FILE):
        return None
    with open(PRIVATE_FILE, encoding='utf-8') as f:
        return json.load(f)


def merge_sealed(d, bundle):
    """Put the sealed research back into the data, as the reader does after unlocking."""
    k, s = d['continuity'], bundle['continuity']
    by_id = {c['id']: c for c in s['cases']}
    k['cases'] = [by_id.get(c['id'], c) if c.get('sealed') else c for c in k['cases']]
    k['gate'] = s['gate']
    k['backlog'] = sorted(k['backlog'] + s['backlog'], key=lambda b: int(b['id'][2:]))
    for ch in k['meta']['changes']:
        if ch['version'] in s.get('meta_changes', {}):
            ch['change'] = s['meta_changes'][ch['version']]
    k.pop('sealed', None)
    d['disputed'] = d['disputed'] + bundle.get('disputed', [])
    related = bundle.get('disputed_related', {})
    for q in d['disputed']:
        if q['id'] in related:
            q['related'] = related[q['id']]
    return d


def validate_sealed(d, P):
    """The public placeholders and the encrypted file agree with each other."""
    k = d['continuity']
    m = k.get('sealed')
    stubs = [c['id'] for c in k['cases'] if c.get('sealed')]
    if not m:
        if stubs or k.get('gate', {}).get('sealed'):
            P.add('continuity.json', 'sealed placeholders need the "sealed" list')
        return
    if sorted(x['id'] for x in m.get('cases', [])) != sorted(stubs):
        P.add('continuity.json, sealed', 'the sealed list and the sealed cases differ')
    for c in k['cases']:
        if c.get('sealed') and set(c) - {'id', 'group', 'title', 'sealed', 'hard_gate'}:
            P.add(f'continuity.json, {c["id"]}', 'a sealed case must hold only its id, group, title and hard_gate: the rest belongs in private/')
    disp = {q['id'] for q in d['disputed']}
    for x in m.get('disputed', []):
        if x['id'] in disp:
            P.add('disputed.json', f'{x["id"]} is listed as sealed but is still public')
    if not os.path.exists(SEALED_FILE):
        P.add('src/data/sealed.json', 'missing: run node tools/seal/seal.mjs seal')
    else:
        with open(SEALED_FILE, encoding='utf-8') as f:
            s = json.load(f)
        if s.get('format') != 'eodem-sealed' or s.get('cipher', {}).get('name') != 'AES-GCM':
            P.add('src/data/sealed.json', 'not a sealed research file')


def stale_note():
    """A note when private/ has changed since the encrypted file was written."""
    if not os.path.exists(PRIVATE_FILE) or not os.path.exists(SEALED_FILE):
        return None
    newest = max(os.path.getmtime(os.path.join(dp, f)) for dp, _, fs in os.walk(PRIVATE_DIR) for f in fs)
    if newest > os.path.getmtime(SEALED_FILE):
        return 'private/ has changed since src/data/sealed.json was sealed: run node tools/seal/seal.mjs seal'
    return None
