#!/usr/bin/env python3
"""
Translate verse content into multiple languages.

This command translates verse content from canonical sources into target languages.
By default, translates short fields (translation, literal_translation, interpretive_meaning).
Use --all-fields to also translate long fields (story, practical_application).

Usage:
    # Translate to Hindi
    verse-translate --collection sundar-kaand --verse 5 --language hi

    # Translate to multiple languages
    verse-translate --collection sundar-kaand --verse 5 --language es --language fr

    # Translate all verses in collection
    verse-translate --collection sundar-kaand --all --language hi

    # Translate all fields including story
    verse-translate --collection sundar-kaand --verse 5 --language hi --all-fields

Requirements:
    - OPENAI_API_KEY environment variable (for translation)
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional

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

# Supported languages with their full names
SUPPORTED_LANGUAGES = {
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'pt': 'Portuguese',
    'it': 'Italian',
    'ru': 'Russian',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    'ne': 'Nepali',
}


def translate_text(text: str, target_language: str, field_name: str, devanagari: str = None) -> str:
    """
    Translate text to target language using GPT-4.

    Args:
        text: Text to translate (usually English)
        target_language: Target language code (e.g., 'hi', 'es')
        field_name: Name of the field being translated (for context)
        devanagari: Original Devanagari text (for reference)

    Returns:
        Translated text
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    language_name = SUPPORTED_LANGUAGES.get(target_language, target_language)

    # Build context-aware prompt
    context = f"You are translating a verse from the Ramcharitmanas (Sundar Kanda).\n"
    if devanagari:
        context += f"Original Devanagari: {devanagari}\n"
    context += f"Field being translated: {field_name}\n\n"

    prompt = f"""{context}Translate the following English text to {language_name}:

{text}

Provide ONLY the translation, no explanations or additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are an expert translator specializing in spiritual and religious texts. Translate accurately while preserving the sacred and devotional tone."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  ✗ Error translating: {e}", file=sys.stderr)
        return None


def parse_verse_file(verse_file: Path) -> tuple:
    """
    Parse verse markdown file and extract frontmatter and body.

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    if not verse_file.exists():
        return None, None

    try:
        with open(verse_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter between --- markers
        if not content.startswith('---'):
            return {}, content

        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2]

        return frontmatter, body

    except Exception as e:
        print(f"Error parsing {verse_file}: {e}", file=sys.stderr)
        return None, None


def update_verse_file(verse_file: Path, frontmatter: Dict, body: str) -> bool:
    """
    Update verse file with new frontmatter.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Build updated content
        updated_content = "---\n"
        updated_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False)
        updated_content += "---"
        updated_content += body

        # Write updated file
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return True

    except Exception as e:
        print(f"  ✗ Error updating verse file: {e}", file=sys.stderr)
        return False


def translate_verse(
    verse_file: Path,
    target_languages: List[str],
    all_fields: bool = False
) -> bool:
    """
    Translate verse content to target languages.

    Args:
        verse_file: Path to verse markdown file
        target_languages: List of language codes to translate to
        all_fields: If True, translate all fields including long ones

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Translating: {verse_file.name}")
    print(f"{'='*60}\n")

    # Parse verse file
    frontmatter, body = parse_verse_file(verse_file)
    if frontmatter is None:
        print(f"  ✗ Failed to parse verse file", file=sys.stderr)
        return False

    devanagari = frontmatter.get('devanagari', '')

    # Define fields to translate
    short_fields = ['translation', 'literal_translation', 'interpretive_meaning']

    # Handle nested fields for all_fields
    if all_fields:
        nested_fields = [
            ('story', None),
            ('practical_application', 'teaching'),
            ('practical_application', 'when_to_use'),
        ]
    else:
        nested_fields = []

    # Translate short fields
    for field in short_fields:
        if field not in frontmatter:
            continue

        if not isinstance(frontmatter[field], dict):
            print(f"  ⚠ Skipping {field}: not in dict format", file=sys.stderr)
            continue

        # Get English text (source)
        source_text = frontmatter[field].get('en')
        if not source_text:
            print(f"  ⚠ Skipping {field}: no English text found", file=sys.stderr)
            continue

        # Translate to each target language
        for lang in target_languages:
            if lang == 'en':
                continue  # Skip English

            # Skip if translation already exists
            if lang in frontmatter[field]:
                print(f"  ⊘ {field} ({lang}): Already exists, skipping")
                continue

            print(f"  → Translating {field} to {SUPPORTED_LANGUAGES.get(lang, lang)}...")

            translated = translate_text(source_text, lang, field, devanagari)
            if translated:
                frontmatter[field][lang] = translated
                print(f"  ✓ {field} ({lang}): Done")
            else:
                print(f"  ✗ {field} ({lang}): Failed", file=sys.stderr)

    # Translate nested fields (if --all-fields)
    for parent_field, child_field in nested_fields:
        if parent_field not in frontmatter:
            continue

        # Handle nested structure
        if child_field:
            if not isinstance(frontmatter[parent_field], dict):
                continue
            if child_field not in frontmatter[parent_field]:
                continue

            field_ref = frontmatter[parent_field][child_field]
            field_name = f"{parent_field}.{child_field}"
        else:
            field_ref = frontmatter[parent_field]
            field_name = parent_field

        if not isinstance(field_ref, dict):
            print(f"  ⚠ Skipping {field_name}: not in dict format", file=sys.stderr)
            continue

        # Get English text
        source_text = field_ref.get('en')
        if not source_text:
            print(f"  ⚠ Skipping {field_name}: no English text found", file=sys.stderr)
            continue

        # Translate to each target language
        for lang in target_languages:
            if lang == 'en':
                continue

            # Skip if translation already exists
            if lang in field_ref:
                print(f"  ⊘ {field_name} ({lang}): Already exists, skipping")
                continue

            print(f"  → Translating {field_name} to {SUPPORTED_LANGUAGES.get(lang, lang)}...")

            translated = translate_text(source_text, lang, field_name, devanagari)
            if translated:
                field_ref[lang] = translated
                print(f"  ✓ {field_name} ({lang}): Done")
            else:
                print(f"  ✗ {field_name} ({lang}): Failed", file=sys.stderr)

    # Update verse file
    print(f"\n  → Updating verse file...")
    if update_verse_file(verse_file, frontmatter, body):
        print(f"  ✓ Verse file updated successfully\n")
        return True
    else:
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Translate verse content into multiple languages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate to Hindi
  verse-translate --collection sundar-kaand --verse 5 --language hi

  # Translate to multiple languages
  verse-translate --collection sundar-kaand --verse 5 --language es --language fr

  # Translate all verses
  verse-translate --collection sundar-kaand --all --language hi

  # Translate all fields including long story
  verse-translate --collection sundar-kaand --verse 5 --language hi --all-fields

  # List supported languages
  verse-translate --list-languages

Note:
  - By default translates: translation, literal_translation, interpretive_meaning
  - Use --all-fields to also translate: story, practical_application
  - Skips translations that already exist
  - Requires OPENAI_API_KEY environment variable
        """
    )

    # List languages
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List supported languages and exit"
    )

    # Collection and verse identification
    parser.add_argument(
        "--collection",
        type=str,
        help="Collection key (e.g., sundar-kaand, hanuman-chalisa)",
        metavar="KEY"
    )
    parser.add_argument(
        "--verse",
        type=int,
        action='append',
        dest='verses',
        help="Verse number to translate (can be used multiple times)",
        metavar="N"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Translate all verses in collection"
    )

    # Translation options
    parser.add_argument(
        "--language",
        type=str,
        action='append',
        dest='languages',
        help="Target language code (e.g., hi, es, fr). Can be used multiple times",
        metavar="CODE"
    )
    parser.add_argument(
        "--all-fields",
        action="store_true",
        help="Translate all fields including story and practical_application (slower, more expensive)"
    )

    # Project directory
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    args = parser.parse_args()

    # Handle list languages
    if args.list_languages:
        print("\n" + "="*60)
        print("SUPPORTED LANGUAGES")
        print("="*60 + "\n")
        for code, name in sorted(SUPPORTED_LANGUAGES.items()):
            print(f"  {code:4s} - {name}")
        print()
        sys.exit(0)

    # Validate required arguments
    if not args.collection:
        parser.error("--collection is required")
    if not args.verses and not args.all:
        parser.error("Must specify --verse or --all")
    if not args.languages:
        parser.error("Must specify at least one --language")

    # Validate languages
    for lang in args.languages:
        if lang not in SUPPORTED_LANGUAGES and lang != 'en':
            print(f"⚠ Warning: '{lang}' is not in the supported languages list")
            print(f"Use --list-languages to see supported languages")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: OPENAI_API_KEY environment variable not set")
        print("Set it in .env file or environment")
        sys.exit(1)

    project_dir = args.project_dir
    verses_dir = project_dir / "_verses" / args.collection

    if not verses_dir.exists():
        print(f"✗ Error: Collection directory not found: {verses_dir}")
        sys.exit(1)

    # Display header
    print("\n" + "="*60)
    print("VERSE TRANSLATION")
    print("="*60)
    print(f"\nCollection: {args.collection}")
    print(f"Target languages: {', '.join([SUPPORTED_LANGUAGES.get(l, l) for l in args.languages])}")
    print(f"Fields: {'All fields' if args.all_fields else 'Short fields only (translation, literal_translation, interpretive_meaning)'}\n")

    # Determine which verses to translate
    if args.all:
        # Get all verse files
        verse_files = sorted(verses_dir.glob("*.md"))
        if not verse_files:
            print(f"✗ Error: No verse files found in {verses_dir}")
            sys.exit(1)
    else:
        # Specific verses
        verse_files = []
        for verse_num in args.verses:
            # Find verse file (handle different naming patterns)
            patterns = [
                f"*_{verse_num:02d}.md",
                f"*{verse_num:02d}.md",
                f"*-{verse_num:02d}.md",
            ]

            matches = []
            for pattern in patterns:
                matches.extend(verses_dir.glob(pattern))

            if not matches:
                print(f"⚠ Warning: No verse file found for verse {verse_num}")
                continue
            elif len(matches) > 1:
                print(f"⚠ Warning: Multiple verse files found for verse {verse_num}:")
                for m in matches:
                    print(f"  - {m.name}")
                print(f"Skipping verse {verse_num}")
                continue

            verse_files.append(matches[0])

    if not verse_files:
        print("✗ Error: No verse files to translate")
        sys.exit(1)

    # Translate each verse
    total = len(verse_files)
    success = 0
    failed = 0

    try:
        for verse_file in verse_files:
            if translate_verse(verse_file, args.languages, args.all_fields):
                success += 1
            else:
                failed += 1

    except KeyboardInterrupt:
        print("\n\n⚠ Translation interrupted by user")
        sys.exit(1)

    # Summary
    print("="*60)
    print("TRANSLATION SUMMARY")
    print("="*60)
    print(f"Total verses: {total}")
    print(f"✓ Success: {success}")
    print(f"✗ Failed: {failed}")
    print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
