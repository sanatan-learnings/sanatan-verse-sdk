# Verse Content SDK

A Python SDK for generating rich multimedia content for verse-based texts. Provides utilities for:

- **Embeddings**: Generate vector embeddings for semantic search (local and OpenAI)
- **Audio**: Text-to-speech generation using ElevenLabs
- **Images**: AI-generated images using DALL-E
- **Deployment**: Cloudflare Workers deployment utilities

## Installation

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

## Usage

### Command-Line Tools (Recommended)

After installation, the SDK provides command-line tools:

#### Generate Embeddings
```bash
# Using OpenAI (default)
verse-embeddings --verses-dir _verses --output data/embeddings.json

# Using local models (free)
verse-embeddings --verses-dir _verses --output data/embeddings.json --provider huggingface

# With custom paths
verse-embeddings --verses-dir path/to/verses --output path/to/output.json
```

#### Generate Audio
```bash
verse-audio --help  # Coming soon
```

#### Generate Images
```bash
verse-images --help  # Coming soon
```

#### Deploy Cloudflare Worker
```bash
# Run from your project root (where wrangler.toml is located)
cd /path/to/your/project
verse-deploy
```

### Python API (For Custom Scripts)

You can also import and use the SDK in your Python code:

```python
from verse_content_sdk.embeddings import generate_embeddings

generate_embeddings(
    verses_dir="path/to/_verses",
    output_file="path/to/embeddings.json",
    provider="openai"  # or "huggingface"
)
```

## Configuration

Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

## Requirements

- Python 3.8+
- OpenAI API key (for embeddings and image generation)
- ElevenLabs API key (for audio generation)

## License

MIT License - See LICENSE file for details
