# verse-status

Check the status and completion of verse collections.

## Overview

The `verse-status` command provides a comprehensive overview of your verse collections, showing what content exists and what's missing. It helps you track progress and identify gaps in your content generation.

## Usage

```bash
# Check specific collection
verse-status --collection hanuman-chalisa

# Check all enabled collections
verse-status --all-collections

# Detailed report with verse-by-verse breakdown
verse-status --collection sundar-kaand --detailed

# JSON output for scripting
verse-status --collection hanuman-chalisa --format json

# Check embeddings status only
verse-status --embeddings-only
```

## Options

| Option | Description |
|--------|-------------|
| `--collection KEY` | Collection key to check |
| `--all-collections` | Check all enabled collections |
| `--detailed` | Show detailed verse-by-verse breakdown |
| `--format {text,json}` | Output format (default: text) |
| `--embeddings-only` | Only check embeddings status |
| `--project-dir PATH` | Project directory (default: current directory) |

## What It Checks

### For Each Verse
- ✓ Verse markdown file exists
- ✓ Devanagari text present in frontmatter
- ✓ Transliteration present
- ✓ Meaning present
- ✓ English translation present
- ✓ Full-speed audio file exists (`audio/{collection}/{verse}_full.mp3`)
- ✓ Slow-speed audio file exists (`audio/{collection}/{verse}_slow.mp3`)
- ✓ Image files exist (checks multiple themes)

### Collection Statistics
- Total verse count
- Completion percentage (verses with all content)
- Count of verses with each content type
- Missing content summary

### Embeddings Status
- Total verses indexed
- Verses per collection
- File size and last modified date
- Missing verses not in embeddings

## Output Examples

### Basic Status

```bash
$ verse-status --collection hanuman-chalisa

============================================================
VERSE COLLECTION STATUS
============================================================

📚 Collection: hanuman-chalisa
   Verses: 43
   Completion: 95.3% (41/43 verses)

   Content Status:
   ├─ Devanagari text:   43/43 verses
   ├─ Translation:       43/43 verses
   ├─ Audio (full):      41/43 verses
   ├─ Audio (slow):      41/43 verses
   └─ Images:            42/43 verses

🔍 Embeddings Status:
   ✓ Total verses indexed: 43
   Collections:
   ├─ hanuman-chalisa                 43 verses

   File: /path/to/data/embeddings.json
   Size: 2.3 MB, Modified: 2026-02-14 10:30:15
```

### Detailed Status

```bash
$ verse-status --collection sundar-kaand --detailed

============================================================
VERSE COLLECTION STATUS
============================================================

📚 Collection: sundar-kaand
   Verses: 20
   Completion: 90.0% (18/20 verses)

   Content Status:
   ├─ Devanagari text:   20/20 verses
   ├─ Translation:       20/20 verses
   ├─ Audio (full):      18/20 verses
   ├─ Audio (slow):      18/20 verses
   └─ Images:            19/20 verses

   Verse Details:
   ├─ verse_01              │ Text:✓ │ Audio:✓✓ │ Image:✓
   ├─ verse_02              │ Text:✓ │ Audio:✓✓ │ Image:✓
   ├─ verse_03              │ Text:✓ │ Audio:✗✗ │ Image:✗
   │  └─ Missing: audio_full, audio_slow, images
   ├─ verse_04              │ Text:✓ │ Audio:✓✓ │ Image:✓
   ...
```

### All Collections

```bash
$ verse-status --all-collections

============================================================
VERSE COLLECTION STATUS
============================================================

📚 Collection: hanuman-chalisa
   Verses: 43
   Completion: 95.3% (41/43 verses)
   ...

📚 Collection: sundar-kaand
   Verses: 20
   Completion: 90.0% (18/20 verses)
   ...

📚 Collection: sankat-mochan-hanumanashtak
   Verses: 8
   Completion: 100.0% (8/8 verses)
   ...

🔍 Embeddings Status:
   ✓ Total verses indexed: 71

============================================================
SUMMARY
============================================================
Collections: 3
Total verses: 71
✓ All verses indexed in embeddings
```

### JSON Output

```bash
$ verse-status --collection hanuman-chalisa --format json
```

```json
{
  "collections": [
    {
      "collection": "hanuman-chalisa",
      "exists": true,
      "verse_count": 43,
      "statistics": {
        "completion_percentage": 95.3,
        "verses_complete": 41,
        "verses_with_audio_full": 41,
        "verses_with_audio_slow": 41,
        "verses_with_images": 42,
        "verses_with_devanagari": 43,
        "verses_with_translation": 43
      },
      "verses": [
        {
          "verse_id": "verse_01",
          "verse_file": {
            "exists": true,
            "size": 1248,
            "modified": "2026-02-10 14:23:10"
          },
          "audio": {
            "full": {
              "exists": true,
              "size": 45632,
              "modified": "2026-02-11 09:15:22"
            },
            "slow": {
              "exists": true,
              "size": 67890,
              "modified": "2026-02-11 09:15:30"
            }
          },
          "images": {
            "modern-minimalist": {
              "exists": true,
              "size": 245678
            }
          },
          "has_devanagari": true,
          "has_transliteration": true,
          "has_meaning": true,
          "has_translation": true
        }
      ]
    }
  ],
  "embeddings": {
    "exists": true,
    "verse_count": 43,
    "collections": {
      "hanuman-chalisa": 43
    }
  }
}
```

## Use Cases

### 1. Track Progress
Check how many verses are complete and what's left to do:
```bash
verse-status --all-collections
```

### 2. Find Missing Content
Use detailed mode to identify specific verses missing content:
```bash
verse-status --collection sundar-kaand --detailed
```

### 3. Verify Embeddings
Check if all verses are indexed for search:
```bash
verse-status --embeddings-only
```

### 4. Scripting and Automation
Use JSON output in scripts:
```bash
# Get completion percentage
verse-status --collection hanuman-chalisa --format json | \
  jq '.collections[0].statistics.completion_percentage'

# Find verses missing audio
verse-status --collection sundar-kaand --format json | \
  jq '.collections[0].verses[] | select(.audio.full == null) | .verse_id'
```

### 5. CI/CD Integration
Check content completeness in automated pipelines:
```bash
#!/bin/bash
# Fail if collection is less than 90% complete

COMPLETION=$(verse-status --collection hanuman-chalisa --format json | \
  jq '.collections[0].statistics.completion_percentage')

if (( $(echo "$COMPLETION < 90" | bc -l) )); then
  echo "Error: Collection is only ${COMPLETION}% complete"
  exit 1
fi
```

## Related Commands

- [`verse-generate`](verse-generate.md) - Generate missing content for verses
- [`verse-embeddings`](verse-embeddings.md) - Update embeddings for search
- [`verse-validate`](verse-validate.md) - Validate verse content (coming soon)

## Exit Codes

- `0` - Success
- `1` - Error (collection not found, invalid arguments)

## Notes

- Checks actual files on disk, not just database records
- Supports multiple image themes (modern-minimalist, traditional, kids-friendly, etc.)
- Completion percentage requires: verse file + both audios + image + devanagari + translation
- Embeddings check compares verses in collections.yml vs. embeddings.json
