# Chapter-Based Verse Formats

Starting with version 0.26.0, `verse-add` supports multi-chapter collections using the `--chapter` flag.

## Overview

Some collections (like the Bhagavad Gita) organize verses into chapters. The SDK now supports verse ID formats like:
- `chapter-01-shloka-01` (Chapter 1, Shloka 1)
- `chapter-02-shloka-01` (Chapter 2, Shloka 1)
- `chapter-18-shloka-78` (Chapter 18, Shloka 78)

## Usage

### Adding Verses to Specific Chapters

```bash
# Add shloka 1 to chapter 2
verse-add --collection bhagavad-gita --verse 1 --chapter 2

# Add shlokas 1-10 to chapter 2
verse-add --collection bhagavad-gita --verse 1-10 --chapter 2

# Add shloka 47 to chapter 2 (the famous Karma Yoga verse)
verse-add --collection bhagavad-gita --verse 47 --chapter 2
```

### How It Works

1. **Format Detection**: The SDK automatically detects chapter-based formats by looking for `chapter-XX` patterns in existing verses

2. **Chapter Substitution**: When you provide `--chapter N`, the SDK:
   - Detects the current chapter number in the format
   - Replaces it with your specified chapter number
   - Generates verse IDs accordingly

3. **Padding Preservation**: The SDK preserves zero-padding:
   - `chapter-01` → `chapter-02` (preserves 2-digit padding)
   - `chapter-1` → `chapter-2` (no padding)

### Example Workflow

**Initial Setup:**
```yaml
# data/verses/bhagavad-gita.yaml
_meta:
  collection: bhagavad-gita
  total_shlokas: 700
  chapters: 18

chapter-01-shloka-01:
  devanagari: 'धृतराष्ट्र उवाच...'
```

**Adding Chapter 2 Verses:**
```bash
# Add all 72 shlokas of Chapter 2
verse-add --collection bhagavad-gita --verse 1-72 --chapter 2
```

**Result:**
```yaml
chapter-01-shloka-01:
  devanagari: 'धृतराष्ट्र उवाच...'

chapter-02-shloka-01:
  devanagari: ''

chapter-02-shloka-02:
  devanagari: ''

# ... through chapter-02-shloka-72
```

## Supported Format Patterns

The chapter detection works with any format containing `chapter-XX`:
- ✓ `chapter-01-shloka-01`
- ✓ `chapter-1-verse-1`
- ✓ `ch-01-shloka-01` (won't detect - must use literal "chapter")
- ✓ `chapter-001-shloka-001` (3-digit padding)

## Backward Compatibility

The `--chapter` flag is **optional** and only applies to chapter-based formats:

```bash
# Simple formats (no --chapter needed)
verse-add --collection hanuman-chalisa --verse 1-40

# Chapter-based formats (--chapter optional)
verse-add --collection bhagavad-gita --verse 1-10 --chapter 2

# If --chapter is used with simple format, it's ignored with a warning
verse-add --collection hanuman-chalisa --verse 1 --chapter 2
# Warning: --chapter flag provided but collection doesn't use chapter-based format
```

## Best Practices

1. **Consistent Format**: Use the same format throughout your collection
   - Good: `chapter-01-shloka-01`, `chapter-02-shloka-01`
   - Bad: Mixing `chapter-1-shloka-1` and `chapter-02-shloka-02`

2. **Zero Padding**: Match the padding used in existing verses
   - If existing verses use `chapter-01`, continue with 2-digit padding
   - SDK will auto-detect and preserve padding

3. **Sequential Addition**: Add chapters in order when possible
   - Easier to maintain and review

4. **Use _meta.sequence**: For chapter-based collections, maintain a sequence list:
   ```yaml
   _meta:
     sequence:
       # Chapter 1
       - chapter-01-shloka-01
       - chapter-01-shloka-02
       # Chapter 2
       - chapter-02-shloka-01
       - chapter-02-shloka-02
   ```

## Complete Example

```bash
# Initialize collection with Chapter 1
verse-add --collection bhagavad-gita --verse 1-47 --chapter 1

# Add Chapter 2
verse-add --collection bhagavad-gita --verse 1-72 --chapter 2

# Add specific verses from Chapter 18
verse-add --collection bhagavad-gita --verse 65-66 --chapter 18

# Generate content for Chapter 2, Verse 47
verse-generate --collection bhagavad-gita --verse chapter-02-shloka-47
```

## Limitations

- The `--chapter` flag works with the inferred format, not custom formats
- If you use `--format` to override the format, you must manually include the chapter number
- The SDK doesn't automatically create chapter metadata or validate chapter numbers

## Migration from Simple Formats

If you have an existing collection using simple formats (e.g., `shloka-001`) and want to migrate to chapter-based formats:

1. Backup your YAML file
2. Manually restructure with chapter numbers
3. Update `_meta.sequence` if used
4. Use `--chapter` flag for future additions

Or continue using simple formats with a `chapter` field in each verse entry:
```yaml
shloka-001:
  devanagari: '...'
  chapter: 1

shloka-002:
  devanagari: '...'
  chapter: 1
```
