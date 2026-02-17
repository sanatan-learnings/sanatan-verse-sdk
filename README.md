# Sanatan Verse SDK - Python SDK for Spiritual Verse Collections

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

### New Project Setup (Recommended)

```bash
# 1. Install
pip install sanatan-verse-sdk

# 2. Create project with collection templates
verse-init --project-name my-verse-project --collection hanuman-chalisa
cd my-verse-project

# 3. Configure API keys
cp .env.example .env
# Edit .env and add your API keys from:
# - OpenAI: https://platform.openai.com/api-keys
# - ElevenLabs: https://elevenlabs.io/app/settings/api-keys

# 4. Add canonical Devanagari text
# Edit data/verses/hanuman-chalisa.yaml with actual verse text

# 5. Validate setup
verse-validate

# 6. Generate multimedia content
verse-generate --collection hanuman-chalisa --verse 1
```

**What you get**: Verse file, AI-generated image, audio (full + slow speed), and search embeddings!

### Existing Project

```bash
# Validate and fix structure
verse-validate --fix

# Generate content
verse-generate --collection hanuman-chalisa --verse 15

# Check status
verse-status --collection hanuman-chalisa
```

### Advanced Usage

```bash
# Multiple collections at once
verse-init --collection hanuman-chalisa --collection sundar-kaand

# Custom number of sample verses
verse-init --collection my-collection --num-verses 10

# Generate specific components only
verse-generate --collection sundar-kaand --verse 3 --image
verse-generate --collection sundar-kaand --verse 3 --audio

# Skip embeddings update (faster)
verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings
```

### What Gets Generated

Each verse generation creates:
- 🎨 **Image**: `images/{collection}/{theme}/verse-01.png` (DALL-E 3)
- 🎵 **Audio (full)**: `audio/{collection}/verse-01-full.mp3` (ElevenLabs)
- 🎵 **Audio (slow)**: `audio/{collection}/verse-01-slow.mp3` (0.75x speed)
- 🔍 **Embeddings**: `data/embeddings.json` (for semantic search)

**Text Source**: Canonical Devanagari text from `data/verses/{collection}.yaml` ([Local Verses Guide](docs/local-verses.md))

## Installation

```bash
pip install sanatan-verse-sdk
```

## Commands

### Project Setup
- **[verse-init](docs/commands/verse-init.md)** - Initialize new project with recommended structure
- **[verse-validate](docs/commands/verse-validate.md)** - Validate project structure and configuration

### Content Generation
- **[verse-generate](docs/commands/verse-generate.md)** - Complete orchestrator for verse content (text fetching, multimedia generation, embeddings)
- **[verse-translate](docs/commands/verse-translate.md)** - Translate verses into multiple languages (Hindi, Spanish, French, etc.)
- **[verse-images](docs/commands/verse-images.md)** - Generate images using DALL-E 3
- **[verse-audio](docs/commands/verse-audio.md)** - Generate audio pronunciations using ElevenLabs
- **[verse-embeddings](docs/commands/verse-embeddings.md)** - Generate vector embeddings for semantic search ([multi-collection guide](docs/multi-collection.md))

### Project Management
- **[verse-status](docs/commands/verse-status.md)** - Check status, completion, and validate text against canonical source
- **[verse-sync](docs/commands/verse-sync.md)** - Sync verse text with canonical source (fix mismatches)
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

- [GitHub Issues](https://github.com/sanatan-learnings/sanatan-verse-sdk/issues)
- [Documentation](docs/README.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
