import json, sys, re
IDX = {p: json.load(open(f'idx_{p}.json')) for p in ('paul-vi', 'john-paul-ii')}
def find(pope, pat):
    for it in IDX[pope]:
        hay = it['title'] + ' ' + ' '.join(it['links'].values()) + ' ' + (it['any'] or '')
        if re.search(pat, hay, re.I):
            yield it['title'][:100], sorted(it['links']), it['links'].get('EN') or it['any']
for q in sys.argv[1:]:
    p, pat = q.split(':', 1)
    print('##', q)
    for r in list(find({'p': 'paul-vi', 'j': 'john-paul-ii'}[p], pat))[:6]: print('  ', r)
