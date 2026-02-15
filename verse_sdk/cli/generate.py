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


def generate_verse_content(devanagari_text: str, collection: str, verse_id: str = None) -> dict:
    """
    Generate AI content (transliteration, meaning, translation, story) from Devanagari text.

    Args:
        devanagari_text: The canonical Devanagari verse text
        collection: Collection key for context
        verse_id: Verse identifier (e.g., chaupai_02, shloka_01)

    Returns:
        Dictionary with generated content fields in complete chaupai format
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    prompt = f"""You are an expert in Sanskrit/Hindi spiritual texts. Given this verse from {collection}:

Devanagari: {devanagari_text}
Verse ID: {verse_id or 'unknown'}

Please provide complete verse analysis in the following format:

1. VERSE TITLE (short, descriptive - 3-6 words capturing the essence):
English: [Title in English]
Hindi: [शीर्षक हिंदी में]

2. TRANSLITERATION (IAST format, single line, precisely matching the Devanagari):
[Your transliteration here]

3. PHONETIC NOTES (for 2-3 key words that may be difficult to pronounce):
CRITICAL: Only include words that ACTUALLY APPEAR in the Devanagari text above.
Format each as:
PHONETIC: [Devanagari word from verse] | PRONUNCIATION: [syllable-by-syllable] | EMPHASIS: [which syllable]

Example (only if these words appear in the verse):
PHONETIC: हनुमंत | PRONUNCIATION: ha-nu-mant | EMPHASIS: first syllable
PHONETIC: परिखेहु | PRONUNCIATION: pa-ri-khe-hu | EMPHASIS: third syllable

4. WORD-BY-WORD MEANINGS (structured list of ALL key words):
Format each word exactly as:
WORD: [Devanagari word] | ROMAN: [romanization] | EN: [English meaning] | HI: [Hindi meaning]

Example:
WORD: तब | ROMAN: Tab | EN: then/until then | HI: तब/तब तक
WORD: लगि | ROMAN: Lagi | EN: until | HI: तक

5. WORD-BY-WORD BREAKDOWN (plain text explanation):
[Simple word-by-word meaning explanation]

6. LITERAL TRANSLATION:
English: [Direct, literal translation]
Hindi: [शाब्दिक अनुवाद]

7. INTERPRETIVE MEANING (deeper spiritual/contextual explanation):
English: [2-3 sentences explaining the deeper meaning]
Hindi: [गहरा अर्थ 2-3 वाक्य]

8. STORY & CONTEXT:
English: [2-3 paragraphs explaining context, significance, and narrative]
Hindi: [संदर्भ और कथा 2-3 पैराग्राफ]

9. PRACTICAL APPLICATION:
Teaching (English): [Core teaching in 1-2 sentences]
Teaching (Hindi): [मुख्य शिक्षा 1-2 वाक्य]
When to Use (English): [When to recite/apply this verse]
When to Use (Hindi): [कब उपयोग करें]

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

        # Parse the response into structured fields (complete chaupai format)
        result = {
            "devanagari": devanagari_text,
            "transliteration": "",
            "title_en": "",
            "title_hi": "",
            "phonetic_notes": [],
            "word_meanings": [],
            "meaning": "",
            "literal_translation": {"en": "", "hi": ""},
            "interpretive_meaning": {"en": "", "hi": ""},
            "story": {"en": "", "hi": ""},
            "practical_application": {
                "teaching": {"en": "", "hi": ""},
                "when_to_use": {"en": "", "hi": ""}
            },
            "translation": {"en": ""}  # For backward compatibility
        }

        # Parse sections
        lines = content.split("\n")
        current_section = None
        current_lang = None

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Section headers
            if "VERSE TITLE" in line.upper() or line.strip() == "1.":
                current_section = "title"
            elif "TRANSLITERATION" in line.upper() or line.strip() == "2.":
                current_section = "transliteration"
            elif "PHONETIC NOTES" in line.upper() or line.strip() == "3.":
                current_section = "phonetic_notes"
            elif "WORD-BY-WORD MEANINGS" in line.upper() or line.strip() == "4.":
                current_section = "word_meanings"
            elif "WORD-BY-WORD BREAKDOWN" in line.upper() or line.strip() == "5.":
                current_section = "meaning"
            elif "LITERAL TRANSLATION" in line.upper() or line.strip() == "6.":
                current_section = "literal_translation"
            elif "INTERPRETIVE MEANING" in line.upper() or line.strip() == "7.":
                current_section = "interpretive_meaning"
            elif "STORY" in line.upper() or line.strip() == "8.":
                current_section = "story"
            elif "PRACTICAL APPLICATION" in line.upper() or line.strip() == "9.":
                current_section = "practical_application"
            # Language indicators
            elif line_stripped.startswith("English:"):
                current_lang = "en"
                text = line_stripped[8:].strip()
                if current_section == "title" and text:
                    result["title_en"] = text
                elif current_section == "literal_translation" and text:
                    result["literal_translation"]["en"] = text
                elif current_section == "interpretive_meaning" and text:
                    result["interpretive_meaning"]["en"] = text
                elif current_section == "story" and text:
                    result["story"]["en"] = text
            elif line_stripped.startswith("Hindi:") or line_stripped.startswith("हिंदी:"):
                current_lang = "hi"
                text = line_stripped.split(":", 1)[1].strip()
                if current_section == "title" and text:
                    result["title_hi"] = text
                elif current_section == "literal_translation" and text:
                    result["literal_translation"]["hi"] = text
                elif current_section == "interpretive_meaning" and text:
                    result["interpretive_meaning"]["hi"] = text
                elif current_section == "story" and text:
                    result["story"]["hi"] = text
            elif "Teaching" in line and "English" in line:
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                result["practical_application"]["teaching"]["en"] = text
            elif "Teaching" in line and ("Hindi" in line or "हिंदी" in line):
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                result["practical_application"]["teaching"]["hi"] = text
            elif "When to Use" in line and "English" in line:
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                result["practical_application"]["when_to_use"]["en"] = text
            elif "When to Use" in line and ("Hindi" in line or "कब" in line):
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                result["practical_application"]["when_to_use"]["hi"] = text
            # Content lines
            elif current_section == "transliteration" and line_stripped and not any(x in line.upper() for x in ["TRANSLITERATION", "2."]):
                result["transliteration"] = line_stripped
            elif current_section == "phonetic_notes" and line_stripped and "PHONETIC:" in line_stripped:
                # Parse phonetic note entry: PHONETIC: word | PRONUNCIATION: syllables | EMPHASIS: which
                try:
                    parts = line_stripped.split("|")
                    if len(parts) >= 3:
                        word = ""
                        phonetic = ""
                        emphasis = ""

                        for part in parts:
                            part = part.strip()
                            if part.startswith("PHONETIC:"):
                                word = part[9:].strip()
                            elif part.startswith("PRONUNCIATION:"):
                                phonetic = part[14:].strip()
                            elif part.startswith("EMPHASIS:"):
                                emphasis = part[9:].strip()

                        if word and phonetic:
                            # Validate that the word exists in the devanagari text
                            if word in devanagari_text:
                                result["phonetic_notes"].append({
                                    "word": word,
                                    "phonetic": phonetic,
                                    "emphasis": emphasis
                                })
                            else:
                                print(f"  ⚠ Warning: Skipping phonetic note for '{word}' - not found in verse", file=sys.stderr)
                except Exception as e:
                    print(f"  ⚠ Warning: Failed to parse phonetic note: {line_stripped}", file=sys.stderr)
                    pass  # Skip malformed entries
            elif current_section == "word_meanings" and line_stripped and "WORD:" in line_stripped:
                # Parse word meaning entry: WORD: ... | ROMAN: ... | EN: ... | HI: ...
                try:
                    parts = line_stripped.split("|")
                    if len(parts) >= 4:
                        word = ""
                        roman = ""
                        meaning_en = ""
                        meaning_hi = ""

                        for part in parts:
                            part = part.strip()
                            if part.startswith("WORD:"):
                                word = part[5:].strip()
                            elif part.startswith("ROMAN:"):
                                roman = part[6:].strip()
                            elif part.startswith("EN:"):
                                meaning_en = part[3:].strip()
                            elif part.startswith("HI:"):
                                meaning_hi = part[3:].strip()

                        if word and roman:
                            result["word_meanings"].append({
                                "word": word,
                                "roman": roman,
                                "meaning": {
                                    "en": meaning_en,
                                    "hi": meaning_hi
                                }
                            })
                except Exception:
                    pass  # Skip malformed entries
            elif current_section == "meaning" and line_stripped and not any(x in line.upper() for x in ["BREAKDOWN", "4."]):
                result["meaning"] += line_stripped + " "
            elif current_section == "literal_translation" and current_lang == "en" and not "English:" in line:
                result["literal_translation"]["en"] += " " + line_stripped
            elif current_section == "literal_translation" and current_lang == "hi" and not "Hindi:" in line:
                result["literal_translation"]["hi"] += " " + line_stripped
            elif current_section == "interpretive_meaning" and current_lang == "en" and not "English:" in line:
                result["interpretive_meaning"]["en"] += " " + line_stripped
            elif current_section == "interpretive_meaning" and current_lang == "hi" and not "Hindi:" in line:
                result["interpretive_meaning"]["hi"] += " " + line_stripped
            elif current_section == "story" and current_lang == "en" and not "English:" in line:
                result["story"]["en"] += " " + line_stripped
            elif current_section == "story" and current_lang == "hi" and not "Hindi:" in line:
                result["story"]["hi"] += " " + line_stripped

        # Clean up whitespace
        result["meaning"] = result["meaning"].strip()
        result["literal_translation"]["en"] = result["literal_translation"]["en"].strip()
        result["literal_translation"]["hi"] = result["literal_translation"]["hi"].strip()
        result["interpretive_meaning"]["en"] = result["interpretive_meaning"]["en"].strip()
        result["interpretive_meaning"]["hi"] = result["interpretive_meaning"]["hi"].strip()
        result["story"]["en"] = result["story"]["en"].strip()
        result["story"]["hi"] = result["story"]["hi"].strip()

        # Set translation.en for backward compatibility (use literal or interpretive)
        result["translation"]["en"] = result["literal_translation"]["en"] or result["interpretive_meaning"]["en"]

        print(f"  ✓ Generated complete verse content with titles, translations, story, and practical applications", file=sys.stderr)
        return result

    except Exception as e:
        print(f"  ✗ Error generating content: {e}", file=sys.stderr)
        sys.exit(1)


def create_verse_file_with_content(verse_file: Path, content: dict, collection: str, verse_num: int, verse_id: str = None) -> bool:
    """
    Create a new verse markdown file with generated content in complete chaupai format.

    Args:
        verse_file: Path to the verse markdown file to create
        content: Dictionary with generated content fields
        collection: Collection key
        verse_num: Verse number
        verse_id: Verse identifier (e.g., chaupai_02, shloka_01)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        verse_file.parent.mkdir(parents=True, exist_ok=True)

        # Extract verse_id from filename if not provided
        if not verse_id:
            verse_id = verse_file.stem  # e.g., chaupai_02 from chaupai_02.md

        # Determine verse type and format IDs
        verse_type = verse_id.split('_')[0] if '_' in verse_id else 'verse'  # chaupai, shloka, doha, etc.

        # Build complete frontmatter (chaupai format)
        frontmatter = {
            'layout': 'verse',
            'collection_key': collection,
            'permalink': f'/{collection}/{verse_id}/',
            'title_en': content.get('title_en', f'{verse_type.title()} {verse_num}'),
            'title_hi': content.get('title_hi', f'{verse_type} {verse_num}'),
            'verse_number': verse_num,
            'verse_type': verse_type,
            'previous_verse': f'/{collection}/{verse_type}_{verse_num-1:02d}' if verse_num > 1 else None,
            'next_verse': f'/{collection}/{verse_type}_{verse_num+1:02d}',
            'image': f'/images/{collection}/modern-minimalist/{verse_id.replace("_", "-")}.png',
            'devanagari': content['devanagari'],
            'transliteration': content['transliteration'],
            'phonetic_notes': content.get('phonetic_notes', []),
            'word_meanings': content.get('word_meanings', []),
            'literal_translation': content.get('literal_translation', {'en': '', 'hi': ''}),
            'interpretive_meaning': content.get('interpretive_meaning', {'en': '', 'hi': ''}),
            'story': content.get('story', {'en': '', 'hi': ''}),
            'practical_application': content.get('practical_application', {
                'teaching': {'en': '', 'hi': ''},
                'when_to_use': {'en': '', 'hi': ''}
            }),
            'meaning': content.get('meaning', ''),
            'translation': content.get('translation', {'en': ''})
        }

        # Remove None values
        frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

        # Build file content
        file_content = "---\n"
        file_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False)
        file_content += "---\n"

        # Add body sections (minimal, most content is in frontmatter)
        # Only add if story/practical_application are strings (legacy format)
        if isinstance(content.get('story'), str) and content.get('story'):
            file_content += f"\n## Story & Context\n\n{content['story']}\n"

        if isinstance(content.get('practical_applications'), str) and content.get('practical_applications'):
            file_content += f"\n## Practical Applications\n\n{content['practical_applications']}\n"

        # Write file
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(file_content)

        print(f"  ✓ Created verse file: {verse_file.name}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"  ✗ Error creating verse file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


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

        # Get verse info from existing frontmatter or filename
        verse_num = frontmatter.get('verse_number', 0)
        collection = frontmatter.get('collection_key') or frontmatter.get('collection', 'unknown')
        verse_id = verse_file.stem  # e.g., shloka_02
        verse_type = verse_id.split('_')[0] if '_' in verse_id else 'verse'

        # Update frontmatter with ALL generated content (complete chaupai format)
        # Preserve existing metadata fields but add/update with new structure
        frontmatter.update({
            'layout': frontmatter.get('layout', 'verse'),
            'collection_key': collection,  # Use collection_key, not just collection
            'permalink': frontmatter.get('permalink', f'/{collection}/{verse_id}/'),
            'title_en': content.get('title_en', frontmatter.get('title_en', f'{verse_type.title()} {verse_num}')),
            'title_hi': content.get('title_hi', frontmatter.get('title_hi', f'{verse_type} {verse_num}')),
            'verse_number': verse_num,
            'verse_type': verse_type,
            'previous_verse': frontmatter.get('previous_verse', f'/{collection}/{verse_type}_{verse_num-1:02d}' if verse_num > 1 else None),
            'next_verse': frontmatter.get('next_verse', f'/{collection}/{verse_type}_{verse_num+1:02d}'),
            'image': frontmatter.get('image', f'/images/{collection}/modern-minimalist/{verse_id.replace("_", "-")}.png'),
            'devanagari': content['devanagari'],
            'transliteration': content['transliteration'],
            'phonetic_notes': content.get('phonetic_notes', frontmatter.get('phonetic_notes', [])),
            'word_meanings': content.get('word_meanings', frontmatter.get('word_meanings', [])),
            'literal_translation': content.get('literal_translation', {'en': '', 'hi': ''}),
            'interpretive_meaning': content.get('interpretive_meaning', {'en': '', 'hi': ''}),
            'story': content.get('story', {'en': '', 'hi': ''}),
            'practical_application': content.get('practical_application', {
                'teaching': {'en': '', 'hi': ''},
                'when_to_use': {'en': '', 'hi': ''}
            }),
            'meaning': content.get('meaning', ''),
            'translation': content.get('translation', {'en': ''})
        })

        # Remove None values and old 'collection' field
        frontmatter = {k: v for k, v in frontmatter.items() if v is not None and k != 'collection'}

        # Build updated content
        updated_content = "---\n"
        updated_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False)
        updated_content += "---"

        # Remove body sections (everything should be in frontmatter now for complete format)
        # Only keep body if there's custom content beyond standard sections
        updated_content += "\n"

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
    # First, try to find command in the same directory as current Python executable
    # This ensures we use commands from the same virtual environment
    python_executable = Path(sys.executable)
    bin_dir = python_executable.parent
    cmd_in_venv = bin_dir / command_name

    if cmd_in_venv.exists():
        return str(cmd_in_venv)

    # Try shutil.which (checks PATH)
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


def ensure_scene_description_exists(collection: str, verse_number: int, verse_id: str, devanagari_text: str, title_en: str = None) -> bool:
    """
    Ensure scene description exists for the verse. Creates file and/or adds scene if missing.

    Args:
        collection: Collection key
        verse_number: Verse number (for ordering)
        verse_id: Verse identifier (e.g., chaupai_05)
        devanagari_text: Canonical Devanagari text for generating description
        title_en: English title of the verse (optional)

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

    # Extract verse type from verse_id (e.g., "chaupai" from "chaupai_05")
    verse_type = verse_id.split('_')[0] if '_' in verse_id else 'verse'
    verse_type_title = verse_type.title()  # Capitalize: Chaupai, Shloka, Doha, etc.

    # Generate new scene description
    print(f"  → Generating scene description for {verse_type_title} {verse_number}...")
    scene_description = generate_scene_description(devanagari_text, verse_id, collection)

    if not scene_description:
        print(f"  ✗ Failed to generate scene description")
        return False

    # Build header: "### Chaupai 5 (chaupai_05): Title" or "### Chaupai 5 (chaupai_05)" if no title
    if title_en:
        header = f"### {verse_type_title} {verse_number} ({verse_id}): {title_en}"
    else:
        header = f"### {verse_type_title} {verse_number} ({verse_id})"

    # Prepare new verse entry
    verse_entry = f"""{header}

**Scene Description**:
{scene_description}

---

"""

    # Check if scene description already exists (match both old and new formats)
    import re
    # Match verse header followed by content until the next --- separator or end of file
    # Use \s* to handle variable whitespace before ---
    verse_pattern = rf'### (?:Verse {verse_number}|{verse_type_title} {verse_number})[^\n]*\n.*?(?=\n---\s*\n|\Z)'

    if re.search(verse_pattern, content, re.DOTALL):
        # Replace existing scene description
        print(f"  → Replacing existing scene description for {verse_type_title} {verse_number}...")
        updated_content = re.sub(
            verse_pattern,
            verse_entry.rstrip('\n'),
            content,
            flags=re.DOTALL
        )

        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  ✓ Updated scene description for {verse_type_title} {verse_number} in {prompts_file.name}")
    else:
        # Append new scene description
        with open(prompts_file, 'a', encoding='utf-8') as f:
            f.write(verse_entry)

        print(f"  ✓ Added scene description for {verse_type_title} {verse_number} to {prompts_file.name}")

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

        # Verify that audio files were actually created with non-zero size
        audio_dir = Path.cwd() / "audio" / collection
        full_audio = audio_dir / f"{verse_id}_full.mp3"
        slow_audio = audio_dir / f"{verse_id}_slow.mp3"

        # Check if files exist
        if not full_audio.exists() or not slow_audio.exists():
            print(f"\n✗ Audio generation reported success but files not found:")
            if not full_audio.exists():
                print(f"  Missing: {full_audio}")
            if not slow_audio.exists():
                print(f"  Missing: {slow_audio}")
            print("\nThis may indicate an issue with the audio generation workflow.")
            return False

        # Check if files have non-zero size (not corrupted/empty)
        full_size = full_audio.stat().st_size
        slow_size = slow_audio.stat().st_size

        if full_size == 0 or slow_size == 0:
            print(f"\n✗ Audio generation created corrupted files (0 bytes):")
            if full_size == 0:
                print(f"  Corrupted: {full_audio.name} (0 bytes)")
            if slow_size == 0:
                print(f"  Corrupted: {slow_audio.name} (0 bytes)")
            print("\nPossible causes:")
            print("  - ElevenLabs API returned empty response")
            print("  - Network interruption during download")
            print("  - Insufficient disk space")
            print("\nTry regenerating with: verse-audio --collection {collection} --verse {verse_id} --force")
            return False

        print(f"\n✓ Audio generated successfully")
        print(f"  ✓ {full_audio.name}")
        print(f"  ✓ {slow_audio.name}")
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

  # Regenerate AI content only (no multimedia)
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content

  # Regenerate content AND multimedia
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content --all

  # Override auto-detected verse ID (only needed for ambiguous cases)
  verse-generate --collection sundar-kaand --verse 5 --verse-id chaupai_05

  # List available collections
  verse-generate --list-collections

Note:
  - Complete workflow by default: generates image + audio, updates embeddings
  - Use --regenerate-content ALONE to only regenerate text (no multimedia)
  - Use --regenerate-content --all to regenerate text AND multimedia
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
        type=str,
        help="Verse number or range (e.g., 5, 1-10, 5-20)",
        metavar="N or M-N"
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
    # BUT: if only --regenerate-content is specified, don't generate multimedia
    if not any([args.all, args.image, args.audio, args.regenerate_content]):
        args.all = True

    # Validate collection
    if not validate_collection(args.collection):
        sys.exit(1)

    # Parse verse argument (supports single number or range)
    verse_numbers = []
    if '-' in args.verse:
        # Range format: M-N
        try:
            start, end = args.verse.split('-')
            start_num = int(start.strip())
            end_num = int(end.strip())
            if start_num > end_num:
                print(f"✗ Error: Invalid range {args.verse} (start must be <= end)")
                sys.exit(1)
            verse_numbers = list(range(start_num, end_num + 1))
        except ValueError:
            print(f"✗ Error: Invalid verse range format: {args.verse}")
            print("Use format: M-N (e.g., 1-10, 5-20)")
            sys.exit(1)
    else:
        # Single verse number
        try:
            verse_numbers = [int(args.verse)]
        except ValueError:
            print(f"✗ Error: Invalid verse number: {args.verse}")
            sys.exit(1)

    # Validate verse_id is not used with ranges
    if len(verse_numbers) > 1 and args.verse_id:
        print("✗ Error: Cannot use --verse-id with verse ranges")
        print("The verse ID is auto-detected for each verse in the range")
        sys.exit(1)

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
    if len(verse_numbers) == 1:
        print(f"Verse: {verse_numbers[0]}")
    else:
        print(f"Verses: {verse_numbers[0]}-{verse_numbers[-1]} ({len(verse_numbers)} verses)")
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

    # Track overall success across all verses
    overall_results = []

    # Process each verse in the range
    try:
        for idx, verse_num in enumerate(verse_numbers, 1):
            # Show progress for batch operations
            if len(verse_numbers) > 1:
                print(f"\n{'#'*60}")
                print(f"# Processing verse {idx}/{len(verse_numbers)}: Verse {verse_num}")
                print(f"{'#'*60}\n")

            # Determine verse ID (with smart inference)
            if args.verse_id:
                # User explicitly specified verse ID (only for single verse)
                verse_id = args.verse_id
            else:
                # Try to infer verse ID from existing files
                inferred = infer_verse_id(args.collection, verse_num)
                if inferred is None:
                    # Inference failed (multiple matches found)
                    print(f"⚠ Skipping verse {verse_num} (ambiguous verse ID)")
                    overall_results.append({
                        'verse': verse_num,
                        'success': False,
                        'reason': 'Ambiguous verse ID'
                    })
                    continue
                verse_id = inferred

                # Show inference result if it's not the default
                if len(verse_numbers) == 1 and verse_id != f"verse_{verse_num:02d}":
                    print(f"\n✓ Auto-detected verse ID: {verse_id}")
                    print(f"  (To override, use --verse-id)\n")

            # Track success for this verse
            results = {
                'verse': verse_num,
                'verse_id': verse_id,
                'verse_file_created': None,
                'regenerate_content': None,
                'image': None,
                'audio': None,
                'embeddings': None
            }

            # Check if verse file exists, create if needed
            verse_file = Path.cwd() / "_verses" / args.collection / f"{verse_id}.md"
            verse_file_existed = verse_file.exists()

            # Step 0: Create verse file if it doesn't exist (required for audio generation)
            if not verse_file_existed:
                print(f"\n{'='*60}")
                print("CREATING VERSE FILE")
                print(f"{'='*60}\n")
                print(f"  → Verse file not found, creating from canonical source...")

                from verse_sdk.fetch.fetch_verse_text import fetch_from_local_file

                canonical_data = fetch_from_local_file(args.collection, verse_id)
                if not canonical_data or not canonical_data.get('devanagari'):
                    print(f"  ✗ Error: No canonical Devanagari text found for {verse_id}", file=sys.stderr)
                    print(f"  Please create data/verses/{args.collection}.yaml with canonical text", file=sys.stderr)
                    results['verse_file_created'] = False
                else:
                    # Generate content from canonical text
                    generated_content = generate_verse_content(
                        canonical_data['devanagari'],
                        args.collection,
                        verse_id
                    )

                    # Create verse markdown file
                    results['verse_file_created'] = create_verse_file_with_content(
                        verse_file,
                        generated_content,
                        args.collection,
                        verse_num,
                        verse_id
                    )

                    if results['verse_file_created']:
                        print(f"  ✓ Verse file created successfully")
                    else:
                        print(f"  ✗ Failed to create verse file")

            # Generate content in order: regenerate content → image → audio → embeddings
            # Step 1: Regenerate AI content (optional, only for existing files)
            if regenerate_content_flag and verse_file_existed:
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
                        args.collection,
                        verse_id
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
                    # Try to get title from verse file
                    verse_file = Path.cwd() / "_verses" / args.collection / f"{verse_id}.md"
                    title_en = None
                    if verse_file.exists():
                        try:
                            with open(verse_file, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            if file_content.startswith('---'):
                                parts = file_content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter = yaml.safe_load(parts[1])
                                    title_en = frontmatter.get('title_en')
                        except Exception:
                            pass  # If we can't read title, continue without it

                    # Ensure scene description exists (creates file/adds description if needed)
                    scene_ready = ensure_scene_description_exists(
                        args.collection,
                        verse_num,
                        verse_id,
                        canonical_data['devanagari'],
                        title_en
                    )

                    if scene_ready:
                        results['image'] = generate_image(args.collection, verse_num, args.theme, verse_id)
                    else:
                        print(f"  ✗ Failed to prepare scene description", file=sys.stderr)
                        results['image'] = False

            # Step 3: Generate audio
            if generate_audio_flag:
                results['audio'] = generate_audio(args.collection, verse_num, verse_id)

            # Step 4: Update embeddings (only once at the end for batch)
            if update_embeddings_flag:
                # For batch operations, only update embeddings after all verses
                if len(verse_numbers) == 1 or idx == len(verse_numbers):
                    results['embeddings'] = update_embeddings(args.collection)
                else:
                    results['embeddings'] = None  # Will update at the end

            # Store results for this verse
            overall_results.append(results)

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

    if len(overall_results) == 1:
        # Single verse summary
        results = overall_results[0]

        if results['verse_file_created'] is not None:
            status = "✓" if results['verse_file_created'] else "✗"
            print(f"{status} Verse file creation: {'Success' if results['verse_file_created'] else 'Failed'}")

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
        all_results = [r for r in results.values() if r is not None and r != results['verse'] and r != results['verse_id']]
        if all_results and all(all_results):
            print("✓ All tasks completed successfully!")
            sys.exit(0)
        elif any(all_results):
            print("⚠ Some tasks completed with errors")
            sys.exit(1)
        else:
            print("✗ All tasks failed")
            sys.exit(1)
    else:
        # Batch summary
        print(f"Total verses processed: {len(overall_results)}")
        print()

        success_count = 0
        failed_verses = []

        for result in overall_results:
            if 'reason' in result:
                # Skipped verse
                failed_verses.append(f"  Verse {result['verse']}: {result['reason']}")
                continue

            # Check if all operations succeeded
            ops = []
            if result['verse_file_created'] is not None:
                ops.append(result['verse_file_created'])
            if regenerate_content_flag and result['regenerate_content'] is not None:
                ops.append(result['regenerate_content'])
            if generate_image_flag and result['image'] is not None:
                ops.append(result['image'])
            if generate_audio_flag and result['audio'] is not None:
                ops.append(result['audio'])

            if ops and all(ops):
                success_count += 1
            else:
                failed_ops = []
                if result['verse_file_created'] is False:
                    failed_ops.append("verse file")
                if regenerate_content_flag and not result['regenerate_content']:
                    failed_ops.append("content")
                if generate_image_flag and not result['image']:
                    failed_ops.append("image")
                if generate_audio_flag and not result['audio']:
                    failed_ops.append("audio")

                failed_verses.append(f"  Verse {result['verse']}: {', '.join(failed_ops)}")

        print(f"✓ Successful: {success_count}/{len(overall_results)}")

        if failed_verses:
            print(f"✗ Failed: {len(failed_verses)}/{len(overall_results)}")
            for fv in failed_verses:
                print(fv)

        if update_embeddings_flag:
            # Report embeddings update (done once at the end)
            last_result = overall_results[-1]
            if last_result.get('embeddings'):
                print("\n✓ Embeddings updated for collection")
            else:
                print("\n✗ Embeddings update failed")

        print()

        if success_count == len(overall_results):
            print("✓ All verses completed successfully!")
            sys.exit(0)
        elif success_count > 0:
            print("⚠ Some verses completed with errors")
            sys.exit(1)
        else:
            print("✗ All verses failed")
            sys.exit(1)


if __name__ == '__main__':
    main()
