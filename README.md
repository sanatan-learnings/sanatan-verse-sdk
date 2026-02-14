# verse-sdk

Python SDK for generating multimedia content for spiritual text collections (Hanuman Chalisa, Sundar Kaand, etc.)

## Features

- **📚 Collection-Aware**: Organized support for multiple verse collections
- **🎯 Simple Generation**: Generate images and audio for specific verses
- **🤖 AI-Powered**: DALL-E 3 for images, ElevenLabs for audio
- **🔍 Semantic Search**: Vector embeddings for intelligent verse search
- **🎨 Theme System**: Configurable visual styles for images
- **🎵 Audio**: Verse pronunciation in full and slow speeds

## Quick Start

```bash
# Install
pip install verse-sdk

# Set up API keys
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...

# List available collections
verse-generate --list-collections

# Complete workflow (default) - fetch text, generate media, update embeddings
verse-generate --collection hanuman-chalisa --verse 15

# Skip text fetching (when verse text already exists)
verse-generate --collection sundar-kaand --verse 5 --no-fetch-text

# Or generate specific components only
verse-generate --collection sundar-kaand --verse 3 --image
verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio
```

By default, the complete workflow includes:
- 🔍 Fetch traditional Devanagari text from authoritative sources
- 🎨 DALL-E 3 generated image (saved to `images/{collection}/{theme}/`)
- 🎵 Full-speed pronunciation (saved to `audio/{collection}/{verse}_full.mp3`)
- 🎵 Slow-speed pronunciation (saved to `audio/{collection}/{verse}_slow.mp3`)
- 🔗 Update vector embeddings for semantic search

Opt-out flags (to skip specific steps):
- `--no-fetch-text` - Skip fetching text from authoritative sources
- `--no-update-embeddings` - Skip updating embeddings

## Installation

```bash
pip install verse-sdk
```

### For Development

```bash
git clone https://github.com/sanatan-learnings/verse-sdk.git
cd verse-sdk
pip install -e .
```

## Commands

- **[verse-generate](docs/commands/verse-generate.md)** - Complete orchestrator for verse content (text fetching, multimedia generation, embeddings)
- **[verse-fetch-text](docs/commands/verse-fetch-text.md)** - Fetch traditional Devanagari text from authoritative sources
- **[verse-images](docs/commands/verse-images.md)** - Generate images using DALL-E 3
- **[verse-audio](docs/commands/verse-audio.md)** - Generate audio pronunciations using ElevenLabs
- **[verse-embeddings](docs/commands/verse-embeddings.md)** - Generate vector embeddings for semantic search ([multi-collection guide](docs/multi-collection.md))
- **[verse-deploy](docs/commands/verse-deploy.md)** - Deploy Cloudflare Worker for API proxy

## Configuration

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Directory Structure Conventions

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

### Example collections.yml

```yaml
hanuman-chalisa:
  enabled: true
  name:
    en: "Hanuman Chalisa"
    hi: "हनुमान चालीसा"
  # ... other metadata

sundar-kaand:
  enabled: true
  name:
    en: "Sundar Kaand"
    hi: "सुंदर काण्ड"
```

## API Costs

| Component | Cost per Verse | Provider |
|-----------|---------------|----------|
| Text generation | ~$0.02 | OpenAI GPT-4 |
| Image | $0.04 (standard) / $0.08 (HD) | DALL-E 3 |
| Audio (2 files) | ~$0.001 | ElevenLabs |
| **Total per verse** | **~$0.06** | |

**For 700 verses** (complete Bhagavad Gita): **~$42**

## Batch Processing

Generate media for multiple verses:

```bash
for i in {1..10}; do
  verse-generate --collection hanuman-chalisa --verse $i
  sleep 5  # Rate limiting
done

# With custom theme
for i in {1..10}; do
  verse-generate --collection hanuman-chalisa --verse $i --theme kids-friendly
  sleep 5
done
```

## Documentation

- **[Command Reference](docs/README.md)** - Detailed documentation for all commands
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Multi-Collection Guide](docs/multi-collection.md)** - Working with multiple collections
- **[Publishing Guide](docs/publishing.md)** - For maintainers

## Example Project

[Hanuman GPT](https://github.com/sanatan-learnings/hanuman-gpt) - Multi-collection project with Hanuman Chalisa, Sundar Kaand, and Sankat Mochan Hanumanashtak

## Requirements

- Python 3.8+
- OpenAI API key (for text/images/embeddings)
- ElevenLabs API key (for audio)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Support

- [GitHub Issues](https://github.com/sanatan-learnings/verse-sdk/issues)
- [Documentation](docs/README.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
