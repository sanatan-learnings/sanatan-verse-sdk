#!/usr/bin/env python3
"""
Collection-aware verse content generator - complete orchestration of all verse content.

This command is the one-stop solution for generating all content for a verse:
- Fetch traditional Devanagari text from authoritative sources (optional)
- Generate AI image with DALL-E 3
- Generate audio pronunciation with ElevenLabs (full + slow speed)
- Update vector embeddings for semantic search

Usage:
    # Generate everything for a verse
    verse-generate --collection hanuman-chalisa --verse 15 --all --theme modern-minimalist --update-embeddings

    # Fetch text, then generate image and audio
    verse-generate --collection sundar-kaand --verse 3 --fetch-text --all --theme modern-minimalist

    # Generate only image
    verse-generate --collection sundar-kaand --verse 3 --image --theme modern-minimalist

    # Generate only audio
    verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio

Requirements:
    - OPENAI_API_KEY environment variable (for image generation and embeddings)
    - ELEVENLABS_API_KEY environment variable (for audio generation)
"""

import os
import sys
import argparse
import subprocess
import yaml
import shutil
import json
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed")
    print("Install with: pip install python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


def find_command(command_name: str) -> str:
    """Find the full path to a command, checking common locations."""
    # First try shutil.which (checks PATH)
    cmd_path = shutil.which(command_name)
    if cmd_path:
        return cmd_path

    # Check common installation locations
    common_paths = [
        Path.home() / "Library" / "Python" / "3.13" / "bin" / command_name,
        Path.home() / "Library" / "Python" / "3.12" / "bin" / command_name,
        Path.home() / "Library" / "Python" / "3.11" / "bin" / command_name,
        Path.home() / ".local" / "bin" / command_name,
        Path("/usr/local/bin") / command_name,
    ]

    for path in common_paths:
        if path.exists():
            return str(path)

    # If not found, return command name and hope it's in PATH
    return command_name


def validate_collection(collection: str, project_dir: Path = Path.cwd()) -> bool:
    """Validate that collection exists and is enabled."""
    # Check _verses directory
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        print(f"✗ Error: Collection directory not found: {verses_dir}")
        return False

    # Check collections.yml
    collections_file = project_dir / "_data" / "collections.yml"
    if collections_file.exists():
        with open(collections_file) as f:
            data = yaml.safe_load(f)
            if collection not in data:
                print(f"✗ Error: Collection '{collection}' not found in collections.yml")
                return False
            if not data[collection].get('enabled', False):
                print(f"✗ Error: Collection '{collection}' is disabled in collections.yml")
                return False

    return True


def list_collections(project_dir: Path = Path.cwd()):
    """List available collections from _data/collections.yml"""
    collections_file = project_dir / "_data" / "collections.yml"
    if not collections_file.exists():
        print("No collections.yml found")
        return []

    with open(collections_file) as f:
        data = yaml.safe_load(f)
        enabled = [
            (key, info.get('name', {}).get('en', key))
            for key, info in data.items()
            if info.get('enabled', False)
        ]

    print("\nAvailable collections:")
    for key, name in enabled:
        verses_dir = project_dir / "_verses" / key
        count = len(list(verses_dir.glob("*.md"))) if verses_dir.exists() else 0
        print(f"  ✓ {key:30s} - {name} ({count} verses)")

    return enabled


def infer_verse_id(collection: str, verse_number: int, project_dir: Path = Path.cwd()) -> Optional[str]:
    """
    Infer verse ID by scanning existing verse files in the collection.

    Returns:
        - The inferred verse_id if exactly one match found
        - None if no matches or ambiguous (multiple matches)
    """
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        return None

    # Look for files matching the verse number
    # Patterns: chaupai_05.md, doha_05.md, verse_05.md, verse-05.md, etc.
    patterns = [
        f"*_{verse_number:02d}.md",  # chaupai_05.md, doha_05.md
        f"*{verse_number:02d}.md",   # verse05.md (no separator)
        f"*-{verse_number:02d}.md",  # verse-05.md (dash separator)
    ]

    matches = []
    for pattern in patterns:
        matches.extend(verses_dir.glob(pattern))

    # Remove duplicates
    matches = list(set(matches))

    if len(matches) == 1:
        # Found exactly one match - extract verse_id from filename
        verse_id = matches[0].stem  # Remove .md extension
        return verse_id
    elif len(matches) > 1:
        # Multiple matches - ambiguous
        print(f"\n⚠ Multiple verse files found for verse {verse_number}:")
        for match in matches:
            print(f"  - {match.name}")
        print(f"\nPlease specify which one using --verse-id")
        return None
    else:
        # No matches - this is a new verse, use default pattern
        return f"verse_{verse_number:02d}"


def generate_image(collection: str, verse: int, theme: str) -> bool:
    """Generate image for the specified verse."""
    print(f"\n{'='*60}")
    print("GENERATING IMAGE")
    print(f"{'='*60}\n")

    # Check if prompts file exists
    prompts_file = Path.cwd() / "docs" / "image-prompts" / f"{collection}.md"
    if not prompts_file.exists():
        print(f"✗ Error: Prompts file not found: {prompts_file}")
        print(f"Please create scene descriptions in {prompts_file} first")
        return False

    # Construct the verse identifier
    verse_id = f"verse_{verse:02d}"

    print(f"✓ Collection: {collection}")
    print(f"✓ Verse: {verse_id}")
    print(f"✓ Theme: {theme}")

    # Run verse-images command
    verse_images_cmd = find_command("verse-images")
    cmd = [
        verse_images_cmd,
        "--collection", collection,
        "--theme", theme,
        "--verse", verse_id
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Image generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating image: {e}")
        return False


def generate_audio(collection: str, verse: int) -> bool:
    """Generate audio for the specified verse."""
    print(f"\n{'='*60}")
    print("GENERATING AUDIO")
    print(f"{'='*60}\n")

    # Check if verse file exists
    verses_dir = Path.cwd() / "_verses" / collection
    verse_id = f"verse_{verse:02d}"
    verse_file = verses_dir / f"{verse_id}.md"

    if not verse_file.exists():
        print(f"✗ Error: Verse file not found: {verse_file}")
        print("Please create the verse markdown file first")
        return False

    print(f"✓ Collection: {collection}")
    print(f"✓ Verse: {verse_id}")

    # Run verse-audio command
    verse_audio_cmd = find_command("verse-audio")
    cmd = [
        verse_audio_cmd,
        "--collection", collection,
        "--verse", verse_id
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Audio generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating audio: {e}")
        return False


def fetch_verse_text(collection: str, verse_id: str) -> Optional[dict]:
    """Fetch traditional Devanagari text for the verse."""
    print(f"\n{'='*60}")
    print("FETCHING VERSE TEXT")
    print(f"{'='*60}\n")

    print(f"✓ Collection: {collection}")
    print(f"✓ Verse ID: {verse_id}")

    # Run verse-fetch-text command
    verse_fetch_cmd = find_command("verse-fetch-text")
    cmd = [
        verse_fetch_cmd,
        "--collection", collection,
        "--verse", verse_id,
        "--format", "json"
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Verse text fetched successfully")

        # Parse and return the JSON result
        data = json.loads(result.stdout)
        if data.get('success'):
            print(f"\nDevanagari text:")
            print(f"  {data.get('devanagari', 'N/A')}\n")
            return data
        else:
            print(f"✗ Fetch failed: {data.get('error', 'Unknown error')}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error fetching verse text: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n✗ Error parsing response: {e}")
        return None


def update_embeddings(collection: str) -> bool:
    """Update vector embeddings for the collection."""
    print(f"\n{'='*60}")
    print("UPDATING EMBEDDINGS")
    print(f"{'='*60}\n")

    print(f"✓ Collection: {collection}")

    # Check if collections.yml exists
    collections_file = Path.cwd() / "_data" / "collections.yml"
    if not collections_file.exists():
        print(f"✗ Error: collections.yml not found at {collections_file}")
        return False

    # Run verse-embeddings command
    verse_embeddings_cmd = find_command("verse-embeddings")

    # Use multi-collection mode to update all collections
    cmd = [
        verse_embeddings_cmd,
        "--multi-collection",
        "--collections-file", str(collections_file),
        "--verses-dir", "_verses",
        "--output", "data/embeddings.json"
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Embeddings updated successfully")
        print(f"✓ Output: data/embeddings.json")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error updating embeddings: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate images and audio for a specific verse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simplest form - generates everything with default theme (modern-minimalist)
  verse-generate --collection hanuman-chalisa --verse 15

  # Complete workflow: fetch text, generate media, update embeddings
  verse-generate --collection sundar-kaand --verse 5 \\
    --fetch-text --update-embeddings

  # With custom theme
  verse-generate --collection hanuman-chalisa --verse 15 --theme kids-friendly

  # Fetch text only (useful for previewing before generation)
  verse-generate --collection sundar-kaand --verse 5 --fetch-text

  # Override auto-detected verse ID (only needed for ambiguous cases)
  verse-generate --collection sundar-kaand --verse 5 --verse-id chaupai_05

  # Generate only image
  verse-generate --collection sundar-kaand --verse 3 --image

  # Generate only audio
  verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio

  # List available collections
  verse-generate --list-collections

Note:
  - Generates both image and audio by default (use --image or --audio for specific components)
  - Theme defaults to "modern-minimalist" (use --theme to change)
  - Verse ID is automatically detected from existing verse files
  - Use --verse-id only when multiple files match (e.g., chaupai_05 and doha_05)
  - For new verses, defaults to verse_{N:02d}

Environment Variables:
  OPENAI_API_KEY      - Required for image generation and embeddings
  ELEVENLABS_API_KEY  - Required for audio generation
        """
    )

    # List collections
    parser.add_argument(
        "--list-collections",
        action="store_true",
        help="List available collections and exit"
    )

    # Collection and verse identification
    parser.add_argument(
        "--collection",
        type=str,
        help="Collection key (e.g., hanuman-chalisa, sundar-kaand)",
        metavar="KEY"
    )
    parser.add_argument(
        "--verse",
        type=int,
        help="Verse number (required unless --list-collections)",
        metavar="N"
    )

    # Content types
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate both image and audio (default if no flags specified)"
    )
    parser.add_argument(
        "--image",
        action="store_true",
        help="Generate image only"
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Generate audio pronunciation only"
    )

    # Additional operations
    parser.add_argument(
        "--fetch-text",
        action="store_true",
        help="Fetch traditional Devanagari text from authoritative sources (before generation)"
    )
    parser.add_argument(
        "--update-embeddings",
        action="store_true",
        help="Update vector embeddings for semantic search (after generation)"
    )

    # Theme for image generation
    parser.add_argument(
        "--theme",
        default="modern-minimalist",
        help="Theme name for image generation (default: modern-minimalist)",
        metavar="NAME"
    )

    # Verse ID override (for non-numeric verse identifiers)
    parser.add_argument(
        "--verse-id",
        type=str,
        help="Override verse identifier (e.g., chaupai_05, doha_01). If not specified, auto-detects from existing files or defaults to verse_{N:02d}",
        metavar="ID"
    )

    args = parser.parse_args()

    # Handle list collections
    if args.list_collections:
        list_collections()
        sys.exit(0)

    # Validate required arguments
    if not args.collection:
        parser.error("--collection is required")
    if not args.verse:
        parser.error("--verse is required")

    # Default to --all if no generation flags specified
    if not any([args.all, args.image, args.audio]):
        args.all = True

    # Validate collection
    if not validate_collection(args.collection):
        sys.exit(1)

    # Determine verse ID (with smart inference)
    if args.verse_id:
        # User explicitly specified verse ID
        verse_id = args.verse_id
    else:
        # Try to infer verse ID from existing files
        inferred = infer_verse_id(args.collection, args.verse)
        if inferred is None:
            # Inference failed (multiple matches found)
            sys.exit(1)
        verse_id = inferred

        # Show inference result if it's not the default
        if verse_id != f"verse_{args.verse:02d}":
            print(f"\n✓ Auto-detected verse ID: {verse_id}")
            print(f"  (To override, use --verse-id)\n")

    # Determine what to generate
    generate_image_flag = args.all or args.image
    generate_audio_flag = args.all or args.audio
    fetch_text_flag = args.fetch_text
    update_embeddings_flag = args.update_embeddings

    # Display header
    print("\n" + "="*60)
    print("VERSE CONTENT GENERATOR")
    print("="*60)

    print(f"\nCollection: {args.collection}")
    print(f"Verse: {args.verse}")
    print(f"Verse ID: {verse_id}")
    if generate_image_flag:
        print(f"Theme: {args.theme}")

    print("\nOperations:")
    if fetch_text_flag:
        print("  ✓ Fetch verse text")
    if generate_image_flag:
        print("  ✓ Generate image")
    if generate_audio_flag:
        print("  ✓ Generate audio")
    if update_embeddings_flag:
        print("  ✓ Update embeddings")
    print()

    # Check API keys
    if generate_image_flag or update_embeddings_flag:
        if not os.getenv("OPENAI_API_KEY"):
            print("✗ Error: OPENAI_API_KEY not set (required for image generation and embeddings)")
            print("Set it in .env file or environment")
            sys.exit(1)

    if generate_audio_flag:
        if not os.getenv("ELEVENLABS_API_KEY"):
            print("✗ Error: ELEVENLABS_API_KEY not set (required for audio generation)")
            print("Set it in .env file or environment")
            sys.exit(1)

    # Track success
    results = {
        'fetch_text': None,
        'image': None,
        'audio': None,
        'embeddings': None
    }

    # Generate content in order: fetch → image → audio → embeddings
    try:
        # Step 1: Fetch verse text (optional)
        if fetch_text_flag:
            text_data = fetch_verse_text(args.collection, verse_id)
            results['fetch_text'] = text_data is not None

        # Step 2: Generate image
        if generate_image_flag:
            results['image'] = generate_image(args.collection, args.verse, args.theme)

        # Step 3: Generate audio
        if generate_audio_flag:
            results['audio'] = generate_audio(args.collection, args.verse)

        # Step 4: Update embeddings
        if update_embeddings_flag:
            results['embeddings'] = update_embeddings(args.collection)

    except KeyboardInterrupt:
        print("\n\n⚠ Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}\n")

    if fetch_text_flag:
        status = "✓" if results['fetch_text'] else "✗"
        print(f"{status} Fetch text: {'Success' if results['fetch_text'] else 'Failed'}")

    if generate_image_flag:
        status = "✓" if results['image'] else "✗"
        print(f"{status} Image: {'Success' if results['image'] else 'Failed'}")

    if generate_audio_flag:
        status = "✓" if results['audio'] else "✗"
        print(f"{status} Audio: {'Success' if results['audio'] else 'Failed'}")

    if update_embeddings_flag:
        status = "✓" if results['embeddings'] else "✗"
        print(f"{status} Embeddings: {'Success' if results['embeddings'] else 'Failed'}")

    print()

    # Exit with appropriate code
    all_results = [r for r in results.values() if r is not None]
    if all_results and all(all_results):
        print("✓ All tasks completed successfully!")
        sys.exit(0)
    elif any(all_results):
        print("⚠ Some tasks completed with errors")
        sys.exit(1)
    else:
        print("✗ All tasks failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
