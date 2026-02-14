# verse-sync

Sync verse text with canonical source from `data/verses/{collection}.yaml` (or `.yml`).

## Overview

The `verse-sync` command updates verse files to match the normative text stored in local YAML files, ensuring text accuracy and consistency across your verse collection. It reads canonical text from `data/verses/{collection}.yaml` (or `.yml`) and updates the `devanagari` field in verse markdown files while preserving other fields.

## Usage

```bash
# Sync specific verse
verse-sync --collection sundar-kaand --verse chaupai_01

# Sync all verses in collection
verse-sync --collection sundar-kaand --all

# Dry run (preview changes)
verse-sync --collection sundar-kaand --verse chaupai_01 --dry-run

# Fix all validation mismatches
verse-sync --collection sundar-kaand --fix-mismatches

# Sync multiple specific verses
verse-sync --collection sundar-kaand --verse chaupai_01 --verse chaupai_02 --verse doha_01
```

## Options

| Option | Description |
|--------|-------------|
| `--collection KEY` | **Required.** Collection key (e.g., sundar-kaand) |
| `--verse ID` | Specific verse ID to sync (can be used multiple times) |
| `--all` | Sync all verses in collection |
| `--fix-mismatches` | Sync only verses with validation mismatches |
| `--dry-run` | Preview changes without writing to files |
| `--project-dir PATH` | Project directory (default: current directory) |

## How It Works

1. **Reads canonical text** from `data/verses/{collection}.yaml` (or `.yml`)
2. **Parses verse file** in `_verses/{collection}/{verse_id}.md`
3. **Updates devanagari field** in frontmatter
4. **Preserves other fields** (transliteration, meaning, translation, etc.)
5. **Writes updated file** or shows preview in dry-run mode

## Output Examples

### Sync Specific Verse

```bash
$ verse-sync --collection sundar-kaand --verse chaupai_01

============================================================
VERSE SYNC
============================================================

Collection: sundar-kaand
Source: data/verses/sundar-kaand.yaml

============================================================
SYNC RESULTS
============================================================

✓ chaupai_01             - Updated successfully

============================================================
SUMMARY
============================================================
Total verses: 1
Updated: 1
Errors: 0
Already synced: 0
```

### Dry Run (Preview)

```bash
$ verse-sync --collection sundar-kaand --verse chaupai_02 --dry-run

============================================================
VERSE SYNC - DRY RUN (Preview Only)
============================================================

Collection: sundar-kaand
Source: data/verses/sundar-kaand.yaml

============================================================
SYNC RESULTS
============================================================

📝 chaupai_02             - Would be updated
   Old: जामवंत के बचन सुहाए।
   New: जामवंत के बचन सुहाए।।

============================================================
SUMMARY
============================================================
Total verses: 1
Updated: 1
Errors: 0
Already synced: 0

⚠️  This was a dry run. Run without --dry-run to apply changes.
```

### Fix Validation Mismatches

```bash
$ verse-sync --collection sundar-kaand --fix-mismatches

============================================================
VERSE SYNC
============================================================

Collection: sundar-kaand
Source: data/verses/sundar-kaand.yaml

Finding verses with validation mismatches...
Found 3 verse(s) with mismatches

============================================================
SYNC RESULTS
============================================================

✓ chaupai_02             - Updated successfully
✓ chaupai_03             - Updated successfully
  doha_01                - Already matches normative text

============================================================
SUMMARY
============================================================
Total verses: 3
Updated: 2
Errors: 0
Already synced: 1
```

### Sync All Verses

```bash
$ verse-sync --collection sundar-kaand --all

============================================================
VERSE SYNC
============================================================

Collection: sundar-kaand
Source: data/verses/sundar-kaand.yaml

============================================================
SYNC RESULTS
============================================================

  shloka_01              - Already matches normative text
✓ chaupai_01             - Updated successfully
✓ chaupai_02             - Updated successfully
  chaupai_03             - Already matches normative text
  doha_01                - Already matches normative text

============================================================
SUMMARY
============================================================
Total verses: 5
Updated: 2
Errors: 0
Already synced: 3
```

## Workflows

### 1. Fix Validation Mismatches

```bash
# Step 1: Find mismatches
verse-status --collection sundar-kaand --validate-text

# Step 2: Preview fixes
verse-sync --collection sundar-kaand --fix-mismatches --dry-run

# Step 3: Apply fixes
verse-sync --collection sundar-kaand --fix-mismatches
```

### 2. Sync Specific Verses After Editing

```bash
# After manually editing data/verses/sundar-kaand.yaml
verse-sync --collection sundar-kaand --verse chaupai_01 --verse chaupai_02
```

### 3. Bulk Sync Entire Collection

```bash
# Preview changes
verse-sync --collection sundar-kaand --all --dry-run

# Apply changes
verse-sync --collection sundar-kaand --all
```

### 4. CI/CD Integration

```bash
#!/bin/bash
# Validate and auto-sync in pipeline

# Check for mismatches
MISMATCHES=$(verse-status --collection sundar-kaand --validate-text --format json | \
  jq '[.collections[0].verses[] | select(.validation.status == "mismatch")] | length')

if [ "$MISMATCHES" -gt 0 ]; then
  echo "Found $MISMATCHES mismatches. Syncing..."
  verse-sync --collection sundar-kaand --fix-mismatches

  # Commit changes
  git add _verses/
  git commit -m "Auto-sync verses with canonical source"
fi
```

## What Gets Updated

### Updated
- ✅ `devanagari` field in frontmatter

### Preserved
- ✅ `transliteration` field
- ✅ `meaning` field
- ✅ `translation` field
- ✅ All other frontmatter fields
- ✅ Markdown body content

## Safety Features

1. **Dry-run mode** - Preview changes before applying
2. **Selective sync** - Sync only specific verses or mismatches
3. **Clear output** - Shows what was changed
4. **Error handling** - Reports failures without stopping
5. **Preserves fields** - Only updates devanagari, keeps everything else

## Error Handling

### Missing Normative Source

```bash
$ verse-sync --collection sundar-kaand --verse chaupai_01

✗ Error: No normative verses found for sundar-kaand
```

**Fix**: Create `data/verses/sundar-kaand.yaml` (or `.yml`) with canonical text

### Verse Not Found

```bash
✗ chaupai_99             - Verse file not found: _verses/sundar-kaand/chaupai_99.md
```

**Fix**: Verify verse ID and file exists

### Missing in Normative Source

```bash
✗ chaupai_50             - Not found in normative source
```

**Fix**: Add verse to `data/verses/{collection}.yaml` (or `.yml`)

## Use Cases

### 1. After Updating Canonical Source

When you update `data/verses/sundar-kaand.yaml` with corrected text:
```bash
verse-sync --collection sundar-kaand --all
```

### 2. Quality Assurance

Ensure all verses match canonical source before publishing:
```bash
verse-status --collection sundar-kaand --validate-text
verse-sync --collection sundar-kaand --fix-mismatches
```

### 3. Bulk Import

After importing verses from multiple sources:
```bash
# Standardize all verses to match canonical source
verse-sync --collection sundar-kaand --all --dry-run
verse-sync --collection sundar-kaand --all
```

### 4. Selective Updates

Update only verses that were recently corrected:
```bash
verse-sync --collection sundar-kaand \
  --verse chaupai_15 \
  --verse chaupai_16 \
  --verse doha_03
```

## Best Practices

1. **Always dry-run first** - Preview changes before applying
   ```bash
   verse-sync --collection sundar-kaand --all --dry-run
   ```

2. **Validate before syncing** - Check what needs fixing
   ```bash
   verse-status --collection sundar-kaand --validate-text
   verse-sync --collection sundar-kaand --fix-mismatches
   ```

3. **Commit canonical source** - Version control your normative text
   ```bash
   git add data/verses/
   git commit -m "Update canonical text for Sundar Kaand"
   ```

4. **Use selective sync** - Don't sync everything if only a few verses changed
   ```bash
   verse-sync --collection sundar-kaand --verse chaupai_01
   ```

5. **Review changes** - Check git diff after syncing
   ```bash
   verse-sync --collection sundar-kaand --fix-mismatches
   git diff _verses/
   ```

## Exit Codes

- `0` - Success (all verses synced without errors)
- `1` - Errors occurred during sync

## Related Commands

- [`verse-status`](verse-status.md) - Check status and validate text
- [`verse-fetch-text`](verse-fetch-text.md) - Fetch text from sources
- [`verse-generate`](verse-generate.md) - Generate verse content

## See Also

- [Local Verse Files Guide](../local-verses.md) - Setting up canonical sources
- [Usage Guide](../usage.md) - Project structure and workflows
