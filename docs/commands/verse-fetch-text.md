# verse-fetch-text

Fetch traditional Devanagari verse text from authoritative online sources.

## Synopsis

```bash
verse-fetch-text --collection COLLECTION --verse VERSE_ID [OPTIONS]
```

## Description

The `verse-fetch-text` command retrieves authentic Devanagari verse text from reputable online sources such as ramcharitmanas.net. It scrapes, cleans, and normalizes the text to ensure accuracy and authenticity for sacred texts like Ramcharitmanas and Hanuman Chalisa.

This command is useful for:
- Obtaining verified Devanagari text before generating multimedia content
- Validating verse text against authoritative sources
- Batch-fetching traditional verse text for new collections
- Previewing verse content without API costs

## Options

### Required

- `--collection NAME` - Collection key (e.g., `sundar-kaand`, `hanuman-chalisa`)
- `--verse ID` - Verse identifier (e.g., `chaupai_05`, `doha_01`, `verse_10`)

### Optional

- `--format FORMAT` - Output format: `json` or `text` (default: `json`)

## Examples

### Fetch Sundar Kaand Chaupai

```bash
verse-fetch-text --collection sundar-kaand --verse chaupai_05
```

Output (JSON):
```json
{
  "success": true,
  "collection": "sundar-kaand",
  "verse_id": "chaupai_05",
  "verse_type": "chaupai",
  "verse_number": 5,
  "devanagari": "जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए।।",
  "source": "ramcharitmanas.net",
  "verified": true
}
```

### Fetch Sundar Kaand Doha

```bash
verse-fetch-text --collection sundar-kaand --verse doha_01
```

### Plain Text Output

```bash
verse-fetch-text --collection sundar-kaand --verse chaupai_03 --format text
```

Output:
```
जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए।।
```

### Fetch Different Verse Types

```bash
# Chaupai
verse-fetch-text --collection sundar-kaand --verse chaupai_10

# Doha
verse-fetch-text --collection sundar-kaand --verse doha_02

# Generic verse (auto-detects type)
verse-fetch-text --collection hanuman-chalisa --verse verse_15
```

## Output Format

### JSON Format (Default)

```json
{
  "success": true,
  "collection": "sundar-kaand",
  "verse_id": "chaupai_05",
  "verse_type": "chaupai",
  "verse_number": 5,
  "devanagari": "जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए।।",
  "source": "ramcharitmanas.net",
  "verified": true
}
```

### Error Response

```json
{
  "success": false,
  "error": "Could not fetch verse text from any source",
  "collection": "sundar-kaand",
  "verse_id": "chaupai_999",
  "tried_sources": ["ramcharitmanas.net"]
}
```

### Text Format

Plain Devanagari text only (useful for piping to other commands):

```bash
verse-fetch-text --collection sundar-kaand --verse chaupai_05 --format text
```

## Verse ID Format

Verse identifiers follow these patterns:

- **Chaupai**: `chaupai_01`, `chaupai_02`, `chaupai_05`, etc.
- **Doha**: `doha_01`, `doha_02`, etc.
- **Generic**: `verse_01`, `verse_10`, `verse_15`, etc.

The command parses the verse type and number automatically.

## Supported Collections

Currently supported collections:

- **sundar-kaand** - Ramcharitmanas Sundar Kand
  - Source: ramcharitmanas.net
  - Verse types: `chaupai`, `doha`

- **hanuman-chalisa** - Hanuman Chalisa
  - Verse types: `verse`

Additional collections can be configured in the source code.

## Text Processing

The command performs automatic cleaning and normalization:

- Removes extra whitespace
- Normalizes danda punctuation (। and ।।)
- Removes English characters and numbers
- Strips HTML artifacts from scraping
- Validates that fetched text is substantial (>10 characters)

## Sources

### Primary Source: ramcharitmanas.net

The command tries multiple URL patterns to find verses:

```
https://www.ramcharitmanas.net/sundar-kand/chaupai-{N}
https://www.ramcharitmanas.net/sundar/chaupai-{N}.htm
https://www.ramcharitmanas.net/sunderkand-chaupai-{N}.html
```

It uses multiple CSS selectors to extract Devanagari text reliably.

## Workflow

### Standalone Usage

```bash
# 1. Fetch verse text
verse-fetch-text --collection sundar-kaand --verse chaupai_05 --format json > verse-data.json

# 2. Review the fetched text
cat verse-data.json

# 3. Use in verse file or generation workflow
```

### Integration with verse-generate

```bash
# Fetch text as part of complete generation workflow
verse-generate --collection sundar-kaand --verse 5 \
  --fetch-text --all --theme modern-minimalist
```

This automatically:
1. Fetches traditional Devanagari text
2. Generates image with DALL-E 3
3. Generates audio pronunciations
4. Optionally updates embeddings

### Batch Fetching

```bash
# Fetch multiple verses
for i in {1..10}; do
  verse-fetch-text --collection sundar-kaand --verse chaupai_$i --format json \
    > data/fetched/chaupai_${i}.json
done
```

## Requirements

- Python 3.7+
- `requests` library
- `beautifulsoup4` library

Install dependencies:

```bash
pip install requests beautifulsoup4
```

## Exit Codes

- `0` - Success: verse text fetched successfully
- `1` - Error: verse not found or fetch failed

Check success in scripts:

```bash
if verse-fetch-text --collection sundar-kaand --verse chaupai_05; then
  echo "Fetch succeeded"
else
  echo "Fetch failed"
fi
```

## Performance

- Network request: ~1-3 seconds per verse
- Tries multiple URL patterns automatically
- Timeout: 10 seconds per URL attempt
- Minimal API costs (no paid APIs used)

## Notes

- This command scrapes public websites - respect rate limits
- Text accuracy depends on source website reliability
- ramcharitmanas.net is considered authoritative for Ramcharitmanas verses
- No authentication or API keys required
- Works with any internet connection
- Some verses may not be available online
- The command tries multiple sources and URL patterns automatically

## Troubleshooting

### "Invalid verse_id format"

Ensure verse ID follows the pattern:
- `chaupai_NN`
- `doha_NN`
- `verse_NN`

```bash
# Correct
verse-fetch-text --collection sundar-kaand --verse chaupai_05

# Incorrect
verse-fetch-text --collection sundar-kaand --verse 5
```

### "Could not fetch verse text from any source"

Possible causes:
- Verse number doesn't exist online
- Source website is down or changed structure
- Network connectivity issues
- Rate limiting by source website

Try:
1. Verify verse number exists in the collection
2. Check internet connection
3. Try again after a few minutes (rate limiting)
4. Check if source website is accessible

### Import Errors

```
Error: Required packages not installed
Install with: pip install requests beautifulsoup4
```

Install missing dependencies:

```bash
pip install requests beautifulsoup4
```

## See Also

- [verse-generate](verse-generate.md) - Complete orchestration including text fetching
- [Troubleshooting](../troubleshooting.md) - Common issues
- [Multi-Collection Guide](../multi-collection.md) - Working with multiple collections
