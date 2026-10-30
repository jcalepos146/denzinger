# Sources of Catholic Dogma

A searchable, organized reader for Denzinger's *Enchiridion Symbolorum* in English, with the older numbering (before the 32nd edition of 1963). It is a static site with no accounts, server or tracking, and it works offline once opened.

## What it has

- **The full text:** 2,464 entries, from the creeds to Pius XII, with an appendix numbered from 5000. Scanning errors are corrected conservatively.
- **After 1958:** John XXIII, the Second Vatican Council, Paul VI and John Paul II to 1999, one entry per article of each document, numbered by the document and article (`LG 25`, `GS 22`, `EV 62`); addresses are numbered by their date (`AD 19641203`). Each is labelled by kind of document: encyclical, address or homily, document of the Doctrine of the Faith, and so on. Later years are being added.
- **A page for every entry** at `/n/<number>/`, so that search engines find them and shared links show the text. Each page links back to its place in the reader.
- **Old and new numbers:** each entry shows its Denzinger–Schönmetzer (DS) number, which Denzinger–Hünermann keeps. The Latin text can be shown below each entry or side by side with the English.
- **Weights:** every entry carries a grade (defined dogma, definitive, authoritative teaching, discipline, condemned, prudential and others), checked by hand in 328 ranges, each with a note on why. Condemned propositions also show their censures.
- **Supplement:** the decrees of Constance and Basel that Denzinger leaves out, each with its standing.
- **Guides:**
  - the Roman Catechism (Catechism of the Council of Trent), chapter by chapter, with the texts each chapter explains;
  - a timeline of every entry by date and weight, with the definitions and creeds in order;
  - doctrinal threads that follow a teaching through the collection;
  - *Since 1950*, read by the hermeneutic of continuity;
  - disputed questions.
- **Cross-references:** "cited by" links between entries that refer to each other by number.
- **Search:** words, phrases, numbers (`1839`, `DS 3074`), Scripture (`Matt 16:18`) and filters:

  | Filter | Example |
  |---|---|
  | Pope, council | `pope:"Pius IX"`, `council:trent`, `era:constance` |
  | Date | `year:1850-1900`, `year:16th` (century), `before:800`, `after:1800` |
  | Weight | `weight:dogma`, `weight:condemned`, `weight:discipline` |
  | Kind of text | `kind:anathema`, `kind:creed`, `kind:pbc` |
  | Latin text | `latin:"ex cathedra"` (accents ignored) |
  | DS numbers | `ds:3000-3075` |
  | Leave a word out | `-marriage` |

- **Tools:** side-by-side comparison; saved entries and notes, kept in your browser; Markdown study packets; citations in Chicago and Turabian style with both numbers; a print layout; a text for each day.

## Open data

Each build publishes the data at `/data/`:

| File | Contents |
|---|---|
| `entries.json` | Every entry with its text, DS numbers, year, weight, grade, censure, cross-references and Roman Catechism chapters |
| `crosswalk.csv` | Old number, DS number, and how the pair was matched |
| `weights.csv` | The hand-checked weight ranges and their notes |
| `latin.json` | The Latin text by DS number, as the source page gives it |
| `roman-catechism.json` | The Roman Catechism's chapters and the entries matched to each |
| `guides.json` | Since 1950, the disputed questions and the threads |

## Corrections

Every entry and guide item has a link that opens an issue here with the item filled in. See [CONTRIBUTING.md](CONTRIBUTING.md) to fix something directly.

## Sources

- **English text:** the translation of the older-numbered Denzinger as published on [patristica.net](https://patristica.net/denzinger/), archived from catecheticsonline.com. It appears to be Roy J. Deferrari's translation of the 30th edition (*The Sources of Catholic Dogma*, B. Herder, 1957). Its copyright status is uncertain.
- **Texts after 1958:** the English is the Holy See's own translation on [vatican.va](https://www.vatican.va/). The passages were chosen by following the selection in J. Neuner and J. Dupuis, *The Christian Faith in the Doctrinal Documents of the Catholic Church* (7th ed., 2001), whose numbers each entry records; its own translation is not used. The DS numbers of John XXIII's encyclicals come from its concordance. A few texts of weight that vatican.va gives only in Latin, French or Italian were translated for this site from that official text, and their source line says so.
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

A GitHub Action runs the same script on every push to `main` and publishes `dist/` to GitHub Pages. It also checks pull requests, so a change that breaks the data never reaches the site.

| Path | What it holds |
|---|---|
| `src/data/entries.json` | The entries, one per line |
| `src/data/eras.json` | Popes, councils and creeds, in order |
| `src/data/weights.json` | Hand-checked weight ranges |
| `src/data/catechism.json` | The Roman Catechism map |
| `src/data/since1950.json`, `disputed.json`, `threads.json` | The guides |
| `src/data/latin.json` | Latin text by DS number |
| `src/data/censures.json`, `books.json`, `quality.json` | Censures, Scripture book names, notes on the text |
| `src/app.js`, `src/styles.css`, `src/shell.html` | The reader |
| `src/entry.css` | The single-entry pages |
| `src/sw.js` | Offline support |
| `build/build.py` | Checks the data and builds everything |
