# Quick Start: Multi-Collection Embeddings

## TL;DR

Process multiple verse collections in one command:

```bash
verse-embeddings --multi-collection --collections-file ./collections.yml
```

## Prerequisites

1. **Collections YAML file** with enabled collections
2. **Organized verse directories** under `_verses/`
3. **Permalink fields** in verse frontmatter
4. **API key** (if using OpenAI provider)

## Setup (5 minutes)

### Step 1: Create collections.yml

```yaml
hanuman-chalisa:
  key: "hanuman-chalisa"
  name_en: "Hanuman Chalisa"
  subdirectory: "hanuman-chalisa"
  enabled: true

sundar-kaand:
  key: "sundar-kaand"
  name_en: "Sundar Kaand"
  subdirectory: "sundar-kaand"
  enabled: true
```

### Step 2: Organize verses

```
_verses/
├── hanuman-chalisa/
│   ├── doha_01.md
│   ├── verse_01.md
│   └── ...
└── sundar-kaand/
    ├── doha_01.md
    └── ...
```

### Step 3: Add permalinks to frontmatter

In each verse markdown file:

```yaml
---
permalink: /chalisa/verse_01/
title_en: "Verse 1: Ocean of Knowledge"
# ... other fields
---
```

### Step 4: Generate embeddings

```bash
# Using OpenAI (default)
verse-embeddings --multi-collection --collections-file ./_data/collections.yml

# Using HuggingFace (free, local)
verse-embeddings --multi-collection \
  --collections-file ./collections.yml \
  --provider huggingface
```

## Output

Single `embeddings.json` file with all collections:

```json
{
  "model": "text-embedding-3-small",
  "provider": "openai",
  "verses": {
    "en": [
      {
        "title": "Verse 1: Ocean of Knowledge",
        "url": "/chalisa/verse_01/",
        "embedding": [...],
        "metadata": {
          "collection_key": "hanuman-chalisa",
          "collection_name": "Hanuman Chalisa"
        }
      },
      {
        "title": "Doha 1: ...",
        "url": "/sundar-kaand/doha_01/",
        "metadata": {
          "collection_key": "sundar-kaand",
          "collection_name": "Sundar Kaand"
        }
      }
    ]
  }
}
```

## Verify Output

```bash
# Check verse count per collection
cat data/embeddings.json | jq '[.verses.en[] | .metadata.collection_key] | group_by(.) | map({collection: .[0], count: length})'

# View sample verses with collection info
cat data/embeddings.json | jq '.verses.en[] | {title, url, collection: .metadata.collection_key}' | head -20

# File size
ls -lh data/embeddings.json
```

## Common Issues

### "Collections file not found"
Make sure path to collections.yml is correct:
```bash
ls -la ./_data/collections.yml  # or wherever it is
```

### "No enabled collections"
Check that at least one collection has `enabled: true`:
```bash
cat collections.yml | grep "enabled:"
```

### "Verses directory not found"
Verify subdirectory names match:
```bash
ls -la _verses/
```

### "No permalink in frontmatter"
Add permalink field to verse files:
```yaml
permalink: /collection-name/verse-name/
```

## Single Collection Mode (Backward Compatible)

Old way still works:
```bash
verse-embeddings --verses-dir ./_verses/hanuman-chalisa
```

## Cost Estimation

**OpenAI (text-embedding-3-small)**
- ~$0.02 per 1M tokens
- Average verse: ~750 tokens
- 2 languages per verse
- Example: 40 verses × 2 languages × 750 tokens = 60,000 tokens
- Cost: ~$0.0012 per collection

**HuggingFace**
- Free (runs locally)
- One-time model download (~100MB)
- Slower but no API costs

## Next Steps

1. **Test with one collection** first
2. **Verify output** structure and URLs
3. **Enable more collections** as needed
4. **Integrate with search** (semantic search using embeddings)

## Full Documentation

- [MULTI_COLLECTION_USAGE.md](MULTI_COLLECTION_USAGE.md) - Complete usage guide
- [CHANGELOG_MULTI_COLLECTION.md](CHANGELOG_MULTI_COLLECTION.md) - Technical details
- [test_multi_collection.py](test_multi_collection.py) - Validation tests
- [examples/multi_collection_example.sh](examples/multi_collection_example.sh) - Example script

## Questions?

Check the full documentation or examine the implementation:
- Implementation: `verse_content_sdk/embeddings/generate_embeddings.py`
- Test suite: `test_multi_collection.py`
- Example usage: `examples/multi_collection_example.sh`
