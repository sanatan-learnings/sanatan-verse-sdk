# Sanatan SDK - Python SDK for Spiritual Verse Collections

Complete toolkit for generating rich multimedia content for spiritual text collections (Hanuman Chalisa, Sundar Kaand, etc.)

## Features

- **🔄 Complete Workflow**: Generate media and embeddings from canonical sources - all in one command
- **📖 Canonical Sources**: Local YAML files ensure text accuracy and quality
- **🎨 AI Images**: Generate themed images with DALL-E 3
- **🎵 Audio Pronunciation**: Full and slow-speed audio with ElevenLabs
- **🔍 Semantic Search**: Vector embeddings for intelligent verse discovery
- **📚 Multi-Collection**: Organized support for multiple verse collections
- **🎨 Theme System**: Customizable visual styles (modern, traditional, kids-friendly, etc.)

## Quick Start

```bash
# Install
pip install sanatan-sdk

# Set up API keys (in your project directory)
cp .env.example .env
# Edit .env and add your API keys

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
- 🔍 Read canonical Devanagari text from local YAML files
- 🎨 DALL-E 3 generated image (saved to `images/{collection}/{theme}/`)
- 🎵 Full-speed pronunciation (saved to `audio/{collection}/{verse}_full.mp3`)
- 🎵 Slow-speed pronunciation (saved to `audio/{collection}/{verse}_slow.mp3`)
- 🔗 Update vector embeddings for semantic search

**Text Source**:
- Local YAML file: `data/verses/{collection}.yaml` or `.yml` (required)
- You must create this file with canonical verse text (see [Local Verses Guide](docs/local-verses.md))

Opt-out flags (to skip specific steps):
- `--no-fetch-text` - Skip fetching text (use when verse text already exists)
- `--no-update-embeddings` - Skip updating embeddings

## Installation

```bash
pip install sanatan-sdk
```

## Commands

- **[verse-generate](docs/commands/verse-generate.md)** - Complete orchestrator for verse content (text fetching, multimedia generation, embeddings)
- **[verse-translate](docs/commands/verse-translate.md)** - Translate verses into multiple languages (Hindi, Spanish, French, etc.)
- **[verse-status](docs/commands/verse-status.md)** - Check status, completion, and validate text against canonical source
- **[verse-sync](docs/commands/verse-sync.md)** - Sync verse text with canonical source (fix mismatches)
- **[verse-fetch-text](docs/commands/verse-fetch-text.md)** - Fetch traditional Devanagari text from authoritative sources
- **[verse-images](docs/commands/verse-images.md)** - Generate images using DALL-E 3
- **[verse-audio](docs/commands/verse-audio.md)** - Generate audio pronunciations using ElevenLabs
- **[verse-embeddings](docs/commands/verse-embeddings.md)** - Generate vector embeddings for semantic search ([multi-collection guide](docs/multi-collection.md))
- **[verse-deploy](docs/commands/verse-deploy.md)** - Deploy Cloudflare Worker for API proxy

## Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

See the [Usage Guide](docs/usage.md) for detailed information on project structure, workflows, batch processing, and cost optimization.

## Documentation

- **[Usage Guide](docs/usage.md)** - Project setup, workflows, batch processing, and best practices
- **[Local Verses Guide](docs/local-verses.md)** - Using local YAML files for verse text
- **[Command Reference](docs/README.md)** - Detailed documentation for all commands
- **[Development Guide](docs/development.md)** - Setup and contributing to verse-sdk
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
