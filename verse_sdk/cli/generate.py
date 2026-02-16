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
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

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

try:
    from PIL import Image
except ImportError:
    # PIL is optional - only needed for image verification
    Image = None

# Load environment variables
load_dotenv()

# Global flag for debug mode
DEBUG_MODE = False


# ==================== Custom Exception Classes ====================

class UserFriendlyError(Exception):
    """Custom exception with user-friendly error messages and fix instructions."""

    def __init__(self, message: str, fix_instructions: List[str] = None):
        self.message = message
        self.fix_instructions = fix_instructions or []
        super().__init__(self.message)

    def display(self):
        """Display the error with formatting."""
        print(f"\n✗ Error: {self.message}\n", file=sys.stderr)
        if self.fix_instructions:
            print("How to fix:", file=sys.stderr)
            for i, instruction in enumerate(self.fix_instructions, 1):
                print(f"  {i}. {instruction}", file=sys.stderr)
            print()


# ==================== Cost Tracking ====================

class CostTracker:
    """Track API costs throughout generation."""

    # Pricing (as of 2024)
    GPT4_INPUT_COST = 0.03 / 1000  # $0.03 per 1K tokens
    GPT4_OUTPUT_COST = 0.06 / 1000  # $0.06 per 1K tokens
    DALLE3_STANDARD_COST = 0.040  # $0.040 per image (1024x1024)
    DALLE3_HD_COST = 0.080  # $0.080 per image (1024x1024 HD)
    ELEVENLABS_COST = 0.30 / 1000  # ~$0.30 per 1K characters
    EMBEDDING_COST = 0.0001 / 1000  # $0.0001 per 1K tokens

    def __init__(self):
        self.costs = {
            'content_generation': 0.0,
            'scene_generation': 0.0,
            'image_generation': 0.0,
            'audio_generation': 0.0,
            'embeddings': 0.0
        }

    def track_gpt4(self, category: str, input_tokens: int, output_tokens: int):
        """Track GPT-4 API cost."""
        cost = (input_tokens * self.GPT4_INPUT_COST) + (output_tokens * self.GPT4_OUTPUT_COST)
        self.costs[category] += cost
        return cost

    def track_dalle3(self, hd: bool = False):
        """Track DALL-E 3 image cost."""
        cost = self.DALLE3_HD_COST if hd else self.DALLE3_STANDARD_COST
        self.costs['image_generation'] += cost
        return cost

    def track_elevenlabs(self, character_count: int):
        """Track ElevenLabs audio cost."""
        cost = character_count * self.ELEVENLABS_COST
        self.costs['audio_generation'] += cost
        return cost

    def track_embeddings(self, token_count: int):
        """Track embedding generation cost."""
        cost = token_count * self.EMBEDDING_COST
        self.costs['embeddings'] += cost
        return cost

    def get_total(self) -> float:
        """Get total cost across all categories."""
        return sum(self.costs.values())

    def format_cost(self, cost: float) -> str:
        """Format cost for display."""
        if cost < 0.01:
            return f"${cost:.4f}"
        return f"${cost:.2f}"


# ==================== File Verification ====================

def verify_image_file(image_path: Path) -> Tuple[bool, str, int]:
    """
    Verify that an image file exists and is valid.

    Returns:
        (is_valid, message, file_size)
    """
    if not image_path.exists():
        return False, "File not found", 0

    file_size = image_path.stat().st_size

    if file_size == 0:
        return False, "File is empty", 0

    if file_size < 1000:  # Less than 1KB is suspicious
        return False, f"File is too small ({file_size} bytes)", file_size

    # Try to open with PIL if available
    if Image:
        try:
            with Image.open(image_path) as img:
                # Verify it can be loaded
                img.verify()
            return True, "Valid image", file_size
        except Exception as e:
            return False, f"Invalid image format: {str(e)}", file_size
    else:
        # Without PIL, just check extension and size
        if image_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            return True, "Image exists (format not verified)", file_size
        return False, "Unknown image format", file_size


def verify_audio_files(collection: str, verse_id: str) -> Tuple[bool, str, List[Tuple[Path, int]]]:
    """
    Verify that audio files exist and are valid.

    Returns:
        (is_valid, message, [(file_path, file_size), ...])
    """
    audio_dir = Path.cwd() / "public" / "audio" / collection
    audio_files = []

    # Check for both normal and slow versions
    normal_file = audio_dir / f"{verse_id}.mp3"
    slow_file = audio_dir / f"{verse_id}-slow.mp3"

    all_valid = True
    messages = []

    for audio_file, label in [(normal_file, "normal"), (slow_file, "slow")]:
        if not audio_file.exists():
            all_valid = False
            messages.append(f"{label} version not found")
            continue

        file_size = audio_file.stat().st_size

        if file_size == 0:
            all_valid = False
            messages.append(f"{label} version is empty")
        elif file_size < 1000:  # Less than 1KB is suspicious
            all_valid = False
            messages.append(f"{label} version too small ({file_size} bytes)")
        else:
            audio_files.append((audio_file, file_size))

    if all_valid:
        return True, "All audio files valid", audio_files
    else:
        return False, "; ".join(messages), audio_files


def verify_verse_file(verse_file: Path) -> Tuple[bool, str, int]:
    """
    Verify that a verse markdown file exists and has required frontmatter.

    Returns:
        (is_valid, message, file_size)
    """
    if not verse_file.exists():
        return False, "File not found", 0

    file_size = verse_file.stat().st_size

    if file_size == 0:
        return False, "File is empty", 0

    try:
        with open(verse_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith('---'):
            return False, "Missing frontmatter", file_size

        parts = content.split('---', 2)
        if len(parts) < 3:
            return False, "Invalid frontmatter format", file_size

        # Parse frontmatter
        frontmatter = yaml.safe_load(parts[1])

        # Check required fields
        required_fields = ['verse_id', 'devanagari']
        missing_fields = [f for f in required_fields if f not in frontmatter]

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", file_size

        return True, "Valid verse file", file_size

    except Exception as e:
        return False, f"Error reading file: {str(e)}", file_size


def format_file_size(size_bytes: int) -> str:
    """Format file size for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def generate_verse_content(devanagari_text: str, collection: str, verse_id: str = None,
                          dry_run: bool = False, cost_tracker: CostTracker = None) -> Tuple[dict, float]:
    """
    Generate AI content (transliteration, meaning, translation, story) from Devanagari text.

    Args:
        devanagari_text: The canonical Devanagari verse text
        collection: Collection key for context
        verse_id: Verse identifier (e.g., chaupai_02, shloka_01)
        dry_run: If True, skip API call and return mock data
        cost_tracker: CostTracker instance to record API costs

    Returns:
        Tuple of (content_dict, cost)
    """
    if dry_run:
        print(f"  → [DRY-RUN] Would generate AI content from canonical text...", file=sys.stderr)
        mock_result = {
            "devanagari": devanagari_text,
            "transliteration": "[mock transliteration]",
            "title_en": "[Mock Title]",
            "title_hi": "[नकली शीर्षक]",
            "phonetic_notes": [],
            "word_meanings": [],
            "meaning": "[mock word-by-word meaning]",
            "literal_translation": {"en": "[mock literal translation]", "hi": "[नकली शाब्दिक अनुवाद]"},
            "interpretive_meaning": {"en": "[mock interpretive meaning]", "hi": "[नकली व्याख्यात्मक अर्थ]"},
            "story": {"en": "[mock story]", "hi": "[नकली कथा]"},
            "practical_application": {
                "teaching": {"en": "[mock teaching]", "hi": "[नकली शिक्षा]"},
                "when_to_use": {"en": "[mock when to use]", "hi": "[नकली उपयोग]"}
            },
            "translation": {"en": "[mock translation]"}
        }
        return mock_result, 0.0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise UserFriendlyError(
            "OPENAI_API_KEY environment variable not set",
            [
                "Set the OPENAI_API_KEY environment variable with your OpenAI API key",
                "Get an API key from: https://platform.openai.com/api-keys",
                "Add to your .env file: OPENAI_API_KEY=sk-..."
            ]
        )

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

        # Track cost
        cost = 0.0
        if cost_tracker and hasattr(response, 'usage'):
            cost = cost_tracker.track_gpt4(
                'content_generation',
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )

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
        return result, cost

    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        raise UserFriendlyError(
            f"Failed to generate verse content: {str(e)}",
            [
                "Check your OPENAI_API_KEY is valid and has available credits",
                "Verify the Devanagari text is properly formatted",
                "Try again in a few moments if this is a temporary API issue",
                "Use --debug flag to see full error details"
            ]
        )


def create_verse_file_with_content(verse_file: Path, content: dict, collection: str, verse_num: int, verse_id: str = None, project_dir: Path = None) -> bool:
    """
    Create a new verse markdown file with generated content in complete chaupai format.

    Args:
        verse_file: Path to the verse markdown file to create
        content: Dictionary with generated content fields
        collection: Collection key
        verse_num: Verse number (for display, not navigation)
        verse_id: Verse identifier (e.g., chaupai-02, shloka-01)
        project_dir: Project directory (for reading sequence)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        verse_file.parent.mkdir(parents=True, exist_ok=True)

        # Extract verse_id from filename if not provided
        if not verse_id:
            verse_id = verse_file.stem  # e.g., chaupai-02 from chaupai-02.md

        # Determine verse type and extract number from ID
        verse_type = verse_id.split('-')[0] if '-' in verse_id else 'verse'  # chaupai, shloka, doha, etc.
        id_number = extract_verse_number_from_id(verse_id) or verse_num

        # Get navigation from sequence
        if project_dir is None:
            project_dir = verse_file.parent.parent.parent  # Go up from _verses/collection/file.md
        prev_id, next_id = get_navigation_from_sequence(collection, verse_id, project_dir)

        # Build complete frontmatter (chaupai format)
        frontmatter = {
            'layout': 'verse',
            'collection_key': collection,
            'permalink': f'/{collection}/{verse_id}/',
            'title_en': content.get('title_en', f'{verse_type.title()} {id_number}'),
            'title_hi': content.get('title_hi', f'{verse_type} {id_number}'),
            'verse_number': verse_num,
            'verse_type': verse_type,
            'previous_verse': f'/{collection}/{prev_id}/' if prev_id else None,
            'next_verse': f'/{collection}/{next_id}/' if next_id else None,
            'image': f'/images/{collection}/modern-minimalist/{verse_id}.png',
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


def update_previous_verse_navigation(collection: str, current_verse_id: str, project_dir: Path = Path.cwd()) -> bool:
    """
    Update the previous verse's next_verse field to point to the current verse.

    Args:
        collection: Collection key
        current_verse_id: Current verse ID
        project_dir: Project directory

    Returns:
        True if successful or not needed, False if failed
    """
    # Get previous verse ID from sequence
    prev_id, _ = get_navigation_from_sequence(collection, current_verse_id, project_dir)
    if not prev_id:
        # No previous verse, nothing to update
        return True

    # Find the previous verse file
    verses_dir = project_dir / "_verses" / collection
    prev_verse_file = verses_dir / f"{prev_id}.md"

    if not prev_verse_file.exists():
        # Previous verse file doesn't exist yet, skip
        return True

    try:
        # Read the previous verse file
        with open(prev_verse_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return True

        parts = content.split('---', 2)
        if len(parts) < 3:
            return True

        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2]

        # Update next_verse to point to current verse
        frontmatter['next_verse'] = f'/{collection}/{current_verse_id}/'

        # Write back
        frontmatter_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
        updated_content = f"---\n{frontmatter_str}---{body}"

        with open(prev_verse_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  ✓ Updated previous verse ({prev_id}) navigation")
        return True

    except Exception as e:
        print(f"  ⚠ Warning: Could not update previous verse navigation: {e}", file=sys.stderr)
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
        verse_id = verse_file.stem  # e.g., shloka-02
        verse_type = verse_id.split('-')[0] if '-' in verse_id else 'verse'
        id_number = extract_verse_number_from_id(verse_id) or verse_num

        # Get navigation from sequence
        project_dir = verse_file.parent.parent.parent  # Go up from _verses/collection/file.md
        prev_id, next_id = get_navigation_from_sequence(collection, verse_id, project_dir)

        # Update frontmatter with ALL generated content (complete chaupai format)
        # Preserve existing metadata fields but add/update with new structure
        frontmatter.update({
            'layout': frontmatter.get('layout', 'verse'),
            'collection_key': collection,  # Use collection_key, not just collection
            'permalink': frontmatter.get('permalink', f'/{collection}/{verse_id}/'),
            'title_en': content.get('title_en', frontmatter.get('title_en', f'{verse_type.title()} {id_number}')),
            'title_hi': content.get('title_hi', frontmatter.get('title_hi', f'{verse_type} {id_number}')),
            'verse_number': verse_num,
            'verse_type': verse_type,
            'previous_verse': f'/{collection}/{prev_id}/' if prev_id else None,
            'next_verse': f'/{collection}/{next_id}/' if next_id else None,
            'image': frontmatter.get('image', f'/images/{collection}/modern-minimalist/{verse_id}.png'),
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


def get_verse_sequence(collection: str, project_dir: Path = Path.cwd()) -> Optional[list]:
    """
    Read the verse sequence from the data file's _meta.sequence list.

    Args:
        collection: Collection key (e.g., "sundar-kaand")
        project_dir: Project directory (defaults to current working directory)

    Returns:
        List of verse IDs in sequence order, or None if not found
    """
    # Look for data file - try .yaml first, then .yml
    data_file = project_dir / "data" / "verses" / f"{collection}.yaml"
    if not data_file.exists():
        data_file = project_dir / "data" / "verses" / f"{collection}.yml"

    if not data_file.exists():
        return None

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Check for _meta.sequence
        if '_meta' in data and isinstance(data['_meta'], dict):
            sequence = data['_meta'].get('sequence')
            if sequence and isinstance(sequence, list):
                return sequence

        return None

    except Exception as e:
        print(f"Warning: Error reading sequence from {data_file}: {e}", file=sys.stderr)
        return None


def extract_verse_number_from_id(verse_id: str) -> Optional[int]:
    """
    Extract the number from a verse ID.

    Args:
        verse_id: Verse ID like "chaupai-16", "doha-03", "shloka-01"

    Returns:
        The number from the ID, or None if not found
    """
    match = re.search(r'[-_](\d+)$', verse_id)
    if match:
        return int(match.group(1))
    return None


def get_navigation_from_sequence(collection: str, verse_id: str, project_dir: Path = Path.cwd()) -> tuple[Optional[str], Optional[str]]:
    """
    Get previous and next verse IDs from the sequence.

    Args:
        collection: Collection key
        verse_id: Current verse ID
        project_dir: Project directory

    Returns:
        Tuple of (previous_verse_id, next_verse_id), None if not found
    """
    sequence = get_verse_sequence(collection, project_dir)
    if not sequence:
        return None, None

    try:
        idx = sequence.index(verse_id)
        prev_id = sequence[idx - 1] if idx > 0 else None
        next_id = sequence[idx + 1] if idx < len(sequence) - 1 else None
        return prev_id, next_id
    except ValueError:
        # verse_id not in sequence
        return None, None


def validate_generation_requirements(
    collection: str,
    verse_id: str,
    generate_image: bool,
    generate_audio: bool,
    regenerate_content: bool,
    update_embeddings: bool,
    project_dir: Path = Path.cwd()
) -> tuple[bool, list[str]]:
    """
    Validate all requirements before starting generation.

    Args:
        collection: Collection key
        verse_id: Verse ID to generate
        generate_image: Whether image generation is requested
        generate_audio: Whether audio generation is requested
        regenerate_content: Whether content regeneration is requested
        update_embeddings: Whether embeddings update is requested
        project_dir: Project directory

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # 1. Check collection exists
    collections_file = project_dir / "data" / "collections.yaml"
    if not collections_file.exists():
        collections_file = project_dir / "data" / "collections.yml"

    if collections_file.exists():
        try:
            with open(collections_file, 'r', encoding='utf-8') as f:
                collections_data = yaml.safe_load(f)
            if collections_data and collection not in collections_data.get('collections', {}):
                errors.append(f"Collection '{collection}' not found in collections.yaml")
        except Exception as e:
            errors.append(f"Error reading collections.yaml: {e}")
    else:
        errors.append("collections.yaml not found in data/ directory")

    # 2. Check verse exists in data file
    data_file = project_dir / "data" / "verses" / f"{collection}.yaml"
    if not data_file.exists():
        data_file = project_dir / "data" / "verses" / f"{collection}.yml"

    verse_in_data = False
    if data_file.exists():
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                verses_data = yaml.safe_load(f)
            if verses_data and verse_id in verses_data:
                verse_data = verses_data[verse_id]
                if isinstance(verse_data, dict) and 'devanagari' in verse_data:
                    verse_in_data = True
                elif isinstance(verse_data, str):
                    verse_in_data = True
                else:
                    errors.append(f"Verse '{verse_id}' exists but missing 'devanagari' field")
            else:
                errors.append(f"Verse '{verse_id}' not found in {data_file.name}")
        except Exception as e:
            errors.append(f"Error reading {data_file.name}: {e}")
    else:
        errors.append(f"Data file not found: data/verses/{collection}.yaml")

    # 3. Check API keys
    if generate_image or regenerate_content or update_embeddings:
        if not os.getenv("OPENAI_API_KEY"):
            errors.append("OPENAI_API_KEY not set (required for image/content/embeddings)")

    if generate_audio:
        if not os.getenv("ELEVENLABS_API_KEY"):
            errors.append("ELEVENLABS_API_KEY not set (required for audio)")

    # 4. Check scene description exists (warning only, not fatal)
    if generate_image and verse_in_data:
        if not validate_scene_description_exists(collection, verse_id, project_dir):
            # This is just a warning - we can generate it
            print(f"  ⚠ Warning: Scene description not found for {verse_id} (will be generated)")

    # 5. Check verses directory exists
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        try:
            verses_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create verses directory: {e}")

    return len(errors) == 0, errors


def find_next_verse(collection: str, project_dir: Path = Path.cwd()) -> Optional[int]:
    """
    Find the next verse position to generate.

    If a data file with sequence exists, uses the sequence to find the next position.
    Otherwise, falls back to scanning existing verse files.

    Returns:
        Next verse position (1-based) to generate, or 1 if no verses exist
    """
    # Try to use sequence from data file
    sequence = get_verse_sequence(collection, project_dir)
    if sequence:
        # Find which verses in the sequence already have files
        verses_dir = project_dir / "_verses" / collection
        if not verses_dir.exists():
            return 1  # Start from position 1

        # Check each position in the sequence
        for position, verse_id in enumerate(sequence, start=1):
            # Check if file exists for this verse_id
            verse_file = verses_dir / f"{verse_id}.md"
            if not verse_file.exists():
                # Found first missing verse
                return position

        # All verses in sequence exist
        return len(sequence) + 1

    # Fallback: scan existing files (old behavior)
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        return 1

    verse_files = list(verses_dir.glob("*.md"))
    if not verse_files:
        return 1

    # Extract verse numbers from filenames
    verse_numbers = []
    for verse_file in verse_files:
        match = re.search(r'[-_](\d+)\.md$', verse_file.name)
        if match:
            verse_numbers.append(int(match.group(1)))

    if not verse_numbers:
        return 1

    return max(verse_numbers) + 1


def infer_verse_id(collection: str, verse_position: int, project_dir: Path = Path.cwd()) -> Optional[str]:
    """
    Infer verse ID from verse position.

    If a data file with sequence exists, maps position to verse_id from the sequence.
    Otherwise, falls back to scanning existing verse files.

    Args:
        collection: Collection key
        verse_position: Position in the sequence (1-based index)
        project_dir: Project directory

    Returns:
        - The verse_id at the given position
        - None if position is invalid or data is missing
    """
    # Try to use sequence from data file
    sequence = get_verse_sequence(collection, project_dir)
    if sequence:
        # Map position to verse_id
        if verse_position < 1 or verse_position > len(sequence):
            print(f"\n✗ Error: Verse position {verse_position} is out of range", file=sys.stderr)
            print(f"  The sequence in data/verses/{collection}.yaml has {len(sequence)} verses", file=sys.stderr)
            print(f"  Valid positions: 1-{len(sequence)}", file=sys.stderr)
            return None

        # Get verse_id from sequence (1-based position)
        verse_id = sequence[verse_position - 1]
        return verse_id

    # Fallback: scan existing files (old behavior)
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        return None

    # Look for files matching the verse number
    # Patterns: chaupai_05.md, doha_05.md, verse_05.md, verse-05.md, etc.
    patterns = [
        f"*_{verse_position:02d}.md",  # chaupai_05.md, doha_05.md
        f"*{verse_position:02d}.md",   # verse05.md (no separator)
        f"*-{verse_position:02d}.md",  # verse-05.md (dash separator)
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
        print(f"\n⚠ Multiple verse files found for verse {verse_position}:")
        for match in matches:
            print(f"  - {match.name}")
        print(f"\nPlease specify which one using --verse-id")
        return None
    else:
        # No matches - this is a new verse, use default pattern
        return f"verse-{verse_position:02d}"


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


def validate_scene_description_exists(collection: str, verse_id: str, project_dir: Path = Path.cwd()) -> bool:
    """
    Check if a scene description already exists for the verse.

    Args:
        collection: Collection key
        verse_id: Verse identifier
        project_dir: Project directory

    Returns:
        True if scene description exists, False otherwise
    """
    prompts_dir = project_dir / "docs" / "image-prompts"
    prompts_file = prompts_dir / f"{collection}.md"

    if not prompts_file.exists():
        return False

    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if verse_id appears in a header (matches the pattern we use)
        import re
        # Match headers with verse_id in parentheses
        verse_id_pattern = rf'###[^\n]*\({re.escape(verse_id)}\)[^\n]*\n'
        if re.search(verse_id_pattern, content, re.DOTALL):
            return True

        return False

    except Exception:
        return False


def ensure_scene_description_exists(collection: str, verse_position: int, verse_id: str, devanagari_text: str, title_en: str = None) -> bool:
    """
    Ensure scene description exists for the verse. Creates file and/or adds scene if missing.

    Args:
        collection: Collection key
        verse_position: Verse position in sequence (for ordering, not used in scene header)
        verse_id: Verse identifier (e.g., chaupai-05)
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

    # Extract verse type and number from verse_id (e.g., "chaupai" and 5 from "chaupai-05")
    verse_type = verse_id.split('-')[0] if '-' in verse_id else 'verse'
    verse_type_title = verse_type.title()  # Capitalize: Chaupai, Shloka, Doha, etc.
    verse_number = extract_verse_number_from_id(verse_id) or verse_position  # Extract from ID, fallback to position

    # Generate new scene description
    print(f"  → Generating scene description for {verse_type_title} {verse_number}...")
    scene_description = generate_scene_description(devanagari_text, verse_id, collection)

    if not scene_description:
        print(f"  ✗ Failed to generate scene description")
        return False

    # Build header: "### Chaupai 5 (chaupai-05): Title" or "### Chaupai 5 (chaupai-05)" if no title
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
    # First try to match by verse_id in parentheses (most specific)
    # Support both dash and underscore formats for backward compatibility
    verse_id_dash = re.escape(verse_id)
    verse_id_underscore = re.escape(verse_id.replace('-', '_'))
    verse_id_pattern = rf'###[^\n]*\((?:{verse_id_dash}|{verse_id_underscore})\)[^\n]*\n.*?(?=\n---\s*\n|\Z)'
    # Fallback: match by verse number (for entries without verse_id)
    verse_number_pattern = rf'### (?:Verse {verse_number}|{verse_type_title} {verse_number})(?![^\n]*\()\s*[^\n]*\n.*?(?=\n---\s*\n|\Z)'

    # Try verse_id match first (catches duplicates with any verse number)
    verse_pattern = verse_id_pattern if re.search(verse_id_pattern, content, re.DOTALL) else verse_number_pattern

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

    # Use provided verse_id or default to verse-{N:02d}
    if not verse_id:
        verse_id = f"verse-{verse:02d}"

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

    # Use provided verse_id or default to verse-{N:02d}
    if not verse_id:
        verse_id = f"verse-{verse:02d}"

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

  # Auto-generate next verse after the last generated verse
  verse-generate --collection sundar-kaand --next --all

  # Regenerate AI content only (no multimedia)
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content

  # Regenerate content AND multimedia
  verse-generate --collection sundar-kaand --verse 3 --regenerate-content --all

  # Override auto-detected verse ID (only needed when not using sequence)
  verse-generate --collection sundar-kaand --verse 5 --verse-id chaupai-05

  # List available collections
  verse-generate --list-collections

Note:
  - The --verse flag refers to POSITION in the sequence (from data/verses/{collection}.yaml)
  - Position 1 = first verse in sequence, position 15 = 15th verse in sequence, etc.
  - If data file has sequence, verse ID is mapped from sequence (e.g., position 15 → chaupai-11)
  - If no sequence exists, falls back to old behavior (scanning existing files)
  - Use --next to auto-generate the next verse in the sequence
  - Complete workflow by default: generates image + audio, updates embeddings
  - Use --regenerate-content ALONE to only regenerate text (no multimedia)
  - Use --regenerate-content --all to regenerate text AND multimedia
  - Use --no-update-embeddings to skip embeddings (faster generation)
  - Theme defaults to "modern-minimalist" (use --theme to change)

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
        help="Verse position in sequence or range (e.g., 5, 1-10, 5-20). Position is mapped to verse ID from data/verses/{collection}.yaml sequence.",
        metavar="N or M-N"
    )
    parser.add_argument(
        "--next",
        action="store_true",
        help="Auto-detect and generate the next verse after the last generated verse"
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
        help="Override verse identifier (e.g., chaupai-05, doha-01). If not specified, auto-detects from existing files or defaults to verse-{N:02d}",
        metavar="ID"
    )

    # Dry-run mode
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be generated without actually creating files or making API calls"
    )

    # Debug mode
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full error tracebacks and debug information"
    )

    args = parser.parse_args()

    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.debug

    # Handle list collections
    if args.list_collections:
        list_collections()
        sys.exit(0)

    # Validate required arguments
    if not args.collection:
        parser.error("--collection is required")

    # Either --verse or --next must be specified (but not both)
    if args.next and args.verse:
        parser.error("--next and --verse are mutually exclusive")
    if not args.verse and not args.next:
        parser.error("Either --verse or --next is required")

    # Default to --all if no generation flags specified
    # BUT: if only --regenerate-content is specified, don't generate multimedia
    if not any([args.all, args.image, args.audio, args.regenerate_content]):
        args.all = True

    # Validate collection
    if not validate_collection(args.collection):
        sys.exit(1)

    # Handle --next by finding the next verse to generate
    if args.next:
        next_verse = find_next_verse(args.collection)
        if next_verse is None:
            print(f"✗ Error: Could not determine next verse for collection '{args.collection}'")
            sys.exit(1)
        args.verse = str(next_verse)
        print(f"✓ Auto-detected next verse: {next_verse}")

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
            print(f"✗ Error: Invalid verse position: {args.verse}")
            print(f"")
            print(f"The --verse flag expects a POSITION NUMBER (e.g., 15), not a verse ID.")
            print(f"Position refers to the verse's location in the sequence (1st, 2nd, 3rd, etc.)")
            print(f"")
            print(f"Examples:")
            print(f"  verse-generate --collection {args.collection} --verse 15    # Generate 15th verse in sequence")
            print(f"  verse-generate --collection {args.collection} --verse 1     # Generate 1st verse in sequence")
            print(f"  verse-generate --collection {args.collection} --next        # Auto-generate next verse")
            print(f"")
            print(f"If you need to specify a verse ID directly, use --verse-id:")
            print(f"  verse-generate --collection {args.collection} --verse-id {args.verse}")
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
        print(f"Position: {verse_numbers[0]}")
    else:
        print(f"Positions: {verse_numbers[0]}-{verse_numbers[-1]} ({len(verse_numbers)} verses)")
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

    if args.dry_run:
        print("\n⚠ DRY-RUN MODE: No files will be created or API calls made")

    print()

    # Pre-generation validation for all verses
    print("="*60)
    print("PRE-GENERATION VALIDATION")
    print("="*60)
    print()

    validation_failed = False
    for idx, verse_position in enumerate(verse_numbers, 1):
        # Determine verse ID first
        if args.verse_id:
            verse_id = args.verse_id
        else:
            verse_id = infer_verse_id(args.collection, verse_position)
            if verse_id is None:
                print(f"✗ Position {verse_position}: Cannot determine verse ID")
                validation_failed = True
                continue

        print(f"Validating position {verse_position} ({verse_id})...")

        # Run comprehensive validation
        is_valid, errors = validate_generation_requirements(
            args.collection,
            verse_id,
            generate_image_flag,
            generate_audio_flag,
            regenerate_content_flag,
            update_embeddings_flag,
            Path.cwd()
        )

        if not is_valid:
            print(f"✗ Validation failed for {verse_id}:")
            for error in errors:
                print(f"  - {error}")
            validation_failed = True
        else:
            print(f"✓ Validation passed for {verse_id}")

    print()

    if validation_failed:
        print("="*60)
        print("✗ VALIDATION FAILED - Cannot proceed with generation")
        print("="*60)
        print("\nPlease fix the errors above and try again.")
        sys.exit(1)

    print("="*60)
    print("✓ ALL VALIDATIONS PASSED - Starting generation")
    print("="*60)
    print()

    # Track overall success across all verses
    overall_results = []

    # Initialize cost tracker
    cost_tracker = CostTracker()

    # Process each verse in the range
    try:
        for idx, verse_position in enumerate(verse_numbers, 1):
            # Show progress for batch operations
            if len(verse_numbers) > 1:
                print(f"\n{'#'*60}")
                print(f"# Processing verse {idx}/{len(verse_numbers)}: Position {verse_position}")
                print(f"{'#'*60}\n")

            # Determine verse ID (with smart inference)
            if args.verse_id:
                # User explicitly specified verse ID (only for single verse)
                verse_id = args.verse_id
            else:
                # Try to infer verse ID from position (using sequence or fallback)
                inferred = infer_verse_id(args.collection, verse_position)
                if inferred is None:
                    # Inference failed (out of range or ambiguous)
                    print(f"⚠ Skipping position {verse_position} (cannot determine verse ID)")
                    overall_results.append({
                        'position': verse_position,
                        'success': False,
                        'reason': 'Cannot determine verse ID'
                    })
                    continue
                verse_id = inferred

                # Show inference result
                if len(verse_numbers) == 1:
                    print(f"\n✓ Position {verse_position} → Verse ID: {verse_id}")
                    print(f"  (To override, use --verse-id)\n")

            # Track success for this verse
            results = {
                'position': verse_position,
                'verse_id': verse_id,
                'verse_file_created': None,
                'regenerate_content': None,
                'image': None,
                'audio': None,
                'embeddings': None,
                'content_cost': 0.0,
                'image_cost': 0.0,
                'audio_cost': 0.0,
                'embeddings_cost': 0.0,
                'verse_file_path': None,
                'verse_file_size': 0,
                'image_file_path': None,
                'image_file_size': 0,
                'audio_files': [],
                'prev_verse': None,
                'next_verse': None
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
                    generated_content, content_cost = generate_verse_content(
                        canonical_data['devanagari'],
                        args.collection,
                        verse_id,
                        dry_run=args.dry_run,
                        cost_tracker=cost_tracker
                    )
                    results['content_cost'] = content_cost

                    # Create verse markdown file
                    results['verse_file_created'] = create_verse_file_with_content(
                        verse_file,
                        generated_content,
                        args.collection,
                        verse_position,
                        verse_id,
                        Path.cwd()  # Pass current directory as project_dir
                    )

                    if results['verse_file_created']:
                        print(f"  ✓ Verse file created successfully")
                        # Update previous verse's next_verse field
                        update_previous_verse_navigation(args.collection, verse_id, Path.cwd())
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
                    generated_content, content_cost = generate_verse_content(
                        canonical_data['devanagari'],
                        args.collection,
                        verse_id,
                        dry_run=args.dry_run,
                        cost_tracker=cost_tracker
                    )
                    results['content_cost'] = content_cost

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

                    # Check if scene description already exists
                    scene_exists = validate_scene_description_exists(args.collection, verse_id, Path.cwd())

                    if scene_exists:
                        print(f"  ✓ Scene description already exists for {verse_id}")
                        scene_ready = True
                    else:
                        # Ensure scene description exists (creates file/adds description if needed)
                        print(f"  → Scene description not found, generating...")
                        scene_ready = ensure_scene_description_exists(
                            args.collection,
                            verse_position,
                            verse_id,
                            canonical_data['devanagari'],
                            title_en
                        )

                    if scene_ready:
                        results['image'] = generate_image(args.collection, verse_position, args.theme, verse_id)
                    else:
                        print(f"  ✗ Failed to prepare scene description", file=sys.stderr)
                        results['image'] = False

            # Step 3: Generate audio
            if generate_audio_flag:
                results['audio'] = generate_audio(args.collection, verse_position, verse_id)

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
    except UserFriendlyError as e:
        e.display()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}", file=sys.stderr)
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        else:
            print("Use --debug flag to see full error details", file=sys.stderr)
        sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}\n")

    if len(overall_results) == 1:
        # Single verse summary
        results = overall_results[0]

        # Operations status
        print("Operations:")
        if results['verse_file_created'] is not None:
            status = "✓" if results['verse_file_created'] else "✗"
            print(f"  {status} Verse file creation: {'Success' if results['verse_file_created'] else 'Failed'}")

        if regenerate_content_flag:
            status = "✓" if results['regenerate_content'] else "✗"
            cost_str = cost_tracker.format_cost(results.get('content_cost', 0))
            print(f"  {status} Regenerate content: {'Success' if results['regenerate_content'] else 'Failed'} ({cost_str})")

        if generate_image_flag:
            status = "✓" if results['image'] else "✗"
            cost_str = cost_tracker.format_cost(results.get('image_cost', 0))
            print(f"  {status} Image: {'Success' if results['image'] else 'Failed'} ({cost_str})")

        if generate_audio_flag:
            status = "✓" if results['audio'] else "✗"
            cost_str = cost_tracker.format_cost(results.get('audio_cost', 0))
            print(f"  {status} Audio: {'Success' if results['audio'] else 'Failed'} ({cost_str})")

        if update_embeddings_flag:
            status = "✓" if results['embeddings'] else "✗"
            cost_str = cost_tracker.format_cost(results.get('embeddings_cost', 0))
            print(f"  {status} Embeddings: {'Success' if results['embeddings'] else 'Failed'} ({cost_str})")

        # File paths and sizes
        print("\nGenerated Files:")
        if results.get('verse_file_path'):
            size_str = format_file_size(results.get('verse_file_size', 0))
            print(f"  📄 Verse: {results['verse_file_path']} ({size_str})")

        if results.get('image_file_path'):
            size_str = format_file_size(results.get('image_file_size', 0))
            print(f"  🖼️  Image: {results['image_file_path']} ({size_str})")

        if results.get('audio_files'):
            for audio_path, audio_size in results['audio_files']:
                size_str = format_file_size(audio_size)
                print(f"  🔊 Audio: {audio_path} ({size_str})")

        # Navigation
        if results.get('prev_verse') or results.get('next_verse'):
            print("\nNavigation:")
            if results.get('prev_verse'):
                print(f"  ← Previous: {results['prev_verse']}")
            if results.get('next_verse'):
                print(f"  → Next: {results['next_verse']}")

        # Total cost
        total_cost = cost_tracker.get_total()
        if total_cost > 0:
            print(f"\nTotal Cost: {cost_tracker.format_cost(total_cost)}")
            print("  Breakdown:")
            for category, cost in cost_tracker.costs.items():
                if cost > 0:
                    print(f"    - {category.replace('_', ' ').title()}: {cost_tracker.format_cost(cost)}")

        print()

        # Exit with appropriate code
        all_results = [r for r in results.values() if isinstance(r, bool)]
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
