# Deploy Eodem Sensu with the source editions

This package contains the repository source and the GitHub Pages workflow. The public site adds a searchable **Source editions** page under **Sources and coverage** with 343 edition references and four selected Latin transcriptions. Most source records link to the edition for reading. Your five original ZIPs supply the complete local collection for research, collation and review.

## Deploy at the existing GitHub Pages address

1. Extract the package into the root of a current local checkout of [jcalepos146/denzinger1.0](https://github.com/jcalepos146/denzinger1.0). Keep the `.github` directory. This snapshot is based on commit `d597ef7`. If your checkout has newer work, copy only the integration files listed in the command below and merge any overlapping edits.
2. In [Settings → Pages](https://github.com/jcalepos146/denzinger1.0/settings/pages), set **Build and deployment → Source** to **GitHub Actions**. The source setting controls whether the Pages address serves the built reader or the branch’s README.
3. Commit and push the extracted changes to `main`, or merge them through a pull request. Run these from the checkout root.

   ```sh
   git add .github/workflows/pages.yml .gitignore DEPLOYMENT.md build/build.py build/source_editions.py src/app.js src/sw.js src/data/source-editions.json tools/source_archive.py tests/test_source_archive.py
   git diff --cached --name-only
   git commit -m "Integrate source editions and local research preview"
   git push origin main
   ```

4. The **Build and publish** workflow tests the source and deploys the generated `dist/`. If the files are already on `main`, select **Run workflow** from the [workflow page](https://github.com/jcalepos146/denzinger1.0/actions/workflows/pages.yml) and choose `main`. When it succeeds, open [the reader](https://jcalepos146.github.io/denzinger1.0/) and [Source editions](https://jcalepos146.github.io/denzinger1.0/editions/).

For another static host, run `python3 build/build.py --url https://example.com/your-site/` and deploy the contents of `dist/` as the site root. A ZIP of this repository is source input for the build.

## Preview all five archives on your computer

Put the five original ZIPs in a directory outside the repository, or in the ignored `source-archives/` directory. The original names and copies with numeric suffixes such as `(1)` work. Start the preview using Python 3.10 or later.

```sh
python3 tools/source_archive.py "/path/to/folder-with-the-five-ZIPs"
```

Open the printed address. **Browse local source ZIPs** opens the archive view. Search by title or file name, or select **Include text inside files**. Text, JSON and CSV open as plain text. Scans download from your original archives. The preview listens on this computer only and never extracts ZIP members into the generated site. Press Ctrl+C to stop it.

## Sealed scholarship and source review

The public build uses the checked-in edition catalogue and the repository’s existing encrypted research payload. It omits the original ZIPs, their research indexes, unreviewed OCR and scans, and any decrypted research in `private/`. The established password flow and ciphertext for the Constance, Basel and Vatican I scholarship still apply. Publication of revised sealed scholarship uses the existing `node tools/seal/seal.mjs seal` process and the password you already use. The local preview requires local access to the original source ZIPs and does not open or change that encrypted payload.

Before adding more full text to the public source catalogue, verify the edition, permission to redistribute the text, and whether provenance or notes belong to the sealed research. Preserve existing Denzinger numbers and doctrinal grades when adding source witnesses.
