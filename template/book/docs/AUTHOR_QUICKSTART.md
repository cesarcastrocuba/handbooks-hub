# Author quickstart

This page is the shortest path from an empty repository to a published, listed handbook. It assumes
you are new to the platform; every step names the exact screen or command.

The template uses Quarto, Python and a pinned `handbook-toolkit` package. You do not copy shared
scripts, and you do not need to understand the hub internals to publish a book.

## 1. Create your repository from the template

1. Open <https://github.com/cesarcastrocuba/handbooks-template>.
2. Select **Use this template** and then **Create a new repository**.
3. Choose the owner, a repository name, and **Public** visibility. The catalog and the reading site
   are public, so a private book cannot be listed.
4. Create the repository. GitHub copies the template tree, including `.github/`, into your new
   repository.

If the template repository is not marked as a template yet, ask the Owner. Do not copy the files by
hand: the export and mirror procedure is described in the hub's
[template distribution guide](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/template-distribution.md).

## 2. Configure the repository once

1. **Pages:** open **Settings → Pages** and set **Source** to **GitHub Actions**. The release
   workflow deploys the HTML edition with the same verified bytes it publishes.
2. **Branch protection:** open **Settings → Branches**, add a rule for `main`, require a pull
   request before merging, and require the `ci` status check. This keeps the release branch clean.
3. **Actions:** confirm that workflows are enabled under **Actions → General**. The default
   `GITHUB_TOKEN` of a new repository may create branches and releases; it may not open pull
   requests or change workflow files. The template never asks it to. If your account or organization
   sets the token to read-only, change **Workflow permissions** to **Read and write**; otherwise the
   initialize and release workflows cannot push a branch or a release.

Nothing else is required: the pinned toolkit installs from the committed `requirements.txt`.

## 3. Run Initialize book

1. Open **Actions → initialize-book → Run workflow**.
2. Fill in the title, identifier, author, summary and category. The identifier is a lower-case slug
   such as `platform-handbook`; the summary is at most 280 characters; the category comes from the
   catalog vocabulary.
3. Run the workflow. It rewrites `book.yaml`, `publishing/_quarto.yml`, `publishing/metadata.yaml`,
   `NOTICE.md`, `LICENSE-CODE` and the README title, then runs `make check`.
4. Read the job summary. It prints the branch `init/<id>` and a compare URL.

The workflow refuses to run a second time once the identifier is no longer `template-book`. It does
not open a pull request.

## 4. Open and merge the initialization pull request

1. Open the compare URL from the job summary.
2. Create the pull request. Check that the `ci` workflow passes on the branch.
3. Merge it. The default branch now contains your book identity.

## 5. Write the manuscript

1. Replace `manuscript/chapters/01-example.qmd` with your first chapter.
2. Add one file per chapter under `manuscript/chapters/` and list every file exactly once in
   `manuscript/book.yml`, under `chapters`, `appendices` or `back`.
3. Keep `book.yaml` `status` at `draft` while you write. The descriptor, reading order and
   cross-references are validated on every push.
4. Run the fast checks locally when you can:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   make check
   ```

   `make check` validates the descriptor, the reading order, the cross-reference gate and local
   images. It needs no Quarto. `make full` additionally renders the editions and needs Quarto
   `1.11.9` and Poppler `pdfinfo`. The build writes its verified directory to `../dist`, outside the
   book repository, because the toolkit refuses an output path inside the source tree; use
   `make build OUTPUT=/an/external/path` to change it.

## 6. Publish a release

1. Merge your content to `main` and wait for `ci` to pass.
2. Open **Actions → release → Run workflow**, choose the default branch, and enter the version as
   `X.Y.Z` without a leading `v`.
3. The workflow refuses to run outside the default branch, refuses an existing tag or release,
   refuses a book whose identifier is still `template-book`, runs `make check`, and builds once from
   the exact commit.
4. It publishes every verified file in the build directory as release assets and deploys the HTML
   edition to GitHub Pages. The reading site is
   `https://<owner>.github.io/<repository>/` and the release page is
   `https://github.com/<owner>/<repository>/releases/tag/vX.Y.Z`.

   A release carries seven files: `book-html.zip`, `book.pdf`, `book.docx`, `book.md`,
   `book-source.zip`, `publication-manifest.json` and `SHA256SUMS.txt`. `book.md` is the
   single-file Markdown edition for AI tools and plain-text readers; the HTML ZIP is the edition
   Pages serves.

Never edit the release assets by hand. If a release is wrong, follow the withdrawal procedure in the
hub's [author guide](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/author-guide.md)
instead of replacing files.

## 7. Request catalog listing

1. Keep the release page and the reading site live; the hub verifies both.
2. Open the listing form:
   <https://github.com/cesarcastrocuba/handbooks-hub/issues/new?template=request-listing.yml>
3. Provide the repository URL, the release tag and URL, the reading site URL, the summary, the
   categories, and confirm the license, the third-party rights review and that the release was built
   by the pinned toolkit.
4. The Owner reviews the request and merges a manual catalog pull request. The first listing is
   always manual; `catalog-update` only moves an already listed book to a newer release.
5. After the merge, the portal rebuilds automatically and links to your release.

## Where to go next

- [Hub author guide](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/author-guide.md):
  the whole lifecycle, release contents, listing and withdrawal rules, FAQ.
- [Book upgrade guide](https://github.com/cesarcastrocuba/handbooks-hub/blob/main/docs/book-upgrade.md):
  upgrade the toolkit pin deliberately.
- [README](../README.md): the file map, the build commands and the repository rules.

The toolkit supplies a web cover, part groups, caption list pages, edition footer and social
metadata. Keep the canonical reading order focused on your manuscript; do not add generated pages
to manuscript/book.yml. See [Figures](figures.md) for the original example illustration and image
format/alt-text guidance. Metadata subtitle/author/status and optional site_url, release_url and
edition_urls belong in publishing/metadata.yaml. Supply release/download URLs only after they are
known; preview builds omit them.
