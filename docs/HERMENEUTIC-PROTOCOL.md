# Hermeneutic of ecclesial continuity: the research protocol

Version 0.4, 18 November 2026. Reader: <https://jcalepos146.github.io/denzinger/#continuity>

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
| `id`, `group`, `title`, `question` | A1–A5, B1–B7, C1–C6, D1–D6; the question is a test, not a predetermined answer |
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

When a change affects the method, record the earlier test and apply the revised test to the case. Preserve the previous verdict and show the effect of the change. D1 compares the narrower account of settling disputed titles with the proposal that notorious and incorrigible scandal can make an otherwise legitimate pope subject to a council. The seven conditions continue to govern both. [D1 evidence review](https://jcalepos146.github.io/denzinger/#case-D1-sources)

## The regression subset

The ten cases of the earlier guide *Reading a condemnation* (`READING_CASES` in `app.js`) are kept unchanged and listed in `regression`, with the new cases that take them further. Eckhart, Fénelon and Rosmini have no new case yet.

## Assumptions made in version 0.2

- The "original ten" of the handoff are taken to be the ten cases of *Reading a condemnation*.
- The furthest stage drafted is recorded as `stage`; most cases reached the adversarial review on the texts the site holds, but stage 1 (retrieval in a critical edition) is not complete for any case, which `source_verified: false` records.
- Basel's session numbers and dates in the D1 inventory were checked on 18 November 2026 against Tanner's *Decrees of the Ecumenical Councils* (COD, following Mansi 29). The Latin is still to be read (backlog BL6).

## Verification log

- **18 November 2026, D1.** Checked against Tanner (COD): Haec Sancta (sessions 4 and 5), Frequens and the decree on schisms (session 39), sessions 37 and 41, Martin V's conciliariter declaration (session 45), Basel sessions 2, 3, 11, 16, 18–21, 23 and 25, Moyses vir Dei (Florence, session 7) and Lateran V session 11. The wording on the site held. The check found a text the draft had missed: Basel session 11 (27 April 1433) makes it a general law that a pope who dissolves or moves any council in session without its consent is suspended after four months. Pass condition 3 moved from undetermined to fail, and the hypothesis was narrowed. Not reachable: the Latin of Basel over a verified connection, and Dudum sacrum, which Tanner does not print. The changes are applied in a separate, dated step so they can be traced.
- **18 November 2026, D1, second step.** *A Companion to the Council of Basel* (Brill, 2017) located *Dudum sacrum* (Mansi 29, cols. 78–90) and supplied Eugene IV's letter to the doge (1433) and *Etsi non dubitemus* (1441). Finke, *Acta* IV, located for the Falkenberg trial and for Aragon and Castile.
- **18 November 2026, D1, third step.** *Dudum sacrum* (15 December 1433) read in Mansi 29, cols. 78–79 (the 1904 Paris reprint on archive.org, checked against the page images). It declares the council lawfully continued from its beginning and the dissolution void, and adheres to the council "pure, simpliciter & cum effectu", in words almost identical to the form the council prescribed at session 14 (cols. 73–74). It approves no decree, names neither Haec Sancta nor session 11, and states no principle about dissolution. Pass condition 3 moved from fail back to undetermined, for the narrower hypothesis only; the 1446–1447 instruments now decide it.
- **18 November 2026, D1, fourth step.** The 1447 settlement read in Mercati, *Raccolta di concordati* (1919), pp. 168–170 and 176–177, checked against the page images. *Ad ea ex debito* receives Constance and Frequens by name and does not mention Basel; a separate bull lets the German nation use the Basel decrees accepted by Albert II, pending negotiation, as an injury to the Apostolic See; the protest holds as not granted anything that derogates from its authority. Condition 3 stays undetermined, now resting on two items: the 1446 instructions (B13, not found in the Raynald OCR) and the list of decrees in the Acceptation of Mainz (1439).
- **18 November 2026, D1, fifth step.** Both read in C. G. Koch, *Sanctio pragmatica Germanorum illustrata* (1789; Bayerische Staatsbibliothek), checked against the page images. The Acceptation of Mainz lists sessions 1 (Frequens), 12, 15, 19, 20, 21, 23, 30 and 31, not session 11 (pp. 95–99). The 1446 instructions (22 July 1446) receive Constance and Basel "ab ejus initio usque ad translationem per nos factam", saving "the power given by Christ in the person of blessed Peter" (p. 175). Condition 3 moved to partly met. D1 remains unresolved because condition 4 fails.
- **18 November 2026, protocol v0.3.** Pass condition 4 reworded at the user's request: "Give an objective criterion for the emergency that a council could never invoke against a certain and peacefully accepted pope; show that the historical case met it under each rival account of which papal line was legitimate, and who convoked the council under each. A full procedure for future cases is not required." The v0.2 wording ("Specify who discerns an emergency and who can convoke a legitimate council"), the reason and a disclosure that the change came after D1 failed are kept in `gate.history` and shown on the site. D1 now carries lineage counterfactuals (Roman, Pisan, Avignon, doubtful pope). Condition 4 moved to partly met; D1's verdict moved to plausible concord, low confidence, and its `verdict_history` keeps the v0.2 verdict (unresolved). The hinge left is John XXIII's acceptance of his deposition (Finke, Acta II–III).
- **18 November 2026, D1, seventh step.** John XXIII's consent read in Finke, *Acta* II (1923), pp. 40 (Fillastre) and 249–250 (Cerretanus), checked against the page images: before the sentence he promised in writing to ratify it ("approbo, confirmo ac scienter et libere volo adimplere"); after the sentence of 29 May 1415 "papa sentencie acquievit et ex habundanti renunciavit". Under the Pisan scenario the deposition therefore took effect by consent; the live objection is that the consent was given in detention. Condition 4 stays partly met because of the Avignon scenario; the next source is the sentence deposing Benedict XIII (session 37).
- **18 November 2026, D1, eighth step.** The sentence against Benedict XIII (Constance, session 37) read in Mansi 27, col. 1141, checked against the page image. It "pronunciat, decernit et declarat" him a pertinacious heretic against the article "Unam sanctam catholicam Ecclesiam", "a Deo ejectum" and "ipso jure privatum", and only then, "quatenus de facto papatum … tenet", "ad omnem cautelam privat, deponit & abjicit". Under the Avignon scenario the council's act is declaratory. Condition 4 moved to pass under v0.3; the dependence on the classical thesis of the heretical pope, and on treating schism as heresy, is recorded under conditions 6 and 7. D1 remains plausible concord, low confidence.
- **18 November 2026, D1, ninth step.** Basel session 11 read in the Latin, Mansi 29, cols. 53–55, checked against the page image. Besides automatic suspension it provides that "papalis administratio ad sacrum Concilium ipso jure devolvatur", and it binds every future lawful council. Recorded as a contradiction with Vatican I resolved by non-reception, not by interpretation.

- **18 November 2026, D1, publication review.** Mansi 27, cols. 717–719 records Cossa’s 31 May 1415 oath, ratification and express renunciation while detained. Fillastre reports a second ratification in Florence after Cossa gained his liberty in 1419 (Finke II, pp. 169–170). This strengthens the Pisan scenario while leaving the legal effect of detention in 1415 open. [Notarial instrument](https://archive.org/details/sacrorumconcilio0027joan/page/n372/mode/1up) · [Fillastre](https://archive.org/details/actaconciliicons02counuoft/page/169/mode/2up)
- Read the Latin of Basel sessions 2–3 in Mansi 29, cols. 21–26, alongside session 11, cols. 53–55. Session 2 expressly protects Basel, session 3 applies that claim to Eugene IV’s dissolution, and session 11 extends it to future councils. The 1446 reservation and the Mainz list support the non-reception of session 11’s general rule. [Sessions 2–3](https://archive.org/details/sacrorumconcilio0029vari/page/n26/mode/2up) · [Session 11](https://archive.org/details/sacrorumconcilio0029vari/page/n42/mode/2up)
- Read Martin V’s session 45 declaration in Hardt IV, cols. 1557–1558, and Mansi 27, col. 1201. It answers the Falkenberg petition, qualifies approval by matters of faith and *conciliariter*, and leaves the reception of *Haec Sancta* disputed. Pius II’s *In minoribus agentes* distinguishes the situation in which an undoubted Roman pontiff holds office. All four chapters of Vatican I’s *Pastor aeternus* were checked in the Holy See’s Latin edition. [Hardt](https://www.digitale-sammlungen.de/en/view/bsb10321568?page=1138,1139) · [Mansi](https://archive.org/details/sacrorumconcilio0027joan/page/n614/mode/1up) · [Vatican I](https://www.vatican.va/archive/hist_councils/i-vatican-council/documents/vat-i_const_18700718_pastor-aeternus_la.html)
- The updated D1 case reaches stage 11. It records a provisional verdict of plausible concord with medium confidence for Constance’s acts settling the schism and Basel’s received acts. Conditions 2, 3, 6 and 7 remain partly met. The source review remains incomplete. Earlier assessments and both versions of condition 4 are recorded in the reader.

## Protocol versions

Each change to the protocol is listed in `meta.changes`, newest first. A reworded condition keeps its earlier wording in `gate.history`, and a case re-judged under a new version keeps its earlier verdict in `verdict_history`. The build refuses a change list that does not start with the current version, and a verdict history whose last entry differs from the current verdict or confidence. Stage 11 means the reader-facing case is complete with the current verdict, sources and open objections. Source verification is tracked separately.
