# Importing texts after 1958

Scripts used to build the John XXIII and Vatican II entries. They are not part of the site build.

1. `nd_units.py nd.txt`: splits the text of Neuner–Dupuis, *The Christian Faith* (7th ed., 2001; `pdftotext -layout`) into its numbered passages (`units.json`). The book is not in this repository.
2. Download the documents' English pages from vatican.va into `../vat/docs/<key>.html` (keys in `batch1.py`).
3. `batch1.py`: matches each passage to the sentences of the official text, in order (`align2.py`). Where Neuner–Dupuis prints article numbers, only those articles are searched.
4. `j23review.py pp,mm,pt`: John XXIII's English on vatican.va is a different translation, so those passages were matched by hand, paragraph by paragraph; the result is the `J23` table in `gen1.py`.
5. `gen1.py`: one entry per article, the union of every passage taken from it, with "..." for what is left out.
6. `eras_tool.py`: adds or removes eras and renumbers the entries' `era`.

Paul VI to John Paul II (1964-1999): `crawl.py` indexes the popes' documents on vatican.va; `match_idx.py` and `find.py` find each document Neuner-Dupuis quotes; `manifest2.py` lists those with an official English text; `batch2.py` and `gen2.py` build the entries; `grades2.py` holds the hand-checked grades. `put_entries.py` replaces an era's entries in `src/data/entries.json`.
