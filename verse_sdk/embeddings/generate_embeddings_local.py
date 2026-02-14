#!/usr/bin/env python3
"""
Generate embeddings for verse-based texts using local models.

This script reads all verse markdown files, extracts YAML front matter,
combines fields into rich semantic documents, generates embeddings locally
using sentence-transformers (no API calls needed), and outputs embeddings.json.

Installation:
  pip install sentence-transformers

Usage:
  from verse_sdk.embeddings import generate_embeddings_local
  generate_embeddings_local(verses_dir, output_file)

Or as a script:
  python -m verse_sdk.embeddings.generate_embeddings_local --verses-dir _verses --output data/embeddings.json
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import yaml
import argparse

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed")
    print("Please install it with: pip install sentence-transformers")
    sys.exit(1)

# Default Configuration
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSIONS = 384

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
    lit_key = f'literal_translation'
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

def generate_verse_url(verse_data):
    """Generate URL path for verse page."""
    verse_num = verse_data.get('verse_number', 0)

    # Handle special cases (dohas, closing verses)
    title_en = verse_data.get('title_en', '')
    if 'Doha' in title_en:
        if 'Opening' in title_en:
            return '/verses/doha_01/'
        else:
            return '/verses/doha_02/'
    elif 'Closing' in title_en:
        return '/verses/closing_verse/'
    else:
        return f'/verses/verse_{verse_num:02d}/'

def process_verse_file(file_path, model):
    """Process a single verse file and return metadata + embeddings."""
    print(f"Processing {file_path.name}...")

    verse_data = extract_yaml_frontmatter(file_path)
    if not verse_data:
        print(f"  Warning: Could not extract YAML from {file_path.name}")
        return None

    verse_num = verse_data.get('verse_number', 0)

    # Build documents for both languages
    doc_en = build_document(verse_data, 'en')
    doc_hi = build_document(verse_data, 'hi')

    # Get embeddings (locally, no API calls)
    print(f"  Generating embeddings...")
    emb_en = model.encode(doc_en).tolist()
    emb_hi = model.encode(doc_hi).tolist()

    # Prepare result structure
    result = {
        'en': {
            'verse_number': verse_num,
            'title': verse_data.get('title_en', ''),
            'url': generate_verse_url(verse_data),
            'embedding': emb_en,
            'metadata': {
                'devanagari': verse_data.get('devanagari', ''),
                'transliteration': verse_data.get('transliteration', ''),
                'literal_translation': verse_data.get('literal_translation', {}).get('en', '')
            }
        },
        'hi': {
            'verse_number': verse_num,
            'title': verse_data.get('title_hi', ''),
            'url': generate_verse_url(verse_data),
            'embedding': emb_hi,
            'metadata': {
                'devanagari': verse_data.get('devanagari', ''),
                'transliteration': verse_data.get('transliteration', ''),
                'literal_translation': verse_data.get('literal_translation', {}).get('hi', '')
            }
        }
    }

    return result

def generate_embeddings(
    verses_dir: Path,
    output_file: Path,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
):
    """
    Generate embeddings for all verses in a directory.

    Args:
        verses_dir: Path to directory containing verse markdown files
        output_file: Path where embeddings JSON will be saved
        model_name: HuggingFace model name for embeddings
        dimensions: Expected embedding dimensions
    """
    print("=" * 60)
    print("Verse Embeddings Generator (Local)")
    print("=" * 60)
    print(f"Model: {model_name}")
    print(f"Dimensions: {dimensions}")
    print(f"Method: Local (sentence-transformers)")
    print(f"Verses directory: {verses_dir}")
    print(f"Output file: {output_file}")
    print()

    # Check verses directory
    if not verses_dir.exists():
        print(f"Error: Verses directory not found: {verses_dir}")
        sys.exit(1)

    # Load model
    print("Loading embedding model (this may take a moment on first run)...")
    model = SentenceTransformer(model_name)
    print("Model loaded successfully!")
    print()

    # Find all verse files
    verse_files = sorted(verses_dir.glob("*.md"))
    print(f"Found {len(verse_files)} verse files")
    print()

    # Process all verses
    verses_en = []
    verses_hi = []

    for verse_file in verse_files:
        result = process_verse_file(verse_file, model)
        if result:
            verses_en.append(result['en'])
            verses_hi.append(result['hi'])
        print()

    # Sort by verse number (convert to int for proper sorting)
    verses_en.sort(key=lambda v: int(v['verse_number']) if isinstance(v['verse_number'], (int, str)) and str(v['verse_number']).isdigit() else 999)
    verses_hi.sort(key=lambda v: int(v['verse_number']) if isinstance(v['verse_number'], (int, str)) and str(v['verse_number']).isdigit() else 999)

    # Build output structure
    output = {
        'model': model_name,
        'dimensions': dimensions,
        'provider': 'local',
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
    print("=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    print(f"Total verses processed: {len(verses_en)}")
    print(f"English embeddings: {len(verses_en)}")
    print(f"Hindi embeddings: {len(verses_hi)}")
    print(f"Output file size: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"Cost: FREE (generated locally)")
    print()


def main():
    """Main execution flow when run as script."""
    parser = argparse.ArgumentParser(description="Generate embeddings for verse-based texts")
    parser.add_argument(
        "--verses-dir",
        type=Path,
        default=Path.cwd() / "_verses",
        help="Directory containing verse markdown files (default: ./_verses)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "data" / "embeddings.json",
        help="Output file path (default: ./data/embeddings.json)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"HuggingFace model name (default: {DEFAULT_EMBEDDING_MODEL})"
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        help=f"Embedding dimensions (default: {DEFAULT_EMBEDDING_DIMENSIONS})"
    )

    args = parser.parse_args()

    generate_embeddings(
        verses_dir=args.verses_dir,
        output_file=args.output,
        model_name=args.model,
        dimensions=args.dimensions
    )

if __name__ == '__main__':
    main()
