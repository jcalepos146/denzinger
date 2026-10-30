# Split Neuner-Dupuis into numbered units, chapter by chapter.
# ND numbers follow the chapter (ch. XXI holds 2101-2199), which tells them from DS margin numbers.
import re, json, sys
L = open(sys.argv[1]).read().split('\n')
heads = [3198, 5808, 7643, 8611, 9968, 10806, 13551, 14386, 17357, 19285, 21236, 23341, 25215,
         25956, 27190, 29239, 31907, 33852, 34999, 37575, 39486, 42570, 44187]
end = next(i for i, l in enumerate(L) if re.search(r'^\s*CHRONOLOGICAL\s+TABLE OF DOCUMENTS\s*$', l))
bounds = [(0, 2000, 3198)] + [(k + 1, heads[k] - 1, (heads + [end + 1])[k + 1] - 1) for k in range(len(heads))]
start_re = re.compile(r'^\s{0,10}(\d{1,4})(?:\s?([A-Z][a-z]|[a-z]{1,2}\d?))?(?:\s?/\s?(\d{1,2}))?(?![\d/])[\s_—=‘’\'"“\-~.]*(.*)$')
head_re = re.compile(r'^\s*(\d{1,4}\s+)?[A-Z][A-Z ,\'’—\-]{6,}[A-Z](\s+\S{1,5})?\s*$')
def key(m): return (int(m.group(1)), (m.group(2) or '').lower(), int(m.group(3) or 0))
units = []
for ch, a, b in bounds:
    cands = []
    for i in range(a, b):
        l = L[i]
        if re.search(r'THE CHRISTIAN\s+FAITH', l): continue
        m = start_re.match(l)
        if not m or not m.group(4).strip() or re.match(r'\s*[),;]', l[m.end(3) if m.group(3) else (m.end(2) if m.group(2) else m.end(1)):]): continue
        n = int(m.group(1))
        inch = (n // 100 == ch) or (ch == 0 and n < 100) or (ch == 19 and n == 2000)
        if inch and not head_re.match(l):
            cands.append((key(m), i, m))
    # longest non-decreasing run of ids drops stray margin numbers
    best, prev = [1] * len(cands), [-1] * len(cands)
    for j in range(len(cands)):
        for q in range(max(0, j - 40), j):
            if cands[q][0] <= cands[j][0] and best[q] + 1 > best[j]:
                best[j], prev[j] = best[q] + 1, q
    j = max(range(len(cands)), key=lambda x: best[x]) if cands else -1
    keep = []
    while j >= 0: keep.append(cands[j]); j = prev[j]
    keep.reverse()
    for x, (k, i, m) in enumerate(keep):
        stop = keep[x + 1][1] if x + 1 < len(keep) else b
        sid = m.group(1) + (m.group(2) or '') + ('/' + m.group(3) if m.group(3) else '')
        units.append({'id': sid, 'ch': ch, 'line': i, 'lines': [m.group(4)] + L[i + 1:stop]})
json.dump(units, open('units.json', 'w'), ensure_ascii=False)
print(len(units))
