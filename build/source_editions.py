"""Render the checked-in public bibliography, without opening any research archives."""
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

CATALOGUE = Path(__file__).resolve().parents[1] / 'src/data/source-editions.json'
FIELDS = {'title', 'edition', 'url', 'language'}
TRANSCRIPTION = {'transcription', 'textStatus'}


def load_editions():
    records = json.loads(CATALOGUE.read_text(encoding='utf-8'))
    for row in records:
        if set(row) not in (FIELDS, FIELDS | TRANSCRIPTION) or any(
            not isinstance(value, str) for value in row.values()
        ):
            raise ValueError('Invalid public source edition fields')
        if any(not row[field].strip() for field in ('title', 'edition', 'url')):
            raise ValueError('A public source edition needs a title, edition and URL')
        url = urlsplit(row['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Public source edition links must use HTTPS without credentials')
    return records


def render_editions(records, heading):
    esc = html.escape
    rows = []
    for row in records:
        language = ' · ' + esc(row['language']) if row['language'] else ''
        text = ''
        if 'transcription' in row:
            text = (f'<details><summary>{esc(row["textStatus"])}</summary>'
                    f'<p class="witness" lang="la">{esc(row["transcription"])}</p></details>')
        rows.append(f'<li><h2>{esc(row["title"])}</h2>'
                    f'<p>{esc(row["edition"])}{language} · '
                    f'<a href="{esc(row["url"])}" rel="noreferrer">Open the source edition</a></p>{text}</li>')
    return heading + f'''
<main>
<p><a href="../#library">← Sources and coverage</a></p>
<h1>Source editions</h1>
<p>{len(records)} edition references and selected transcriptions from the source collection. Source links may lead to a page, an entire volume, or a complete document. Page OCR and transcriptions should be checked against the cited edition.</p>
<label>Filter by title, edition or language <input type="search" id="query"></label>
<p id="matches" role="status"></p>
<ul id="editions">{''.join(rows)}</ul>
</main>
<style>
main {{max-width: 52rem; margin: 2rem auto; padding: 0 1rem;}}
input {{font: inherit; width: min(100%, 22rem);}}
li {{margin: 1rem 0;}}
li h2 {{font-size: 1.15rem; margin: 0;}}
li p {{margin: .3rem 0;}}
.witness {{white-space: pre-wrap; padding: .6rem 0;}}
</style>
<script>
const query = document.getElementById('query');
const matches = document.getElementById('matches');
const fold = text => text.normalize('NFD').replace(/\\p{{M}}/gu, '').toLowerCase();
const rows = [...document.querySelectorAll('#editions li')].map(item =>
  [item, fold(item.textContent)]);
query.addEventListener('input', () => {{
  const words = fold(query.value).trim().split(/\\s+/);
  let count = 0;
  for (const [item, text] of rows) {{
    item.hidden = !words.every(word => text.includes(word));
    if (!item.hidden) count++;
  }}
  matches.textContent = count + ' matching editions';
}});
</script>
</body></html>
'''
