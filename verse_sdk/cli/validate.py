#!/usr/bin/env python3
"""
Project structure validation command - validates directory structure and configuration.

This command checks if your project follows the recommended conventions and
identifies missing or misconfigured components.

Usage:
    # Validate current project
    verse-validate

    # Validate and show detailed information
    verse-validate --detailed

    # Auto-fix common issues (creates missing directories)
    verse-validate --fix

    # Check specific collection
    verse-validate --collection hanuman-chalisa

    # JSON output for scripting
    verse-validate --format json
"""

import os
import sys
import argparse
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed")
    print("Install with: pip install python-dotenv")
    sys.exit(1)


class ProjectValidator:
    """Validates project structure and configuration."""

    def __init__(self, project_dir: Path):
        """
        Initialize validator.

        Args:
            project_dir: Project root directory
        """
        self.project_dir = project_dir
        self.issues = []
        self.warnings = []
        self.successes = []

    def validate_directory_structure(self) -> None:
        """Validate required directory structure."""
        required_dirs = {
            "_data": "Collection registry and configuration",
            "_verses": "Verse markdown files",
            "data": "Canonical verse text and themes",
        }

        optional_dirs = {
            "data/themes": "Theme configurations (created as needed per collection)",
            "data/verses": "Canonical verse YAML files",
            "data/scenes": "Scene descriptions for image generation (YAML format)",
            "data/sources": "Source texts for RAG indexing (used by verse-index-sources)",
            "data/puranic-index": "Indexed Puranic episodes for RAG retrieval",
            "data/embeddings": "Vector embeddings per source (used by verse-puranic-context)",
            "images": "Generated images (created automatically)",
            "audio": "Generated audio files (created automatically)",
        }

        # Check required directories
        for dir_name, description in required_dirs.items():
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.successes.append(f"✅ {dir_name}/ directory exists - {description}")
            else:
                self.issues.append(f"❌ {dir_name}/ directory missing - {description}")

        # Check optional directories
        for dir_name, description in optional_dirs.items():
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.successes.append(f"✅ {dir_name}/ directory exists - {description}")
            else:
                self.warnings.append(f"⚠️  {dir_name}/ directory missing (optional) - {description}")

    def validate_configuration_files(self) -> None:
        """Validate configuration files."""
        # Check collections.yml
        collections_file = self.project_dir / "_data" / "collections.yml"
        if collections_file.exists():
            try:
                with open(collections_file, 'r') as f:
                    collections = yaml.safe_load(f)
                if collections and isinstance(collections, dict):
                    enabled_count = sum(1 for c in collections.values() if isinstance(c, dict) and c.get('enabled'))
                    self.successes.append(f"✅ _data/collections.yml is valid ({enabled_count} enabled collections)")
                else:
                    self.warnings.append("⚠️  _data/collections.yml exists but contains no collections")
            except yaml.YAMLError as e:
                self.issues.append(f"❌ _data/collections.yml has invalid YAML syntax: {e}")
        else:
            self.issues.append("❌ _data/collections.yml not found - required for defining collections")

        # Check .env file
        env_file = self.project_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            api_keys = {
                'OPENAI_API_KEY': 'OpenAI API (for images, embeddings, content)',
                'ELEVENLABS_API_KEY': 'ElevenLabs API (for audio)',
            }
            for key, description in api_keys.items():
                if os.getenv(key):
                    # Check if it's not the placeholder value
                    value = os.getenv(key)
                    if 'your_' in value.lower() or value == 'sk-your_openai_key_here':
                        self.warnings.append(f"⚠️  {key} is set but appears to be placeholder - {description}")
                    else:
                        self.successes.append(f"✅ {key} is configured - {description}")
                else:
                    self.warnings.append(f"⚠️  {key} not set in .env - {description}")
        else:
            self.warnings.append("⚠️  .env file not found - copy .env.example and add your API keys")

        # Check .env.example
        env_example = self.project_dir / ".env.example"
        if env_example.exists():
            self.successes.append("✅ .env.example exists - template for environment variables")
        else:
            self.warnings.append("⚠️  .env.example not found (optional) - helpful for new developers")

    def validate_collection(self, collection_key: str) -> Dict:
        """
        Validate a specific collection.

        Args:
            collection_key: Collection key (e.g., 'hanuman-chalisa')

        Returns:
            Dictionary with validation results
        """
        results = {
            'collection': collection_key,
            'issues': [],
            'warnings': [],
            'successes': [],
        }

        # Check verse directory
        verses_dir = self.project_dir / "_verses" / collection_key
        if verses_dir.exists() and verses_dir.is_dir():
            verse_files = list(verses_dir.glob("*.md"))
            if verse_files:
                results['successes'].append(f"✅ Found {len(verse_files)} verse files in _verses/{collection_key}/")
            else:
                results['warnings'].append(f"⚠️  _verses/{collection_key}/ exists but contains no .md files")
        else:
            results['issues'].append(f"❌ _verses/{collection_key}/ directory not found")

        # Check canonical verse YAML file
        yaml_files = [
            self.project_dir / "data" / "verses" / f"{collection_key}.yaml",
            self.project_dir / "data" / "verses" / f"{collection_key}.yml",
        ]
        yaml_found = False
        for yaml_file in yaml_files:
            if yaml_file.exists():
                yaml_found = True
                try:
                    with open(yaml_file, 'r') as f:
                        verses = yaml.safe_load(f)
                    if verses:
                        verse_count = len([k for k in verses.keys() if not k.startswith('_')])
                        results['successes'].append(f"✅ Canonical verse file exists: {yaml_file.name} ({verse_count} verses)")
                    else:
                        results['warnings'].append(f"⚠️  {yaml_file.name} exists but is empty")
                except yaml.YAMLError as e:
                    results['issues'].append(f"❌ {yaml_file.name} has invalid YAML syntax: {e}")
                break

        if not yaml_found:
            results['warnings'].append(f"⚠️  No canonical verse file found in data/verses/{collection_key}.yaml")

        # Check theme directory
        theme_dir = self.project_dir / "data" / "themes" / collection_key
        if theme_dir.exists() and theme_dir.is_dir():
            theme_files = list(theme_dir.glob("*.yml")) + list(theme_dir.glob("*.yaml"))
            if theme_files:
                results['successes'].append(f"✅ Found {len(theme_files)} theme(s) in data/themes/{collection_key}/")
            else:
                results['warnings'].append(f"⚠️  data/themes/{collection_key}/ exists but contains no theme files")
        else:
            results['warnings'].append(f"⚠️  data/themes/{collection_key}/ not found - needed for image generation")

        # Check scene descriptions (YAML format in data/scenes/)
        scene_files = [
            self.project_dir / "data" / "scenes" / f"{collection_key}.yml",
            self.project_dir / "data" / "scenes" / f"{collection_key}.yaml",
        ]
        scene_found = any(sf.exists() for sf in scene_files)
        if scene_found:
            scene_file = next((sf for sf in scene_files if sf.exists()), None)
            results['successes'].append(f"✅ Scene descriptions file exists: data/scenes/{scene_file.name}")
        else:
            results['warnings'].append(f"⚠️  data/scenes/{collection_key}.yml not found - needed for image generation")

        return results

    def validate_all_collections(self) -> List[Dict]:
        """
        Validate all enabled collections.

        Returns:
            List of validation results for each collection
        """
        collections_file = self.project_dir / "_data" / "collections.yml"
        if not collections_file.exists():
            return []

        try:
            with open(collections_file, 'r') as f:
                collections = yaml.safe_load(f)
        except yaml.YAMLError:
            return []

        results = []
        if collections and isinstance(collections, dict):
            for key, config in collections.items():
                if isinstance(config, dict) and config.get('enabled'):
                    results.append(self.validate_collection(key))

        return results

    def get_validation_summary(self) -> Dict:
        """
        Get validation summary.

        Returns:
            Dictionary with validation summary
        """
        return {
            'project_dir': str(self.project_dir),
            'issues': self.issues,
            'warnings': self.warnings,
            'successes': self.successes,
            'total_issues': len(self.issues),
            'total_warnings': len(self.warnings),
            'is_valid': len(self.issues) == 0,
        }

    def fix_common_issues(self, dry_run: bool = False) -> List[str]:
        """
        Auto-fix common issues (creates missing directories).

        Args:
            dry_run: If True, only report what would be done without making changes

        Returns:
            List of actions taken (or would be taken if dry_run)
        """
        actions = []
        prefix = "Would create" if dry_run else "Created"

        # Create missing required directories
        required_dirs = ["_data", "_verses", "data", "data/themes", "data/verses", "data/scenes",
                         "data/sources", "data/puranic-index", "data/embeddings"]
        for dir_name in required_dirs:
            dir_path = self.project_dir / dir_name
            if not dir_path.exists():
                if not dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                actions.append(f"{prefix} {dir_name}/")

        # Create .env.example if missing
        env_example = self.project_dir / ".env.example"
        if not env_example.exists():
            if not dry_run:
                content = """# OpenAI API Key (for images, embeddings, and content generation)
OPENAI_API_KEY=sk-your_openai_key_here

# ElevenLabs API Key (for audio generation)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
"""
                env_example.write_text(content)
            actions.append(f"{prefix} .env.example")

        # Create collections.yml if missing
        collections_file = self.project_dir / "_data" / "collections.yml"
        if not collections_file.exists():
            if not dry_run:
                content = """# Collection registry
# Add your verse collections here
#
# Example:
# hanuman-chalisa:
#   enabled: true
#   name:
#     en: "Hanuman Chalisa"
#     hi: "हनुमान चालीसा"
#   subdirectory: "hanuman-chalisa"
#   permalink_base: "/hanuman-chalisa"
#   total_verses: 43
"""
                collections_file.write_text(content)
            actions.append(f"{prefix} _data/collections.yml")

        # Infer and add missing collection entries
        verses_dir = self.project_dir / "_verses"
        if verses_dir.exists() and collections_file.exists():
            # Load existing collections
            try:
                with open(collections_file, 'r') as f:
                    collections = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                collections = {}

            # Find all collection directories
            collection_dirs = [d for d in verses_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

            # Check which collections are missing
            missing_collections = []
            for collection_dir in collection_dirs:
                collection_key = collection_dir.name
                if collection_key not in collections:
                    missing_collections.append(collection_key)

            # Add missing collections
            if missing_collections:
                add_prefix = "Would add" if dry_run else "Added"
                for collection_key in missing_collections:
                    # Count verse files
                    verse_files = list((verses_dir / collection_key).glob("*.md"))
                    verse_count = len(verse_files)

                    # Generate display name (title case from key)
                    display_name = collection_key.replace('-', ' ').title()

                    if not dry_run:
                        # Add to collections dict
                        collections[collection_key] = {
                            'enabled': True,
                            'name': {
                                'en': display_name,
                            },
                            'subdirectory': collection_key,
                            'permalink_base': f"/{collection_key}",
                            'total_verses': verse_count,
                        }

                    actions.append(f"{add_prefix} {collection_key} collection to _data/collections.yml ({verse_count} verses)")

                # Write updated collections.yml
                if not dry_run and missing_collections:
                    with open(collections_file, 'w') as f:
                        yaml.dump(collections, f, default_flow_style=False, allow_unicode=True, sort_keys=True)

        # Create template canonical verse YAML files for collections that don't have one
        if verses_dir.exists() and collections_file.exists():
            # Load collections
            try:
                with open(collections_file, 'r') as f:
                    collections = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                collections = {}

            # Check each enabled collection
            for collection_key, config in collections.items():
                if isinstance(config, dict) and config.get('enabled'):
                    # Check if canonical verse file exists
                    canonical_files = [
                        self.project_dir / "data" / "verses" / f"{collection_key}.yaml",
                        self.project_dir / "data" / "verses" / f"{collection_key}.yml",
                    ]
                    canonical_exists = any(cf.exists() for cf in canonical_files)

                    if not canonical_exists:
                        # Get verse files to create template structure
                        collection_verses_dir = verses_dir / collection_key
                        if collection_verses_dir.exists():
                            verse_files = sorted(collection_verses_dir.glob("*.md"))

                            if verse_files:
                                create_prefix = "Would create template" if dry_run else "Created template"
                                canonical_file = self.project_dir / "data" / "verses" / f"{collection_key}.yaml"

                                if not dry_run:
                                    # Create template with entries for each verse file
                                    template_content = f"# Canonical verse text for {collection_key}\n"
                                    template_content += f"# Edit this file to add the original Devanagari text for each verse\n\n"

                                    for verse_file in verse_files:
                                        # Extract verse number/id from filename (e.g., verse-01.md -> verse-01)
                                        verse_id = verse_file.stem
                                        template_content += f"{verse_id}:\n"
                                        template_content += f"  devanagari: |\n"
                                        template_content += f"    # Add Devanagari text here\n"
                                        template_content += f"  transliteration: |\n"
                                        template_content += f"    # Add transliteration here (optional)\n\n"

                                    canonical_file.write_text(template_content)

                                actions.append(f"{create_prefix} data/verses/{collection_key}.yaml ({len(verse_files)} verse entries)")

        # Rename verse files from underscore to dash format
        verses_dir = self.project_dir / "_verses"
        if verses_dir.exists():
            rename_prefix = "Would rename" if dry_run else "Renamed"
            for collection_dir in verses_dir.iterdir():
                if collection_dir.is_dir():
                    for verse_file in collection_dir.glob("*_*.md"):
                        # Convert underscores to dashes in filename
                        old_name = verse_file.name
                        new_name = old_name.replace('_', '-')
                        new_path = verse_file.parent / new_name

                        # Check if target already exists
                        if new_path.exists():
                            actions.append(f"⚠️  Skipped {collection_dir.name}/{old_name} (target {new_name} already exists)")
                        else:
                            if not dry_run:
                                verse_file.rename(new_path)
                            actions.append(f"{rename_prefix} {collection_dir.name}/{old_name} → {new_name}")

        # Create theme directories with default templates
        if collections_file.exists():
            try:
                with open(collections_file, 'r') as f:
                    collections = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                collections = {}

            theme_prefix = "Would create" if dry_run else "Created"
            for collection_key, config in collections.items():
                if isinstance(config, dict) and config.get('enabled'):
                    theme_dir = self.project_dir / "data" / "themes" / collection_key
                    theme_file = theme_dir / "modern-minimalist.yml"

                    if not theme_file.exists():
                        if not dry_run:
                            theme_dir.mkdir(parents=True, exist_ok=True)
                            theme_content = """# Theme configuration for image generation
# Visual style for DALL-E 3 prompts

base_style: |
  Modern minimalist illustration style with clean lines and vibrant colors.
  Flat design with subtle gradients. Contemporary and approachable aesthetic.

mood: Peaceful, contemplative, uplifting
color_palette: Warm and inviting - golds, deep blues, soft whites
art_style: Digital illustration, clean vector-style art
quality: standard
size: "1024x1024"
"""
                            theme_file.write_text(theme_content)
                        actions.append(f"{theme_prefix} default theme: data/themes/{collection_key}/modern-minimalist.yml")

        # Fix path formats and missing frontmatter fields in verse markdown files
        if verses_dir.exists():
            fix_prefix = "Would fix" if dry_run else "Fixed"

            for collection_dir in verses_dir.iterdir():
                if collection_dir.is_dir() and not collection_dir.name.startswith('.'):
                    collection_key = collection_dir.name

                    for verse_file in collection_dir.glob("*.md"):
                        try:
                            content = verse_file.read_text()
                            original_content = content
                            changes_made = []

                            # Extract verse ID from filename (without .md extension)
                            verse_id = verse_file.stem

                            # Check if frontmatter exists
                            if content.startswith('---\n'):
                                # Parse frontmatter
                                parts = content.split('---\n', 2)
                                if len(parts) >= 3:
                                    frontmatter = parts[1]
                                    body = parts[2] if len(parts) > 2 else ""

                                    # Fix missing chapter field for Bhagavad Gita format
                                    if 'chapter-' in verse_id and 'chapter:' not in frontmatter:
                                        # Extract chapter number from verse_id (e.g., chapter-01-verse-05 → 1)
                                        chapter_match = re.search(r'chapter-(\d+)', verse_id)
                                        if chapter_match:
                                            chapter_num = int(chapter_match.group(1))
                                            # Add chapter field after layout field
                                            if 'layout:' in frontmatter:
                                                frontmatter = frontmatter.replace(
                                                    'layout: verse\n',
                                                    f'layout: verse\nchapter: {chapter_num}\n'
                                                )
                                                changes_made.append('added chapter field')

                                    # Reconstruct content with updated frontmatter
                                    content = f"---\n{frontmatter}---\n{body}"

                            # Fix image paths: /images/theme/verse.png -> /images/collection/theme/verse.png
                            # Pattern: image: /images/THEME/VERSE.png (missing collection)
                            before_image_fix = content
                            content = re.sub(
                                r'image:\s*/images/([^/\s]+)/([^/\s]+\.png)',
                                rf'image: /images/{collection_key}/\1/\2',
                                content
                            )
                            if content != before_image_fix:
                                changes_made.append('fixed image paths')

                            # Fix audio paths with underscores: chapter_01_verse_01 -> chapter-01-verse-01
                            # And add collection name if missing
                            def fix_audio_path(match):
                                prefix = match.group(1)  # audio_full or audio_slow
                                path = match.group(2)

                                # Convert underscores to dashes in the filename
                                filename = path.split('/')[-1]  # Get just the filename
                                filename = filename.replace('_', '-')

                                # Check if path already has collection
                                if path.startswith(f'/audio/{collection_key}/'):
                                    # Already correct format, just fix underscores
                                    return f'{prefix}: /audio/{collection_key}/{filename}'
                                else:
                                    # Add collection name
                                    return f'{prefix}: /audio/{collection_key}/{filename}'

                            before_audio_fix = content
                            content = re.sub(
                                r'(audio_(?:full|slow)):\s*(/audio/[^\s]+)',
                                fix_audio_path,
                                content
                            )
                            if content != before_audio_fix:
                                changes_made.append('fixed audio paths')

                            # Only write if content changed
                            if content != original_content:
                                if not dry_run:
                                    verse_file.write_text(content)
                                change_desc = ', '.join(changes_made) if changes_made else 'updated'
                                actions.append(f"{fix_prefix} {collection_key}/{verse_file.name} ({change_desc})")

                        except Exception as e:
                            actions.append(f"⚠️  Error processing {collection_key}/{verse_file.name}: {e}")

        return actions


def print_validation_results(summary: Dict, detailed: bool = False, collection_results: Optional[List[Dict]] = None) -> None:
    """
    Print validation results in human-readable format.

    Args:
        summary: Validation summary
        detailed: Show detailed information
        collection_results: Collection-specific validation results
    """
    print()
    print("=" * 70)
    print("📋 Project Structure Validation")
    print("=" * 70)
    print()
    print(f"Project directory: {summary['project_dir']}")
    print()

    # Print successes
    if summary['successes']:
        print("✅ Valid Configuration:")
        print("-" * 70)
        for success in summary['successes']:
            print(f"  {success}")
        print()

    # Print warnings
    if summary['warnings']:
        print("⚠️  Warnings (optional items):")
        print("-" * 70)
        for warning in summary['warnings']:
            print(f"  {warning}")
        print()

    # Print issues
    if summary['issues']:
        print("❌ Issues (must be fixed):")
        print("-" * 70)
        for issue in summary['issues']:
            print(f"  {issue}")
        print()

    # Print collection-specific results
    if collection_results:
        print("📚 Collection Validation:")
        print("-" * 70)
        for result in collection_results:
            print(f"\n  Collection: {result['collection']}")
            for success in result['successes']:
                print(f"    {success}")
            for warning in result['warnings']:
                print(f"    {warning}")
            for issue in result['issues']:
                print(f"    {issue}")
        print()

    # Summary
    print("=" * 70)
    if summary['is_valid']:
        print("✅ Project structure is valid!")
    else:
        print(f"❌ Found {summary['total_issues']} issue(s) that must be fixed")

    if summary['warnings']:
        print(f"⚠️  {len(summary['warnings'])} warning(s) - optional items")

    print()

    # Recommendations
    if summary['issues'] or summary['warnings']:
        print("💡 Recommendations:")
        print("-" * 70)
        if summary['issues']:
            print("  • Fix critical issues with: verse-validate --fix")
            print("  • Or manually create missing directories and files")
        if any('API' in w for w in summary['warnings']):
            print("  • Configure API keys in .env file")
        if any('collections.yml' in w for w in summary['warnings']):
            print("  • Define your collections in _data/collections.yml")
        print()


def main():
    """Main entry point for verse-validate command."""
    parser = argparse.ArgumentParser(
        description="Validate project structure and configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate current project
  verse-validate

  # Validate with detailed information
  verse-validate --detailed

  # Preview what would be fixed (dry-run)
  verse-validate --fix --dry-run

  # Auto-fix common issues
  verse-validate --fix

  # Check specific collection
  verse-validate --collection hanuman-chalisa

  # JSON output for scripting
  verse-validate --format json

For more information:
  https://github.com/sanatan-learnings/sanatan-verse-sdk/blob/main/docs/usage.md
        """
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed validation information"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix common issues (creates missing directories)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them (use with --fix)"
    )

    parser.add_argument(
        "--collection",
        help="Validate specific collection only"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    args = parser.parse_args()

    try:
        project_dir = Path.cwd()
        validator = ProjectValidator(project_dir)

        # Auto-fix if requested
        if args.fix:
            if args.dry_run:
                print("🔍 Dry-run mode: Previewing changes (no files will be modified)...")
            else:
                print("🔧 Auto-fixing common issues...")
            actions = validator.fix_common_issues(dry_run=args.dry_run)
            if actions:
                for action in actions:
                    print(f"  {'→' if args.dry_run else '✓'} {action}")
            else:
                print(f"  ✓ No issues to fix")
            print()
        elif args.dry_run:
            print("⚠️  Note: --dry-run requires --fix flag")
            print()

        # Run validation
        validator.validate_directory_structure()
        validator.validate_configuration_files()

        # Validate collections
        collection_results = None
        if args.collection:
            collection_results = [validator.validate_collection(args.collection)]
        elif not args.collection:
            collection_results = validator.validate_all_collections()

        # Get summary
        summary = validator.get_validation_summary()

        # Output results
        if args.format == "json":
            output = summary.copy()
            if collection_results:
                output['collections'] = collection_results
            print(json.dumps(output, indent=2))
        else:
            print_validation_results(summary, args.detailed, collection_results)

        # Exit with appropriate code
        sys.exit(0 if summary['is_valid'] else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
