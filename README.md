# Eodem Sensu

**[Open the Denzinger reader](https://jcalepos146.github.io/denzinger/)**

Eodem Sensu is a searchable English edition of Denzinger’s *Enchiridion Symbolorum*, with the older Denzinger numbering, the Denzinger–Schönmetzer (DS) concordance, and selected Catholic teaching documents through Leo XIV.

| Start here | Try this |
|---|---|
| Find an entry | [Old no. 1839](https://jcalepos146.github.io/denzinger/n/1839/) or [DS 3074](https://jcalepos146.github.io/denzinger/ds/3074/) |
| Read a document | [Lumen gentium §25](https://jcalepos146.github.io/denzinger/lg/25/) or [all included passages](https://jcalepos146.github.io/denzinger/lg/) |
| Verify a source | [Sources and coverage](https://jcalepos146.github.io/denzinger/#library) and [Source editions](https://jcalepos146.github.io/denzinger/editions/) |
| Browse a teaching | [Doctrinal threads](https://jcalepos146.github.io/denzinger/#threads) and [continuity research](https://jcalepos146.github.io/denzinger/#continuity) |
| Use the data | [Export index](https://jcalepos146.github.io/denzinger/data/index.json), [AI client guide](https://jcalepos146.github.io/denzinger/llms.txt), and [Atom feed](https://jcalepos146.github.io/denzinger/feed.xml) |

The name comes from Vincent of Lérins’s rule, taken up by Vatican I, that doctrine grows *eodem sensu*, “in the same dogma, the same sense and the same meaning.” Doctrinal grades and the continuity studies are editorial aids. The research on Constance, Basel, and Vatican I remains [sealed](#sealed-research).

## What it has

- **The full text:** 2,431 entries, from the creeds to Pius XII, including an appendix numbered from 5000. Scanning errors are corrected conservatively.
- **After 1958:** 968 entries from John XXIII, the Second Vatican Council, Paul VI, John Paul II, Benedict XVI, Francis and Leo XIV to October 2026, one entry per article of each document, numbered by the document and article (`LG 25`, `GS 22`, `EV 62`); addresses are numbered by their date (`AD 19641203`). Each is labelled by kind of document: encyclical, address or homily, document of the Doctrine of the Faith, and so on. Interviews and press conferences are marked as private opinion.
- **A page for every entry** at `/n/<number>/`, so that search engines find them and shared links show the text, with structured data (JSON-LD) and a share image. Each page links back to its place in the reader and, after 1958, to its whole document. Short links lead to them by the numbers people cite: `ds/3074/`, `lg/25/`.
- **Document selections and sources:** each document selection can be read on its own (`lg/` opens the Lumen Gentium excerpts). This is not a complete-text claim. **Sources and coverage** maps every entry to a source record, separates inferred headings from catalogued documents, and links to complete external texts. All 16 Vatican II documents are catalogued; five are external-only.
- **Old and new numbers:** each entry shows its Denzinger–Schönmetzer (DS) number, which Denzinger–Hünermann keeps. The Latin text can be shown below each entry or side by side with the English; it is loaded only when first needed, and each Latin block says whether it has been proofread and links to a correction form.
- **Weights:** every entry carries a grade (defined dogma, definitive, authoritative teaching, discipline, condemned, prudential and others), checked by hand in 512 ranges, each with a note on why; a page lists every range with its reason so the grades can be audited. Condemned propositions also show their censures.
- **Supplement:** 49 texts: the decrees of Constance and Basel that Denzinger leaves out, Moyses vir Dei and the last bulls of union of Florence (with the Syrians, and with the Chaldeans and Maronites of Cyprus), Pius IV's bull confirming Trent, and the witnesses to the Synod of Sutri (1046), each with its standing.
- **Guides:**
  - the Roman Catechism (Catechism of the Council of Trent), chapter by chapter, with the texts each chapter explains;
  - a timeline of every entry by date and weight, with the definitions and creeds in order;
  - 18 doctrinal threads that follow a teaching through the collection, each with a chart of its steps by date and weight;
  - *Since 1950*, 47 points read by the hermeneutic of continuity;
  - 45 disputed questions.
- **Hermeneutics:** ten principles for reading magisterial texts (development in the same sense, weighing a text before reading it, what is proposed as against its reasoning, the occasion a text answers, formula and truth, the analogy of faith, Scripture read in the Church, principle and application, condemnations, private words), each stated as a rule, grounded in texts of the collection, with the misreading it guards against and test cases among the disputed questions; then the two hermeneutics and a method. The rules also go into every prompt Ask writes and into `llms.txt`.
- **Continuity research** (a research layer, not Church teaching): the hermeneutic of ecclesial continuity, taking Benedict XVI's address of 22 December 2005 as its method, with eight principles for testing an apparent conflict (P1–P8) and four levels of continuity (logical, doctrinal, juridical, constitutional). Twenty-four cases, from Cum occasione and Unigenitus to Dignitatis Humanae, the death penalty, slavery and Anglican orders, are each broken into propositions with their doctrinal grade and legal force kept apart, a contradiction matrix, a graph of relations, the strongest objection, a provisional verdict and the evidence still required. The case on Constance, Basel and Vatican I is untested research and is kept encrypted: it opens with a password, in the browser only (see [Sealed research](#sealed-research)). A verification backlog lists every claim still resting on an unchecked source. See [the protocol](docs/HERMENEUTIC-PROTOCOL.md).
- **Reading a condemnation:** a guide to reading condemned propositions in the sense they were condemned, with the case of Unigenitus; every condemned proposition links to it.
- **Ask or check a statement:** ask a question, or test a statement against the texts for formation; an AI answers from the entries and cites them. The texts are chosen from the words of the question, the doctrines it names (with their defining texts), the guides that discuss them and any numbers it gives (`n. 1839`, `DS 3074`, `LG 25`, `Matt 16:18`), with binding texts first. The page lists them before you ask, with the reason for each, so you can untick some or add others by number or words. Opened in Claude it answers in the page; anywhere else it copies or downloads a prompt with the texts in full, a link to each, what their labels mean and the reading rules, optionally with the Latin, for any AI client. `llms.txt` describes the data for AI clients and agents.
- **Cross-references:** "cited by" links between entries that refer to each other by number.
- **Search:** words, phrases, numbers (`1839`, `DS 3074`), Scripture (`Matt 16:18`) and filters:

  | Filter | Example |
  |---|---|
  | Document | `document:"Mediator Dei"`, `doc:LG` |
  | Issuing body | `issuer:"Doctrine of the Faith"` |
  | Local coverage | `coverage:excerpts`, `coverage:none` |
  | Pope, council | `pope:"Pius IX"`, `council:trent`, `era:constance` |
  | Date | `year:1850-1900`, `year:16th` (century), `before:800`, `after:1800` |
  | Weight | `weight:dogma`, `weight:condemned`, `weight:discipline` |
  | Kind of text | `kind:anathema`, `kind:creed`, `kind:pbc` |
  | Latin text | `latin:"ex cathedra"` (accents ignored) |
  | DS numbers | `ds:3000-3075` |
  | Leave a word out | `-marriage` |

- **Tools:** side-by-side comparison; saved entries and notes, kept in your browser; Markdown study packets; citations in Chicago and Turabian style with both numbers; a print layout; a text for each day; the latest additions on the home page and as an Atom feed.

## Open data

Each build publishes the data at `/data/`:

| File | Contents |
|---|---|
| `entries.json` | Every entry with its text, DS numbers, year, weight, grade, censure, cross-references and Roman Catechism chapters |
| `crosswalk.csv` | Old number, DS number, and how the pair was matched |
| `weights.csv` | The hand-checked weight ranges and their notes |
| `latin.json` | The Latin text by DS number, as the source page gives it |
| `roman-catechism.json` | The Roman Catechism's chapters and the entries matched to each |
| `documents.json` | Source inventory, coverage, provenance, review status and full-text links |
| `coverage.csv` | The source inventory as a spreadsheet |
| `guides.json` | Since 1950, the disputed questions, the threads and the principles of hermeneutics |
| `continuity.json` | The continuity research layer: principles, cases, propositions, comparisons, verdicts and evidence gaps |
| `continuity-audio.md` | Listening scripts for each case: what was taught, by what authority, what is permanent |

## Using the collection with AI

The data was made to be read by machines as well as people: every text carries its source, its kind of document, often a hand-checked grade with the reason for it, censures, cross-references and both numbering systems, and `llms.txt` gives an AI client the reading rules. That makes it suited to two uses.

- **A wrapper around an existing model (recommended).** `tools/mcp/server.py` is one, ready to use: an MCP server that lets Claude Desktop, Claude Code or another MCP client search the entries, quote them with their weight, follow the continuity cases and cite by number (see [its README](tools/mcp/README.md); Claude Code finds it through `.mcp.json`). More generally: The model answers from entries looked up for each question and cites them by number, as **Ask** already does in the reader. The wording stays exact, the weight of each text travels with it, a correction reaches every answer at once, and nothing needs retraining. `entries.json`, `latin.json`, `guides.json` and `llms.txt` are what such a wrapper needs; `tools/sources/` can add the complete official texts as a local reference collection.
- **Training or fine-tuning a model.** The grades, censures, disputed questions and cross-references are labelled examples (what kind of act is this text, what assent does it ask, which text defines this doctrine). A trained model can still misquote or blur a text's weight, so answers should cite and be checked against the entries.

Before training on the texts or publishing a dataset, settle their rights. This repository has no licence. The pre-1958 English appears to be Deferrari's translation (1957), whose copyright status is uncertain; reuse permission for the Holy See's texts has not been established; the guides, grades and continuity research were written for this site. The grades are a reading aid, not an official classification, and the continuity layer is research, not Church teaching: a dataset should keep those labels.

## Sealed research

Research that has not yet been tested is published only encrypted. At present that is the case on Constance, Basel and Vatican I (D1) with its pass conditions and the theory they test, its verification backlog (BL1–BL6), its protocol history and verification log, the disputed questions on conciliarism and on Sutri, and two research documents (the decree-by-decree review of Basel and the sealed parts of the protocol). Everything else stays open.

- **Where it lives.** The readable copy is in `private/` (`sealed-research.json` and `docs/*.md`), which git ignores. `node tools/seal/seal.mjs seal` encrypts it into `src/data/sealed.json`, which is committed and published as `data/sealed.json`. The public files keep only placeholders: a case marked `"sealed": true` with its title, and a list of what is withheld.
- **How it opens.** On the reader, the sealed items show a password form. The file is decrypted in the browser with the Web Crypto API and kept for that tab only; nothing is sent anywhere. It is AES-256-GCM, with the key derived from the password by PBKDF2-SHA-256 (600,000 iterations) and a random salt. The site and the repository hold no password, hash or key, so whoever downloads the file can only guess passwords, one slow guess at a time: its safety is the password's length and randomness.
- **Working on it.** Edit `private/`, then run the build: when `private/` is present it merges the sealed research into a copy of the data and runs every check on it, and it warns if `private/` has changed since the last seal. Then run `node tools/seal/seal.mjs seal` (it asks for the password twice, at a hidden prompt) and commit `src/data/sealed.json`. On a new machine, `node tools/seal/seal.mjs open` restores `private/` from the sealed file; `check` tells you whether a password opens it and whether it matches `private/`.
- **Limits.** Versions published before 25 November 2026 remain in the repository's history and older branches. Sealed research is left out of search, Ask, `llms.txt`, the listening scripts and the open data. Anyone given the password can read it. If the password is lost, the sealed copy cannot be opened, so keep a backup of `private/`.

## Corrections

Every entry and guide item has a link that opens an issue here with the item filled in. See [CONTRIBUTING.md](CONTRIBUTING.md) to fix something directly.

## Sources

- **English text:** the translation of the older-numbered Denzinger as published on [patristica.net](https://patristica.net/denzinger/), archived from catecheticsonline.com. It appears to be Roy J. Deferrari's translation of the 30th edition (*The Sources of Catholic Dogma*, B. Herder, 1957). Its copyright status is uncertain.
- **Texts after 1958:** the English is the Holy See's own translation on [vatican.va](https://www.vatican.va/). To 1999 the passages were chosen by following the selection in J. Neuner and J. Dupuis, *The Christian Faith in the Doctrinal Documents of the Catholic Church* (7th ed., 2001), whose numbers each entry records; its own translation is not used. From 2000 the passages were chosen for this site, favouring texts that define, declare or settle a point. The DS numbers of John XXIII's encyclicals come from its concordance. A few texts of weight that vatican.va gives only in Latin, French or Italian were translated for this site from that official text, and their source line says so.
- **Latin text and DS numbers:** the Latin page of the same site, which prints both numbers. Accented characters it lost (mostly French *é*) were restored by context. The Latin is otherwise as that page gives it, and has not been proofread.
- **Roman Catechism:** chapter titles follow McHugh and Callan's translation (1923). The cross-references to Denzinger were made by topic for this site.
- **Summaries:** the guides were written for this site. Use the linked official texts before citing.

Weights, kinds of text and indexes are a reading aid, not an official classification.

## Building

The site is built from `src/` by one Python script that needs nothing beyond the standard library:

```sh
python3 build/build.py        # writes the site to dist/
python3 -m http.server -d dist
```

The build writes the reader, standalone entry pages, the source editions and the public exports. The repository currently includes a generated copy for GitHub Pages branch publishing. See [deployment instructions](DEPLOYMENT.md) to refresh it or return to automatic publishing with GitHub Actions.

The build stops on problems (a reference to an entry that does not exist, an unknown grade) and prints notes on things worth a look (an "n." reference that points nowhere, a DS number given to two entries, a weight range that can never apply); `--strict` makes the notes stop it too. The reader's page is small: the app, styles and data are separate files named by their content, so browsers keep them until they change. Once a month another Action runs `tools/check_links.py`, which checks the external links.

| Path | What it holds |
|---|---|
| `src/data/entries.json` | The entries, one per line |
| `src/data/eras.json` | Popes, councils and creeds, in order |
| `src/data/weights.json` | Hand-checked weight ranges |
| `src/data/catechism.json` | The Roman Catechism map |
| `src/data/since1950.json`, `disputed.json`, `threads.json`, `hermeneutics.json` | The guides |
| `src/data/continuity.json` | The continuity research layer (see [the protocol](docs/HERMENEUTIC-PROTOCOL.md)); checked by `build/continuity.py` |
| `src/data/changes.json` | What was added and when, for the home page and the feed |
| `src/data/latin-checked.json` | Which Latin texts have been proofread, against what |
| `src/data/concepts.json` | The doctrines Ask recognises in a question, and their defining texts |
| `src/data/latin.json` | Latin text by DS number |
| `src/data/censures.json`, `books.json`, `quality.json` | Censures, Scripture book names, notes on the text |
| `src/app.js`, `src/styles.css`, `src/shell.html` | The reader |
| `src/entry.css` | The single-entry pages |
| `src/og.png` | The share image |
| `src/sw.js` | Offline support |
| `build/build.py` | Checks the data and builds everything |
| `tools/check_links.py` | Checks the external links (not part of the build) |
| `tools/sources/` | Finds what the collection lacks, downloads complete texts and public-domain editions, and ranks the gaps for the continuity research (not part of the build; see [Finding what is missing](#finding-what-is-missing)) |
| `tools/mcp/` | An MCP server so an AI assistant can look up, quote and cite the texts (not part of the build; see its README) |
| `tools/post1958/` | The scripts that imported and aligned the texts after 1958 (see its README) |

## Source inventory

`src/data/documents.json` holds explicit source records. Unassigned entries are conservatively grouped by their inherited source headings; these groups are marked unreviewed, not counted as verified documents. An abbreviation is scoped to its era to prevent collisions such as DCE. Passage grades are editorial assessments, distinct from genre labels. No new document-level grades are inferred from titles.

Run `python3 tools/audit_library.py` for a reproducible coverage report and `python3 -m unittest discover -s tests` for source-integrity regression checks.

Document title searches also show matching source records, including external-only texts. Those texts are not part of local passage search. `kind:encyclical`, `kind:cdf` and `kind:papal-address` complement the existing structural filters. See [the editorial workflow](docs/EDITORIAL-WORKFLOW.md) and [collection roadmap](docs/COLLECTION-ROADMAP.md).

The [Papal definition collection](https://jcalepos146.github.io/denzinger/#weight-papal-def) includes received papal letters, Roman synodal acts and definitions promulgated with a council. The source records give the basis for inclusion, and each entry retains its own genre and editorial grade.

Evidence-backed relationships appear alongside passages and relevant doctrinal threads. `src/data/relations.json` stores direction, kind, editorial explanation and quotations from both endpoints; the build rejects missing references or quotations absent from the text. **Coverage and requests** publishes the backlog and offers explicitly saved, browser-local research gaps. GitHub proposals are opened by the reader; no search history is transmitted automatically. The monthly link checker now includes catalogue sources and saves a downloadable availability report.

## Finding what is missing

Three tools in `tools/sources/` keep track of what the collection still lacks. None is part of the build, and none writes to `src/data`: what they download and draft stays in `.sources/`, which git ignores, for an editor to check. See [their README](tools/sources/README.md).

| Command | What it does |
|---|---|
| `python3 tools/sources/sources.py all` | Downloads the complete text of every catalogued document the site holds only in part or not at all, compares it article by article with the local entries, and drafts entries for the missing articles (`.sources/report.md`). |
| `python3 tools/sources/sources.py editions` | Fetches the public-domain editions the continuity cases need (Bullarium Romanum, Migne, Davenport, Hernáez, the Acta of Gregory XVI and others, all printed before 1931), finds each text in the scan and links to its page (`.sources/editions.md`). |
| `python3 tools/sources/priorities.py` | Ranks everything missing by how much it could change a continuity verdict: unresolved tensions first, texts that bind in faith before disciplinary ones, uncited coverage last (`.sources/priorities.md`). |

The first full run (25 November 2026) found 13 catalogued documents with no local text, and 4,745 articles missing in all; every passage already taken from vatican.va matched the official text. Of 238 ranked gaps, 12 are critical, chiefly the primary texts behind the five unresolved tensions (Lateran IV beside Dignitatis Humanae, slavery, torture, Quierzy and Valence, the death penalty). Twelve of the editions they need were found in public-domain scans or on vatican.va; eight more, still in copyright or not online, are listed for consultation in a library.
