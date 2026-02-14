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

## Commands

- **[verse-generate](docs/commands/verse-generate.md)** - Complete orchestrator for verse content (text fetching, multimedia generation, embeddings)
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
