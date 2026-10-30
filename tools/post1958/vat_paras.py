# Official text -> list of (article number, paragraph text) from a vatican.va page.
import re, html, sys, json
HEAD, HEADS, NOTE = [], [], [False]
def paras(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    s = re.sub(r'(?is)<(script|style|head)\b.*?</\1>', ' ', s)
    s = re.sub(r'(?is)<sup>.*?</sup>|<a [^>]*name="_ftnref[^"]*"[^>]*>.*?</a>|\(\d{1,3}\)', ' ', s)
    s = re.sub(r'(?i)<br\s*/?>', ' ', s)
    s = re.sub(r'(?is)</?(p|div|h\d|li|blockquote|td)\b[^>]*>', '\x01', s)   # unclosed <p> on some pages
    blocks = s.split('\x01')
    out, art = [], None
    HEAD.clear(); HEADS.clear(); NOTE[0] = False
    for b in blocks:
        t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', b))).strip()
        t = t.replace('\ufeff', '').replace('ï»¿', '').strip()
        if not t or t.startswith('PDF generation in progress'): continue
        if re.match(r'^(NOTES|Footnotes)\s*$', t, re.I): break
        if re.match(r'^[\[(]?1[\])]?\.?\s', t) and re.search(r'\b(AAS|Cf\.|cf\.|PL|PG|Mansi|Denz|ASS|op\. cit|Ibid)\b', t[:200]) and art and len(out) > 20: break
        m = re.match(r'^(\d{1,3}|\d \d{1,2})\s?\.(?:\s+(.*)|$)', t)       # "14." and the split "1 4."
        if m:
            art = int(m.group(1).replace(' ', '')); t = m.group(2) or ''
            if not t: continue
        if re.fullmatch(r'[IVXL]{1,6}\.?', t):                # a section numbered only by a Roman numeral
            R = {'I': 1, 'V': 5, 'X': 10, 'L': 50}; v = [R[c] for c in t.rstrip('.')]
            art = sum(-x if i + 1 < len(v) and x < v[i + 1] else x for i, x in enumerate(v)); continue
        if re.match(r'Preliminary Note of Explanation\s*$|COMPLEMENTARY NORMS\b', t, re.I):
            NOTE[0] = True                                  # LG's Nota praevia numbers its points 1-4 again
        if len(t) < 140 and not re.search(r'[.:;?!"”]$', t) or t.isupper() and len(t) < 200:  # heading
            if not re.search(r'\b(AR|EN|ES)\b.*-', t): HEAD.append(t)
            continue
        out.append((('NP', art) if NOTE[0] else art, t))
        HEADS.append(HEAD[-1] if HEAD else None)
    return out
if __name__ == '__main__':
    P = paras(sys.argv[1])
    print(len(P)); [print(a, t[:110]) for a, t in P[:int(sys.argv[2]) if len(sys.argv) > 2 else 12]]
