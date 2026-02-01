# verse-content-sdk Usage Guide

Quick reference for all SDK commands.

## Installation

```bash
pip install verse-content-sdk
# Or for development:
pip install -e path/to/verse-content-sdk
```

## Commands

### `verse-generate` - Generate Complete Verses

Generate text, images, and audio for any verse with one command.

```bash
# Simplest usage (everything auto-fetched from GPT-4)
verse-generate --chapter 1 --verse 3 --all

# Generate specific components
verse-generate --chapter 1 --verse 3 --text      # Text only
verse-generate --chapter 1 --verse 3 --prompt    # Scene description only
verse-generate --chapter 1 --verse 3 --image     # Image only
verse-generate --chapter 1 --verse 3 --audio     # Audio only

# Custom Sanskrit text
verse-generate --chapter 1 --verse 3 --all --sanskrit "..."

# Override chapter names
verse-generate --chapter 1 --verse 3 --all \
  --chapter-name-en "Custom Name" \
  --chapter-name-hi "कस्टम नाम"
```

**Auto-fetches from GPT-4:**
- Sanskrit text (Devanagari)
- Chapter names (English & Hindi)
- Transliteration, meanings, translations, commentary

**Generates:**
- Complete verse markdown file
- Scene description in `docs/image-prompts.md`
- Image using DALL-E 3
- Audio files (full + slow speed)

### `verse-images` - Generate Images

Generate images from scene descriptions.

```bash
# Generate all images
verse-images --theme-name modern-minimalist

# Regenerate specific image
verse-images --theme-name modern-minimalist \
  --regenerate chapter-01-verse-01.png

# Force regenerate all
verse-images --theme-name modern-minimalist --force
```

**Requires:**
- Scene descriptions in `docs/image-prompts.md`
- Theme config in `docs/themes/THEME_NAME.yml`

### `verse-audio` - Generate Audio

Generate audio pronunciations.

```bash
# Generate all audio
verse-audio

# Regenerate specific files
verse-audio --regenerate chapter_01_verse_01_full.mp3,chapter_01_verse_01_slow.mp3

# Custom voice
verse-audio --voice-id YOUR_VOICE_ID
```

**Requires:**
- Verse files in `_verses/` with `devanagari:` field
- ElevenLabs API key

### `verse-embeddings` - Generate Embeddings

Generate vector embeddings for semantic search.

```bash
# Using OpenAI
verse-embeddings --verses-dir _verses --output data/embeddings.json

# Using local models (free)
verse-embeddings --verses-dir _verses --output data/embeddings.json --provider huggingface
```

### `verse-deploy` - Deploy Cloudflare Worker

Deploy OpenAI API proxy to Cloudflare Workers.

```bash
verse-deploy
```

**Requires:** Wrangler CLI configured

## Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...           # Required for text/images
ELEVENLABS_API_KEY=...          # Required for audio
```

## Project Structure

```
your-project/
├── .env                        # API keys
├── _verses/                    # Verse markdown files
├── docs/
│   ├── image-prompts.md        # Scene descriptions
│   └── themes/
│       └── modern-minimalist.yml  # Theme config
├── images/                     # Generated images
│   └── modern-minimalist/
├── audio/                      # Generated audio
└── data/
    └── embeddings.json         # Search embeddings
```

## Common Workflows

### Create New Verse

```bash
verse-generate --chapter 3 --verse 10 --all
```

Done! Creates everything in one command.

### Regenerate Just Images

```bash
verse-images --theme-name modern-minimalist --force
```

### Regenerate Just Audio

```bash
verse-audio --force
```

### Update Search

```bash
verse-embeddings --verses-dir _verses --output data/embeddings.json
```

## API Costs

| Component | Cost per Verse | Provider |
|-----------|---------------|----------|
| Text generation | ~$0.02 | OpenAI GPT-4 |
| Image | $0.04 (standard) / $0.08 (HD) | DALL-E 3 |
| Audio (2 files) | ~$0.001 | ElevenLabs |
| **Total per verse** | **~$0.06** | |

**For 700 verses:** ~$42

## Tips

- Start with standard image quality, upgrade to HD if needed
- Review AI-generated content for accuracy
- Use `--regenerate` flags to avoid regenerating everything
- Commands find themselves even if not in PATH
- All content is cached - safe to re-run commands

## Help

```bash
verse-generate --help
verse-images --help
verse-audio --help
verse-embeddings --help
```

## Documentation

- Full guide: `docs/content-generation-guide.md`
- Theme creation: See `docs/themes/` examples
- Examples: Check verse-content-sdk test projects
