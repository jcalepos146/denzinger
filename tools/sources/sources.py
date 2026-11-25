#!/usr/bin/env python3
"""Find the texts the site lacks, download them from their sources, and report what is missing.

    python3 tools/sources/sources.py gaps              # list what is missing -> .sources/todo.json
    python3 tools/sources/sources.py fetch [--only cd pc] [--limit 5] [--refresh]
    python3 tools/sources/sources.py extract           # pages -> numbered articles
    python3 tools/sources/sources.py diff              # -> .sources/report.md and .sources/drafts/
    python3 tools/sources/sources.py all               # the four in order
    python3 tools/sources/sources.py status

Everything it writes goes in .sources/, which git ignores. It never changes
src/data: drafts are for an editor to check and copy in by hand, and a
downloaded text is kept for checking, not cleared for publication (see the
"rights" of each record). It uses only the standard library, like the build.

Sources are limited to official and public-domain hosts (vatican.va,
archive.org and a few reference sites); anything else is listed as manual.
It obeys robots.txt and waits at least two seconds between requests to a host.
"""
import argparse
import datetime
import difflib
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paras as P  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, 'src', 'data')
OUT = os.path.join(ROOT, '.sources')
AGENT = 'Mozilla/5.0 (compatible; source fetcher for a static reader of Denzinger)'
MIN_DELAY = 2.0

# Hosts the fetcher will download from, and what is known of their texts' standing.
HOSTS = {
    'www.vatican.va': {'adapter': 'html', 'rights': 'Official Holy See text; reuse permission not established. Kept locally for checking.'},
    'archive.org': {'adapter': 'archive', 'rights': 'See the item\'s own copyright status in provenance.json.'},
    'www.newadvent.org': {'adapter': 'html', 'rights': 'Reference copy; check the edition it reproduces before reuse.'},
    'www.papalencyclicals.net': {'adapter': 'html', 'rights': 'Reference copy; check the translation it reproduces before reuse.'},
    'www.ewtn.com': {'adapter': 'html', 'rights': 'Reference copy; check the translation it reproduces before reuse.'},
}
MONTHS = ['Jan.', 'Feb.', 'March', 'April', 'May', 'June', 'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']


# ---------------------------------------------------------------- files

def path(*parts):
    return os.path.join(OUT, *parts)


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def write_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def data(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


def safe(rid):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', rid)


# ---------------------------------------------------------------- gaps

def local_articles(ids):
    """The prefix and article numbers of entry ids such as LG25, LG4 (LGNP and the like are skipped)."""
    prefixes, arts = set(), set()
    for i in ids:
        m = re.fullmatch(r'([A-Z]+)(\d+)', i)
        if m:
            prefixes.add(m.group(1))
            arts.add(int(m.group(2)))
    return (prefixes.pop() if len(prefixes) == 1 else None), arts


def initials(title, taken):
    words = [w for w in re.findall(r"[A-Za-z]+", title) if w[0].isupper()]
    guess = ''.join(w[0] for w in words).upper()
    if guess and guess not in taken:
        return guess, False
    return ''.join(w[:2] for w in words).upper(), True


def gaps(args):
    records, entries = data('documents.json'), data('entries.json')
    taken = {m.group(1) for e in entries for m in [re.fullmatch(r'([A-Z]+)\d+', e['id'])] if m}
    todo = []
    for r in records:
        if r.get('coverage') not in ('none', 'excerpts'):
            continue
        links = [l for l in r.get('sourceLinks', []) if l.get('scope') == 'full-document'] or r.get('sourceLinks', [])
        link = next((l for l in links if urllib.parse.urlparse(l['url']).netloc in HOSTS), None)
        prefix, arts = local_articles(r.get('entryIds', []))
        item = {
            'id': r['id'], 'title': r['title'], 'date': r.get('date'), 'genre': r.get('genre'),
            'kind': 'no-text' if r['coverage'] == 'none' else 'excerpts',
            'url': link['url'] if link else None,
            'host': urllib.parse.urlparse(link['url']).netloc if link else None,
            'status': 'auto' if link else 'manual',
            'localArticles': sorted(arts), 'totalSections': r.get('totalSections'),
            'rights': r.get('rights'),
        }
        if prefix:
            item['prefix'] = prefix
        elif r['coverage'] == 'none':
            item['prefix'], item['prefixNeedsReview'] = initials(r['title'], taken)
        if not link:
            item['why'] = 'No link to a host the fetcher uses: ' + ', '.join(l['url'] for l in links) if links else 'No source link'
        todo.append(item)
    for b in data('continuity.json').get('backlog', []):
        todo.append({'id': 'research-' + b['id'], 'title': b['what'], 'kind': 'research', 'status': 'manual',
                     'why': b['need'], 'cases': b.get('cases', [])})
    write_json(path('todo.json'), todo)
    counts = {}
    for t in todo:
        counts[(t['kind'], t['status'])] = counts.get((t['kind'], t['status']), 0) + 1
    print(f'{len(todo)} gaps written to .sources/todo.json')
    for (kind, status), n in sorted(counts.items()):
        print(f'  {kind:9} {status:6} {n}')
    return todo


# ---------------------------------------------------------------- fetch

class Fetcher:
    def __init__(self):
        self.robots, self.last = {}, {}

    def allowed(self, url):
        u = urllib.parse.urlparse(url)
        rp = self.robots.get(u.netloc)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                body = self.get(f'{u.scheme}://{u.netloc}/robots.txt', check=False).decode('utf-8', 'replace')
                rp.parse(body.splitlines())
            except Exception:
                rp.parse([])  # no robots.txt: allowed
            self.robots[u.netloc] = rp
        return rp.can_fetch(AGENT, url)

    def wait(self, host):
        rp = self.robots.get(host)
        delay = max(MIN_DELAY, float((rp.crawl_delay(AGENT) if rp else None) or 0))
        gap = time.monotonic() - self.last.get(host, -1e9)
        if gap < delay:
            time.sleep(delay - gap)
        self.last[host] = time.monotonic()

    def get(self, url, check=True, meta=None):
        if check and not self.allowed(url):
            raise PermissionError('robots.txt disallows ' + url)
        host = urllib.parse.urlparse(url).netloc
        for attempt in range(3):
            self.wait(host)
            req = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': '*/*'})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                    if meta is not None:
                        meta.update(finalUrl=r.geturl(), status=r.status, contentType=r.headers.get('Content-Type'))
                    return body
            except urllib.error.HTTPError as err:
                if err.code in (429, 503) and attempt < 2:
                    time.sleep(min(int(err.headers.get('Retry-After') or 10 * (attempt + 1)), 120))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))


def archive_item(url):
    m = re.match(r'https?://archive\.org/(?:details|download|stream)/([^/?#]+)', url)
    return m.group(1) if m else None


def fetch_one(f, t):
    meta = {'id': t['id'], 'source': t['url'], 'fetched': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'rights': HOSTS[t['host']]['rights']}
    if HOSTS[t['host']]['adapter'] == 'archive':
        item = archive_item(t['url'])
        if not item:
            raise ValueError('not an archive.org item address')
        md = json.loads(f.get(f'https://archive.org/metadata/{item}'))
        m = md.get('metadata', {})
        meta['item'] = {k: m.get(k) for k in ('title', 'date', 'year', 'creator', 'possible-copyright-status', 'licenseurl')}
        if not m.get('possible-copyright-status') and not m.get('licenseurl'):
            meta['rights'] += ' The item states no copyright status: check it before reuse.'
        txt = next((x['name'] for x in md.get('files', []) if x['name'].endswith('_djvu.txt')), None)
        if not txt:
            raise ValueError('the archive.org item has no full-text (_djvu.txt) file')
        url = f'https://archive.org/download/{item}/{urllib.parse.quote(txt)}'
        body, ext = f.get(url, meta=meta), 'txt'
    else:
        body = f.get(t['url'], meta=meta)
        ext = 'html'
    name = f'{safe(t["id"])}.{ext}'
    os.makedirs(path('raw'), exist_ok=True)
    with open(path('raw', name), 'wb') as out:
        out.write(body)
    meta.update(file=f'raw/{name}', bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    return meta


def selected(todo, args):
    for t in todo:
        if args.only and t['id'] not in args.only:
            continue
        yield t


def fetch(args):
    todo = read_json(path('todo.json')) or gaps(args)
    prov = read_json(path('provenance.json'), {})
    f, done, failed, skipped = Fetcher(), 0, [], 0
    for t in selected(todo, args):
        if t['status'] != 'auto':
            continue
        if t['id'] in prov and not args.refresh and os.path.exists(path(prov[t['id']]['file'])):
            skipped += 1
            continue
        if args.limit and done >= args.limit:
            break
        try:
            prov[t['id']] = fetch_one(f, t)
            done += 1
            print(f'  fetched {t["id"]:28} {prov[t["id"]]["bytes"]:>9,} bytes  {t["url"]}')
        except Exception as err:
            failed.append((t['id'], str(err)[:160]))
            print(f'  failed  {t["id"]:28} {str(err)[:160]}')
        write_json(path('provenance.json'), prov)  # after each, so an interrupted run keeps its work
    old = read_json(path('failed.json'), {})
    old = {k: v for k, v in old.items() if k not in prov}
    old.update(dict(failed))
    write_json(path('failed.json'), old)
    print(f'{done} fetched, {skipped} already cached, {len(failed)} failed')
    return failed


# ---------------------------------------------------------------- extract

def extract(args):
    todo = {t['id']: t for t in read_json(path('todo.json'), [])}
    prov = read_json(path('provenance.json'), {})
    n = 0
    for rid, meta in prov.items():
        if args.only and rid not in args.only:
            continue
        with open(path(meta['file']), 'rb') as fh:
            raw = fh.read().decode('utf-8', 'replace')
        if meta['file'].endswith('.txt'):
            out = {'id': rid, 'structured': False, 'chars': len(raw),
                   'note': 'Scanned book text (OCR); not split into articles. Find the passage by hand.'}
        else:
            total = (todo.get(rid) or {}).get('totalSections')
            ps = P.paras(raw, max_article=max(total or 0, 999))
            arts = P.articles(ps)
            heads = {}
            for p in ps:
                if isinstance(p['art'], int) and p['head']:
                    heads.setdefault(p['art'], p['head'])
            out = {'id': rid, 'structured': True, 'articles': {str(k): v for k, v in sorted(arts.items())},
                   'heads': {str(k): v for k, v in heads.items()}, 'unnumbered': sum(1 for p in ps if p['art'] is None)}
        write_json(path('text', safe(rid) + '.json'), out)
        n += 1
    print(f'{n} texts extracted to .sources/text/')


# ---------------------------------------------------------------- diff

def norm(s):
    """Lower-case words only. Bare numbers are dropped: footnote markers survive in some pages
    in forms the splitter cannot tell from text, and a difference in a number alone is rare."""
    s = s.lower().replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return ' '.join(w for w in re.findall(r"[a-z0-9]+", s) if not w.isdigit())


def fragments(paragraphs):
    """The pieces of a local entry between the "..." that mark omissions."""
    for p in paragraphs:
        for frag in re.split(r'\.\.\.|…|\[\.+\]', p):
            n = norm(frag)
            if len(n) >= 40:
                yield frag.strip(), n


def check_entry(entry, source_text):
    """Fragments of a local entry that are not found word for word in the source article."""
    bad = []
    for frag, n in fragments(entry.get('text', [])):
        if n in source_text:
            continue
        sm = difflib.SequenceMatcher(None, n, source_text, autojunk=False)
        m = sm.find_longest_match(0, len(n), 0, len(source_text))
        lo = max(0, m.b - m.a)
        ratio = difflib.SequenceMatcher(None, n, source_text[lo:lo + len(n) + 40], autojunk=False).ratio()
        bad.append({'fragment': frag[:160], 'similarity': round(ratio, 2)})
    return bad


def source_line(t):
    try:
        y, mo, d = (int(x) for x in t['date'].split('-'))
        when = f'{MONTHS[mo - 1]} {d}, {y}'
    except Exception:
        when = t.get('date') or 'date unknown'
    genre = t.get('genre') or 'Document'
    return f'[From the {genre}, "{t["title"]}," {when}]'


def diff(args):
    todo = {t['id']: t for t in read_json(path('todo.json'), [])}
    prov = read_json(path('provenance.json'), {})
    entries = {e['id']: e for e in data('entries.json')}
    records = {r['id']: r for r in data('documents.json')}
    rows, unstructured = [], []
    for rid, meta in sorted(prov.items()):
        if args.only and rid not in args.only:
            continue
        text = read_json(path('text', safe(rid) + '.json'))
        t = todo.get(rid)
        if not text or not t:
            continue
        if not text['structured']:
            unstructured.append((rid, t, text))
            continue
        fetched = {int(k): v for k, v in text['articles'].items()}
        local = set(t['localArticles'])
        prefix = t.get('prefix')
        if not prefix or not fetched:
            rows.append(whole_document(rid, t, text, records[rid], entries))
            continue
        missing = sorted(set(fetched) - local)
        not_found = sorted(local - set(fetched))
        mismatches = {}
        for a in sorted(local & set(fetched)):
            e = entries.get(f'{prefix}{a}')
            if e:
                bad = check_entry(e, norm(' '.join(fetched[a])))
                if bad:
                    mismatches[a] = bad
        # draft entries for the missing articles, shaped like src/data/entries.json
        sibling = next((entries[i] for i in records[rid].get('entryIds', []) if i in entries), None)
        drafts = []
        for a in missing:
            drafts.append({
                'id': f'{prefix}{a}',
                'era': sibling['era'] if sibling else None,
                'topic': text['heads'].get(str(a)) or (sibling or {}).get('topic') or t['title'],
                'source': sibling['source'] if sibling else source_line(t),
                'text': fetched[a],
                '_draft': {'record': rid, 'from': meta['source'], 'fetched': meta['fetched'], 'sha256': meta['sha256'],
                           'rights': meta['rights'], 'needs': ['era' if not sibling else None, 'weight', 'kinds',
                                                              'prefix' if t.get('prefixNeedsReview') else None]},
            })
            drafts[-1]['_draft']['needs'] = [x for x in drafts[-1]['_draft']['needs'] if x]
        if drafts:
            write_json(path('drafts', safe(rid) + '.json'), drafts)
        rows.append({'id': rid, 'title': t['title'], 'kind': t['kind'], 'fetched': len(fetched), 'local': len(local),
                     'total': t.get('totalSections'), 'missing': missing, 'notFound': not_found,
                     'mismatches': mismatches, 'drafts': len(drafts), 'prefix': prefix,
                     'prefixNeedsReview': t.get('prefixNeedsReview', False)})
    write_json(path('report.json'), rows)
    write_report(rows, unstructured, todo, prov)
    print(f'{len(rows)} documents compared; {sum(r["drafts"] for r in rows)} draft entries; '
          f'{sum(len(r["mismatches"]) for r in rows)} local articles differ from their source. See .sources/report.md')
    return rows


def whole_document(rid, t, text, record, entries):
    """Records whose entries are not numbered by article (old Denzinger numbers, addresses by date,
    one entry for a whole text) or whose page has no article numbers: look for each local entry
    anywhere in the document. No drafts: what is missing cannot be told article by article."""
    if text['articles']:
        body = ' '.join(p for v in text['articles'].values() for p in v)
    else:
        with open(path('raw', safe(rid) + '.html'), 'rb') as fh:
            body = ' '.join(P.blocks(fh.read().decode('utf-8', 'replace')))
    src = norm(body)
    found, close, other = 0, {}, 0
    for eid in record.get('entryIds', []):
        e = entries.get(eid)
        if not e:
            continue
        bad = check_entry(e, src) if len(src) < 400_000 else []
        if not bad:
            found += 1
        elif max(b['similarity'] for b in bad) >= 0.85:
            close[eid] = [b for b in bad if b['similarity'] >= 0.85]
        else:
            other += 1
    return {'id': rid, 'title': t['title'], 'kind': t['kind'], 'mode': 'whole-document',
            'fetched': len(text['articles']), 'local': len(record.get('entryIds', [])), 'total': t.get('totalSections'),
            'missing': [], 'notFound': [], 'mismatches': close, 'drafts': 0, 'prefix': '',
            'prefixNeedsReview': False, 'entriesFound': found, 'entriesOtherText': other}


def ranges(ns):
    out, start, prev = [], None, None
    for n in ns + [None]:
        if start is not None and (n is None or n != prev + 1):
            out.append(str(start) if start == prev else f'{start}-{prev}')
            start = None
        if n is not None and start is None:
            start = n
        prev = n
    return ', '.join(out) or '-'


def write_report(rows, unstructured, todo, prov):
    L = ['# Source gaps', '', f'Generated {datetime.date.today().isoformat()} by `tools/sources/sources.py diff`. '
         'Drafts are in `.sources/drafts/`; nothing in `src/data` was changed. A downloaded text is not cleared for '
         'publication: see each record\'s rights.', '',
         '| Record | Kind | Articles at source | Local | Missing locally | Drafts | Local text differs |',
         '|---|---|---:|---:|---|---:|---:|']
    whole = [r for r in rows if r.get('mode') == 'whole-document']
    rows = [r for r in rows if r.get('mode') != 'whole-document']
    for r in sorted(rows, key=lambda r: (-len(r['missing']), r['id'])):
        flag = ' (prefix to choose)' if r['prefixNeedsReview'] else ''
        L.append(f'| {r["id"]} {r["title"]}{flag} | {r["kind"]} | {r["fetched"]} | {r["local"]} | {ranges(r["missing"])} '
                 f'| {r["drafts"]} | {len(r["mismatches"])} |')
    odd = [r for r in rows if r['notFound'] or (r['total'] and r['total'] != r['fetched'])]
    if odd:
        L += ['', '## Numbering to check', '',
              'Articles the site has that were not found at the source, or a source whose count differs from `totalSections`. '
              'Usually the page splitter missed a number; sometimes the local id is wrong.', '']
        for r in odd:
            L.append(f'- **{r["id"]}**: not found at source: {ranges(r["notFound"])}; totalSections {r["total"]}, found {r["fetched"]}')
    if whole:
        L += ['', '## Compared as whole documents', '',
              'Entries not numbered by article (old Denzinger numbers, addresses by date), or pages without article numbers. '
              'Each local entry is looked for anywhere in the text; no drafts are made. "Other text" means a different '
              'translation or language (for example the Deferrari English against a Latin or newer English page).', '',
              '| Record | Local entries | Found word for word | Nearly (check) | Other text |', '|---|---:|---:|---:|---:|']
        for r in sorted(whole, key=lambda r: r['id']):
            L.append(f'| {r["id"]} {r["title"]} | {r["local"]} | {r["entriesFound"]} | {len(r["mismatches"])} | {r["entriesOtherText"]} |')
    failed = read_json(path('failed.json'), {})
    if failed:
        L += ['', '## Downloads that failed', '',
              'A certificate error means the site sends an incomplete certificate chain; the fetcher does not turn checking off. '
              'Save the page by hand as `.sources/raw/<id>.html` and add it to `provenance.json`, or link a better source.', '']
        for rid, why in sorted(failed.items()):
            L.append(f'- **{rid}** {todo.get(rid, {}).get("url", "")}: {why}')
    diffs = [r for r in rows + whole if r['mismatches']]
    if diffs:
        L += ['', '## Local text that differs from its source', '',
              'Fragments (between omission marks) not found word for word in the official article. '
              'Similarity near 1 is usually punctuation or a typo; low similarity may be a different translation.', '']
        for r in diffs:
            for a, bad in r['mismatches'].items():
                for b in bad[:3]:
                    L.append(f'- {r["prefix"]}{a} ({b["similarity"]}): "{b["fragment"]}"')
    if unstructured:
        L += ['', '## Scanned books', '']
        for rid, t, text in unstructured:
            L.append(f'- **{rid}** {t["title"]}: {text["chars"]:,} characters of OCR text in `.sources/{prov[rid]["file"]}`. '
                     f'{text["note"]} Rights: {prov[rid]["rights"]}')
    manual = [t for t in todo.values() if t['status'] == 'manual']
    if manual:
        L += ['', '## Needs finding by hand', '']
        for t in manual:
            L.append(f'- **{t["id"]}** {t["title"]}: {t.get("why", "")}')
    L.append('')
    with open(path('report.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))


# ---------------------------------------------------------------- editions

PD_BEFORE = 1931  # published before this year: public domain in the United States, where archive.org serves it


def phrase(words):
    """A pattern for a phrase in OCR text: any spacing, u for v, ae printed as æ or e, and the long s
    of older printings, which OCR reads as f (Haec fancta)."""
    parts = []
    for w in words.split():
        parts.append(re.escape(w.lower()).replace('v', '[uv]').replace('ae', '(?:ae|æ|e)').replace('s', '[sfſ]'))
    return re.compile(r'[\s\-]+'.join(parts), re.I)


def locate(text, finds, pages=None, limit=5):
    """How often each phrase occurs in the text, with the words around it. `pages(words)`, when given,
    returns the page (leaf) of each hit from archive.org's own search inside the book."""
    text = re.sub(r'(\w)-[ \t]*\r?\n\s*(\w)', r'\1\2', text)  # rejoin words hyphenated across lines
    out = {}
    for words in finds:
        found = list(phrase(words).finditer(text))
        hits = [{'snippet': re.sub(r'\s+', ' ', text[max(0, m.start() - 120):m.end() + 200]).strip()} for m in found[:limit]]
        if found and pages:
            try:  # ask for the spellings the OCR actually has (Dudum facrum), not the modern one
                leaves, seen = [], set()
                for m in found:
                    s = re.sub(r'\s+', ' ', m.group(0))
                    if s.lower() not in seen and len(leaves) < limit:
                        seen.add(s.lower())
                        leaves += [x for x in pages(s) if x['leaf'] not in {y['leaf'] for y in leaves}]
                leaves = leaves[:limit]
                for h, leaf in zip(hits, leaves):
                    h.update(leaf)
                hits += leaves[len(hits):]
            except Exception as err:  # the search service is optional: the count stands without it
                hits.append({'note': f'page search unavailable: {str(err)[:80]}'})
        out[words] = {'count': len(found), 'hits': hits}
    return out


def inside(f, meta):
    """archive.org's search inside a book (what its viewer uses): the leaf of each hit and a link to its scan."""
    def pages(words):
        q = urllib.parse.urlencode({'item_id': meta['item'], 'doc': meta['doc'], 'path': meta['dir'], 'q': f'"{words}"'})
        d = json.loads(f.get(f'https://{meta["server"]}/fulltext/inside.php?{q}', check=False))
        out = []
        for m in d.get('matches', []):
            leaf = m['par'][0]['page']
            out.append({'leaf': leaf, 'scan': f'https://archive.org/details/{meta["item"]}/page/n{leaf}/mode/1up',
                        'ocr': re.sub(r'</?IA_FTS_MATCH>', '', m['text'])[:300]})
        return out
    return pages


def editions(args):
    spec = json.load(open(os.path.join(HERE, 'editions.json'), encoding='utf-8'))
    done = read_json(path('editions.json'), {})
    f = Fetcher()
    for t in spec['targets']:
        if args.only and t['id'] not in args.only:
            continue
        res = {'title': t['title'], 'cases': t['cases'], 'sources': []}
        for s in t['sources']:
            r = {'label': s['label']}
            try:
                if 'archive' in s:
                    item = s['archive']
                    r['source'] = f'https://archive.org/details/{item}'
                    if s.get('published', 0) >= PD_BEFORE:
                        raise PermissionError(f'published {s["published"]}: not certainly in the public domain; consult it by hand')
                    fn = path('editions', safe(item) + '.txt')
                    meta_fn = fn + '.meta.json'
                    if not os.path.exists(fn) or not os.path.exists(meta_fn) or 'server' not in read_json(meta_fn, {}) or args.refresh:
                        md = json.loads(f.get(f'https://archive.org/metadata/{item}'))
                        m = md.get('metadata', {})
                        txt = next((x['name'] for x in md.get('files', []) if x['name'].endswith('_djvu.txt')), None)
                        if not txt:
                            raise ValueError('no OCR text (_djvu.txt) in this item')
                        body = f.get(f'https://archive.org/download/{item}/{urllib.parse.quote(txt)}')
                        os.makedirs(path('editions'), exist_ok=True)
                        with open(fn, 'wb') as out:
                            out.write(body)
                        write_json(meta_fn, {'item': item, 'server': md.get('server'), 'dir': md.get('dir'), 'doc': txt[:-len('_djvu.txt')],
                                             'title': m.get('title'), 'volume': m.get('volume'),
                                             'date': m.get('date') or m.get('year'), 'copyright': m.get('possible-copyright-status'),
                                             'fetched': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                                             'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
                        print(f'  fetched {item:32} {len(body):>11,} bytes')
                    r['meta'] = read_json(meta_fn)
                    with open(fn, 'rb') as fh:
                        text = fh.read().decode('utf-8', 'replace')
                    r['file'] = os.path.relpath(fn, OUT).replace(os.sep, '/')
                    r['rights'] = f'Published {s["published"]}; public domain in the United States.'
                    r['found'] = locate(text, t['find'], inside(f, r['meta']) if r['meta'].get('server') else None)
                else:
                    r['source'] = s['url']
                    fn = path('editions', safe(t['id']) + '.html')
                    if not os.path.exists(fn) or args.refresh:
                        body = f.get(s['url'])
                        os.makedirs(path('editions'), exist_ok=True)
                        with open(fn, 'wb') as out:
                            out.write(body)
                        print(f'  fetched {t["id"]:32} {len(body):>11,} bytes')
                    with open(fn, 'rb') as fh:
                        text = '\n'.join(P.blocks(fh.read().decode('utf-8', 'replace')))
                    r['file'] = os.path.relpath(fn, OUT).replace(os.sep, '/')
                    r['rights'] = HOSTS.get(urllib.parse.urlparse(s['url']).netloc, {}).get(
                        'rights', 'Official Holy See text; reuse permission not established. Kept locally for checking.')
                    r['found'] = locate(text, t['find'])
            except Exception as err:
                r['error'] = str(err)[:200]
                print(f'  failed  {t["id"]:32} {r["error"]}')
            res['sources'].append(r)
        res['located'] = any(any(v['count'] for v in r.get('found', {}).values()) for r in res['sources'])
        done[t['id']] = res
        write_json(path('editions.json'), done)
    write_editions_report(done, spec)
    print(f'{sum(r["located"] for r in done.values())} of {len(done)} texts located; see .sources/editions.md')


def write_editions_report(done, spec):
    L = ['# Primary-source editions', '', 'Generated by `tools/sources/sources.py editions` from `tools/sources/editions.json`. '
         'OCR of old printings is imperfect: a phrase not found may still be there in another spelling, and a hit '
         'must be read on the page scan before it is cited.', '']
    for tid, r in done.items():
        L.append(f'## {r["title"]} ({", ".join(r["cases"])})')
        L.append('')
        L.append('Located.' if r['located'] else '**Not located** in the sources tried.')
        for s in r['sources']:
            L.append(f'- {s["label"]}: {s["source"]}' + (f' (error: {s["error"]})' if s.get('error') else ''))
            for words, v in s.get('found', {}).items():
                if v['count']:
                    first = v['hits'][0]
                    where = f'[page n{first["leaf"]}]({first["scan"]})' if first.get('scan') else 'in the page'
                    L.append(f'  - "{words}": {v["count"]} times; first {where}: "...{first["snippet"][:220]}..."')
                else:
                    L.append(f'  - "{words}": not found')
        L.append('')
    L += ['## To consult by hand', '']
    for m in spec.get('manual', []):
        L.append(f'- **{m["title"]}** ({", ".join(m["cases"])}): {m["where"]}')
    L.append('')
    with open(path('editions.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))


# ---------------------------------------------------------------- cli

def status(args):
    todo = read_json(path('todo.json'), [])
    prov = read_json(path('provenance.json'), {})
    texts = len(os.listdir(path('text'))) if os.path.isdir(path('text')) else 0
    print(f'{len(todo)} gaps, {sum(t["status"] == "auto" for t in todo)} fetchable; {len(prov)} fetched; {texts} extracted')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['gaps', 'fetch', 'extract', 'diff', 'all', 'status', 'editions'])
    ap.add_argument('--only', nargs='+', help='record ids to work on')
    ap.add_argument('--limit', type=int, help='fetch at most this many documents')
    ap.add_argument('--refresh', action='store_true', help='download again even if cached')
    a = ap.parse_args(argv)
    if a.command in ('gaps', 'all'):
        gaps(a)
    if a.command in ('fetch', 'all'):
        fetch(a)
    if a.command in ('extract', 'all'):
        extract(a)
    if a.command in ('diff', 'all'):
        diff(a)
    if a.command == 'editions':
        editions(a)
    if a.command == 'status':
        status(a)


if __name__ == '__main__':
    main()
