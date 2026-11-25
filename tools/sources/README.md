# Fetching missing source texts

`sources.py` finds the documents the site has only in part or not at all, downloads their complete texts from the sources already linked in `src/data/documents.json`, and reports what is missing. Like the build, it needs only Python's standard library. It is not part of the build.

```sh
python3 tools/sources/sources.py all       # gaps, fetch, extract, diff
python3 tools/sources/sources.py fetch --only cd pc --refresh
python3 tools/sources/sources.py status
```

| Step | Reads | Writes (all in `.sources/`, which git ignores) |
|---|---|---|
| `gaps` | `documents.json` (records with coverage `none` or `excerpts`), the backlog in `continuity.json` | `todo.json`: each gap, its kind, the address to fetch, or why it must be found by hand |
| `fetch` | `todo.json` | `raw/<id>.html` or `.txt`, and `provenance.json`: address, time, size, SHA-256 and rights note of each download |
| `extract` | `raw/` | `text/<id>.json`: the page split into numbered articles (with `paras.py`); scanned books are kept as plain text |
| `diff` | `text/`, `entries.json` | `report.md` and `report.json`: articles missing locally, numbering to check, local text that differs from its source; `drafts/<id>.json`: draft entries for the missing articles |

## What to find first

`python3 tools/sources/priorities.py` ranks everything missing by how much it could change a continuity verdict, into `.sources/priorities.md`: the cases by urgency, then each item (a case's research gap, a text not yet checked against a critical edition, an unresolved claim, Latin to proofread, the research backlog, missing articles) with its score. Unresolved tensions and low-confidence cases come first, because new evidence is most likely to change them; a text that binds in faith counts more than a disciplinary one; coverage that no case cites comes last.

## Primary-source editions

`python3 tools/sources/sources.py editions` fetches the editions listed in `editions.json`: for each text a continuity case still needs (Ad extirpanda, Dum diversas, Sublimis Deus, In supremo apostolatus, Nicholas I's Responsa, the Waldensian profession, Exsurge Domine, Mansi 27 and 29, Finke's Acta, the 2018 letter on the death penalty, Mortalium animos), the volumes to try and the words that identify it. It downloads the OCR text of each archive.org volume once (`.sources/editions/`), finds the words, tolerating OCR spelling (u for v, e for ae, words split across lines), and asks archive.org's search inside the book for the page, so `.sources/editions.md` links each hit to its page scan. Read the scan before citing: OCR is not a transcription.

Only volumes published before 1931 (public domain in the United States) and official vatican.va pages are fetched; a test enforces it. Editions still in copyright, or not found online, are listed under `manual` with where to consult them.

## What it will and will not do

- **Sources.** It downloads only from the hosts listed in `HOSTS` in `sources.py` (vatican.va, archive.org and a few reference sites). Everything else, and the research backlog, is listed under "Needs finding by hand". It does not use shadow libraries, and a book still in copyright is for a library or a purchase, not this tool.
- **Politeness.** It obeys each host's `robots.txt`, waits at least two seconds between requests to a host (longer if `Crawl-delay` asks), retries a busy server after a pause, and caches what it has downloaded so a second run asks for nothing new. `--refresh` downloads again.
- **No change to the data.** It never writes to `src/data`. A draft entry has `era`, `weight` and `kinds` to fill in, and an `_draft` block with its source and checksum, which must be removed before the entry is copied into `entries.json`. For a document with no local entries the id prefix is the title's initials; if those are taken (Vita Consecrata and the Vademecum would both be `VC`) the draft says the prefix needs choosing.
- **Rights.** A downloaded text is kept for checking. That the site can show it is a separate decision, recorded in each record's `rights` (see `docs/EDITORIAL-WORKFLOW.md`).

## For AI use

The downloaded texts in `.sources/text/` are split into numbered articles, and `provenance.json` records where and when each came from, with a checksum. That makes them a ready reference collection for a wrapper that looks up and cites passages, alongside the site's own entries (see "Using the collection with AI" in the main README). They stay out of the repository: their reuse is not cleared, and a model trained on them inherits that question.

## Reading the report

- **Missing locally**: article numbers found at the source that the site has no entry for. For a selection (`excerpts`) these are often left out on purpose; the report shows them so the choice can be made, not so they are all added.
- **Numbering to check**: local entries whose article was not found at the source, or a source whose article count differs from the record's `totalSections`. Usually the splitter missed a number on an irregular page; sometimes the local id is wrong.
- **Local text that differs**: a passage of a local entry, between its "..." marks, that is not in the official article word for word. Case, punctuation and bare numbers (footnote markers) are ignored, so what is left is a changed, added or missing word, or a different translation.
- **Scanned books** (archive.org) are saved as OCR text and not split; find the passage by hand.
