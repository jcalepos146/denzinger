# Contributing

Corrections are welcome, from a single misprint to a new document. There are two ways to send one.

## 1. Open an issue

Use the **Suggest a correction** or **Report a problem** link on the site. It opens a form with the item already filled in. Say what is wrong and, if you can, give a source: a printed edition with page or column, a scan, or an official text.

To propose a new text, such as a decree of Constance or Basel or a papal letter about one, use **Propose a document** on the [new issue](../../issues/new/choose) page.

## 2. Edit the data yourself

Every file in `src/data/` can be edited on github.com: open the file, choose the pencil icon, make the change and propose it. The site is checked automatically before anything is published, and the check names the file and line of any problem.

### An entry's text

`src/data/entries.json` has one entry per line:

```json
{"id": "1839", "era": 113, "session": "Session IV (July 18, 1870)", "topic": "Chap. 4. …", "text": ["And so We, …"], "weight": "papal-def", "ds": ["3073", "3074"]}
```

- `text` is a list of paragraphs. Correct scanning errors; leave the translator's spelling and bracketed insertions as printed.
- `era` is the line number (counting from 0) of the pope or council in `eras.json`.
- `ds` lists the Denzinger–Schönmetzer numbers. `dsHow` is `series` when the number is inferred from the neighboring entries, `checked` when it was matched by hand.
- `weight` is the rule-based label: `papal-def`, `conc-def`, `conc-canon`, `conc-decree`, `papal`, `particular`, `curia`, `pbc`, `condemned`, `creed`, `note` or `supplement`.

### A weight

`src/data/weights.json` holds the hand-checked grades as ranges of entries:

```json
{"from": "1839", "to": "1840", "g": "dogma", "n": "The definition of papal infallibility and its canon."}
```

An entry takes the first range that contains it. Grades: `dogma`, `definitive`, `authentic`, `discipline`, `condemned`, `condemned-heresy`, `profession`, `disputed`, `act`, `void`, `prudential`, `witness`, `editorial`. The note should say why, in a sentence or two.

### The Roman Catechism map

`src/data/catechism.json` lists the Catechism's chapters. Each has `refs`, the entries that teach the same doctrine. A range in the order of the collection can be written `"857–870"`. Entries up to 1566 appear as the texts the chapter explains; later ones are listed separately.

### A guide

`since1950.json`, `disputed.json` and `threads.json` hold the guides. Every entry number they cite must exist in `entries.json`; the check catches any that do not.

## Checking a change on your own computer

```sh
python3 build/build.py
python3 -m http.server -d dist
```

Then open <http://localhost:8000>.

## What gets accepted

- Corrections of the text against a printed edition or scan.
- Weights argued from what the text proposes and how it was received, with sources.
- New documents with a citation to a printed edition, and a translation whose source is stated.

Summaries follow the hermeneutic of continuity and say where others see a break. Changes that argue a position should present it fairly and cite the texts.
