#!/usr/bin/env python3
"""
Add new verse placeholders to existing collections.

This command adds verse entries to the canonical YAML file and optionally
creates corresponding markdown files.

Usage:
    # Add single verse
    verse-add --collection hanuman-chalisa --verse 44

    # Add multiple verses (range)
    verse-add --collection hanuman-chalisa --verse 44-50

    # Add without creating markdown files
    verse-add --collection hanuman-chalisa --verse 44 --no-markdown
"""

import os
import sys
import argparse
import yaml
import re
from pathlib import Path
from typing import List, Tuple, Optional


def parse_verse_range(verse_arg: str) -> List[int]:
    """
    Parse verse argument into list of verse numbers.

    Args:
        verse_arg: Verse number or range (e.g., "5" or "5-10")

    Returns:
        List of verse numbers
    """
    if '-' in verse_arg:
        start, end = verse_arg.split('-')
        return list(range(int(start), int(end) + 1))
    else:
        return [int(verse_arg)]


def infer_verse_format(existing_verses: dict) -> Tuple[str, str]:
    """
    Infer verse ID format from existing verses.

    Args:
        existing_verses: Dictionary of existing verse entries

    Returns:
        Tuple of (prefix, format_string)
        e.g., ("verse", "{:02d}") for verse-01, verse-02, etc.
        e.g., ("chaupai", "{:d}") for chaupai-1, chaupai-2, etc.
    """
    if not existing_verses:
        # Default format if no verses exist
        return "verse", "{:02d}"

    # Get a sample verse key
    sample_keys = list(existing_verses.keys())

    # Filter out metadata keys (keys starting with _)
    verse_keys = [k for k in sample_keys if not k.startswith('_')]

    if not verse_keys:
        return "verse", "{:02d}"

    # Analyze first verse key to infer pattern
    first_key = verse_keys[0]

    # Try to parse pattern: prefix-number
    match = re.match(r'^([a-z\-]+)-(\d+)$', first_key)
    if match:
        prefix = match.group(1)
        number = match.group(2)

        # Determine if zero-padded
        if len(number) > 1 and number[0] == '0':
            # Zero-padded (e.g., 01, 02)
            padding = len(number)
            format_str = f"{{:0{padding}d}}"
        else:
            # No padding (e.g., 1, 2)
            format_str = "{:d}"

        return prefix, format_str

    # Fallback to default
    return "verse", "{:02d}"


def get_collection_info(project_dir: Path, collection_key: str) -> dict:
    """
    Get collection information from collections.yml.

    Args:
        project_dir: Project root directory
        collection_key: Collection key

    Returns:
        Collection configuration dict
    """
    collections_file = project_dir / "_data" / "collections.yml"
    if not collections_file.exists():
        print(f"Error: {collections_file} not found")
        sys.exit(1)

    with open(collections_file, 'r') as f:
        collections = yaml.safe_load(f) or {}

    if collection_key not in collections:
        print(f"Error: Collection '{collection_key}' not found in collections.yml")
        print(f"Available collections: {', '.join(collections.keys())}")
        sys.exit(1)

    return collections[collection_key]


def add_verses_to_yaml(project_dir: Path, collection_key: str, verse_numbers: List[int], custom_format: Optional[str] = None) -> Tuple[int, int, str]:
    """
    Add verse placeholders to canonical YAML file.

    Args:
        project_dir: Project root directory
        collection_key: Collection key
        verse_numbers: List of verse numbers to add
        custom_format: Optional custom format (overrides inferred format)

    Returns:
        Tuple of (added_count, skipped_count, format_used)
    """
    yaml_files = [
        project_dir / "data" / "verses" / f"{collection_key}.yaml",
        project_dir / "data" / "verses" / f"{collection_key}.yml",
    ]

    # Find existing YAML file or create new one
    yaml_file = None
    existing_verses = {}

    for yf in yaml_files:
        if yf.exists():
            yaml_file = yf
            with open(yf, 'r') as f:
                existing_verses = yaml.safe_load(f) or {}
            break

    if yaml_file is None:
        yaml_file = project_dir / "data" / "verses" / f"{collection_key}.yaml"
        yaml_file.parent.mkdir(parents=True, exist_ok=True)

    # Infer format from existing verses (unless custom format provided)
    if custom_format:
        # Parse custom format: "prefix-{format}"
        match = re.match(r'^([a-z\-]+)-(.+)$', custom_format)
        if match:
            prefix = match.group(1)
            format_str = match.group(2)
        else:
            print(f"Warning: Invalid custom format '{custom_format}', using inferred format")
            prefix, format_str = infer_verse_format(existing_verses)
    else:
        prefix, format_str = infer_verse_format(existing_verses)

    format_used = f"{prefix}-{format_str}"

    added = 0
    skipped = 0

    # Add new verses
    for verse_num in verse_numbers:
        verse_id = f"{prefix}-{format_str.format(verse_num)}"

        if verse_id in existing_verses:
            print(f"  ⚠️  Skipped {verse_id} (already exists)")
            skipped += 1
        else:
            existing_verses[verse_id] = {
                'devanagari': ''
            }
            print(f"  ✓ Added {verse_id} to {yaml_file.name}")
            added += 1

    # Write back to file with blank lines between verses
    with open(yaml_file, 'w', encoding='utf-8') as f:
        sorted_keys = sorted(existing_verses.keys())
        for i, key in enumerate(sorted_keys):
            # Write verse key
            f.write(f"{key}:\n")

            # Write verse data
            verse_data = existing_verses[key]
            if isinstance(verse_data, dict):
                for field_key, field_value in verse_data.items():
                    if isinstance(field_value, str):
                        if '\n' in field_value and field_value.strip():
                            # Multi-line string - use literal style
                            f.write(f"  {field_key}: |\n")
                            for line in field_value.split('\n'):
                                if line or field_value.endswith('\n'):  # Keep empty lines
                                    f.write(f"    {line}\n")
                        elif field_value:
                            # Single line string
                            f.write(f"  {field_key}: {yaml.dump(field_value, allow_unicode=True).strip()}\n")
                        else:
                            # Empty string
                            f.write(f"  {field_key}: ''\n")
                    else:
                        # Other types
                        f.write(f"  {field_key}: {yaml.dump(field_value, allow_unicode=True).strip()}\n")
            else:
                # Non-dict value
                f.write(f"  {yaml.dump(verse_data, allow_unicode=True)}")

            # Add blank line between verses (except after last verse)
            if i < len(sorted_keys) - 1:
                f.write("\n")

    return added, skipped, format_used


def create_markdown_files(project_dir: Path, collection_key: str, verse_numbers: List[int], verse_prefix: str, format_str: str) -> Tuple[int, int]:
    """
    Create markdown files for verses.

    Args:
        project_dir: Project root directory
        collection_key: Collection key
        verse_numbers: List of verse numbers to create
        verse_prefix: Verse prefix (e.g., "verse", "chaupai")
        format_str: Format string (e.g., "{:02d}", "{:d}")

    Returns:
        Tuple of (created_count, skipped_count)
    """
    verses_dir = project_dir / "_verses" / collection_key
    verses_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for verse_num in verse_numbers:
        verse_id = f"{verse_prefix}-{format_str.format(verse_num)}"
        verse_file = verses_dir / f"{verse_id}.md"

        if verse_file.exists():
            print(f"  ⚠️  Skipped {verse_file.name} (already exists)")
            skipped += 1
        else:
            content = f"""---
layout: verse
collection: {collection_key}
verse_number: {verse_num}
title: "{verse_prefix.title()} {verse_num}"
---

Add verse content here.
"""
            verse_file.write_text(content)
            print(f"  ✓ Created {verse_file.name}")
            created += 1

    return created, skipped


def main():
    """Main entry point for verse-add command."""
    parser = argparse.ArgumentParser(
        description="Add new verse placeholders to existing collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add single verse
  verse-add --collection hanuman-chalisa --verse 44

  # Add multiple verses (range)
  verse-add --collection hanuman-chalisa --verse 44-50

  # Add verses without creating markdown files
  verse-add --collection hanuman-chalisa --verse 44-50 --no-markdown

  # Add verses with custom verse ID format
  verse-add --collection bhagavad-gita --verse 1 --format "chapter-01-verse-{:02d}"

For more information:
  https://github.com/sanatan-learnings/sanatan-verse-sdk/blob/main/docs/usage.md
        """
    )

    parser.add_argument(
        "--collection",
        required=True,
        help="Collection key (e.g., hanuman-chalisa)"
    )

    parser.add_argument(
        "--verse",
        required=True,
        help="Verse number or range (e.g., 44 or 44-50)"
    )

    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Don't create markdown files (only update YAML)"
    )

    parser.add_argument(
        "--format",
        default="verse-{:02d}",
        help="Verse ID format (default: verse-{:02d})"
    )

    args = parser.parse_args()

    try:
        project_dir = Path.cwd()

        # Parse verse numbers
        try:
            verse_numbers = parse_verse_range(args.verse)
        except ValueError as e:
            print(f"Error: Invalid verse format '{args.verse}'. Use a number (e.g., 44) or range (e.g., 44-50)")
            sys.exit(1)

        # Get collection info
        collection_info = get_collection_info(project_dir, args.collection)
        collection_name = collection_info.get('name', {}).get('en', args.collection)

        print()
        print(f"📝 Adding verses to {collection_name}")
        print(f"   Collection: {args.collection}")
        print(f"   Verses: {args.verse} ({len(verse_numbers)} verse(s))")
        print()

        # Add to YAML
        print("Updating canonical YAML file:")
        custom_format = args.format if args.format != "verse-{:02d}" else None
        yaml_added, yaml_skipped, format_used = add_verses_to_yaml(project_dir, args.collection, verse_numbers, custom_format)

        # Parse format for markdown creation
        match = re.match(r'^([a-z\-]+)-(.+)$', format_used)
        if match:
            verse_prefix = match.group(1)
            format_str = match.group(2)
        else:
            verse_prefix = "verse"
            format_str = "{:02d}"

        if yaml_added > 0:
            print(f"   Format: {format_used}")

        # Create markdown files
        if not args.no_markdown:
            print()
            print("Creating markdown files:")
            md_created, md_skipped = create_markdown_files(project_dir, args.collection, verse_numbers, verse_prefix, format_str)
        else:
            md_created = 0
            md_skipped = len(verse_numbers)
            print()
            print("Skipping markdown file creation (--no-markdown flag)")

        # Summary
        print()
        print("=" * 70)
        print("✅ Summary:")
        print(f"   YAML entries added: {yaml_added}")
        if yaml_skipped > 0:
            print(f"   YAML entries skipped: {yaml_skipped} (already exist)")
        if not args.no_markdown:
            print(f"   Markdown files created: {md_created}")
            if md_skipped > 0:
                print(f"   Markdown files skipped: {md_skipped} (already exist)")
        print()

        # Next steps
        if yaml_added > 0 or md_created > 0:
            print("📌 Next steps:")
            if yaml_added > 0:
                print(f"   1. Edit data/verses/{args.collection}.yaml to add Devanagari text")
            if md_created > 0:
                print(f"   2. Edit verse markdown files in _verses/{args.collection}/")
            print(f"   3. Update total_verses in _data/collections.yml if needed")
            print(f"   4. Generate content with: verse-generate --collection {args.collection}")
            print()

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
