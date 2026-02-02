# Multi-Collection Support

The `verse-embeddings` command now supports processing multiple collections in a single run.

## Features

- **Backward Compatible**: Single collection mode still works exactly as before
- **Multi-Collection Mode**: Process multiple verse collections at once
- **Permalink Support**: Uses actual permalinks from frontmatter instead of generating URLs
- **Collection Metadata**: Adds collection_key and collection_name to verse metadata
- **Merged Output**: Single embeddings.json file with all collections

## Usage

### Single Collection Mode (Backward Compatible)

```bash
# Default behavior - processes _verses/ directory
verse-embeddings --provider openai

# Custom verses directory
verse-embeddings --provider openai --verses-dir ./my_verses --output ./embeddings.json
```

### Multi-Collection Mode

```bash
# Process all enabled collections from collections.yml
verse-embeddings --multi-collection --collections-file ./_data/collections.yml

# With specific provider
verse-embeddings --multi-collection \
  --collections-file ./_data/collections.yml \
  --provider huggingface \
  --output ./data/embeddings.json
```

## Collections File Format

The collections YAML file should follow this structure:

```yaml
hanuman-chalisa:
  key: "hanuman-chalisa"
  name_en: "Hanuman Chalisa"
  name_hi: "हनुमान चालीसा"
  permalink_base: "/chalisa/"
  subdirectory: "hanuman-chalisa"
  enabled: true

sundar-kaand:
  key: "sundar-kaand"
  name_en: "Sundar Kaand"
  name_hi: "सुंदर कांड"
  permalink_base: "/sundar-kaand/"
  subdirectory: "sundar-kaand"
  enabled: true

bajrang-baan:
  key: "bajrang-baan"
  name_en: "Bajrang Baan"
  name_hi: "बजरंग बाण"
  permalink_base: "/bajrang-baan/"
  subdirectory: "bajrang-baan"
  enabled: false
```

### Required Fields

- `key`: Unique identifier for the collection
- `name_en`: English name of the collection
- `subdirectory`: Subdirectory name under `_verses/`
- `enabled`: Boolean to enable/disable collection processing

### Optional Fields

- `name_hi`: Hindi name (used in metadata)
- `permalink_base`: Base URL path (for reference only; actual permalinks come from frontmatter)

## Directory Structure

When using multi-collection mode:

```
project/
├── _data/
│   └── collections.yml
├── _verses/
│   ├── hanuman-chalisa/
│   │   ├── doha_01.md
│   │   ├── verse_01.md
│   │   └── ...
│   ├── sundar-kaand/
│   │   ├── doha_01.md
│   │   └── ...
│   └── bajrang-baan/
│       └── ...
└── data/
    └── embeddings.json
```

## Verse Frontmatter

Each verse markdown file should have frontmatter with a `permalink` field:

```yaml
---
layout: verse
collection_key: "hanuman-chalisa"
permalink: /chalisa/verse_01/
title_en: "Verse 1: Ocean of Knowledge and Virtues"
title_hi: "चौपाई 1: ज्ञान और गुणों का सागर"
verse_number: 1
# ... other fields
---
```

### Key Fields

- `permalink`: Full URL path (used instead of generating URLs)
- `collection_key`: Collection identifier (optional, added by generator in multi-collection mode)
- `title_en` / `title_hi`: Titles in English and Hindi
- `verse_number`: Verse sequence number

## Output Format

The generated `embeddings.json` includes collection metadata:

```json
{
  "model": "text-embedding-3-small",
  "dimensions": 1536,
  "provider": "openai",
  "generated_at": "2026-02-02T...",
  "verses": {
    "en": [
      {
        "verse_number": 1,
        "title": "Verse 1: Ocean of Knowledge and Virtues",
        "url": "/chalisa/verse_01/",
        "embedding": [...],
        "metadata": {
          "devanagari": "...",
          "transliteration": "...",
          "literal_translation": "...",
          "collection_key": "hanuman-chalisa",
          "collection_name": "Hanuman Chalisa"
        }
      },
      {
        "verse_number": 1,
        "title": "Doha 1: ...",
        "url": "/sundar-kaand/doha_01/",
        "embedding": [...],
        "metadata": {
          "collection_key": "sundar-kaand",
          "collection_name": "Sundar Kaand",
          ...
        }
      }
    ],
    "hi": [...]
  }
}
```

### Metadata Fields

In multi-collection mode, each verse includes:
- `collection_key`: The collection's unique identifier
- `collection_name`: The English name of the collection

In single-collection mode, these fields are not added (backward compatible).

## Implementation Details

### Helper Functions

- `load_collections_config(collections_file)`: Loads YAML collections file
- `get_enabled_collections(collections_config)`: Filters enabled collections
- `extract_permalink_from_frontmatter(verse_data)`: Extracts permalink from verse data
- `process_single_collection()`: Single directory processing (original behavior)
- `process_multi_collection()`: Multi-collection processing with metadata

### URL Resolution Priority

1. **Permalink from frontmatter** (preferred): Uses the `permalink` field directly
2. **Generated URL** (fallback): Uses `generate_verse_url()` if no permalink exists

### Collection Processing

In multi-collection mode:
1. Load and parse collections.yml
2. Filter enabled collections
3. For each enabled collection:
   - Find verse files in `_verses/{subdirectory}/`
   - Extract frontmatter and embeddings
   - Add collection metadata (key, name)
   - Use permalink from frontmatter
4. Merge all collections into single output

## Testing

Test single collection mode:
```bash
cd /path/to/project
verse-embeddings --provider openai --verses-dir ./_verses/hanuman-chalisa
```

Test multi-collection mode:
```bash
verse-embeddings --multi-collection --collections-file ./_data/collections.yml
```

Verify output:
```bash
# Check embeddings file
cat data/embeddings.json | jq '.verses.en[] | {title, url, collection: .metadata.collection_key}' | head -20

# Count verses per collection
cat data/embeddings.json | jq '[.verses.en[] | .metadata.collection_key] | group_by(.) | map({key: .[0], count: length})'
```

## Migration Guide

Existing single-collection projects work without any changes. To add multi-collection support:

1. Create a `collections.yml` file with your collections
2. Organize verses into subdirectories under `_verses/`
3. Add `permalink` field to verse frontmatter
4. Use `--multi-collection` flag when generating embeddings

No changes needed to existing scripts or workflows using single-collection mode.
