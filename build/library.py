"""Conservative source inventory. Grouping is not a claim of document completeness."""
import hashlib
import re
from datetime import date
from urllib.parse import urlparse


COVERAGE = {'none', 'excerpts', 'summary', 'editorial', 'unreviewed', 'full-text'}


def validate_library(d, order, problems):
    seen, assigned = set(), set()
    for record in d['document_metadata']:
        where = 'documents.json, ' + str(record.get('id', '?'))
        rid = record.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9-]*', rid) or rid in seen:
            problems.add(where, 'id must be unique and use lowercase letters, numbers and hyphens')
        seen.add(rid)
        for field in ('title', 'issuer', 'genre', 'translation', 'textVerification', 'rights', 'review'):
            if not record.get(field):
                problems.add(where, 'missing ' + field)
        if record.get('coverage') not in COVERAGE:
            problems.add(where, 'unknown coverage')
        ids = record.get('entryIds', [])
        for eid in ids:
            if eid not in order or eid in assigned:
                problems.add(where, 'entry missing or assigned twice: ' + eid)
            assigned.add(eid)
        if not ids and record.get('coverage') != 'none':
            problems.add(where, 'a record without local entries must have coverage none')
        if ids and record.get('coverage') == 'none':
            problems.add(where, 'coverage none cannot contain local entries')
        if record.get('coverage') == 'full-text':
            evidence = record.get('completenessEvidence')
            fields = ('edition', 'reviewer', 'date', 'scope', 'comparison')
            if not isinstance(evidence, dict) or any(not evidence.get(f) for f in fields):
                problems.add(where, 'full-text requires completenessEvidence: edition, reviewer, date, scope and comparison')
        if record.get('date'):
            try:
                date.fromisoformat(record['date'])
            except (TypeError, ValueError):
                problems.add(where, 'date must be a valid YYYY-MM-DD date')
        if 'totalSections' in record and (not isinstance(record['totalSections'], int) or record['totalSections'] < 1):
            problems.add(where, 'totalSections must be a positive integer')
        for link in record.get('sourceLinks', []):
            parsed = urlparse(link.get('url', ''))
            if parsed.scheme != 'https' or not parsed.netloc:
                problems.add(where, 'source links must be HTTPS URLs')
            if link.get('scope') not in ('full-document', 'source-page') or not link.get('language'):
                problems.add(where, 'source links need scope and language')


def validate_relations(d, order, problems):
    entries = {e['id']: e for e in d['entries']}
    seen = set()
    for relation in d['relations']:
        where = 'relations.json, ' + str(relation.get('id', '?'))
        if not relation.get('id') or relation['id'] in seen:
            problems.add(where, 'relationship id must be unique')
        seen.add(relation.get('id'))
        a, b = relation.get('from'), relation.get('to')
        if a not in order or b not in order or a == b:
            problems.add(where, 'relationship needs two distinct existing entries')
        if relation.get('kind') not in {'quotes', 'references', 'reaffirms', 'explains', 'changes-discipline'}:
            problems.add(where, 'unknown relationship kind')
        if not relation.get('note') or relation.get('status') != 'editorial relationship':
            problems.add(where, 'relationship needs an editorial explanation and status')
        evidence = relation.get('evidence', [])
        if {e.get('entry') for e in evidence} != {a, b}:
            problems.add(where, 'quote evidence from both endpoints')
        for item in evidence:
            entry = entries.get(item.get('entry'))
            quote = re.sub(r'\s+', ' ', item.get('quote', '')).strip()
            if not entry or not quote or quote not in re.sub(r'\s+', ' ', ' '.join(entry['text'])):
                problems.add(where, 'evidence quotation is not present in the named entry')


def source_key(entry):
    """Keep dated addresses separate and never combine abbreviations across eras.

    Legacy source headings can be incomplete; inferred groups remain unreviewed.
    """
    eid = entry['id']
    m = re.fullmatch(r'([A-Z]{2,})(\d+)(?:-\d+)?', eid)
    if m:
        return ('code', entry['era'], eid if len(m[2]) >= 8 else m[1])
    if re.fullmatch(r'[A-Z]{2,}', eid):
        return ('code', entry['era'], eid)
    src = entry.get('source')
    if src:
        return ('source', entry['era'], re.sub(r'\s+', ' ', src).strip())
    return ('entry', entry['era'], eid)


def inventory(d, entry_year):
    by_id = {e['id']: e for e in d['entries']}
    records, assigned = [], set()
    for meta in d['document_metadata']:
        record = dict(meta, grouping='catalogued')
        records.append(record)
        assigned.update(record['entryIds'])
    groups = {}
    for entry in d['entries']:
        if entry['id'] not in assigned:
            groups.setdefault(source_key(entry), []).append(entry)
    for key, entries in groups.items():
        first = entries[0]
        source = first.get('source', '')
        quoted = re.search(r'["“]([^"”]+?),?["”]', source)
        rid = 'source-' + hashlib.sha256(repr(key).encode()).hexdigest()[:14]
        coverage = 'editorial' if all(e.get('note') or e['weight'] == 'note' for e in entries) else 'summary' if 'summary written for this site' in source.lower() else 'unreviewed'
        records.append(dict(id=rid, title=quoted.group(1).strip() if quoted else first.get('topic') or first['id'],
                            issuer=None, genre=None, date=None, collection='Inherited source groups',
                            entryIds=[e['id'] for e in entries], sourceLinks=[], coverage=coverage,
                            grouping='inferred', translation='Translation provenance needs document-level review',
                            textVerification='Not independently checked in this inventory',
                            rights='Reuse status not established', review={'status': 'unreviewed',
                            'note': 'Automatically grouped from collection headings; document identity and completeness need review'}))
    entry_map = {}
    for record in records:
        entries = [by_id[eid] for eid in record['entryIds']]
        record['sourceLines'] = list(dict.fromkeys(e.get('source', '') for e in entries if e.get('source')))
        record['collectionHeadings'] = list(dict.fromkeys(d['eras'][e['era']]['name'] for e in entries))
        record['kinds'] = list(dict.fromkeys(e['weight'] for e in entries))
        years = [entry_year(e, d['eras'][e['era']]) for e in entries]
        record['year'] = int(record['date'][:4]) if record.get('date') else (years[0][0] if years else None)
        record['yearExact'] = bool(record.get('date')) or bool(years and all(exact for _, exact in years))
        record['authorityNote'] = 'Document genre and issuing body do not determine the authority of every passage. Passage grades are editorial assessments; consult their reasons and the primary sources.'
        for eid in record['entryIds']:
            entry_map[eid] = record['id']
    return {'records': records, 'entryMap': entry_map, 'scope': 'All local entries, plus explicitly catalogued external documents. Inferred source groups are not a verified count of distinct documents.'}
