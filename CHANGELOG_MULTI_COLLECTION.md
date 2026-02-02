# Multi-Collection Support - Changelog

## Overview

Added multi-collection support to the `verse-embeddings` command, allowing processing of multiple verse collections in a single run while maintaining full backward compatibility.

## Changes Made

### 1. New Command-Line Arguments

**`--multi-collection`** (flag)
- Enables multi-collection processing mode
- When set, processes multiple collections from a configuration file
- Default: disabled (single-collection mode)

**`--collections-file`** (path)
- Path to YAML file containing collections configuration
- Required when `--multi-collection` is used
- Format: See collections.yml specification below

### 2. New Helper Functions

**`load_collections_config(collections_file)`**
- Loads and parses collections YAML configuration file
- Returns dictionary of collection metadata
- Validates file exists before processing

**`get_enabled_collections(collections_config)`**
- Filters collections to only those with `enabled: true`
- Returns dictionary of enabled collections
- Used to skip disabled collections during processing

**`extract_permalink_from_frontmatter(verse_data)`**
- Extracts `permalink` field from verse frontmatter
- Returns None if permalink not present
- Used to prefer actual permalinks over generated URLs

**`process_single_collection(verses_dir, embed_func, client_or_model, config)`**
- Refactored original processing logic for single directory
- Maintains backward compatibility with existing behavior
- Returns tuple of (verses_en, verses_hi) lists

**`process_multi_collection(collections_file, base_verses_dir, embed_func, client_or_model, config)`**
- New function for multi-collection processing
- Iterates through enabled collections
- Adds collection metadata to each verse
- Returns merged tuple of (verses_en, verses_hi) lists

### 3. Modified Functions

**`process_verse_file(file_path, embed_func, client_or_model, config, collection_metadata=None)`**
- Added optional `collection_metadata` parameter
- When provided, adds `collection_key` and `collection_name` to verse metadata
- Uses permalink from frontmatter if available, otherwise generates URL
- Maintains backward compatibility (None = single-collection mode)

**`main()`**
- Added argument parsing for new flags
- Validates that `--collections-file` is provided when `--multi-collection` is used
- Routes to appropriate processing function based on mode
- Creates output directory if it doesn't exist

### 4. URL Resolution Changes

Priority order for verse URLs:
1. **Permalink from frontmatter** (preferred): Uses `permalink` field directly
2. **Generated URL** (fallback): Uses existing `generate_verse_url()` function

This ensures correct collection-specific URLs (e.g., `/chalisa/verse_01/` instead of `/verses/verse_01/`).

### 5. Metadata Enhancements

In multi-collection mode, each verse includes additional metadata:

```json
{
  "metadata": {
    "devanagari": "...",
    "transliteration": "...",
    "literal_translation": "...",
    "collection_key": "hanuman-chalisa",
    "collection_name": "Hanuman Chalisa"
  }
}
```

In single-collection mode, collection fields are NOT added (backward compatible).

## Collections Configuration Format

The collections YAML file should follow this structure:

```yaml
collection-key:
  key: "collection-key"              # Required: Unique identifier
  name_en: "Collection Name"         # Required: English name
  name_hi: "हिंदी नाम"               # Optional: Hindi name
  subdirectory: "collection-dir"     # Required: Directory under _verses/
  permalink_base: "/collection/"     # Optional: Base URL (for reference)
  enabled: true                      # Required: Enable/disable collection
```

### Required Fields
- `key`: Unique identifier matching the YAML key
- `name_en`: English name (used in metadata)
- `subdirectory`: Directory name under `_verses/`
- `enabled`: Boolean flag to enable/disable

### Optional Fields
- `name_hi`: Hindi name
- `permalink_base`: Base URL (for documentation; actual URLs from frontmatter)
- `description_en`, `description_hi`: Collection descriptions
- `author_en`, `author_hi`: Author information
- `icon`: Display icon/emoji

## Backward Compatibility

All existing functionality is preserved:

✓ **Single-collection mode** (default) works exactly as before
✓ **Existing command-line arguments** unchanged
✓ **Output format** compatible (single-collection mode)
✓ **No breaking changes** to verse processing
✓ **Library usage** remains the same

Existing scripts and workflows require no modifications.

## Usage Examples

### Single Collection (Backward Compatible)

```bash
# Default behavior - unchanged
verse-embeddings --provider openai

# Custom directory - unchanged
verse-embeddings --verses-dir ./my_verses --output ./embeddings.json
```

### Multi-Collection

```bash
# Process all enabled collections
verse-embeddings --multi-collection --collections-file ./collections.yml

# With specific provider and output
verse-embeddings \
  --multi-collection \
  --collections-file ./_data/collections.yml \
  --provider huggingface \
  --output ./data/embeddings.json
```

## Testing

A comprehensive test suite is included:

```bash
# Run tests
python3 test_multi_collection.py

# Run example (dry run)
./examples/multi_collection_example.sh
```

Test coverage:
- Collections configuration loading
- Enabled/disabled filtering
- Verse directory validation
- Permalink extraction from frontmatter
- Collection metadata structure
- URL resolution priority

## File Changes

### Modified Files
- `verse_content_sdk/embeddings/generate_embeddings.py`
  - Added 5 new functions
  - Modified 2 existing functions
  - Added 2 new command-line arguments
  - ~150 lines added

### New Files
- `MULTI_COLLECTION_USAGE.md` - User documentation
- `CHANGELOG_MULTI_COLLECTION.md` - This file
- `test_multi_collection.py` - Test suite
- `examples/multi_collection_example.sh` - Example script

## Migration Guide

### For Single-Collection Projects
No changes needed. Continue using existing commands.

### For Multi-Collection Projects

1. **Create collections.yml**
   ```yaml
   my-collection:
     key: "my-collection"
     name_en: "My Collection"
     subdirectory: "my-collection"
     enabled: true
   ```

2. **Organize verses**
   ```
   _verses/
   ├── my-collection/
   │   ├── verse_01.md
   │   └── ...
   └── another-collection/
       └── ...
   ```

3. **Add permalinks to frontmatter**
   ```yaml
   ---
   permalink: /my-collection/verse_01/
   # ... other fields
   ---
   ```

4. **Generate embeddings**
   ```bash
   verse-embeddings --multi-collection --collections-file ./collections.yml
   ```

## Dependencies

No new dependencies required. Uses existing:
- `yaml` (already required)
- `pathlib` (standard library)
- `argparse` (standard library)

## Performance Considerations

- Multi-collection mode processes collections sequentially
- API rate limiting applies to total verses across all collections
- Output file size scales linearly with number of verses
- Memory usage proportional to total embeddings (same as before)

## Future Enhancements

Potential improvements (not implemented):
- Parallel collection processing
- Per-collection output files
- Collection filtering by name/pattern
- Incremental updates (only changed verses)
- Progress bars for multi-collection processing

## Version

This feature was implemented for verse-content-sdk version 0.1.x.

## Author

Implementation: Claude Code (Anthropic)
Date: 2026-02-02
