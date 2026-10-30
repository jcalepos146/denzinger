# Neuner-Dupuis number ranges: "149-153", "1439c-d", "1690/1-5", "900Aa-b", "2000a-2000d", "2244a-2252".
import re
def key(s):
    m = re.fullmatch(r'(\d+)([A-Za-z]{0,2})(?:/?(\d+))?', s.replace(' ', ''))
    if not m: return None
    return (int(m.group(1)), m.group(2).lower(), int(m.group(3)) if m.group(3) else 0, bool(m.group(3)))
def parts(spec):
    for p in re.split(r',\s*', spec or ''):
        p = p.strip().strip('()')
        if not p: continue
        if '-' not in p:
            yield key(p), key(p); continue
        a, b = [x.strip() for x in p.split('-', 1)]
        ka = key(a)
        if re.fullmatch(r'\d+', b) and '/' in a:                      # 1690/1-5
            kb = (ka[0], ka[1], int(b), True)
        elif re.fullmatch(r'[a-z]{1,2}', b):                          # 1439c-d, 900Aa-b
            base = re.match(r'(\d+[A-Z]?)', a.replace(' ', '')).group(1)
            kb = key(base + b)
        else:
            kb = key(b)
        yield ka, kb
def member(uid, spec):
    u = key(uid)
    if not u: return False
    for a, b in parts(spec):
        if not a or not b: continue
        if a[:3] <= u[:3] <= b[:3]:
            # passages numbered n/1, n/2 belong to n only when the range itself counts them
            if u[3] and not (a[3] or b[3]) and u[:2] in (a[:2], b[:2]): continue
            return True
    return False
if __name__ == '__main__':
    for uid, spec, want in [('2000d/1', '2000a-2000d', False), ('2000d', '2000a-2000d', True), ('1690/3', '1687-1689, 1690/1-5', True),
                            ('900Ab', '900Aa-b', True), ('900Ba', '900Aa-b', False), ('1439d', '1439c-d', True), ('2245', '2244a-2252', True),
                            ('2140/2', '2124-2140/2', True), ('716b', '716a-718a', True), ('718b', '716a-718a', False), ('39/5', '39/1-23', True)]:
        print(uid, spec, member(uid, spec), 'OK' if member(uid, spec) == want else 'WRONG')
