# Usage Guide

Comprehensive guide for using sanatan-sdk to generate multimedia content for spiritual text collections.

## Table of Contents

- [Project Setup](#project-setup)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Basic Workflows](#basic-workflows)
- [Batch Processing](#batch-processing)
- [Theme Customization](#theme-customization)
- [API Costs](#api-costs)
- [Best Practices](#best-practices)

## Project Setup

### Initial Structure

Create your project with the following structure:

```bash
mkdir my-verse-project
cd my-verse-project

# Create required directories
mkdir -p _data
mkdir -p _verses
mkdir -p docs/image-prompts
mkdir -p docs/themes
mkdir -p images
mkdir -p audio
mkdir -p data

# Set up environment file
cp /path/to/sanatan-sdk/.env.example .env
# Or create manually - see Configuration section below
```

### Collections Configuration

Create `_data/collections.yml` to define your collections:

```yaml
hanuman-chalisa:
  enabled: true
  name:
    en: "Hanuman Chalisa"
    hi: "हनुमान चालीसा"
  subdirectory: "hanuman-chalisa"
  permalink_base: "/hanuman-chalisa"
  total_verses: 43

sundar-kaand:
  enabled: true
  name:
    en: "Sundar Kaand"
    hi: "सुंदर काण्ड"
  subdirectory: "sundar-kaand"
  permalink_base: "/sundar-kaand"
  total_verses: 60
```

## Directory Structure

The SDK follows a **convention-over-configuration** approach. Your project must follow this structure:

```
your-project/
├── .env                                  # API keys
├── _data/
│   └── collections.yml                   # Collection registry
├── _verses/
│   ├── <collection-key>/                 # Verse files by collection
│   │   ├── verse_01.md
│   │   ├── verse_02.md
│   │   └── ...
│   ├── sundar-kaand/
│   │   ├── chaupai_01.md
│   │   └── ...
│   └── sankat-mochan-hanumanashtak/
│       ├── verse_01.md
│       └── ...
├── docs/
│   ├── image-prompts/                    # Scene descriptions by collection
│   │   ├── <collection-key>.md
│   │   ├── sundar-kaand.md
│   │   └── sankat-mochan-hanumanashtak.md
│   └── themes/
│       └── <collection-key>/             # Theme configs by collection
│           ├── modern-minimalist.yml
│           ├── kids-friendly.yml
│           └── ...
├── images/
│   └── <collection-key>/                 # Generated images by collection and theme
│       ├── <theme-name>/
│       │   ├── verse-01.png
│       │   └── ...
│       └── kids-friendly/
│           └── ...
├── audio/
│   └── <collection-key>/                 # Generated audio by collection
│       ├── verse_01_full.mp3
│       ├── verse_01_slow.mp3
│       └── ...
└── data/
    └── embeddings.json                   # Search embeddings (all collections)
```

### Key Conventions

1. **Collection Keys**: Use kebab-case (e.g., `hanuman-chalisa`, `sundar-kaand`)
2. **Verse Files**: Named `verse_NN.md` or custom names like `chaupai_NN.md`
3. **Image Prompts**: One file per collection in `docs/image-prompts/<collection-key>.md`
4. **Theme Files**: One YAML file per theme in `docs/themes/<collection-key>/<theme-name>.yml`
5. **Collections Registry**: Define all collections in `_data/collections.yml` with `enabled: true`

### Verse File Format

Create verse files in `_verses/<collection-key>/verse_NN.md`:

```markdown
---
verse_number: 1
verse_id: verse_01
permalink: /hanuman-chalisa/verse-01/
---

# Verse Content

## Devanagari
श्रीगुरु चरन सरोज रज, निजमन मुकुर सुधारि।

## Transliteration
Śrīguru carana saroja raja, nijamana mukura sudhāri.

## Meaning
With the dust of the lotus feet of my Guru, I cleanse the mirror of my mind.

## Translation
I clean the mirror of my mind with the dust of the lotus feet of my Guru.
```

## Configuration

### Environment Variables

Set required API keys in `.env` (copy from `.env.example`):

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your keys:
# OPENAI_API_KEY=sk-your_openai_key     # Required for images and embeddings
# ELEVENLABS_API_KEY=your_elevenlabs_key # Required for audio
```

Get your API keys:
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys

### Theme Configuration

Create theme files in `docs/themes/<collection-key>/<theme-name>.yml`:

**Example: `docs/themes/hanuman-chalisa/modern-minimalist.yml`**

```yaml
name: Modern Minimalist
style: |
  Clean, minimal design with focus on spiritual essence.
  Soft gradients, simple geometric patterns.
  Calm and serene color palette.

colors:
  primary: "#FF6B35"
  secondary: "#004E89"
  background: "#F7F7F7"

art_direction: |
  - Minimalist composition
  - Soft lighting
  - Divine atmosphere
  - Focus on key spiritual elements
  - No clutter or excessive details
```

### Image Prompts

Create scene descriptions in `docs/image-prompts/<collection-key>.md`:

**Example: `docs/image-prompts/hanuman-chalisa.md`**

```markdown
# Hanuman Chalisa - Image Prompts

## Verse 1
Scene: Lord Hanuman meditating at the feet of his Guru, surrounded by divine light.
Focus on devotion, spiritual learning, and reverence.

## Verse 2
Scene: Young Hanuman attempting to swallow the sun, thinking it's a golden fruit.
Show his divine power and innocent devotion.
```

## Basic Workflows

### Complete Workflow (Default)

Generate everything for a verse:

```bash
verse-generate --collection hanuman-chalisa --verse 15
```

This will:
1. Fetch traditional Devanagari text from authoritative sources
2. Generate AI image with DALL-E 3 (theme: modern-minimalist)
3. Generate full-speed audio pronunciation
4. Generate slow-speed audio pronunciation
5. Update vector embeddings for semantic search

### Partial Workflows

**Skip text fetching (when verse already exists):**
```bash
verse-generate --collection sundar-kaand --verse 5 --no-fetch-text
```

**Skip embeddings update:**
```bash
verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings
```

**Generate only image:**
```bash
verse-generate --collection sundar-kaand --verse 3 --image --theme kids-friendly
```

**Generate only audio:**
```bash
verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio
```

### Individual Commands

**Fetch text only:**
```bash
verse-fetch-text --collection sundar-kaand --verse chaupai_01
```

**Generate images:**
```bash
verse-images --collection hanuman-chalisa --theme modern-minimalist --verse verse_01
```

**Generate audio:**
```bash
verse-audio --collection hanuman-chalisa --verse verse_01
```

**Update embeddings:**
```bash
verse-embeddings --multi-collection --collections-file _data/collections.yml
```

## Batch Processing

Generate content for multiple verses efficiently.

### Sequential Processing

**Process a range of verses:**
```bash
for i in {1..10}; do
  verse-generate --collection hanuman-chalisa --verse $i
  sleep 5  # Rate limiting to avoid API throttling
done
```

**Process all verses in a collection:**
```bash
# Get total verses from collections.yml (e.g., 43 for Hanuman Chalisa)
for i in {1..43}; do
  verse-generate --collection hanuman-chalisa --verse $i
  sleep 5
done
```

### With Custom Theme

```bash
for i in {1..10}; do
  verse-generate --collection hanuman-chalisa --verse $i --theme kids-friendly
  sleep 5
done
```

### Skip Existing Content

Only generate missing content:

```bash
for i in {1..43}; do
  # Check if image exists
  if [ ! -f "images/hanuman-chalisa/modern-minimalist/verse-$(printf "%02d" $i).png" ]; then
    verse-generate --collection hanuman-chalisa --verse $i --image
    sleep 5
  fi
done
```

### Batch Script Example

Create `scripts/batch_generate.sh`:

```bash
#!/bin/bash

COLLECTION="hanuman-chalisa"
THEME="modern-minimalist"
START=1
END=43

echo "Batch generating $COLLECTION verses $START to $END"

for i in $(seq $START $END); do
  echo ""
  echo "Processing verse $i..."

  verse-generate --collection $COLLECTION --verse $i --theme $THEME

  # Check exit status
  if [ $? -eq 0 ]; then
    echo "✓ Verse $i completed successfully"
  else
    echo "✗ Verse $i failed"
    # Optionally continue or exit
    # exit 1
  fi

  # Rate limiting
  sleep 5
done

echo ""
echo "Batch processing complete!"
```

Run it:
```bash
chmod +x scripts/batch_generate.sh
./scripts/batch_generate.sh
```

## Theme Customization

### Creating a New Theme

1. **Create theme file:**
   ```bash
   mkdir -p docs/themes/hanuman-chalisa
   touch docs/themes/hanuman-chalisa/watercolor-art.yml
   ```

2. **Define theme:**
   ```yaml
   name: Watercolor Art
   style: |
     Soft watercolor painting style with flowing colors.
     Dreamy and artistic interpretation.
     Warm, vibrant colors with gentle blending.

   colors:
     primary: "#E63946"
     secondary: "#457B9D"
     background: "#F1FAEE"

   art_direction: |
     - Watercolor painting technique
     - Soft edges and flowing colors
     - Artistic interpretation
     - Warm and inviting atmosphere
     - Hand-painted aesthetic
   ```

3. **Use the theme:**
   ```bash
   verse-generate --collection hanuman-chalisa --verse 1 --theme watercolor-art
   ```

### Theme Examples

**Kids-Friendly Theme:**
```yaml
name: Kids Friendly
style: |
  Bright, colorful, and cheerful design appealing to children.
  Cartoon-like characters with friendly expressions.
  Bold colors and simple compositions.

colors:
  primary: "#FF6B9D"
  secondary: "#4ECDC4"
  background: "#FFE66D"

art_direction: |
  - Cartoon style illustration
  - Bright and cheerful colors
  - Simple, child-friendly imagery
  - Fun and engaging composition
  - Friendly character designs
```

**Traditional Art Theme:**
```yaml
name: Traditional Art
style: |
  Traditional Indian art style inspired by ancient manuscripts.
  Rich colors, intricate patterns, and classical composition.
  Spiritual and authentic aesthetic.

colors:
  primary: "#B8860B"
  secondary: "#8B0000"
  background: "#FFF8DC"

art_direction: |
  - Traditional Indian art style
  - Intricate details and patterns
  - Rich, royal colors
  - Classical composition
  - Authentic spiritual imagery
```

## API Costs

Understanding the costs of generating verse content:

| Component | Cost per Verse | Provider | Notes |
|-----------|---------------|----------|-------|
| Text generation | ~$0.02 | OpenAI GPT-4 | Only if fetching from GPT |
| Image | $0.04 (standard) / $0.08 (HD) | DALL-E 3 | Per image generated |
| Audio (2 files) | ~$0.001 | ElevenLabs | Full + slow speed |
| Embeddings | ~$0.0001 | OpenAI | Per verse added |
| **Total per verse** | **~$0.06-0.10** | | Varies by options |

### Cost Examples

**Small collection (40 verses):**
- Hanuman Chalisa: ~$2.40 - $4.00

**Medium collection (200 verses):**
- Bhagavad Gita chapter: ~$12 - $20

**Large collection (700 verses):**
- Complete Bhagavad Gita: ~$42 - $70

### Cost Optimization

1. **Skip text fetching when not needed:**
   ```bash
   verse-generate --collection hanuman-chalisa --verse 1 --no-fetch-text
   ```

2. **Use standard quality images (not HD):**
   Default is standard quality ($0.04 vs $0.08)

3. **Batch process during off-peak hours:**
   No cost difference, but better for rate limiting

4. **Generate only what you need:**
   ```bash
   # Only image
   verse-generate --collection hanuman-chalisa --verse 1 --image

   # Only audio
   verse-generate --collection hanuman-chalisa --verse 1 --audio
   ```

5. **Update embeddings once after batch:**
   ```bash
   # Generate media for all verses
   for i in {1..43}; do
     verse-generate --collection hanuman-chalisa --verse $i --no-update-embeddings
   done

   # Update embeddings once at the end
   verse-embeddings --multi-collection
   ```

## Best Practices

### 1. Version Control

- Commit verse files before generating media
- Use `.gitignore` for large media files
- Store themes and prompts in version control

```gitignore
# Generated content
images/
audio/
data/embeddings.json

# Environment
.env
.venv/
```

### 2. Rate Limiting

Always add delays between API calls:
```bash
for i in {1..43}; do
  verse-generate --collection hanuman-chalisa --verse $i
  sleep 5  # 5 second delay
done
```

### 3. Backup Strategy

- Keep backups of generated content
- Store original verse files separately
- Export embeddings periodically

### 4. Quality Control

Review generated content:
```bash
# Generate one verse first
verse-generate --collection hanuman-chalisa --verse 1

# Review image in images/hanuman-chalisa/modern-minimalist/verse-01.png
# Review audio in audio/hanuman-chalisa/verse_01_full.mp3

# If satisfied, proceed with batch
```

### 5. Theme Consistency

- Use the same theme for all verses in a collection
- Create theme variants for different audiences
- Test themes on a few verses before batch processing

### 6. Documentation

Keep notes on:
- Which verses have been generated
- Theme choices and rationale
- Any custom modifications
- Prompt adjustments for specific verses

### 7. Error Handling

```bash
# Log output for debugging
verse-generate --collection hanuman-chalisa --verse 1 2>&1 | tee generation.log

# Check for errors
if [ $? -ne 0 ]; then
  echo "Error occurred, check generation.log"
fi
```

## Troubleshooting

Common issues and solutions:

### API Key Errors
```bash
# Verify keys are set
echo $OPENAI_API_KEY
echo $ELEVENLABS_API_KEY

# Reload environment
source .env
```

### Collection Not Found
```bash
# List available collections
verse-generate --list-collections

# Check collections.yml
cat _data/collections.yml
```

### Image Generation Fails
- Check prompt file exists: `docs/image-prompts/<collection-key>.md`
- Verify theme file exists: `docs/themes/<collection-key>/<theme-name>.yml`
- Review OpenAI API quota

### Audio Generation Fails
- Check verse file exists: `_verses/<collection-key>/verse_NN.md`
- Verify Devanagari text is present
- Review ElevenLabs API quota

For more detailed troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

- Review [Command Reference](README.md) for detailed command options
- Check [Multi-Collection Guide](multi-collection.md) for managing multiple collections
- See [Development Guide](development.md) for contributing
- Visit [Example Project](https://github.com/sanatan-learnings/hanuman-gpt) for reference
