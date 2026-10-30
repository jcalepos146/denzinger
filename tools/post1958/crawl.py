# Crawl the vatican.va indexes of a pope: every document with its title, date and language links.
import re, html, json, sys, os, urllib.request, concurrent.futures as cf
BASE = 'https://www.vatican.va'
def get(path):
    fn = '../vat/idx/' + re.sub(r'[^a-z0-9]+', '_', path.lower()) + '.html'
    if os.path.exists(fn): return open(fn, encoding='utf-8', errors='replace').read()
    req = urllib.request.Request(BASE + path, headers={'User-Agent': 'Mozilla/5.0'})
    try: s = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
    except Exception as e: s = ''
    open(fn, 'w').write(s); return s
def items(s):
    out = []
    for blk in re.findall(r'(?s)<div class="item">(.*?)</div>\s*</div>', s):
        h = re.search(r'(?s)<h2>(.*?)</h2>', blk)
        links = dict((l.upper(), u) for u, l in re.findall(r'<a href="([^"]+/documents/[^"]+)"[^>]*>\s*([A-Z]{2})\s*</a>', blk))
        a = re.search(r'<a href="([^"]+/documents/[^"]+)"', blk)
        if h or links:
            out.append({'title': re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', h.group(1) if h else ''))).strip(),
                        'links': links, 'any': a.group(1) if a else None})
    return out
def crawl(pope, years):
    seen, todo, docs = set(), [], []
    types = ['encyclicals', 'apost_exhortations', 'apost_letters', 'apost_constitutions', 'motu_proprio', 'bulls',
             'speeches', 'homilies', 'messages', 'letters', 'audiences']
    todo = [f'/content/{pope}/en/{t}.index.html' for t in types]
    while todo:
        batch, todo = todo, []
        with cf.ThreadPoolExecutor(12) as ex:
            pages = list(ex.map(get, batch))
        for path, s in zip(batch, pages):
            seen.add(path)
            for it in items(s): it['index'] = path; docs.append(it)
            for sub in set(re.findall(rf'href="(/content/{pope}/en/[a-z_]+/[^"]*?\.index(?:\.\d+)?\.html)"', s)):
                y = re.search(r'/(\d{4})[./]', sub)
                if sub in seen or sub in todo or sub in batch: continue
                if y and int(y.group(1)) not in years: continue
                todo.append(sub)
    uniq = {}
    for d in docs:
        k = d['any'] or d['title']
        uniq[k] = d
    return list(uniq.values())
if __name__ == '__main__':
    pope, y0, y1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    D = crawl(pope, set(range(y0, y1 + 1)))
    json.dump(D, open(f'idx_{pope}.json', 'w'), ensure_ascii=False, indent=0)
    print(pope, len(D), 'documents;', sum(1 for d in D if 'EN' in d['links']), 'in English')
