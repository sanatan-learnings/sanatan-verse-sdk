# verse-init

Initialize a new verse project with recommended directory structure and template files.

## Synopsis

```bash
verse-init [OPTIONS]
```

## Description

The `verse-init` command scaffolds a new verse collection project with the recommended directory structure, template configuration files, and optional example collections. This is the fastest way to get started with sanatan-verse-sdk.

## Options

### Optional

- `--project-name NAME` - Create project in new subdirectory with given name
- `--collection NAME` - Create collection with template files (can be used multiple times)
- `--num-verses N` - Number of canonical placeholder verse IDs per collection (default: 3)
- `--minimal` - Create minimal structure without example files
- `--update-templates` - Overwrite existing SDK scaffolded templates/assets for existing projects (safe default: no overwrites unless this flag is set)
- `--github-pages ORG REPO` - Set `_config.yml` for a GitHub Pages **project** site: `url: https://ORG.github.io`, `baseurl: /REPO`, and `project_repository_url`. Layouts already use `relative_url` for assets.

## GitHub Pages

New projects can pass **`--github-pages ORG REPO`** with `--project-name` (or after `verse-init` in a new dir). Templates use `relative_url` so images and collection links work under `baseurl`.

Existing repos: run **[verse-site-pages](verse-site-pages.md)** to merge `url`/`baseurl` and refresh `index.html` + collection/verse layouts.

Local preview: open `http://127.0.0.1:4000<BASEURL>/`, or use `_config.local.yml.example` for root-local serve (see project README).

## Examples

### Initialize in Current Directory

```bash
# Initialize with full structure
verse-init

# Initialize with minimal structure
verse-init --minimal
```

This creates the structure in the current directory. You'll be prompted for confirmation if the directory is not empty.

### Create New Project Directory

```bash
# Create new project
verse-init --project-name my-verse-project

# Create with collection
verse-init --project-name hanuman-gpt --collection hanuman-chalisa
```

This creates a new subdirectory with the project name and initializes the structure inside it.

### Add Collections to Existing Project

**Important**: You can run `verse-init --collection` in an existing project to add new collections!

```bash
# In your existing project directory
cd my-existing-project

# Add a new collection
verse-init --collection sundar-kaand --num-verses 60

# Or add multiple collections
verse-init --collection sundar-kaand --collection bhagavad-gita
```

**What happens:**
- ✅ Creates new collection files (doesn't overwrite existing)
- ✅ Appends to `_data/collections.yml` (preserves existing collections)
- ✅ Creates templates for the new collection only

**Safety**: Existing scaffolded files are never overwritten by default. Use `--update-templates` to refresh SDK-managed templates/assets on an existing project.

### Initialize with Collections

```bash
# Single collection with 3 canonical placeholders (default)
verse-init --collection hanuman-chalisa

# Single collection with custom number of verses
verse-init --collection sundar-kaand --num-verses 10

# Multiple collections
verse-init --collection hanuman-chalisa --collection sundar-kaand

# Complete setup
verse-init --project-name my-project \
  --collection hanuman-chalisa --num-verses 43 \
  --collection sundar-kaand --num-verses 60
```

**What gets created for each collection:**
- ✅ Canonical text template: `data/verses/<collection>.yaml`
- ✅ Source text placeholder: `data/sources/<collection>.txt`
- ✅ Sample theme: `data/themes/<collection>/modern-minimalist.yml`
- ✅ Site scenes template (`cover` prompt): `data/scenes/site.yml`
  - Home page hero cover image is generated from `data/scenes/site.yml` into `images/site/<theme>/cover.png`.
- ✅ Collection-aware scene descriptions template (`cover` prompt): `data/scenes/<collection>.yml`
- ✅ Collection/site cover generation wiring (generate via `verse-images --verse cover`; output is normalized to 16:9)
- ✅ Collection landing page: `<collection>/index.html`
- ✅ Collection entry in `_data/collections.yml`

**UI theming defaults:**
- Header banner palette auto-adapts by collection subject (for example, Shiva collections use a blue-toned banner).
- You can override this per collection with `banner_theme` in `_data/collections.yml` (example: `banner_theme: shiva`).

## Created Structure

The command creates the following directory structure:

```
your-project/
├── .env.example                 # API keys template
├── .gitignore                   # Git ignore file
├── README.md                    # Project documentation
├── favicon.ico                  # Default site icon (avoids Jekyll `/favicon.ico` 404 noise)
├── _data/
│   ├── collections.yml          # Collection registry
│   ├── verse-config.yml         # Project defaults
│   └── translations/            # UI translation keys (e.g. en.yml)
├── assets/
│   ├── css/style.css            # Baseline CSS (compact centered home hero; larger hero on collection pages)
│   ├── css/print.css            # Print stylesheet
│   └── js/                      # Baseline JS bundle (navigation/language/theme/guidance)
├── _verses/                     # Verse markdown files
├── data/
│   ├── themes/                  # Theme configurations
│   ├── verses/                  # Canonical verse YAML files
│   ├── scenes/                  # Scene descriptions
│   └── sources/                 # Canonical plain-text source files
├── images/                      # Generated images (gitignored)
└── audio/                       # Generated MP3s (versioned by default)
```

## Template Files

### .env.example

Contains placeholders for required API keys:
- `OPENAI_API_KEY` - For images, embeddings, content generation
- `ELEVENLABS_API_KEY` - For audio generation

### _data/collections.yml

Template for defining collections with example structure.

### _config.yml

Includes Jekyll plugin wiring and configurable header keys:
- `plugins: [jekyll-seo-tag]`
- `title` / `banner_title` — human-readable from the project folder name (e.g. `shiva-gpt` → **Shiva GPT**)
- `banner_subtitle` — short tagline for the **site header** on every page
- `home_hero_subtitle_en` / `home_hero_subtitle_hi` — longer copy under the **home hero** only (so it is not duplicated in the header)

### .gitignore

Configured to ignore:
- Generated images and embeddings (not `audio/` — commit MP3s for static hosting unless you opt out)
- Jekyll build output: `_site/`, `.jekyll-cache/`
- Environment files (.env)
- Python cache files

### README.md

Project documentation with:
- Human-readable project title (from folder slug) and a short note on Jekyll `_site/` vs source
- Setup instructions
- Directory structure explanation
- Links to SDK documentation

### `_layouts/verse.html`

Default verse layout matches the frontmatter that **`verse-generate`** writes, so new projects show full verse UX (original text, transliteration, pronunciation table, word-by-word meanings, literal/interpretive meaning, story, practical application, optional puranic context). Bilingual blocks use `data-lang="en"` / `data-lang="hi"` and the header language switcher.

Expected frontmatter keys (when generated): `title_en`, `title_hi`, `collection_key`, `permalink`, `image`, optional `audio`, `devanagari`, `transliteration`, `phonetic_notes`, `word_meanings`, `literal_translation`, `interpretive_meaning`, `story`, `practical_application`, `previous_verse`, `next_verse`, and optionally `puranic_context` (from `verse-generate --puranic-context`).

## Workflow

For the full lifecycle (init → generate → embeddings → index → deploy), see `docs/end-to-end-workflow.md`.

### New Project with Collection

```bash
# 1. Initialize with collection
verse-init --project-name my-verse-project --collection hanuman-chalisa
cd my-verse-project

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your actual API keys

# 3. Add canonical text
# Edit data/verses/hanuman-chalisa.yaml

# 4. Validate
verse-validate

# 5. Generate first verse
verse-generate --collection hanuman-chalisa --verse 1

#    collection/site cover images are auto-generated in this first-verse flow when OPENAI_API_KEY is available
#    paths: images/cover.png and images/hanuman-chalisa/modern-minimalist/cover.png
```

### Add Collection to Existing Project

```bash
# 1. Navigate to existing project
cd my-existing-project

# 2. Add new collection
verse-init --collection sundar-kaand --num-verses 60

# 3. Add canonical text
# Edit data/verses/sundar-kaand.yaml

# 4. Validate
verse-validate

# 5. Generate first verse
verse-generate --collection sundar-kaand --verse 1

#    collection/site cover images are auto-generated in this first-verse flow when OPENAI_API_KEY is available
#    paths: images/cover.png and images/sundar-kaand/modern-minimalist/cover.png
```

## After Initialization

Once initialized, you should:

1. **Set up API keys**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

2. **Define collections**
   Edit `_data/collections.yml` to add your collections:
   ```yaml
   hanuman-chalisa:
     enabled: true
     name:
       en: "Hanuman Chalisa"
       hi: "हनुमान चालीसा"
     subdirectory: "hanuman-chalisa"
     permalink_base: "/hanuman-chalisa"
     # total_verses is synced after canonical parse:
     # verse-parse-source --collection hanuman-chalisa
   ```

3. **Add canonical verse text**
   Create `data/verses/<collection>.yaml` with Devanagari text

4. **Validate structure**
   ```bash
   verse-validate
   ```

5. **Generate content**
   ```bash
   verse-generate --collection <collection-key> --verse 1
   ```

## Notes

- **Safe for existing projects**: Can add collections to existing projects without overwriting files
- **Prompts for confirmation**: When run in non-empty directory
- **Never overwrites**: Existing files are preserved, only new files are created
- **Appends to collections.yml**: New collections are added to existing registry
- **Creates `.gitignore`**: Configured to prevent committing generated content
- **Template files**: Use current best practices and conventions
- **Multiple uses**: Can be run multiple times to add more collections

## See Also

- [verse-validate](verse-validate.md) - Validate project structure
- [verse-generate](verse-generate.md) - Generate content
- [Usage Guide](../usage.md) - Complete setup guide
