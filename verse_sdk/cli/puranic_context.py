#!/usr/bin/env python3
"""
Generate Puranic context boxes for verse files.

This command uses AI to identify relevant Puranic references (stories, characters,
concepts, etymologies) and injects a puranic_context block into the verse
file's frontmatter.

Usage:
    # Generate for a specific verse
    verse-puranic-context --collection hanuman-chalisa --verse chaupai-15

    # Generate for all verses missing context
    verse-puranic-context --collection bajrang-baan --all

    # Force regenerate even if context exists
    verse-puranic-context --collection hanuman-chalisa --verse chaupai-18 --regenerate

Requirements:
    - OPENAI_API_KEY environment variable
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

load_dotenv()

VALID_TYPES = {"story", "concept", "character", "etymology", "practice", "cross_reference"}
VALID_PRIORITIES = {"high", "medium", "low"}

SYSTEM_PROMPT = """You are an expert in Hindu scriptures, Puranas, and devotional literature
(bhakti). You generate structured Puranic context boxes for verses from sacred texts like
Hanuman Chalisa, Sundar Kaand, Bajrang Baan, and Sankat Mochan Hanumanashtak.

Each context entry must be a YAML object with these fields:
  id: unique-slug (kebab-case)
  type: story | concept | character | etymology | practice | cross_reference
  priority: high | medium | low
  title:
    en: "English title"
    hi: "Hindi title in Devanagari"
  icon: single emoji
  story_summary:
    en: "2-4 sentence summary"
    hi: "Same in Hindi Devanagari"
  theological_significance:
    en: "2-4 sentences on spiritual meaning"
    hi: "Same in Hindi Devanagari"
  practical_application:
    en: "2-4 sentences on practical use"
    hi: "Same in Hindi Devanagari"
  source_texts:
    - text: "Scripture name"
      section: "Book/chapter/kanda"
  related_verses: []

Rules:
- Generate 1-3 entries per verse (only the most relevant references)
- For short invocations, closing verses, or verses with no meaningful Puranic
  content, return an empty list []
- Prioritise accuracy over quantity
- All Hindi text must be in Devanagari script
- Return ONLY valid YAML — no markdown fences, no explanation"""


def parse_verse_file(verse_file: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """Parse verse frontmatter and body. Returns (frontmatter, body)."""
    if not verse_file.exists():
        return None, None
    try:
        content = verse_file.read_text(encoding='utf-8')
        if not content.startswith('---'):
            return {}, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except Exception as e:
        print(f"  ✗ Error parsing {verse_file.name}: {e}", file=sys.stderr)
        return None, None


def update_verse_file(verse_file: Path, frontmatter: Dict, body: str) -> bool:
    """Write updated frontmatter back to verse file."""
    try:
        content = "---\n"
        content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False,
                             default_flow_style=False)
        content += "---"
        content += body
        verse_file.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  ✗ Error writing {verse_file.name}: {e}", file=sys.stderr)
        return False


def build_prompt(frontmatter: Dict, verse_id: str) -> str:
    """Build the user prompt from verse frontmatter fields."""
    devanagari = frontmatter.get('devanagari', '')
    transliteration = frontmatter.get('transliteration', '')
    title_en = frontmatter.get('title_en', verse_id)

    # Collect meaning fields
    meaning_parts = []
    for field in ('translation', 'interpretive_meaning', 'literal_translation'):
        val = frontmatter.get(field)
        if isinstance(val, dict):
            val = val.get('en', '')
        if val:
            meaning_parts.append(f"{field}: {val}")

    story = frontmatter.get('story', {})
    if isinstance(story, dict):
        story = story.get('en', '')
    story_text = str(story)[:800] if story else ''

    prompt = f"""Verse: {title_en}
Devanagari: {devanagari}
Transliteration: {transliteration}
"""
    if meaning_parts:
        prompt += "\n".join(meaning_parts) + "\n"
    if story_text:
        prompt += f"\nStory/Context: {story_text}\n"

    prompt += """
Generate Puranic context entries for this verse as a YAML list.
Return [] if the verse has no meaningful Puranic content."""
    return prompt


def generate_puranic_context(frontmatter: Dict, verse_id: str) -> Optional[List]:
    """Call GPT-4 to generate puranic_context entries. Returns a list or None on error."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = build_prompt(frontmatter, verse_id)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        parsed = yaml.safe_load(raw)
        if parsed is None:
            return []
        if not isinstance(parsed, list):
            print(f"  ⚠ Unexpected response format (not a list)", file=sys.stderr)
            return None
        return parsed

    except yaml.YAMLError as e:
        print(f"  ✗ YAML parse error in AI response: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ✗ API error: {e}", file=sys.stderr)
        return None


def process_verse(verse_file: Path, regenerate: bool = False) -> str:
    """
    Process a single verse file.

    Returns: 'added' | 'skipped' | 'regenerated' | 'empty' | 'error'
    """
    frontmatter, body = parse_verse_file(verse_file)
    if frontmatter is None:
        return 'error'

    verse_id = verse_file.stem
    already_has_context = bool(frontmatter.get('puranic_context'))

    if already_has_context and not regenerate:
        print(f"  ⊘ {verse_id}: Already has puranic_context, skipping (use --regenerate to overwrite)")
        return 'skipped'

    print(f"  → {verse_id}: Generating Puranic context...")
    entries = generate_puranic_context(frontmatter, verse_id)

    if entries is None:
        return 'error'

    if len(entries) == 0:
        print(f"  ○ {verse_id}: No Puranic content identified, skipping")
        return 'empty'

    frontmatter['puranic_context'] = entries
    if not update_verse_file(verse_file, frontmatter, body):
        return 'error'

    action = 'regenerated' if already_has_context else 'added'
    print(f"  ✓ {verse_id}: {len(entries)} context entr{'y' if len(entries) == 1 else 'ies'} {action}")
    return action


def main():
    """Main entry point for verse-puranic-context command."""
    parser = argparse.ArgumentParser(
        description="Generate Puranic context boxes for verse files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for a specific verse (by verse ID)
  verse-puranic-context --collection hanuman-chalisa --verse chaupai-15

  # Generate for all verses missing context
  verse-puranic-context --collection bajrang-baan --all

  # Force regenerate even if context already exists
  verse-puranic-context --collection hanuman-chalisa --verse chaupai-18 --regenerate

  # Regenerate all verses in a collection
  verse-puranic-context --collection sundar-kaand --all --regenerate

Note:
  - Skips verses that already have puranic_context (use --regenerate to overwrite)
  - Skips verses with no meaningful Puranic content (short invocations, etc.)
  - Requires OPENAI_API_KEY environment variable
        """
    )

    parser.add_argument(
        "--collection",
        required=True,
        metavar="KEY",
        help="Collection key (e.g., hanuman-chalisa, sundar-kaand)"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--verse",
        metavar="ID",
        help="Verse ID to process (e.g., chaupai-15, doha-01)"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all verses in the collection"
    )

    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Overwrite existing puranic_context entries"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    verses_dir = args.project_dir / "_verses" / args.collection
    if not verses_dir.exists():
        print(f"✗ Error: Collection directory not found: {verses_dir}")
        sys.exit(1)

    # Determine verse files to process
    if args.all:
        verse_files = sorted(verses_dir.glob("*.md"))
        if not verse_files:
            print(f"✗ Error: No verse files found in {verses_dir}")
            sys.exit(1)
    else:
        verse_file = verses_dir / f"{args.verse}.md"
        if not verse_file.exists():
            print(f"✗ Error: Verse file not found: {verse_file}")
            sys.exit(1)
        verse_files = [verse_file]

    print()
    print("=" * 60)
    print("PURANIC CONTEXT GENERATION")
    print("=" * 60)
    print(f"\nCollection : {args.collection}")
    print(f"Verses     : {'all (' + str(len(verse_files)) + ')' if args.all else args.verse}")
    print(f"Regenerate : {'yes' if args.regenerate else 'no (skip existing)'}")
    print()

    counts = {'added': 0, 'regenerated': 0, 'skipped': 0, 'empty': 0, 'error': 0}

    try:
        for verse_file in verse_files:
            result = process_verse(verse_file, regenerate=args.regenerate)
            counts[result] = counts.get(result, 0) + 1
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if counts['added']:
        print(f"  ✓ Added    : {counts['added']}")
    if counts['regenerated']:
        print(f"  ✓ Updated  : {counts['regenerated']}")
    if counts['empty']:
        print(f"  ○ No content : {counts['empty']}")
    if counts['skipped']:
        print(f"  ⊘ Skipped  : {counts['skipped']}")
    if counts['error']:
        print(f"  ✗ Errors   : {counts['error']}")
    print()

    sys.exit(1 if counts['error'] == len(verse_files) else 0)


if __name__ == "__main__":
    main()
