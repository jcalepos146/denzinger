# Remove or insert eras by name, renumbering every entry's era index.
import json, re, sys
R = '/home/user/denzinger/src/data/'
def load():
    return [json.loads(l.rstrip(',')) for l in open(R + 'eras.json').read().split('\n') if l.startswith('{')]
def save(eras, remap):
    open(R + 'eras.json', 'w').write('[\n' + ',\n'.join(json.dumps(e, ensure_ascii=False) for e in eras) + '\n]\n')
    s = open(R + 'entries.json').read()
    s = re.sub(r'"era": (\d+)', lambda m: f'"era": {remap[int(m.group(1))]}', s)
    open(R + 'entries.json', 'w').write(s)
def remove(names):
    eras = load(); keep = [i for i, e in enumerate(eras) if e['name'] not in names]
    remap = {old: new for new, old in enumerate(keep)}
    save([eras[i] for i in keep], remap)
def insert_after(after, new):
    eras = load(); at = next(i for i, e in enumerate(eras) if e['name'] == after) + 1
    remap = {i: (i if i < at else i + len(new)) for i in range(len(eras))}
    save(eras[:at] + new + eras[at:], remap)
if __name__ == '__main__':
    if sys.argv[1] == 'remove': remove(set(sys.argv[2:]))
