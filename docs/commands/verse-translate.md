# verse-translate

Translate verse content into multiple languages using GPT-4.

## Synopsis

```bash
verse-translate --collection COLLECTION --verse N --language CODE [OPTIONS]
```

## Description

The `verse-translate` command translates verse content from English to target languages using GPT-4. By default, it translates the three shorter fields (`translation`, `literal_translation`, `interpretive_meaning`). Use `--all-fields` to also translate longer fields (`story`, `practical_application`).

Translations are added to the verse frontmatter while preserving existing content.

## Options

### Required

- `--collection KEY` - Collection key (e.g., `sundar-kaand`, `hanuman-chalisa`)
- `--verse N` - Verse number to translate (can be used multiple times)
- `--all` - Translate all verses in collection
- `--language CODE` - Target language code (can be used multiple times)

### Optional

- `--all-fields` - Translate all fields including story and practical_application (slower, more expensive)
- `--project-dir PATH` - Project directory (default: current directory)
- `--list-languages` - List supported languages and exit

## Supported Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| hi | Hindi | es | Spanish | fr | French |
| de | German | pt | Portuguese | it | Italian |
| ru | Russian | ja | Japanese | zh | Chinese |
| ar | Arabic | bn | Bengali | ta | Tamil |
| te | Telugu | mr | Marathi | gu | Gujarati |
| kn | Kannada | ml | Malayalam | pa | Punjabi |
| ur | Urdu | ne | Nepali | | |

View full list:
```bash
verse-translate --list-languages
```

## Examples

### List Supported Languages

```bash
verse-translate --list-languages
```

### Translate Single Verse to Hindi

```bash
verse-translate --collection sundar-kaand --verse 5 --language hi
```

### Translate to Multiple Languages

```bash
verse-translate --collection sundar-kaand --verse 5 --language es --language fr --language de
```

### Translate Multiple Specific Verses

```bash
verse-translate --collection sundar-kaand --verse 1 --verse 2 --verse 3 --language hi
```

### Translate All Verses in Collection

```bash
verse-translate --collection sundar-kaand --all --language hi
```

### Translate All Fields (Including Long Story)

By default, only short fields are translated to minimize cost and time:

```bash
# Default: Only translates translation, literal_translation, interpretive_meaning
verse-translate --collection sundar-kaand --verse 5 --language hi

# With --all-fields: Also translates story, practical_application
verse-translate --collection sundar-kaand --verse 5 --language hi --all-fields
```

## What Gets Translated

### Default (Short Fields)

✅ **translation** - Simple verse translation
```yaml
translation:
  en: "On the shore of the ocean..."
  hi: "समुद्र के किनारे पर..." # NEW
```

✅ **literal_translation** - Word-for-word translation
```yaml
literal_translation:
  en: "On the ocean shore, there was one beautiful mountain..."
  hi: "सागर के किनारे पर एक सुंदर पर्वत था..." # NEW
```

✅ **interpretive_meaning** - Deeper meaning and context
```yaml
interpretive_meaning:
  en: "This chaupai describes the moment..."
  hi: "यह चौपाई उस क्षण का वर्णन करती है..." # NEW
```

### With --all-fields

✅ **story** - Background story and context (longer)
```yaml
story:
  en: "After declaring his intentions..."
  hi: "अपने इरादों की घोषणा करने के बाद..." # NEW
```

✅ **practical_application.teaching** - Teaching and lessons
```yaml
practical_application:
  teaching:
    en: "This verse teaches us..."
    hi: "यह पद हमें सिखाता है..." # NEW
```

✅ **practical_application.when_to_use** - When to recite
```yaml
practical_application:
  when_to_use:
    en: "Recite this chaupai when..."
    hi: "इस चौपाई का पाठ करें जब..." # NEW
```

## Features

### Smart Skipping

Existing translations are preserved:
```bash
$ verse-translate --collection sundar-kaand --verse 5 --language hi

  ⊘ translation (hi): Already exists, skipping
  → Translating literal_translation to Hindi...
  ✓ literal_translation (hi): Done
```

### Contextual Translation

The translator uses context for accuracy:
- Original Devanagari text for reference
- Field name for appropriate tone
- Spiritual/devotional context preservation
- GPT-4 for nuanced, culturally-aware translations

### Batch Translation

Translate multiple verses in one command:
```bash
# All verses in collection
verse-translate --collection sundar-kaand --all --language hi

# Multiple specific verses
verse-translate --collection sundar-kaand --verse 1 --verse 2 --verse 5 --language hi

# Multiple languages at once
verse-translate --collection sundar-kaand --verse 5 --language hi --language es --language fr
```

## Output Example

```bash
$ verse-translate --collection sundar-kaand --verse 5 --language hi

============================================================
VERSE TRANSLATION
============================================================

Collection: sundar-kaand
Target languages: Hindi
Fields: Short fields only (translation, literal_translation, interpretive_meaning)

============================================================
Translating: chaupai_05.md
============================================================

  → Translating translation to Hindi...
  ✓ translation (hi): Done
  → Translating literal_translation to Hindi...
  ✓ literal_translation (hi): Done
  → Translating interpretive_meaning to Hindi...
  ✓ interpretive_meaning (hi): Done

  → Updating verse file...
  ✓ Verse file updated successfully

============================================================
TRANSLATION SUMMARY
============================================================
Total verses: 1
✓ Success: 1
✗ Failed: 0
```

## Cost Considerations

### Default (Short Fields)
- **Fields translated**: 3 (translation, literal_translation, interpretive_meaning)
- **Typical cost per verse**: ~$0.02-0.05
- **Recommended for**: Batch translation of many verses

### With --all-fields
- **Fields translated**: 6 (includes story, practical_application.teaching, practical_application.when_to_use)
- **Typical cost per verse**: ~$0.10-0.20 (longer texts)
- **Recommended for**: Individual verses where full translation is needed

**Tip**: Start with default short fields, then use `--all-fields` selectively for important verses.

## Use Cases

### 1. Multi-language Website

Translate all verses for an international audience:
```bash
# Translate to major Indian languages
verse-translate --collection sundar-kaand --all --language hi
verse-translate --collection sundar-kaand --all --language ta
verse-translate --collection sundar-kaand --all --language te

# Translate to European languages
verse-translate --collection sundar-kaand --all --language es
verse-translate --collection sundar-kaand --all --language fr
```

### 2. Selective Full Translation

Translate popular verses with full context:
```bash
# Important verses with full translation
verse-translate --collection sundar-kaand --verse 1 --verse 5 --verse 40 --language hi --all-fields
```

### 3. Progressive Translation

Start with essentials, add details later:
```bash
# Step 1: Translate short fields for all verses (fast)
verse-translate --collection sundar-kaand --all --language hi

# Step 2: Add full translation for select verses (detailed)
verse-translate --collection sundar-kaand --verse 5 --language hi --all-fields
```

### 4. Quality Assurance

Re-translate after updating English content:
```bash
# Translations are skipped if they exist, so delete the old one first
# Then run translation to regenerate
verse-translate --collection sundar-kaand --verse 5 --language hi
```

## Error Handling

### Missing OPENAI_API_KEY
```bash
✗ Error: OPENAI_API_KEY environment variable not set
Set it in .env file or environment
```
**Fix**: Add `OPENAI_API_KEY=sk-...` to your `.env` file

### Unsupported Language
```bash
⚠ Warning: 'xx' is not in the supported languages list
Use --list-languages to see supported languages
```
**Note**: Translation will still be attempted, but quality may vary

### Missing English Source
```bash
  ⚠ Skipping translation: no English text found
```
**Fix**: Ensure verse has English (`en`) translation in the source field

## Related Commands

- [`verse-generate`](verse-generate.md) - Generate verse content with `--regenerate-content`
- [`verse-status`](verse-status.md) - Check verse completion status
- [`verse-sync`](verse-sync.md) - Sync canonical text

## Requirements

- OpenAI API key (GPT-4 access)
- Verse files with English translations in frontmatter
- Sufficient API credits for batch translation

## Exit Codes

- `0` - Success (all translations completed)
- `1` - Error (one or more translations failed)
