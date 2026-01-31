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

### Generate Embeddings (Local)
```python
from verse_content_sdk.embeddings import generate_local_embeddings

generate_local_embeddings(
    input_dir="_verses",
    output_file="data/embeddings.json",
    model="all-MiniLM-L6-v2"
)
```

### Generate Embeddings (OpenAI)
```python
from verse_content_sdk.embeddings import generate_openai_embeddings

generate_openai_embeddings(
    input_dir="_verses",
    output_file="data/embeddings.json",
    api_key="your-api-key"
)
```

### Generate Audio
```python
from verse_content_sdk.audio import generate_audio

generate_audio(
    text="Your verse text",
    output_path="audio/verse.mp3",
    voice_id="your-voice-id"
)
```

### Generate Images
```python
from verse_content_sdk.images import generate_image

generate_image(
    prompt="Your image prompt",
    output_path="images/verse.png"
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
