#!/usr/bin/env python3
"""
Sync verse text with canonical source from data/verses/{collection}.yaml

This command updates verse files to match the normative text stored in local YAML files,
ensuring text accuracy and consistency across your verse collection.

Usage:
    # Sync specific verse
    verse-sync --collection sundar-kaand --verse chaupai_01

    # Sync all verses in collection
    verse-sync --collection sundar-kaand --all

    # Dry run (preview changes without writing)
    verse-sync --collection sundar-kaand --verse chaupai_01 --dry-run

    # Fix all validation mismatches
    verse-sync --collection sundar-kaand --fix-mismatches
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

# Load environment variables
load_dotenv()


def load_normative_verses(collection: str, project_dir: Path) -> Dict:
    """Load normative verses from data/verses/{collection}.yaml"""
    verses_file = project_dir / "data" / "verses" / f"{collection}.yaml"

    if not verses_file.exists():
        return {}

    try:
        with open(verses_file, 'r', encoding='utf-8') as f:
            verses_data = yaml.safe_load(f)

        # Filter out metadata keys (starting with _)
        if verses_data:
            return {k: v for k, v in verses_data.items() if not k.startswith('_')}
        return {}
    except Exception as e:
        print(f"Error: Could not load normative verses from {verses_file}: {e}", file=sys.stderr)
        return {}


def parse_verse_file(verse_file: Path) -> Tuple[Optional[Dict], Optional[str]]:
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


def update_verse_file(
    verse_file: Path,
    frontmatter: Dict,
    body: str,
    normative_text: str,
    dry_run: bool = False
) -> bool:
    """
    Update verse file with canonical text.

    Returns:
        True if file was updated (or would be updated in dry-run), False otherwise
    """
    # Update devanagari field
    old_text = frontmatter.get('devanagari', '')
    frontmatter['devanagari'] = normative_text

    # Build updated content
    updated_content = "---\n"
    updated_content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    updated_content += "---"
    updated_content += body

    if dry_run:
        print(f"  [DRY RUN] Would update: {verse_file.name}")
        if old_text != normative_text:
            print(f"    Old: {old_text[:60]}...")
            print(f"    New: {normative_text[:60]}...")
        return True

    try:
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    except Exception as e:
        print(f"Error writing {verse_file}: {e}", file=sys.stderr)
        return False


def get_mismatched_verses(collection: str, project_dir: Path) -> List[str]:
    """
    Get list of verses with validation mismatches by running verse-status.

    Returns:
        List of verse IDs that have mismatches
    """
    # Import here to avoid circular dependency
    try:
        from verse_sdk.cli.status import (
            analyze_collection,
            load_normative_verses as load_norm,
        )
    except ImportError:
        print("Error: Could not import verse-status functions", file=sys.stderr)
        return []

    # Analyze collection with validation
    analysis = analyze_collection(collection, project_dir, validate_text=True)

    if not analysis.get('exists') or not analysis.get('verses'):
        return []

    # Find verses with mismatches or minor differences
    mismatched = []
    for verse in analysis['verses']:
        if 'validation' in verse:
            status = verse['validation']['status']
            if status in ['mismatch', 'minor_diff']:
                mismatched.append(verse['verse_id'])

    return mismatched


def sync_verse(
    collection: str,
    verse_id: str,
    project_dir: Path,
    normative_verses: Dict,
    dry_run: bool = False
) -> Dict:
    """
    Sync a single verse with normative source.

    Returns:
        Dict with sync result:
        - success: bool
        - message: str
        - updated: bool (whether text was changed)
    """
    # Check if normative text exists
    if verse_id not in normative_verses:
        return {
            'success': False,
            'message': 'Not found in normative source',
            'updated': False
        }

    # Get normative text
    normative_data = normative_verses[verse_id]
    if isinstance(normative_data, dict):
        normative_text = normative_data.get('devanagari')
    else:
        normative_text = None

    if not normative_text:
        return {
            'success': False,
            'message': 'Devanagari text missing in normative source',
            'updated': False
        }

    # Find and parse verse file
    verses_dir = project_dir / "_verses" / collection
    verse_file = verses_dir / f"{verse_id}.md"

    if not verse_file.exists():
        return {
            'success': False,
            'message': f'Verse file not found: {verse_file}',
            'updated': False
        }

    frontmatter, body = parse_verse_file(verse_file)

    if frontmatter is None:
        return {
            'success': False,
            'message': 'Could not parse verse file',
            'updated': False
        }

    # Check if update is needed
    current_text = frontmatter.get('devanagari', '')
    if current_text == normative_text:
        return {
            'success': True,
            'message': 'Already matches normative text',
            'updated': False
        }

    # Update the file
    if update_verse_file(verse_file, frontmatter, body, normative_text, dry_run):
        msg = 'Would be updated' if dry_run else 'Updated successfully'
        return {
            'success': True,
            'message': msg,
            'updated': True,
            'old_text': current_text,
            'new_text': normative_text
        }
    else:
        return {
            'success': False,
            'message': 'Failed to update file',
            'updated': False
        }


def sync_collection(
    collection: str,
    project_dir: Path,
    dry_run: bool = False,
    verse_ids: Optional[List[str]] = None
) -> Dict:
    """
    Sync multiple verses in a collection.

    Args:
        collection: Collection key
        project_dir: Project directory
        dry_run: If True, don't actually write changes
        verse_ids: Specific verses to sync (None = all verses)

    Returns:
        Dict with sync results
    """
    # Load normative verses
    normative_verses = load_normative_verses(collection, project_dir)

    if not normative_verses:
        return {
            'success': False,
            'error': f'No normative verses found for {collection}',
            'results': []
        }

    # Determine which verses to sync
    if verse_ids:
        verses_to_sync = verse_ids
    else:
        verses_to_sync = list(normative_verses.keys())

    # Sync each verse
    results = []
    for verse_id in verses_to_sync:
        result = sync_verse(collection, verse_id, project_dir, normative_verses, dry_run)
        results.append({
            'verse_id': verse_id,
            **result
        })

    # Summary
    total = len(results)
    updated = sum(1 for r in results if r.get('updated'))
    errors = sum(1 for r in results if not r.get('success'))

    return {
        'success': True,
        'total': total,
        'updated': updated,
        'errors': errors,
        'results': results
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync verse text with canonical source",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync specific verse
  verse-sync --collection sundar-kaand --verse chaupai_01

  # Sync all verses in collection
  verse-sync --collection sundar-kaand --all

  # Dry run (preview changes)
  verse-sync --collection sundar-kaand --verse chaupai_01 --dry-run

  # Fix all validation mismatches
  verse-sync --collection sundar-kaand --fix-mismatches

  # Sync multiple specific verses
  verse-sync --collection sundar-kaand --verse chaupai_01 --verse chaupai_02 --verse doha_01

Note:
  - Reads canonical text from data/verses/{collection}.yaml
  - Updates devanagari field in verse frontmatter
  - Preserves other fields (transliteration, meaning, translation)
  - Use --dry-run to preview changes before applying
        """
    )

    parser.add_argument(
        "--collection",
        type=str,
        required=True,
        help="Collection key (e.g., sundar-kaand, hanuman-chalisa)",
        metavar="KEY"
    )

    parser.add_argument(
        "--verse",
        type=str,
        action='append',
        dest='verses',
        help="Specific verse ID to sync (can be used multiple times)",
        metavar="ID"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all verses in collection"
    )

    parser.add_argument(
        "--fix-mismatches",
        action="store_true",
        help="Sync only verses with validation mismatches"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to files"
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    args = parser.parse_args()

    project_dir = args.project_dir

    # Validate arguments
    if not any([args.verses, args.all, args.fix_mismatches]):
        parser.error("Must specify --verse, --all, or --fix-mismatches")

    # Display header
    print("\n" + "="*60)
    if args.dry_run:
        print("VERSE SYNC - DRY RUN (Preview Only)")
    else:
        print("VERSE SYNC")
    print("="*60)
    print(f"\nCollection: {args.collection}")
    print(f"Source: data/verses/{args.collection}.yaml\n")

    # Determine verses to sync
    verse_ids = None

    if args.fix_mismatches:
        print("Finding verses with validation mismatches...")
        verse_ids = get_mismatched_verses(args.collection, project_dir)
        if not verse_ids:
            print("✓ No mismatches found - all verses match normative text!")
            sys.exit(0)
        print(f"Found {len(verse_ids)} verse(s) with mismatches\n")
    elif args.verses:
        verse_ids = args.verses
    elif args.all:
        verse_ids = None  # Will sync all verses

    # Perform sync
    try:
        result = sync_collection(
            args.collection,
            project_dir,
            dry_run=args.dry_run,
            verse_ids=verse_ids
        )

        if not result['success']:
            print(f"✗ Error: {result.get('error')}")
            sys.exit(1)

        # Display results
        print(f"{'='*60}")
        print("SYNC RESULTS")
        print(f"{'='*60}\n")

        for item in result['results']:
            verse_id = item['verse_id']
            success = item['success']
            updated = item.get('updated', False)
            message = item['message']

            if updated:
                icon = "📝" if args.dry_run else "✓"
                print(f"{icon} {verse_id:20s} - {message}")
                if args.dry_run and 'old_text' in item and 'new_text' in item:
                    print(f"   Old: {item['old_text'][:50]}...")
                    print(f"   New: {item['new_text'][:50]}...")
            elif success:
                print(f"  {verse_id:20s} - {message}")
            else:
                print(f"✗ {verse_id:20s} - {message}")

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total verses: {result['total']}")
        print(f"Updated: {result['updated']}")
        print(f"Errors: {result['errors']}")
        print(f"Already synced: {result['total'] - result['updated'] - result['errors']}")

        if args.dry_run and result['updated'] > 0:
            print(f"\n⚠️  This was a dry run. Run without --dry-run to apply changes.")

        print()

        # Exit code based on errors
        sys.exit(0 if result['errors'] == 0 else 1)

    except KeyboardInterrupt:
        print("\n\n⚠ Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
