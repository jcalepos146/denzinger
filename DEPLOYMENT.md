# Deploy Eodem Sensu

The reader is published at <https://jcalepos146.github.io/denzinger/>. The repository contains a generated site at its root for GitHub Pages branch publishing. Make edits under `src/` and regenerate the public files using the Python build.

## Build and preview

```sh
python3 -m unittest discover -s tests
python3 build/build.py --repo jcalepos146/denzinger --url https://jcalepos146.github.io/denzinger/
python3 -m http.server -d dist
```

Open <http://localhost:8000/> to preview the reader. The build output also contains the standalone entry pages, source editions, public exports and redirects.

## Publish

With **Deploy from a branch** selected in [Pages settings](https://github.com/jcalepos146/denzinger/settings/pages), GitHub serves the generated site at the root of `main`. After building, mirror the contents of `dist/` into the repository root, keeping the source directories and skipping the generated `.nojekyll` marker so Pages applies the exclusions in `_config.yml`. Review any removed entry or redirect pages and commit the generated changes alongside the source changes.

For automatic builds, select **GitHub Actions** as the Pages publishing source and run **Build and publish** on `main`. It builds and deploys `dist/` directly.

## Local source archives and sealed research

Keep the five original archives outside the checkout or in the ignored `source-archives/` directory. Preview them with Python 3.10 or later.

```sh
python3 tools/source_archive.py "/path/to/folder-with-the-five-ZIPs"
```

The site publishes the vetted edition catalogue and the existing encrypted scholarship. Use the local preview for raw archives and keep decrypted research in the ignored `private/` directory. The preview listens on this computer and never extracts the source files into the public build. See [Sealed research](README.md#sealed-research) for the password workflow.
