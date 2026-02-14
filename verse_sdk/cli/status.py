#!/usr/bin/env python3
"""
Collection status checker - shows completion status for verse collections.

This command provides a comprehensive overview of what content exists and what's missing:
- Verse files and their metadata
- Audio files (full and slow speed)
- Image files
- Embedding status
- Completion percentage

Usage:
    # Check specific collection
    verse-status --collection hanuman-chalisa

    # Check all enabled collections
    verse-status --all-collections

    # Detailed report with file paths
    verse-status --collection sundar-kaand --detailed

    # JSON output for scripting
    verse-status --collection hanuman-chalisa --format json
"""

import os
import sys
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed")
    print("Install with: pip install python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


def get_file_info(file_path: Path) -> Optional[Dict]:
    """Get file metadata if it exists."""
    if not file_path.exists():
        return None

    stat = file_path.stat()
    return {
        'exists': True,
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'path': str(file_path)
    }


def parse_verse_frontmatter(verse_file: Path) -> Dict:
    """Parse YAML frontmatter from verse markdown file."""
    if not verse_file.exists():
        return {}

    try:
        with open(verse_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter between --- markers
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter or {}
    except Exception as e:
        print(f"Warning: Could not parse {verse_file}: {e}", file=sys.stderr)

    return {}


def check_verse_status(
    collection: str,
    verse_file: Path,
    project_dir: Path
) -> Dict:
    """Check status of a single verse."""
    verse_id = verse_file.stem  # Remove .md extension

    # Parse frontmatter
    frontmatter = parse_verse_frontmatter(verse_file)

    # Check audio files
    audio_dir = project_dir / "audio" / collection
    audio_full = audio_dir / f"{verse_id}_full.mp3"
    audio_slow = audio_dir / f"{verse_id}_slow.mp3"

    # Check image files (check common themes)
    images_dir = project_dir / "images" / collection
    themes = ['modern-minimalist', 'traditional', 'kids-friendly', 'devotional']
    image_files = {}

    for theme in themes:
        theme_dir = images_dir / theme
        img_file = theme_dir / f"{verse_id}.png"
        if img_file.exists():
            image_files[theme] = get_file_info(img_file)

    # Default theme image
    default_image = images_dir / f"{verse_id}.png"
    if default_image.exists():
        image_files['default'] = get_file_info(default_image)

    return {
        'verse_id': verse_id,
        'verse_file': get_file_info(verse_file),
        'frontmatter': frontmatter,
        'audio': {
            'full': get_file_info(audio_full),
            'slow': get_file_info(audio_slow)
        },
        'images': image_files,
        'has_devanagari': bool(frontmatter.get('devanagari')),
        'has_transliteration': bool(frontmatter.get('transliteration')),
        'has_meaning': bool(frontmatter.get('meaning')),
        'has_translation': bool(frontmatter.get('translation', {}).get('en'))
    }


def check_embeddings_status(project_dir: Path) -> Dict:
    """Check embeddings file status."""
    embeddings_file = project_dir / "data" / "embeddings.json"

    if not embeddings_file.exists():
        return {
            'exists': False,
            'verse_count': 0,
            'collections': []
        }

    try:
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Count verses per collection
        collection_counts = defaultdict(int)
        for item in data:
            collection = item.get('collection', 'unknown')
            collection_counts[collection] += 1

        return {
            'exists': True,
            'verse_count': len(data),
            'collections': dict(collection_counts),
            'file_info': get_file_info(embeddings_file)
        }
    except Exception as e:
        return {
            'exists': True,
            'error': str(e)
        }


def get_enabled_collections(project_dir: Path) -> List[Tuple[str, Dict]]:
    """Get list of enabled collections from collections.yml"""
    collections_file = project_dir / "_data" / "collections.yml"

    if not collections_file.exists():
        return []

    try:
        with open(collections_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        enabled = [
            (key, info)
            for key, info in data.items()
            if info.get('enabled', False)
        ]
        return enabled
    except Exception as e:
        print(f"Error reading collections.yml: {e}", file=sys.stderr)
        return []


def analyze_collection(collection: str, project_dir: Path) -> Dict:
    """Analyze a single collection."""
    verses_dir = project_dir / "_verses" / collection

    if not verses_dir.exists():
        return {
            'collection': collection,
            'exists': False,
            'error': f"Collection directory not found: {verses_dir}"
        }

    # Find all verse files
    verse_files = sorted(verses_dir.glob("*.md"))

    if not verse_files:
        return {
            'collection': collection,
            'exists': True,
            'verse_count': 0,
            'verses': []
        }

    # Analyze each verse
    verses = []
    for verse_file in verse_files:
        status = check_verse_status(collection, verse_file, project_dir)
        verses.append(status)

    # Calculate statistics
    total_verses = len(verses)
    verses_with_audio_full = sum(1 for v in verses if v['audio']['full'])
    verses_with_audio_slow = sum(1 for v in verses if v['audio']['slow'])
    verses_with_images = sum(1 for v in verses if v['images'])
    verses_with_devanagari = sum(1 for v in verses if v['has_devanagari'])
    verses_with_translation = sum(1 for v in verses if v['has_translation'])

    # Calculate completion percentage
    # Full completion = verse file + both audios + at least one image + devanagari + translation
    fully_complete = sum(
        1 for v in verses
        if v['audio']['full'] and v['audio']['slow'] and v['images']
        and v['has_devanagari'] and v['has_translation']
    )

    completion_percentage = (fully_complete / total_verses * 100) if total_verses > 0 else 0

    return {
        'collection': collection,
        'exists': True,
        'verse_count': total_verses,
        'statistics': {
            'completion_percentage': completion_percentage,
            'verses_complete': fully_complete,
            'verses_with_audio_full': verses_with_audio_full,
            'verses_with_audio_slow': verses_with_audio_slow,
            'verses_with_images': verses_with_images,
            'verses_with_devanagari': verses_with_devanagari,
            'verses_with_translation': verses_with_translation
        },
        'verses': verses
    }


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def print_collection_status(analysis: Dict, detailed: bool = False):
    """Print collection status in human-readable format."""
    collection = analysis['collection']

    if not analysis.get('exists'):
        print(f"\n✗ Collection '{collection}' not found")
        if 'error' in analysis:
            print(f"  {analysis['error']}")
        return

    verse_count = analysis['verse_count']

    if verse_count == 0:
        print(f"\n📚 Collection: {collection}")
        print("  ⚠ No verses found")
        return

    stats = analysis['statistics']

    print(f"\n📚 Collection: {collection}")
    print(f"   Verses: {verse_count}")
    print(f"   Completion: {stats['completion_percentage']:.1f}% ({stats['verses_complete']}/{verse_count} verses)")

    print(f"\n   Content Status:")
    print(f"   ├─ Devanagari text:  {stats['verses_with_devanagari']:3d}/{verse_count} verses")
    print(f"   ├─ Translation:      {stats['verses_with_translation']:3d}/{verse_count} verses")
    print(f"   ├─ Audio (full):     {stats['verses_with_audio_full']:3d}/{verse_count} verses")
    print(f"   ├─ Audio (slow):     {stats['verses_with_audio_slow']:3d}/{verse_count} verses")
    print(f"   └─ Images:           {stats['verses_with_images']:3d}/{verse_count} verses")

    if detailed:
        print(f"\n   Verse Details:")
        for verse in analysis['verses']:
            verse_id = verse['verse_id']
            audio_full = "✓" if verse['audio']['full'] else "✗"
            audio_slow = "✓" if verse['audio']['slow'] else "✗"
            images = "✓" if verse['images'] else "✗"
            devanagari = "✓" if verse['has_devanagari'] else "✗"

            print(f"   ├─ {verse_id:20s} │ Text:{devanagari} │ Audio:{audio_full}{audio_slow} │ Image:{images}")

            # Show missing content
            missing = []
            if not verse['has_devanagari']:
                missing.append("devanagari")
            if not verse['audio']['full']:
                missing.append("audio_full")
            if not verse['audio']['slow']:
                missing.append("audio_slow")
            if not verse['images']:
                missing.append("images")

            if missing:
                print(f"   │  └─ Missing: {', '.join(missing)}")


def print_embeddings_status(embeddings: Dict):
    """Print embeddings status."""
    print(f"\n🔍 Embeddings Status:")

    if not embeddings['exists']:
        print("   ✗ No embeddings file found (data/embeddings.json)")
        print("   Run: verse-embeddings --multi-collection")
        return

    if 'error' in embeddings:
        print(f"   ✗ Error reading embeddings: {embeddings['error']}")
        return

    print(f"   ✓ Total verses indexed: {embeddings['verse_count']}")

    if embeddings['collections']:
        print(f"   Collections:")
        for collection, count in embeddings['collections'].items():
            print(f"   ├─ {collection:30s} {count:3d} verses")

    if 'file_info' in embeddings and embeddings['file_info']:
        info = embeddings['file_info']
        size = format_size(info['size'])
        modified = info['modified'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n   File: {info['path']}")
        print(f"   Size: {size}, Modified: {modified}")


def print_summary(analyses: List[Dict], embeddings: Dict):
    """Print overall summary."""
    total_verses = sum(a['verse_count'] for a in analyses if a.get('exists'))
    total_collections = len([a for a in analyses if a.get('exists')])

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Collections: {total_collections}")
    print(f"Total verses: {total_verses}")

    if embeddings.get('exists') and 'verse_count' in embeddings and 'error' not in embeddings:
        indexed = embeddings['verse_count']
        missing = total_verses - indexed
        if missing > 0:
            print(f"⚠ Verses not in embeddings: {missing}")
            print(f"  Run: verse-embeddings --multi-collection")
        else:
            print(f"✓ All verses indexed in embeddings")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check status of verse collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific collection
  verse-status --collection hanuman-chalisa

  # Check all enabled collections
  verse-status --all-collections

  # Detailed report with verse-by-verse breakdown
  verse-status --collection sundar-kaand --detailed

  # JSON output for scripting
  verse-status --collection hanuman-chalisa --format json

  # Check embeddings status
  verse-status --embeddings-only
        """
    )

    parser.add_argument(
        "--collection",
        type=str,
        help="Collection key to check",
        metavar="KEY"
    )

    parser.add_argument(
        "--all-collections",
        action="store_true",
        help="Check all enabled collections"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed verse-by-verse breakdown"
    )

    parser.add_argument(
        "--format",
        choices=['text', 'json'],
        default='text',
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--embeddings-only",
        action="store_true",
        help="Only check embeddings status"
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    args = parser.parse_args()

    project_dir = args.project_dir

    # Check embeddings status
    embeddings = check_embeddings_status(project_dir)

    if args.embeddings_only:
        if args.format == 'json':
            print(json.dumps(embeddings, indent=2, default=str))
        else:
            print_embeddings_status(embeddings)
        sys.exit(0)

    # Determine which collections to check
    collections_to_check = []

    if args.all_collections:
        enabled = get_enabled_collections(project_dir)
        collections_to_check = [key for key, _ in enabled]
    elif args.collection:
        collections_to_check = [args.collection]
    else:
        parser.error("Either --collection or --all-collections is required")

    if not collections_to_check:
        print("No collections found to check")
        sys.exit(1)

    # Analyze collections
    analyses = []
    for collection in collections_to_check:
        analysis = analyze_collection(collection, project_dir)
        analyses.append(analysis)

    # Output results
    if args.format == 'json':
        output = {
            'collections': analyses,
            'embeddings': embeddings
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Print header
        print("\n" + "="*60)
        print("VERSE COLLECTION STATUS")
        print("="*60)

        # Print each collection
        for analysis in analyses:
            print_collection_status(analysis, detailed=args.detailed)

        # Print embeddings status
        print_embeddings_status(embeddings)

        # Print summary if multiple collections
        if len(analyses) > 1:
            print_summary(analyses, embeddings)

        print()


if __name__ == '__main__':
    main()
