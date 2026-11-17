#!/usr/bin/env python3
"""Rebuild a reproducible coverage audit without network access."""
import argparse
import collections
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
from build import load_all, check, compact


def report(d):
    records = d['library']['records']
    counts = collections.Counter(r['coverage'] for r in records)
    linked = [r for r in records if any(l['scope'] == 'full-document' for l in r['sourceLinks'])]
    known = [r for r in records if r['grouping'] == 'catalogued']
    vat = [r for r in records if r['collection'] == 'Vatican II']
    lines = ['# Source coverage audit', '',
             'Reproduce with `python3 tools/audit_library.py`. This audits catalogue metadata, not the truth or authority of the texts.', '',
             f'- Local entries: {len(d["entries"])}',
             f'- Entries assigned a source record: {len(d["library"]["entryMap"])}',
             f'- Explicitly catalogued records: {len(known)}',
             f'- Inferred source groups requiring identity review: {len(records) - len(known)}',
             f'- Records with a full-document external link: {len(linked)}',
             f'- Vatican II: {len(vat)} of 16 documents catalogued; {sum(bool(r["entryIds"]) for r in vat)} have local selections.', '',
             '| Local coverage | Records |', '|---|---:|']
    lines.extend(f'| {name} | {count} |' for name, count in sorted(counts.items()))
    lines += ['', '## Limits and next reviews', '',
              '- An inferred source group is not a verified distinct document. Heading variations can split one document, and headings can cover multiple documents.',
              '- Numbered sections represented do not establish full-text coverage: selections can omit text within a section.',
              '- Source-link review is not transcription proofreading, translation approval, rights clearance, or theological review.',
              '- Older Denzinger translation attribution and reuse status remain unresolved. Existing editorial grades have not been independently re-certified.',
              '- DCE refers to both Dominicae Cenae and Deus Caritas Est in the inherited IDs. Source records separate them; the legacy document route offers a choice.',
              '- Review inherited dates against primary texts. Examples: the AS source heading says July 22, 1998, while the official Apostolos Suos page identifies May 21; ATF and DD also need date reconciliation.',
              '- Catalogue links provide access to complete texts externally; they do not add those texts to local full-text search.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='optional Markdown report path')
    args = parser.parse_args()
    data = load_all()
    order, problems = check(data)
    if problems:
        raise SystemExit('\n'.join(problems))
    compact(data, order)
    text = report(data)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding='utf-8')
    print(text)
