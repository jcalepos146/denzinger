"""Split an official document page into numbered articles.

A generalised copy of tools/post1958/vat_paras.py that works on a string and
keeps its state local, so it can be imported and tested. It returns a list of
{'art': number or None, 'head': nearest heading or None, 'text': paragraph}.
Paragraphs before the first article number get art None (titles, preambles).
"""
import html
import re

ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
FOOTNOTE_MARKERS = r'\b(AAS|Cf\.|cf\.|PL|PG|Mansi|Denz|ASS|op\. cit|Ibid)\b'


def roman(s):
    v = [ROMAN[c] for c in s]
    return sum(-x if i + 1 < len(v) and x < v[i + 1] else x for i, x in enumerate(v))


def blocks(page):
    s = re.sub(r'(?is)<(script|style|head|nav|footer)\b.*?</\1>', ' ', page)
    s = re.sub(r'(?is)<sup>.*?</sup>|<a [^>]*name="_ftnref[^"]*"[^>]*>.*?</a>|\(\d{1,3}\*?\)|\[\d{1,3}\*?\]', ' ', s)  # (3), (39*), [12]
    s = re.sub(r'(?i)<br\s*/?>', ' ', s)
    s = re.sub(r'(?is)</?(p|div|h\d|li|blockquote|td)\b[^>]*>', '\x01', s)  # some pages leave <p> unclosed
    for b in s.split('\x01'):
        t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', b)))
        t = t.replace('﻿', '').replace('ï»¿', '').strip()
        if t and not t.startswith('PDF generation in progress'):
            yield t


def is_heading(t):
    return (len(t) < 140 and not re.search(r'[.:;?!"”’)]$', t)) or (t.isupper() and len(t) < 200)


def paras(page, max_article=999):
    """Articles of an HTML page. max_article bounds what counts as an article number."""
    out, art, head, note = [], None, None, False
    width = len(str(max_article))
    num = re.compile(rf'^(\d{{1,{width}}}|\d \d{{1,2}})\s?\.(?:\s+(.*)|$)')  # "14.", or the split "1 4."
    for t in blocks(page):
        if re.match(r'^(NOTES|Footnotes|Notes)\s*$', t):
            break
        if (art and len(out) > 20 and re.match(r'^[\[(]?1[\])]?\.?\s', t)
                and re.search(FOOTNOTE_MARKERS, t[:200])):
            break  # the endnotes start again at 1
        m = num.match(t)
        if m and int(m.group(1).replace(' ', '')) <= max_article:
            art = int(m.group(1).replace(' ', ''))
            t = (m.group(2) or '').strip()
            if not t:
                continue
        if re.fullmatch(r'[IVXL]{1,6}\.?', t):  # a section numbered only by a Roman numeral
            art = roman(t.rstrip('.'))
            continue
        if re.match(r'Preliminary Note of Explanation\s*$|COMPLEMENTARY NORMS\b', t, re.I):
            note = True  # Lumen Gentium's Nota praevia numbers its points 1-4 again
        if is_heading(t):
            if not re.search(r'\b(AR|EN|ES)\b.*-', t):  # language switchers
                head = t
            continue
        out.append({'art': ('NP', art) if note else art, 'head': head, 'text': t})
    return out


def articles(ps):
    """Group paragraphs by article number: {n: [text, ...]} (unnumbered text is left out)."""
    by = {}
    for p in ps:
        if isinstance(p['art'], int):
            by.setdefault(p['art'], []).append(p['text'])
    return by
