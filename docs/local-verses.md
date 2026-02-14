# Local Verse Files

Use local YAML files as the canonical source for verse text instead of web scraping.

## Quick Start

```bash
# 1. Create directory
mkdir -p data/verses

# 2. Create verse file: data/verses/sundar-kaand.yaml (or .yml)
# See example below

# 3. SDK automatically uses local file
verse-generate --collection sundar-kaand --verse 1
```

## File Format

### Location

```
data/verses/{collection}.yaml  (or .yml - both extensions supported)
```

### Structure

```yaml
# Optional: Collection metadata (keys starting with _ are ignored)
_meta:
  collection: sundar-kaand
  source: https://hi.wikipedia.org/wiki/सुन्दरकाण्ड

  # Optional: Define reading sequence for ordered playback
  sequence:
    - shloka_01
    - chaupai_01
    - chaupai_02
    - doha_01

# Opening Shloka (multi-line with |)
shloka_01:
  devanagari: |
    शान्तं शाश्वतमप्रमेयमनघं निर्वाणशान्तिप्रदं
    ब्रह्माशम्भुफणीन्द्रसेव्यमनिशं वेदान्तवेद्यं विभुम् ।
    रामाख्यं जगदीश्वरं सुरगुरुं मायामनुष्यं हरिं
    वन्देऽहं करुणाकरं रघुवरं भूपालचूड़ामणिम्

# Chaupais (single-line verses)
chaupai_01:
  devanagari: "जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए।।"

chaupai_02:
  devanagari: "तब लगि मोहि परिखेहु तुम्ह भाई। सहि दुख कंद मूल फल खाई।।"

# Dohas
doha_01:
  devanagari: "सुनि बचन प्रेम सहित कपीसा। ग्यान जोग विराग निधान प्रतीसा।।"
```

**Key Points:**
- Only `devanagari` field required - AI generates translations/meanings
- Use `|` for multi-line verses (shlokas)
- Use quotes `"..."` for single-line verses
- `_meta` key is optional and ignored by SDK

## Verse ID Patterns

### Traditional Categorization (Recommended)

Use verse type in the ID:

```yaml
shloka_01:    # Invocation verses
chaupai_01:   # Couplets (main narrative)
doha_01:      # Standalone transitional verses
soratha_01:   # Reverse dohas (if applicable)
```

**Benefits:**
- Self-documenting - type is clear from ID
- Matches traditional sacred text structure
- Easy to filter by type
- Compatible with SDK parsing

### Sequential Ordering

Add `sequence` array in `_meta` for reading order:

```yaml
_meta:
  sequence:
    - shloka_01
    - chaupai_01
    - chaupai_02
    - doha_01
```

**Use cases:**
- Audio playlists
- Sequential reading interfaces
- Progress tracking

## How It Works

SDK checks sources in this order:

1. **Local file** (`data/verses/{collection}.yaml` or `.yml`) - instant
2. **Web scraping** (ramcharitmanas.net, etc.) - fallback

```bash
# Found in local file - fast
verse-fetch-text --collection sundar-kaand --verse chaupai_01
# ✓ Found in local file: data/verses/sundar-kaand.{yaml,yml}

# Not in local file - falls back to web
verse-fetch-text --collection sundar-kaand --verse chaupai_99
# ✓ Local file not found, fetching from internet...
```

## Example: Complete File

See `examples/data/verses/sundar-kaand.yaml` for full template.

```yaml
_meta:
  collection: sundar-kaand
  source: https://hi.wikipedia.org/wiki/सुन्दरकाण्ड
  description: Sundar Kaand from Ramcharitmanas
  sequence: [shloka_01, chaupai_01, chaupai_02, doha_01]

shloka_01:
  devanagari: |
    शान्तं शाश्वतमप्रमेयमनघं निर्वाणशान्तिप्रदं
    ब्रह्माशम्भुफणीन्द्रसेव्यमनिशं वेदान्तवेद्यं विभुम् ।

chaupai_01:
  devanagari: "जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए।।"

doha_01:
  devanagari: "सुनि बचन प्रेम सहित कपीसा। ग्यान जोग विराग निधान प्रतीसा।।"
```

## Best Practices

1. **Use authoritative sources** - Published editions, academic texts
2. **Version control** - Commit verse files to git
3. **Validate YAML** - `python -c "import yaml; yaml.safe_load(open('data/verses/sundar-kaand.yaml'))"`
4. **Keep it minimal** - Only canonical text; AI generates rest
5. **Document sources** - Add source URL in `_meta`

## Benefits

| Aspect | Local Files | Web Scraping |
|--------|-------------|--------------|
| Speed | ~10ms | ~1-3 seconds |
| Reliability | 100% | Depends on website |
| Offline | Yes | No |
| Consistency | Guaranteed | May change |

## Troubleshooting

### Missing devanagari field
```
Warning: Verse chaupai_01 missing 'devanagari' field
```
**Fix:** Ensure each verse has `devanagari` field.

### YAML syntax error
```
Error reading local verses file: invalid yaml
```
**Fix:** Validate syntax with `python -c "import yaml; yaml.safe_load(open('file.yaml'))"`

### File not found
```
Error reading local verses file data/verses/sundar-kaand.yaml
```
**Fix:** Create directory: `mkdir -p data/verses && touch data/verses/sundar-kaand.yaml`

## See Also

- [verse-fetch-text](commands/verse-fetch-text.md) - Fetch verse text command
- [verse-generate](commands/verse-generate.md) - Complete content generation
- [Usage Guide](usage.md) - Project structure and workflows
