#!/usr/bin/env python3
"""Check that the external links in the data still answer.

    python3 tools/check_links.py            # every link
    python3 tools/check_links.py --only vatican.va

Collects the "Full text" links of the entries and the official links of the
Since 1950 guide, asks each server for the page, and lists those that fail.
It is not part of the build, which must work offline; a GitHub Action runs it
once a month. Exits with 1 if any link is broken.
"""
import argparse, concurrent.futures, json, os, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'data')
AGENT = 'Mozilla/5.0 (compatible; link-check for a static reader of Denzinger)'


def links():
    with open(os.path.join(DATA, 'entries.json'), encoding='utf-8') as f:
        for e in json.load(f):
            for l in e.get('links', []):
                yield l['url'], f'entry {e["id"]}'
    with open(os.path.join(DATA, 'since1950.json'), encoding='utf-8') as f:
        for s in json.load(f):
            if s.get('url'):
                yield s['url'], f'Since 1950, {s["id"]}'
            if s.get('extra', {}).get('url'):
                yield s['extra']['url'], f'Since 1950, {s["id"]} (extra)'


def probe(url):
    last = 'no answer'
    for method in ('HEAD', 'GET', 'GET'):  # the second GET forgives one dropped connection
        req = urllib.request.Request(url, method=method, headers={'User-Agent': AGENT, 'Accept': '*/*'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, None
        except urllib.error.HTTPError as err:
            if method == 'HEAD':
                continue  # some servers (vatican.va among them) answer HEAD with an error; confirm with GET
            return err.code, str(err.reason)
        except Exception as err:  # network errors, timeouts
            last = str(err)[:120]
            continue
    return None, last


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', help='check only addresses containing this text')
    a = ap.parse_args()
    seen = {}
    for url, where in links():
        if a.only and a.only not in url:
            continue
        seen.setdefault(url, []).append(where)
    bad, refused = [], []
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for url, (code, why) in zip(seen, ex.map(probe, seen)):
            if code in (401, 403, 429):
                refused.append((url, code, why))  # the site turns away scripts; a browser may still open it
            elif code is None or code >= 400:
                bad.append((url, code, why))
    print(f'{len(seen)} links checked, {len(bad)} failed, {len(refused)} refused a script (check those by hand)')
    for label, rows in (('failed', bad), ('refused', refused)):
        for url, code, why in rows:
            print(f'  {label} {code or "error"}  {url}  ({"; ".join(seen[url])}) {why or ""}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
