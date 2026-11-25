#!/usr/bin/env python3
"""Build the Denzinger site and preview all five source ZIPs on this computer."""
import argparse
import csv
import html
import io
import mimetypes
import re
import subprocess
import sys
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urlsplit
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
BATCHES = {
    'Denzinger_Critical_Sources_and_Basel': 'Critical sources and Basel',
    'Denzinger_High_Priority_Sources_13-15': 'High priority 13–15',
    'Denzinger_High_Priority_Sources_16-71': 'High priority 16–71',
    'Denzinger_Medium_Priority_Sources_72-113': 'Medium priority 72–113',
    'Denzinger_Low_Priority_Sources': 'Low priority',
}
MANIFESTS = ('sources.csv', 'source_manifest.csv', 'document_index.csv', 'overflow_index.csv')
TEXT_TYPES = {'.txt', '.md', '.csv', '.json'}
MEDIA_TYPES = {'.jpg': 'image/jpeg', '.pdf': 'application/pdf'}
esc = html.escape


def find_archives(directory):
    for prefix, label in BATCHES.items():
        pattern = re.compile(re.escape(prefix) + r'(?:\s*\(\d+\))?\.zip', re.I)
        matches = sorted(path for path in directory.iterdir() if path.is_file() and pattern.fullmatch(path.name))
        if len(matches) != 1:
            raise ValueError(f'Expected one ZIP for {label}, found {len(matches)}')
        yield label, matches[0]


def catalogue(stack, directory):
    items = []
    for label, path in find_archives(directory):
        archive = stack.enter_context(ZipFile(path))
        titles = {}
        for manifest in MANIFESTS:
            if manifest not in archive.namelist():
                continue
            with archive.open(manifest) as file:
                for row in csv.DictReader(io.TextIOWrapper(file, encoding='utf-8-sig')):
                    title = row.get('title') or row.get('document')
                    member = row.get('path') or row.get('file') or row.get('source_files') or ''
                    if title:
                        for name in member.split('|'):
                            titles.setdefault(name.strip(), title)
        for info in archive.infolist():
            if not info.is_dir():
                items.append((label, archive, info, titles.get(info.filename, info.filename)))
    return items


def archive_page(items, query, batch, full_text):
    terms = query.casefold().split()
    results = []
    for index, (label, archive, info, title) in enumerate(items):
        if batch and batch != label:
            continue
        searchable = f'{title} {info.filename}'.casefold()
        if full_text and terms and PurePosixPath(info.filename).suffix.lower() in TEXT_TYPES:
            searchable += ' ' + archive.read(info).decode('utf-8', errors='replace').casefold()
        if all(term in searchable for term in terms):
            results.append(f'<li><a href="file/{index}">{esc(title)}</a><br>'
                           f'<small>{esc(label)} · {esc(info.filename)}</small></li>')
    options = ['<option value="">All five batches</option>']
    for label in BATCHES.values():
        selected = ' selected' if label == batch else ''
        options.append(f'<option{selected}>{esc(label)}</option>')
    checked = ' checked' if full_text else ''
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Local source collection · Denzinger</title>
<style>
body {{max-width: 50rem; margin: 2rem auto; padding: 0 1rem; font: 1rem/1.5 system-ui;}}
label {{display: block; margin: .5rem 0;}} input, select, button {{font: inherit;}}
li {{margin: .7rem 0; overflow-wrap: anywhere;}} small {{color: #444;}}
</style>
<main><p><a href="../#library">Denzinger reader</a> · <a href="../editions/">Public source editions</a></p>
<h1>Local source collection</h1>
<p>Browse the original source files, scans, transcriptions and research notes on this computer.
Consult the batch manifests and cited editions before relying on OCR or draft section boundaries.</p>
<form><label>Search <input name="q" type="search" value="{esc(query)}" maxlength="200"></label>
<label>Batch <select name="batch">{''.join(options)}</select></label>
<label><input type="checkbox" name="full" value="1"{checked}> Include text inside files</label>
<button type="submit">Search</button></form>
<p>{len(results)} of {len(items)} files</p><ul>{''.join(results)}</ul></main></html>'''


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        super().end_headers()

    def respond(self, content, content_type, archive=False, download=None):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        if archive:
            self.send_header('Content-Security-Policy',
                             "default-src 'none'; style-src 'unsafe-inline'; "
                             "form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        if download:
            name = re.sub(r'[^a-zA-Z0-9._-]', '_', download)
            self.send_header('Content-Disposition', f'attachment; filename="{name}"')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if (self.headers.get('Host') != self.server.origin.removeprefix('http://') or
                self.headers.get('Sec-Fetch-Site') not in (None, 'none', 'same-origin')):
            self.send_error(403)
            return
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path == '/local-sources/':
            try:
                params = parse_qs(request.query, max_num_fields=5)
            except ValueError:
                self.send_error(400)
                return
            page = archive_page(self.server.items, params.get('q', [''])[0][:200],
                                params.get('batch', [''])[0], params.get('full', [''])[0] == '1')
            self.respond(page.encode(), 'text/html; charset=utf-8', archive=True)
            return
        match = re.fullmatch(r'/local-sources/file/([0-9]{1,6})', path)
        if match and int(match[1]) < len(self.server.items):
            _, archive, info, _ = self.server.items[int(match[1])]
            name = PurePosixPath(info.filename)
            suffix = name.suffix.lower()
            text = suffix in TEXT_TYPES
            self.respond(archive.read(info), 'text/plain; charset=utf-8' if text else
                         MEDIA_TYPES.get(suffix, 'application/octet-stream'),
                         archive=True, download=None if text else name.name)
            return
        if path == '/local-sources':
            self.send_response(302)
            self.send_header('Location', '/local-sources/')
            self.end_headers()
            return
        root = self.server.site
        page = (root / path.lstrip('/')).resolve()
        if not page.is_relative_to(root):
            self.send_error(404)
            return
        if page.is_dir():
            page /= 'index.html'
        if not page.is_file():
            self.send_error(404)
            return
        data = page.read_bytes()
        if page == root / 'index.html':
            # The preview link is injected only into the loopback response.
            link = b'<p style="margin:.6rem 1rem"><a href="/local-sources/">Browse local source ZIPs</a></p>'
            data = data.replace(b'</body>', link + b'</body>', 1)
        self.respond(data, mimetypes.guess_type(page.name)[0] or 'application/octet-stream')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archives', type=Path, help='directory containing the five original ZIPs')
    args = parser.parse_args()
    with ExitStack() as stack:
        try:
            items = catalogue(stack, args.archives)
        except (OSError, ValueError, BadZipFile) as error:
            parser.error(str(error))
        site = Path(stack.enter_context(TemporaryDirectory(prefix='denzinger-preview-'))).resolve()
        subprocess.run([sys.executable, str(ROOT / 'build/build.py'), '--out', str(site)], check=True)
        server = stack.enter_context(HTTPServer(('127.0.0.1', 0), PreviewHandler))
        server.items = items
        server.site = site
        server.origin = f'http://127.0.0.1:{server.server_port}'
        print(f'Denzinger preview: {server.origin}/\nSource collection: {server.origin}/local-sources/',
              flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
