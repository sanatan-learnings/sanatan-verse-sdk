#!/usr/bin/env python3
"""
Collection-aware verse content generator - complete orchestration of all verse content.

This command is the one-stop solution for generating all content for a verse:
- Fetch traditional Devanagari text from canonical sources (optional)
- Regenerate AI content from canonical text (transliteration, meaning, translation, story)
- Generate AI image with DALL-E 3
- Generate audio pronunciation with ElevenLabs (full + slow speed)
- Update vector embeddings for semantic search

Usage:
    # Generate everything for a verse
    verse-generate --collection hanuman-chalisa --verse 15 --all --theme modern-minimalist --update-embeddings

    # Regenerate AI content from canonical source
    verse-generate --collection sundar-kaand --verse 3 --regenerate-content

    # Regenerate content and multimedia
    verse-generate --collection sundar-kaand --verse 3 --regenerate-content --all

    # Generate only image
    verse-generate --collection sundar-kaand --verse 3 --image --theme modern-minimalist

    # Generate only audio
    verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio

Requirements:
    - OPENAI_API_KEY environment variable (for content generation, image generation, and embeddings)
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

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed")
    print("Install with: pip install openai")
    sys.exit(1)

# Load environment variables
load_dotenv()


def generate_verse_content(devanagari_text: str, collection: str) -> dict:
    """
    Generate AI content (transliteration, meaning, translation, story) from Devanagari text.

    Args:
        devanagari_text: The canonical Devanagari verse text
        collection: Collection key for context

    Returns:
        Dictionary with generated content fields
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    prompt = f"""You are an expert in Sanskrit/Hindi spiritual texts. Given this verse from {collection}:

Devanagari: {devanagari_text}

Please provide:

1. TRANSLITERATION (IAST format, precisely matching the Devanagari):
[Your transliteration here]

2. WORD-BY-WORD MEANING:
[Detailed breakdown of each word/phrase in the verse]

3. ENGLISH TRANSLATION (natural, flowing translation):
[Your translation here]

4. STORY & CONTEXT (2-3 paragraphs explaining the context, significance, and deeper meaning):
[Your story/explanation here]

5. PRACTICAL APPLICATIONS (2-3 practical ways to apply this verse's teachings in daily life):
[Your practical applications here]

Format your response exactly as above with clear section headers."""

    try:
        print(f"  → Generating AI content from canonical text...", file=sys.stderr)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Sanskrit and Hindi spiritual texts, providing accurate transliterations, translations, and meaningful interpretations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent, accurate results
        )

        content = response.choices[0].message.content

        # Parse the response into structured fields
        result = {
            "devanagari": devanagari_text,
            "transliteration": "",
            "meaning": "",
            "translation": {"en": ""},
            "story": "",
            "practical_applications": ""
        }

        # Simple parsing - split by section headers
        sections = content.split("\n\n")
        current_section = None

        for section in sections:
            section = section.strip()
            if not section:
                continue

            if "TRANSLITERATION" in section.upper():
                current_section = "transliteration"
                # Get text after the header
                lines = section.split("\n")[1:]
                result["transliteration"] = "\n".join(lines).strip()
            elif "WORD-BY-WORD" in section.upper() or "MEANING" in section.upper():
                current_section = "meaning"
                lines = section.split("\n")[1:]
                result["meaning"] = "\n".join(lines).strip()
            elif "TRANSLATION" in section.upper():
                current_section = "translation"
                lines = section.split("\n")[1:]
                result["translation"]["en"] = "\n".join(lines).strip()
            elif "STORY" in section.upper() or "CONTEXT" in section.upper():
                current_section = "story"
                lines = section.split("\n")[1:]
                result["story"] = "\n".join(lines).strip()
            elif "PRACTICAL" in section.upper() or "APPLICATIONS" in section.upper():
                current_section = "practical_applications"
                lines = section.split("\n")[1:]
                result["practical_applications"] = "\n".join(lines).strip()
            elif current_section and not any(keyword in section.upper() for keyword in ["1.", "2.", "3.", "4.", "5."]):
                # Continue current section
                if current_section == "translation":
                    result["translation"]["en"] += "\n" + section
                else:
                    result[current_section] += "\n" + section

        print(f"  ✓ Generated transliteration, meaning, translation, story, and practical applications", file=sys.stderr)
        return result

    except Exception as e:
        print(f"  ✗ Error generating content: {e}", file=sys.stderr)
        sys.exit(1)


def update_verse_file_with_content(verse_file: Path, content: dict) -> bool:
    """
    Update verse markdown file with generated content.

    Args:
        verse_file: Path to the verse markdown file
        content: Dictionary with generated content fields

    Returns:
        True if successful, False otherwise
    """
    if not verse_file.exists():
        print(f"  ✗ Verse file not found: {verse_file}", file=sys.stderr)
        return False

    try:
        # Read existing file
        with open(verse_file, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Parse frontmatter and body
        if not file_content.startswith('---'):
            print(f"  ✗ Invalid verse file format (no frontmatter): {verse_file}", file=sys.stderr)
            return False

        parts = file_content.split('---', 2)
        if len(parts) < 3:
            print(f"  ✗ Invalid verse file format (incomplete frontmatter): {verse_file}", file=sys.stderr)
            return False

        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2]

        # Update frontmatter with generated content
        frontmatter['devanagari'] = content['devanagari']
        frontmatter['transliteration'] = content['transliteration']
        frontmatter['meaning'] = content['meaning']
        frontmatter['translation'] = content['translation']

        # Build updated content
        updated_content = "---\n"
        updated_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
        updated_content += "---"

        # Update body if we have story and practical applications
        if content.get('story') or content.get('practical_applications'):
            # Replace or add story and practical applications sections
            if '## Story' in body or '## Context' in body:
                # Replace existing story section
                import re
                body = re.sub(
                    r'## (Story|Context).*?(?=##|$)',
                    f"## Story & Context\n\n{content.get('story', '')}\n\n",
                    body,
                    flags=re.DOTALL
                )
            else:
                # Add story section
                body += f"\n\n## Story & Context\n\n{content.get('story', '')}\n"

            if '## Practical' in body:
                # Replace existing practical applications
                import re
                body = re.sub(
                    r'## Practical.*?(?=##|$)',
                    f"## Practical Applications\n\n{content.get('practical_applications', '')}\n\n",
                    body,
                    flags=re.DOTALL
                )
            else:
                # Add practical applications section
                body += f"\n## Practical Applications\n\n{content.get('practical_applications', '')}\n"

        updated_content += body

        # Write updated file
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  ✓ Updated verse file: {verse_file.name}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"  ✗ Error updating verse file: {e}", file=sys.stderr)
        return False


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


def generate_scene_description(devanagari_text: str, verse_id: str, collection: str) -> str:
    """
    Generate scene description from Devanagari text using GPT-4.

    Args:
        devanagari_text: The canonical Devanagari verse text
        verse_id: Verse identifier (e.g., chaupai_05, verse_01)
        collection: Collection key for context

    Returns:
        Scene description text
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    prompt = f"""You are an expert in Sanskrit/Hindi spiritual texts and visual storytelling. Given this verse from {collection}:

Devanagari: {devanagari_text}

Create a detailed scene description for generating an image with DALL-E 3. The description should:

1. Describe the key visual elements, characters, and setting
2. Specify the mood, atmosphere, and lighting
3. Include important symbolic elements if relevant
4. Be specific about composition and focus
5. Be 2-4 sentences, rich in visual detail but concise

Provide ONLY the scene description, no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in spiritual texts and visual storytelling, creating vivid scene descriptions for image generation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # Slightly higher for creative descriptions
        )

        scene_description = response.choices[0].message.content.strip()
        return scene_description

    except Exception as e:
        print(f"  ✗ Error generating scene description: {e}", file=sys.stderr)
        return None


def ensure_scene_description_exists(collection: str, verse_number: int, verse_id: str, devanagari_text: str) -> bool:
    """
    Ensure scene description exists for the verse. Creates file and/or adds scene if missing.

    Args:
        collection: Collection key
        verse_number: Verse number (for ordering)
        verse_id: Verse identifier (e.g., chaupai_05)
        devanagari_text: Canonical Devanagari text for generating description

    Returns:
        True if scene description is available, False if failed
    """
    prompts_dir = Path.cwd() / "docs" / "image-prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    prompts_file = prompts_dir / f"{collection}.md"

    # Create file if it doesn't exist
    if not prompts_file.exists():
        print(f"  → Creating scene descriptions file: {prompts_file.name}")
        header = f"""# {collection.replace('-', ' ').title()} - Image Prompts

Scene descriptions for generating images with DALL-E 3.

---

"""
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(header)
        print(f"  ✓ Created {prompts_file.name}")

    # Read current content
    with open(prompts_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate new scene description
    print(f"  → Generating scene description for Verse {verse_number}...")
    scene_description = generate_scene_description(devanagari_text, verse_id, collection)

    if not scene_description:
        print(f"  ✗ Failed to generate scene description")
        return False

    # Prepare new verse entry
    verse_entry = f"""### Verse {verse_number}: {verse_id}

**Scene Description**:
{scene_description}

---

"""

    # Check if scene description already exists
    import re
    verse_pattern = rf'### Verse {verse_number}:.*?(?=\n---\n|\Z)'

    if re.search(verse_pattern, content, re.DOTALL):
        # Replace existing scene description
        print(f"  → Replacing existing scene description for Verse {verse_number}...")
        updated_content = re.sub(
            verse_pattern,
            verse_entry.rstrip('\n'),
            content,
            flags=re.DOTALL
        )

        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  ✓ Updated scene description for Verse {verse_number} in {prompts_file.name}")
    else:
        # Append new scene description
        with open(prompts_file, 'a', encoding='utf-8') as f:
            f.write(verse_entry)

        print(f"  ✓ Added scene description for Verse {verse_number} to {prompts_file.name}")

    return True


def generate_image(collection: str, verse: int, theme: str, verse_id: str = None) -> bool:
    """Generate image for the specified verse."""
    print(f"\n{'='*60}")
    print("GENERATING IMAGE")
    print(f"{'='*60}\n")

    # Prompts file will be created if needed by ensure_scene_description_exists
    prompts_file = Path.cwd() / "docs" / "image-prompts" / f"{collection}.md"

    # Use provided verse_id or default to verse_{N:02d}
    if not verse_id:
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


def generate_audio(collection: str, verse: int, verse_id: str = None) -> bool:
    """Generate audio for the specified verse."""
    print(f"\n{'='*60}")
    print("GENERATING AUDIO")
    print(f"{'='*60}\n")

    # Use provided verse_id or default to verse_{N:02d}
    if not verse_id:
        verse_id = f"verse_{verse:02d}"

    # Check if verse file exists
    verses_dir = Path.cwd() / "_verses" / collection
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
  # Complete workflow (default) - fetch text, generate media, update embeddings
  verse-generate --collection hanuman-chalisa --verse 15

  # With custom theme
  verse-generate --collection hanuman-chalisa --verse 15 --theme kids-friendly

  # Skip embeddings update (faster, but search won't include this verse)
  verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings

  # Just regenerate media (no embeddings update)
  verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings

  # Generate only image
  verse-generate --collection sundar-kaand --verse 3 --image

  # Generate only audio
  verse-generate --collection sankat-mochan-hanumanashtak --verse 5 --audio

  # Regenerate AI content from canonical source
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content

  # Regenerate content and multimedia
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content --all

  # Override auto-detected verse ID (only needed for ambiguous cases)
  verse-generate --collection sundar-kaand --verse 5 --verse-id chaupai_05

  # List available collections
  verse-generate --list-collections

Note:
  - Complete workflow by default: generates image + audio, updates embeddings
  - Use --regenerate-content to regenerate AI text content from canonical source
  - Use --no-update-embeddings to skip embeddings (faster generation)
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

    # Additional operations (enabled by default)
    parser.add_argument(
        "--update-embeddings",
        dest="update_embeddings",
        action="store_true",
        default=True,
        help="Update vector embeddings for semantic search (default: enabled)"
    )
    parser.add_argument(
        "--no-update-embeddings",
        dest="update_embeddings",
        action="store_false",
        help="Skip updating embeddings"
    )

    # Content regeneration
    parser.add_argument(
        "--regenerate-content",
        action="store_true",
        help="Regenerate AI content (transliteration, meaning, translation, story) from canonical Devanagari text"
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
    update_embeddings_flag = args.update_embeddings
    regenerate_content_flag = args.regenerate_content

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
    if regenerate_content_flag:
        print("  ✓ Regenerate AI content (transliteration, meaning, translation, story)")
    if generate_image_flag:
        print("  ✓ Generate image")
    if generate_audio_flag:
        print("  ✓ Generate audio")
    if update_embeddings_flag:
        print("  ✓ Update embeddings")
    print()

    # Check API keys
    if generate_image_flag or update_embeddings_flag or regenerate_content_flag:
        if not os.getenv("OPENAI_API_KEY"):
            print("✗ Error: OPENAI_API_KEY not set (required for content generation, image generation, and embeddings)")
            print("Set it in .env file or environment")
            sys.exit(1)

    if generate_audio_flag:
        if not os.getenv("ELEVENLABS_API_KEY"):
            print("✗ Error: ELEVENLABS_API_KEY not set (required for audio generation)")
            print("Set it in .env file or environment")
            sys.exit(1)

    # Track success
    results = {
        'regenerate_content': None,
        'image': None,
        'audio': None,
        'embeddings': None
    }

    # Generate content in order: regenerate content → image → audio → embeddings
    try:
        # Step 1: Regenerate AI content (optional)
        if regenerate_content_flag:
            # Load canonical Devanagari from data/verses/{collection}.yaml
            from verse_sdk.fetch.fetch_verse_text import fetch_from_local_file

            canonical_data = fetch_from_local_file(args.collection, verse_id)
            if not canonical_data or not canonical_data.get('devanagari'):
                print(f"  ✗ Error: No canonical Devanagari text found for {verse_id}", file=sys.stderr)
                print(f"  Please create data/verses/{args.collection}.yaml with canonical text", file=sys.stderr)
                results['regenerate_content'] = False
            else:
                # Generate content from canonical text
                generated_content = generate_verse_content(
                    canonical_data['devanagari'],
                    args.collection
                )

                # Update verse markdown file
                verse_file = Path.cwd() / "_verses" / args.collection / f"{verse_id}.md"
                results['regenerate_content'] = update_verse_file_with_content(verse_file, generated_content)

        # Step 2: Generate image
        if generate_image_flag:
            # Ensure scene description exists before generating image
            from verse_sdk.fetch.fetch_verse_text import fetch_from_local_file

            print(f"\n{'='*60}")
            print("PREPARING SCENE DESCRIPTION")
            print(f"{'='*60}\n")

            canonical_data = fetch_from_local_file(args.collection, verse_id)
            if not canonical_data or not canonical_data.get('devanagari'):
                print(f"  ✗ Error: No canonical Devanagari text found for {verse_id}", file=sys.stderr)
                print(f"  Please create data/verses/{args.collection}.yaml with canonical text", file=sys.stderr)
                print(f"  Cannot generate scene description without canonical text.", file=sys.stderr)
                results['image'] = False
            else:
                # Ensure scene description exists (creates file/adds description if needed)
                scene_ready = ensure_scene_description_exists(
                    args.collection,
                    args.verse,
                    verse_id,
                    canonical_data['devanagari']
                )

                if scene_ready:
                    results['image'] = generate_image(args.collection, args.verse, args.theme, verse_id)
                else:
                    print(f"  ✗ Failed to prepare scene description", file=sys.stderr)
                    results['image'] = False

        # Step 3: Generate audio
        if generate_audio_flag:
            results['audio'] = generate_audio(args.collection, args.verse, verse_id)

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

    if regenerate_content_flag:
        status = "✓" if results['regenerate_content'] else "✗"
        print(f"{status} Regenerate content: {'Success' if results['regenerate_content'] else 'Failed'}")

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
