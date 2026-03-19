# verse-site-pages

Configure an **existing** verse project for **GitHub Pages** as a **project site** (`https://ORG.github.io/REPO/`) and refresh Jekyll templates so images and links use `relative_url` (correct under `baseurl`).

## Synopsis

```bash
verse-site-pages --org ORG --repo REPO [--project-dir DIR]
verse-site-pages --url URL --baseurl PATH [--project-dir DIR]
```

## Description

- Merges into `_config.yml`: `url`, `baseurl`, and `project_repository_url` (when using `--org`/`--repo`, or via `--project-repository-url`).
- Overwrites **`index.html`**, **`_layouts/collection.html`**, and **`_layouts/verse.html`** with SDK templates that use `relative_url` for site-relative assets and collection links.

Safe to run **multiple times** on the same repo.

Requires an existing `_config.yml` (run `verse-init` first).

## Options

| Option | Description |
|--------|-------------|
| `--org ORG` | GitHub org or username (use with `--repo`) |
| `--repo REPO` | Repository name; `baseurl` becomes `/REPO` |
| `--url URL` | Pages site URL (e.g. `https://myorg.github.io`) |
| `--baseurl PATH` | Path prefix (e.g. `/my-repo`; use `""` for user/org root site if needed) |
| `--project-repository-url URL` | Optional override for `project_repository_url` in `_config.yml` |
| `--project-dir DIR` | Project root (default: current directory) |

## Examples

```bash
cd my-verse-project
verse-site-pages --org sanatan-learnings --repo hanuman-site
```

Custom URL/baseurl:

```bash
verse-site-pages --url https://example.github.io --baseurl /my-project
```

## Local preview

- **Same paths as production:** `bundle exec jekyll serve` → open `http://127.0.0.1:4000<BASEURL>/`.
- **Site root locally:** copy `_config.local.yml.example` to `_config.local.yml`, then  
  `bundle exec jekyll serve --config _config.yml,_config.local.yml` → `http://127.0.0.1:4000/`.

## See also

- [verse-init](verse-init.md) — `--github-pages ORG REPO` for **new** projects
- GitHub issue [#152](https://github.com/sanatan-learnings/sanatan-verse-sdk/issues/152)
