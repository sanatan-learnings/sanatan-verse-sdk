# verse-content-sdk

Python SDK for generating multimedia content for spiritual texts (Bhagavad Gita, Hanuman Chalisa, etc.)

## Features

- **🎯 All-in-One Generation**: Single `--all` command generates text, scene description, image, and audio together
- **🤖 AI-Powered**: Automatic content generation using GPT-4, DALL-E 3, and ElevenLabs
- **🔍 Semantic Search**: Vector embeddings for intelligent verse search
- **🎨 Theme System**: Configurable visual styles for images
- **🎵 Audio**: Verse pronunciation in full and slow speeds
- **☁️ Cloudflare**: Easy deployment utilities for API proxies

## Quick Start

```bash
# Install
pip install verse-content-sdk

# Set up API keys
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...

# Generate EVERYTHING with one command

# For chapter-based texts (Bhagavad Gita)
verse-generate --chapter 2 --verse 47 --all

# For non-chapter texts (Hanuman Chalisa)
verse-generate --verse 15 --all
```

That's it! The `--all` flag generates **all content automatically**:
- ✅ Fetches verse text from GPT-4
- ✅ Fetches chapter names from GPT-4 (if applicable)
- ✅ Generates translations and commentary
- ✅ Creates scene description for artwork
- ✅ Generates DALL-E 3 image
- ✅ Produces audio pronunciation files (full + slow speeds)

## Installation

### From PyPI (Recommended)

```bash
pip install verse-content-sdk
```

### From GitHub

```bash
pip install git+https://github.com/sanatan-learnings/verse-content-sdk.git
```

### For Development

```bash
git clone https://github.com/sanatan-learnings/verse-content-sdk.git
cd verse-content-sdk
pip install -e .
```

## Commands

### verse-generate

Unified command for complete verse generation. The `--all` flag generates **everything in one command**:
- ✅ Text content (translations, commentary, meanings)
- ✅ Scene description (for image generation)
- ✅ Image (DALL-E 3 artwork)
- ✅ Audio (full + slow speed pronunciations)

```bash
# Generate everything in one command (recommended)
verse-generate --chapter 3 --verse 5 --all

# Or generate specific components
verse-generate --chapter 3 --verse 5 --text      # Text only
verse-generate --chapter 3 --verse 5 --prompt    # Scene description only
verse-generate --chapter 3 --verse 5 --image     # Image only
verse-generate --chapter 3 --verse 5 --audio     # Audio only

# Without chapters (e.g., Hanuman Chalisa)
verse-generate --verse 15 --all
```

**[Full documentation](docs/commands/verse-generate.md)**

### verse-images

Generate images using DALL-E 3.

```bash
# Generate all images
verse-images --theme-name modern-minimalist

# Regenerate specific image
verse-images --theme-name modern-minimalist --regenerate chapter-01-verse-01.png
```

**[Full documentation](docs/commands/verse-images.md)**

### verse-audio

Generate audio pronunciations using ElevenLabs.

```bash
# Generate all audio
verse-audio

# Regenerate specific files
verse-audio --regenerate chapter_01_verse_01_full.mp3,chapter_01_verse_01_slow.mp3
```

**[Full documentation](docs/commands/verse-audio.md)**

### verse-embeddings

Generate vector embeddings for semantic search.

```bash
# Using OpenAI (recommended)
verse-embeddings --verses-dir _verses --output data/embeddings.json

# Using local models (free)
verse-embeddings --verses-dir _verses --output data/embeddings.json --provider huggingface
```

**[Full documentation](docs/commands/verse-embeddings.md)**

### verse-deploy

Deploy Cloudflare Worker for API proxy.

```bash
verse-deploy
```

## Configuration

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Project Structure

Your project should have:

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

## API Costs

| Component | Cost per Verse | Provider |
|-----------|---------------|----------|
| Text generation | ~$0.02 | OpenAI GPT-4 |
| Image | $0.04 (standard) / $0.08 (HD) | DALL-E 3 |
| Audio (2 files) | ~$0.001 | ElevenLabs |
| **Total per verse** | **~$0.06** | |

**For 700 verses** (complete Bhagavad Gita): **~$42**

## Examples

### Generate Everything with One Command

The `--all` flag generates complete multimedia content:

**For chapter-based texts (Bhagavad Gita):**

```bash
# Generate text + scene description + image + audio in one command
verse-generate --chapter 5 --verse 10 --all

# Review all generated files
ls _verses/chapter_05_verse_10.md                    # Text content
ls docs/image-prompts.md                             # Scene description (appended)
ls images/modern-minimalist/chapter-05-verse-10.png  # Image
ls audio/chapter_05_verse_10_*.mp3                   # Audio files (full + slow)
```

**For non-chapter texts (Hanuman Chalisa):**

```bash
# Generate complete verse content
verse-generate --verse 7 --all

# Review all generated files
ls _verses/verse_07.md                    # Text content
ls docs/image-prompts.md                  # Scene description (appended)
ls images/modern-minimalist/verse-07.png  # Image
ls audio/verse_07_*.mp3                   # Audio files (full + slow)
```

**Generate embeddings for search:**

```bash
verse-embeddings --verses-dir _verses --output data/embeddings.json
```

### Regenerate Specific Components

**Bhagavad Gita:**

```bash
# Regenerate just the image
verse-generate --chapter 2 --verse 47 --image

# Regenerate just the audio
verse-generate --chapter 2 --verse 47 --audio
```

**Hanuman Chalisa:**

```bash
# Regenerate just the text
verse-generate --verse 12 --text

# Regenerate just the image
verse-generate --verse 12 --image

# Regenerate just the audio
verse-generate --verse 12 --audio
```

### Multiple Verses

**Bhagavad Gita (verses 1-10 of Chapter 1):**

```bash
for i in {1..10}; do
  verse-generate --chapter 1 --verse $i --all
  sleep 5  # Rate limiting
done
```

**Hanuman Chalisa (verses 1-40, complete text):**

```bash
for i in {1..40}; do
  verse-generate --verse $i --all
  sleep 5  # Rate limiting
done
```

## Documentation

### User Guides

- **[Main Documentation](docs/README.md)** - Overview and quick start
- **[verse-generate](docs/commands/verse-generate.md)** - Complete verse generation
- **[verse-images](docs/commands/verse-images.md)** - Image generation
- **[verse-audio](docs/commands/verse-audio.md)** - Audio generation
- **[verse-embeddings](docs/commands/verse-embeddings.md)** - Embeddings generation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues

### For Maintainers

- **[Publishing to PyPI](docs/publishing.md)** - How to publish new releases

## Example Projects

- [Bhagavad Gita](https://github.com/sanatan-learnings/bhagavad-gita) - Complete implementation with RAG system
- [Hanuman Chalisa](https://github.com/sanatan-learnings/hanuman-chalisa) - Simple verse-based text

## Requirements

- Python 3.8+
- OpenAI API key (for text/images/embeddings)
- ElevenLabs API key (for audio)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

- [GitHub Issues](https://github.com/sanatan-learnings/verse-content-sdk/issues)
- [Documentation](docs/README.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
