# Hermeneutic of ecclesial continuity: the research protocol

Version 0.4.1, 18 November 2026. Reader: <https://jcalepos146.github.io/denzinger1.0/#continuity>

This is a research layer, kept apart from the texts. It does not change any entry, its numbering or its weight. Its verdicts, confidence levels and the synthesis proposed for Constance, Basel and Vatican I are scholarly hypotheses, not teaching of the Church and not a judgment of any office of the Holy See.

## Where things are

| Path | What it holds |
|---|---|
| `src/data/continuity.json` | The protocol (Benedict XVI's five rules, principles P1–P8, the four levels, the hard gate, adversarial tests, vocabularies), the regression subset, the global verification backlog, and the 24 cases |
| `build/continuity.py` | The checks the build runs on that file, and the `llms.txt` section and listening scripts it writes |
| `tests/test_continuity.py` | Regression tests for the protocol's rules |
| `src/app.js` (section "hermeneutic of ecclesial continuity") | The views: `#continuity`, `#case-D1`, `#cp-<proposition>` |
| `.github/ISSUE_TEMPLATE/research-source.yml` | The form readers use to send a source for a backlog item |

The build also publishes `data/continuity.json` and `data/continuity-audio.md` (conversational scripts for listening).

## A case record

| Field | Meaning |
|---|---|
| `id`, `group`, `title`, `question` | A1–A7, B1–B7, C1–C6 and D1–D6. Each question states what the case tests. |
| `summary` | The reader's summary |
| `period`, `themes`, `issuers` | For the filters |
| `texts[]` | Primary texts: `label`, `refs` (entry ids), `local` (`full`, `excerpt`, `summary`, `none`), `edition`, `verified`, `url` |
| `propositions[]` | Atomic claims: `id`, `ref` or `ext`, `year`, `says` (the site's words), `quote` (exact words, checked against the entry), `formal_object`, `assent` (doctrinal grade), `binding_status` (legal force), `evidence` (D, H, T, N, U), `note` |
| `matrix[]` | Comparisons: `a`, `b`, `level` (logical, doctrinal, juridical, constitutional), `same_subject`, `same_sense`, `same_time`, `result`, `why` |
| `edges[]` | `[from, to, type]` with the seven relation types |
| `qualifications`, `reception`, `contingency`, `development` | Stages 3–7 |
| `gate` | D1 only: the seven pass conditions with status and note |
| `hypothesis`, `objection`, `rebuttal` | Stages 8–9 |
| `verdict`, `confidence`, `stage`, `provisional`, `source_verified` | Stage 10 |
| `gaps[]`, `next_source` | Evidence still required |
| `benedict` | An application of Benedict XVI's method, always labelled as the site's inference |
| `audio` | `taught`, `authority`, `permanence`: the three recurring questions |
| `related_disputed`, `related_since`, `regression`, `refs_extra` | Links to the rest of the site |
| `log[]`, `last_reviewed` | Every change, dated |

The field checklist of the handoff maps as follows: `entry_id` → `id`; `document`, `session`, `primary_source`, `edition`, `source_verified` → `texts[]` and `source_verified`; `propositions[]`, `formal_object`, `binding_status`, `degree_of_assent` → `propositions[]` (`assent`); `qualifications`; `related_entries[]` → computed from `texts` and `propositions`; `contested_reception` → `reception`; `reconciliation_hypothesis` → `hypothesis`; `strongest_objection` → `objection`; `verdict`; `confidence`; `research_stage` → `stage`; `last_reviewed`.

## What the build refuses

- A missing case, or the cases out of order.
- A label outside the controlled vocabularies.
- A quotation that is not found word for word in the entry it cites (accents and curly quotes aside).
- A Denzinger number in prose (`n. 1234`, `DS 3074`, `DH 2001`) that no entry carries. Numbers still to verify go in `gaps`, nowhere else.
- `demonstrated_concord` on any case whose primary sources are not all verified, whose verdict is provisional, or which rests on an N or U claim.
- On D1: any verdict of concord while a pass condition fails, and `demonstrated_concord` while any condition is not a pass.

## Working on a case

1. Retrieve the text named in `next_source` and record it in `texts[]`, with the edition. Set `verified` only after reading it in that edition.
2. Add or correct propositions. Quote only from entries in the collection; for other texts use `says` and `ext`.
3. Rerun the matrix and the tests. If the result changes, change the verdict, even if it goes against the proposed reading.
4. Add a line to `log`, update `last_reviewed`, and move the item out of `gaps`.
5. `python3 build/build.py` and `python3 -m unittest discover -s tests`.

## Revising the method as evidence changes

Protocol v0.4 records the status of each witness, the claim it bears on, the strongest rival reading and the evidence that could change the result. For a contested act, assess the event, the authority to act, and later reception in their own right. A draft or a canonist’s argument can establish that an explanation was available to historical actors. Its legal authority is a further question.

When an authority revokes a document as a precaution, find independent evidence for its original authorisation and legal force. A record of the document and the order withdrawing it can establish what they said and how they differ. The original act may still require authentication.

Test the wording of a decree separately from its occasion and its application to particular people.

When a change affects the method, record the earlier test and apply the revised test to the case. Preserve the previous verdict and show the effect of the change.

## The regression subset

The ten cases of the earlier guide *Reading a condemnation* (`READING_CASES` in `app.js`) are kept unchanged and listed in `regression`, with the new cases that take them further. Eckhart, Fénelon and Rosmini have no new case yet.

## Assumptions made in version 0.2

- The "original ten" of the handoff are taken to be the ten cases of *Reading a condemnation*.
- The furthest stage drafted is recorded as `stage`; most cases reached the adversarial review on the texts the site holds, but stage 1 (retrieval in a critical edition) is not complete for any case, which `source_verified: false` records.

## Verification log

The verification log of the sealed case is kept with it, encrypted. See "Sealed research" in the README.

## Protocol versions

Each change to the protocol is listed in `meta.changes`, newest first. A reworded condition keeps its earlier wording in `gate.history`, and a case re-judged under a new version keeps its earlier verdict in `verdict_history`. The build refuses a change list that does not start with the current version, and a verdict history whose last entry differs from the current verdict or confidence. Stage 11 means the reader-facing case is complete with the current verdict, sources and open objections. Source verification is tracked separately.
