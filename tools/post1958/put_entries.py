# Replace the entries of the named eras in src/data/entries.json, placing them after the given era.
import json, sys
R = '/home/user/denzinger/src/data/'
def era_index():
    eras = [json.loads(l.rstrip(',\n')) for l in open(R + 'eras.json') if l.startswith('{')]
    return {e['name']: i for i, e in enumerate(eras)}
def put(new, after):
    EI = era_index()
    names = {e['era'] for e in new}
    idx = {EI[n] for n in names}
    src = [l for l in open(R + 'entries.json').read().split('\n')]
    keep = [l for l in src if not (l.startswith('{') and json.loads(l.rstrip(',\n'))['era'] in idx)]
    lines = []
    for e in new:
        e = dict(e); e['era'] = EI[e['era']]
        if 'dsND' in e: e['ds'] = e.pop('dsND')
        lines.append(json.dumps({k: e[k] for k in ['id', 'era', 'topic', 'source', 'text', 'weight', 'ds', 'nd'] if k in e}, ensure_ascii=False) + ',')
    last = max(i for i, l in enumerate(keep) if l.startswith('{') and json.loads(l.rstrip(',\n'))['era'] == EI[after])
    open(R + 'entries.json', 'w').write('\n'.join(keep[:last + 1] + lines + keep[last + 1:]))
    return len(lines)
if __name__ == '__main__':
    E1 = json.load(open('entries1.json'))
    for e in E1: e['era'] = {119: 'John XXIII', 120: 'The Second Vatican Council'}.get(e['era'], e['era'])
    print(put(E1, 'Pius XII'))
    print(put(json.load(open('entries2.json')), 'The Second Vatican Council'))
