#!/usr/bin/env python3
"""
Generate embeddings for verse-based texts.

This script reads all verse markdown files, extracts YAML front matter,
combines fields into rich semantic documents, and generates embeddings
using either OpenAI (default) or HuggingFace (local via sentence-transformers).

Usage as library:
    from verse_content_sdk.embeddings import generate_embeddings
    generate_embeddings(verses_dir, output_file, provider='openai')

Usage as script:
    python -m verse_content_sdk.embeddings.generate_embeddings --provider openai
    python -m verse_content_sdk.embeddings.generate_embeddings --provider huggingface
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (CI/CD environment), use environment variables directly
    pass

# Provider configurations
PROVIDERS = {
    'openai': {
        'model': 'text-embedding-3-small',
        'dimensions': 1536,
        'cost_per_1m': 0.02,
        'requires_api_key': True
    },
    'huggingface': {
        'model': 'sentence-transformers/all-MiniLM-L6-v2',
        'dimensions': 384,
        'cost_per_1m': 0.0,  # Free (local)
        'requires_api_key': False
    }
}


def get_openai_embedding(text, client, model):
    """Get embedding from OpenAI API."""
    try:
        response = client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  Error: {e}")
        return None


def get_huggingface_embedding(text, model_instance):
    """Get embedding from local HuggingFace model."""
    try:
        # The model returns a list of embeddings (one per input)
        embedding = model_instance.encode([text])[0].tolist()
        return embedding
    except Exception as e:
        print(f"  Error: {e}")
        return None


def initialize_provider(provider_name):
    """
    Initialize the embedding provider.

    Returns:
        tuple: (embedding_function, client_or_model, config)
    """
    config = PROVIDERS[provider_name]

    if provider_name == 'openai':
        from openai import OpenAI

        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            print("Error: OPENAI_API_KEY not found in .env file")
            sys.exit(1)

        client = OpenAI(api_key=api_key)
        print(f"✓ OpenAI client initialized (key: {api_key[:8]}...)")

        return get_openai_embedding, client, config

    elif provider_name == 'huggingface':
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("Error: sentence-transformers not installed")
            print("Run: ./venv/bin/pip install sentence-transformers")
            sys.exit(1)

        print(f"Loading model {config['model']}...")
        model = SentenceTransformer(config['model'])
        print(f"✓ Model loaded successfully")

        return get_huggingface_embedding, model, config

    else:
        print(f"Error: Unknown provider '{provider_name}'")
        print(f"Available providers: {', '.join(PROVIDERS.keys())}")
        sys.exit(1)


def extract_yaml_frontmatter(file_path):
    """Extract YAML front matter from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        return None

    end_idx = content.find('---', 3)
    if end_idx == -1:
        return None

    yaml_content = content[3:end_idx].strip()
    return yaml.safe_load(yaml_content)


def load_collections_config(collections_file):
    """Load collections configuration from YAML file."""
    if not collections_file.exists():
        print(f"Error: Collections file not found: {collections_file}")
        sys.exit(1)

    with open(collections_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_enabled_collections(collections_config):
    """Filter and return only enabled collections."""
    return {
        key: info for key, info in collections_config.items()
        if info.get('enabled', False)
    }


def build_document(verse_data, lang='en'):
    """
    Build a rich semantic document from verse data.

    Combines multiple fields to capture full spiritual context:
    - Title (semantic anchor)
    - Transliteration (Sanskrit/Hindi terminology)
    - Literal Translation (basic meaning)
    - Interpretive Meaning (spiritual depth)
    - Story (mythological context)
    - Practical Application (teaching + when to use)
    """
    parts = []

    # Title
    title_key = f'title_{lang}'
    if title_key in verse_data:
        parts.append(verse_data[title_key])

    # Transliteration (same for both languages)
    if 'transliteration' in verse_data:
        parts.append(f"Transliteration: {verse_data['transliteration']}")

    # Literal Translation
    lit_key = 'literal_translation'
    if lit_key in verse_data:
        lit_data = verse_data[lit_key]
        if isinstance(lit_data, dict) and lang in lit_data:
            parts.append(f"Translation: {lit_data[lang]}")

    # Interpretive Meaning
    meaning_key = 'interpretive_meaning'
    if meaning_key in verse_data:
        meaning_data = verse_data[meaning_key]
        if isinstance(meaning_data, dict) and lang in meaning_data:
            parts.append(f"Meaning: {meaning_data[lang]}")

    # Story
    if 'story' in verse_data:
        story_data = verse_data['story']
        if isinstance(story_data, dict) and lang in story_data:
            parts.append(f"Story: {story_data[lang]}")

    # Practical Application
    if 'practical_application' in verse_data:
        app_data = verse_data['practical_application']

        # Teaching
        if 'teaching' in app_data:
            teaching = app_data['teaching']
            if isinstance(teaching, dict) and lang in teaching:
                parts.append(f"Teaching: {teaching[lang]}")

        # When to use
        if 'when_to_use' in app_data:
            when = app_data['when_to_use']
            if isinstance(when, dict) and lang in when:
                parts.append(f"When to Use: {when[lang]}")

    return "\n\n".join(parts)


def extract_permalink_from_frontmatter(verse_data):
    """Extract permalink from verse frontmatter if available."""
    return verse_data.get('permalink', None)


def generate_verse_url(verse_data):
    """Generate URL path for verse page."""
    verse_num = verse_data.get('verse_number', 0)

    # Handle special cases (dohas, closing verses)
    title_en = verse_data.get('title_en', '')
    if 'Doha' in title_en:
        if 'Opening' in title_en or verse_num == 1 or verse_num == '1':
            return '/verses/doha_01/'
        elif verse_num == 2 or verse_num == '2':
            return '/verses/doha_02/'
    elif 'Closing' in title_en:
        return '/verses/doha_closing/'

    # Ensure verse_num is an integer for formatting
    if isinstance(verse_num, str):
        try:
            verse_num = int(verse_num)
        except ValueError:
            verse_num = 0

    return f'/verses/verse_{verse_num:02d}/'


def process_verse_file(file_path, embed_func, client_or_model, config, collection_metadata=None):
    """Process a single verse file and return metadata + embeddings.

    Args:
        file_path: Path to the verse markdown file
        embed_func: Embedding generation function
        client_or_model: API client or local model instance
        config: Provider configuration dict
        collection_metadata: Optional dict with 'key' and 'name' for multi-collection mode
    """
    print(f"Processing {file_path.name}...")

    verse_data = extract_yaml_frontmatter(file_path)
    if not verse_data:
        print(f"  Warning: Could not extract YAML from {file_path.name}")
        return None

    verse_num = verse_data.get('verse_number', 0)

    # Build documents for both languages
    doc_en = build_document(verse_data, 'en')
    doc_hi = build_document(verse_data, 'hi')

    # Get embeddings
    print(f"  Getting English embedding...")
    if config['requires_api_key']:
        emb_en = embed_func(doc_en, client_or_model, config['model'])
    else:
        emb_en = embed_func(doc_en, client_or_model)

    # Small delay for API rate limiting (only if using API)
    if config['requires_api_key']:
        time.sleep(0.1)

    print(f"  Getting Hindi embedding...")
    if config['requires_api_key']:
        emb_hi = embed_func(doc_hi, client_or_model, config['model'])
    else:
        emb_hi = embed_func(doc_hi, client_or_model)

    # Small delay for API rate limiting (only if using API)
    if config['requires_api_key']:
        time.sleep(0.1)

    if not emb_en or not emb_hi:
        print(f"  Warning: Failed to get embeddings for {file_path.name}")
        return None

    # Determine URL: use permalink from frontmatter if available, otherwise generate
    permalink = extract_permalink_from_frontmatter(verse_data)
    verse_url = permalink if permalink else generate_verse_url(verse_data)

    # Prepare base metadata
    base_metadata = {
        'devanagari': verse_data.get('devanagari', ''),
        'transliteration': verse_data.get('transliteration', ''),
    }

    # Add collection metadata if in multi-collection mode
    if collection_metadata:
        base_metadata['collection_key'] = collection_metadata['key']
        base_metadata['collection_name'] = collection_metadata['name']

    # Prepare result structure
    result = {
        'en': {
            'verse_number': verse_num,
            'title': verse_data.get('title_en', ''),
            'url': verse_url,
            'embedding': emb_en,
            'metadata': {
                **base_metadata,
                'literal_translation': verse_data.get('literal_translation', {}).get('en', '')
            }
        },
        'hi': {
            'verse_number': verse_num,
            'title': verse_data.get('title_hi', ''),
            'url': verse_url,
            'embedding': emb_hi,
            'metadata': {
                **base_metadata,
                'literal_translation': verse_data.get('literal_translation', {}).get('hi', '')
            }
        }
    }

    return result


def process_single_collection(verses_dir, embed_func, client_or_model, config):
    """Process verses from a single directory (backward compatibility mode)."""
    # Check verses directory
    if not verses_dir.exists():
        print(f"Error: Verses directory not found: {verses_dir}")
        sys.exit(1)

    # Find all verse files
    verse_files = sorted(verses_dir.glob("*.md"))
    print(f"Found {len(verse_files)} verse files")
    print()

    # Process all verses
    verses_en = []
    verses_hi = []

    for verse_file in verse_files:
        result = process_verse_file(verse_file, embed_func, client_or_model, config)
        if result:
            verses_en.append(result['en'])
            verses_hi.append(result['hi'])
        print()

    # Sort by verse number
    verses_en.sort(key=lambda v: int(v['verse_number']) if isinstance(v['verse_number'], (int, str)) and str(v['verse_number']).isdigit() else 999)
    verses_hi.sort(key=lambda v: int(v['verse_number']) if isinstance(v['verse_number'], (int, str)) and str(v['verse_number']).isdigit() else 999)

    return verses_en, verses_hi


def process_multi_collection(collections_file, base_verses_dir, embed_func, client_or_model, config):
    """Process verses from multiple collections."""
    # Load collections configuration
    collections_config = load_collections_config(collections_file)
    enabled_collections = get_enabled_collections(collections_config)

    if not enabled_collections:
        print("Error: No enabled collections found in collections file")
        sys.exit(1)

    print(f"Found {len(enabled_collections)} enabled collection(s):")
    for key, info in enabled_collections.items():
        print(f"  - {key}: {info.get('name_en', key)}")
    print()

    # Process each collection
    all_verses_en = []
    all_verses_hi = []

    for coll_key, coll_info in enabled_collections.items():
        print("=" * 70)
        print(f"Processing collection: {coll_key}")
        print("=" * 70)

        # Get collection subdirectory
        subdirectory = coll_info.get('subdirectory', coll_key)
        verses_dir = base_verses_dir / subdirectory

        if not verses_dir.exists():
            print(f"Warning: Verses directory not found: {verses_dir}")
            print(f"Skipping collection: {coll_key}")
            print()
            continue

        # Find verse files
        verse_files = sorted(verses_dir.glob("*.md"))
        print(f"Found {len(verse_files)} verse files in {subdirectory}/")
        print()

        # Prepare collection metadata
        collection_metadata = {
            'key': coll_key,
            'name': coll_info.get('name_en', coll_key)
        }

        # Process verses
        for verse_file in verse_files:
            result = process_verse_file(
                verse_file, embed_func, client_or_model, config,
                collection_metadata=collection_metadata
            )
            if result:
                all_verses_en.append(result['en'])
                all_verses_hi.append(result['hi'])
            print()

        print(f"Completed collection: {coll_key}")
        print()

    return all_verses_en, all_verses_hi


def main():
    """Main execution flow."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate embeddings for verse-based texts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single collection mode (backward compatible)
  python generate_embeddings.py --provider openai
  python generate_embeddings.py --verses-dir ./_verses --output ./data/embeddings.json

  # Multi-collection mode
  python generate_embeddings.py --multi-collection --collections-file ./_data/collections.yml
  python generate_embeddings.py --multi-collection --collections-file ./collections.yml --provider huggingface
        """
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'huggingface'],
        default=os.getenv('EMBEDDING_PROVIDER', 'openai'),
        help='Embedding provider to use (default: from EMBEDDING_PROVIDER env var or "openai")'
    )
    parser.add_argument(
        '--verses-dir',
        type=Path,
        default=Path.cwd() / "_verses",
        help='Directory containing verse markdown files (default: ./_verses)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path.cwd() / "data" / "embeddings.json",
        help='Output file path (default: ./data/embeddings.json)'
    )
    parser.add_argument(
        '--multi-collection',
        action='store_true',
        help='Enable multi-collection mode'
    )
    parser.add_argument(
        '--collections-file',
        type=Path,
        help='Path to collections.yml file (required for multi-collection mode)'
    )

    args = parser.parse_args()
    provider_name = args.provider
    verses_dir = args.verses_dir
    output_file = args.output
    multi_collection = args.multi_collection
    collections_file = args.collections_file

    # Validate arguments
    if multi_collection and not collections_file:
        print("Error: --collections-file is required when using --multi-collection")
        sys.exit(1)

    print("=" * 70)
    print("Verse Embeddings Generator")
    print("=" * 70)

    # Initialize provider
    embed_func, client_or_model, config = initialize_provider(provider_name)

    print(f"Provider: {provider_name}")
    print(f"Model: {config['model']}")
    print(f"Dimensions: {config['dimensions']}")

    if multi_collection:
        print(f"Mode: Multi-collection")
        print(f"Collections file: {collections_file}")
        print(f"Base verses directory: {verses_dir}")
    else:
        print(f"Mode: Single collection")
        print(f"Verses directory: {verses_dir}")

    print(f"Output file: {output_file}")
    print()

    # Process verses
    if multi_collection:
        verses_en, verses_hi = process_multi_collection(
            collections_file, verses_dir, embed_func, client_or_model, config
        )
    else:
        verses_en, verses_hi = process_single_collection(
            verses_dir, embed_func, client_or_model, config
        )

    # Build output structure
    output = {
        'model': config['model'],
        'dimensions': config['dimensions'],
        'provider': provider_name,
        'generated_at': datetime.now().isoformat(),
        'verses': {
            'en': verses_en,
            'hi': verses_hi
        }
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    print(f"Writing embeddings to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 70)
    print("Generation Complete!")
    print("=" * 70)
    print(f"Total verses processed: {len(verses_en)}")
    print(f"English embeddings: {len(verses_en)}")
    print(f"Hindi embeddings: {len(verses_hi)}")
    print(f"Output file size: {output_file.stat().st_size / 1024:.1f} KB")

    # Calculate approximate cost
    total_embeddings = len(verses_en) + len(verses_hi)
    if config['cost_per_1m'] > 0:
        approx_tokens = total_embeddings * 750  # Rough estimate
        cost = (approx_tokens / 1_000_000) * config['cost_per_1m']
        print(f"Approximate cost: ${cost:.4f} ({config['model']} @ ${config['cost_per_1m']}/1M tokens)")
    else:
        print(f"Cost: FREE (local model)")
    print()


if __name__ == '__main__':
    main()
