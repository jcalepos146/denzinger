# Adding and reviewing a source

The inventory is complete for the site's local entries, not for the Church's entire documentary history. Complete document access and complete local transcription are different milestones.

## Publication stages

1. **Identify.** Establish the document, issuer acting in an official or private capacity, genre, signature date and publication date where different, audience, language and canonical bibliographic reference. Do not identify a document by abbreviation alone. Compare its heading and closing formula with the primary source. Record uncertain attributions explicitly.
2. **Catalogue.** Add a record to `src/data/documents.json` with a unique stable id. List the exact existing `entryIds`; use an empty list and `coverage: none` for an external-only document. Record the source URL, language and whether it is a complete document or a source page. Links to unofficial publishers must not be labelled official. A successful HTTP response alone is not identity verification.
3. **Establish provenance and reuse.** Record the original edition, translator, translation edition and permission or public-domain basis. Public accessibility is not permission to republish. If permission is uncertain, link to the full text externally and state what remains unresolved. Inherited material remains visible with its actual review status.
4. **Transcribe.** Preserve source wording, paragraph order, section numbers, footnotes and explicit omissions. Keep downloaded originals and extraction experiments outside the published source tree; record retrieval details and checksums in the review notes. Never silently substitute a different translation. Give new entries stable ids without renumbering existing links.
5. **Compare.** Check the transcription against the named edition, including the opening, closing, every numbered section, notes, nonnumbered passages and appendices. Record omissions. Use `excerpts` for selected passages even when every section is represented. `full-text` requires `completenessEvidence` describing the comparison, edition, scope, date and reviewer. Section counts alone never prove completeness.
6. **Assess authority separately.** Keep genre, issuing body, approval form, audience and doctrinal intent distinct. If proposing a grade, add an entry-level range to `weights.json` with a reason and precise primary sources. Mark the assessment as editorial; do not call an automated inference or a link check theological review. Consult LG 25, Donum Veritatis 17–24, Apostolos Suos 22 and the doctrinal commentary on the Professio fidei. Commission work and private papal scholarship require their own status.
7. **Connect.** Add a relationship only when supported by an exact quotation in the local source. Identify its direction, kind and limits. A topical resemblance is not proof of reaffirmation, correction or doctrinal development. Commentary on a relationship must be marked editorial.
8. **Validate and review.** Run `python3 -m unittest discover -s tests`, `python3 build/build.py --strict`, and `python3 tools/audit_library.py`. Check the source page, a passage permalink, search, the mobile layout and the external links. A human reviewer should check uncertain translations and doctrinal judgments before they are represented as verified. Add a dated changelog entry. Submit a pull request; merging main publishes the site.

## Record template

```json
{
  "id": "document-name",
  "title": "Document title",
  "entryIds": [],
  "issuer": "Issuing body, or pope acting in the stated capacity",
  "genre": "Encyclical",
  "date": "1900-01-01",
  "collection": "Named, bounded collection",
  "sourceLinks": [{
    "url": "https://example.org/document",
    "label": "Full text (publisher)",
    "language": "en",
    "scope": "full-document"
  }],
  "coverage": "none",
  "translation": "Translator and edition, or explicitly unresolved",
  "textVerification": "Not independently proofread",
  "rights": "Reuse basis, or unresolved: link externally",
  "review": {
    "status": "unreviewed",
    "note": "What still needs checking"
  }
}
```

Coverage values: `none`, `excerpts`, `summary`, `editorial`, `unreviewed`, `full-text`. `none` means no local entry text. Inferred inherited source groups are generated during the build and remain `unreviewed` until catalogued explicitly. Do not copy an inferred group into the curated list with a verified label without doing the review.

## Release gates

- **First release: source integrity.** Map every local entry; distinguish explicit records from inferred groups; expose extent, provenance and editorial authority judgments; link primary sources.
- **Second release: discovery and bounded expansion.** Search sources and local passages separately; finish the 16-document Vatican II source catalogue; establish repeatable editorial gates. Local complete texts remain a separate task requiring transcription and reuse review.
- **Third release: evidence and reader feedback.** Validate explicit relationships; provide a public coverage backlog; allow readers to save gaps locally and choose to submit proposals or corrections. Never infer a theological conclusion from an empty search result.
