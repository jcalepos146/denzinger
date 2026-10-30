# Crawl the Roman Curia pages of vatican.va for documents in English: url and link text.
import re, html, json, urllib.request, concurrent.futures as cf
BASE = 'https://www.vatican.va'
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
    except Exception: return ''
def links(u, s):
    out = []
    for h, t in re.findall(r'(?is)<a [^>]*href="([^"#]+)"[^>]*>(.*?)</a>', s):
        h = urllib.parse.urljoin(u, h.strip())
        t = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', t))).strip()
        out.append((h, t))
    return out
import urllib.parse
seen, todo, docs = set(), [BASE + '/roman_curia/index.htm', BASE + '/roman_curia/index_en.htm'], {}
while todo:
    batch = [u for u in todo if u not in seen][:400]; todo = []
    seen.update(batch)
    with cf.ThreadPoolExecutor(12) as ex: pages = list(ex.map(get, batch))
    for u, s in zip(batch, pages):
        for h, t in links(u, s):
            if not h.startswith(BASE + '/roman_curia/') and not h.startswith(BASE + '/archive/'): continue
            if '/documents/' in h:
                if h.endswith('_en.html') or h.endswith('_en.htm'):
                    docs.setdefault(h, set()).add(t)
            elif re.search(r'(index|_en)\.html?$|/$', h) and h not in seen and len(seen) < 2500:
                todo.append(h)
json.dump({k: sorted(v) for k, v in docs.items()}, open('curia_docs.json', 'w'), indent=0, ensure_ascii=False)
print(len(seen), 'pages,', len(docs), 'English documents')
