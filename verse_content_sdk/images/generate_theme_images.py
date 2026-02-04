#!/usr/bin/env python3
"""
Generate verse images using DALL-E 3.

This script combines scene descriptions from docs/image-prompts.md with visual
style specifications from docs/themes/<theme-name>.yml to generate images
using OpenAI's DALL-E 3 API.

Supports both:
- Chapter-based texts (Bhagavad Gita): "Chapter X, Verse Y" format
- Simple verse texts (Hanuman Chalisa): "Verse X" format

Architecture:
    1. Scene descriptions (what's happening) come from docs/image-prompts.md
    2. Visual style (colors, character design, mood) comes from docs/themes/*.yml
    3. Script combines both to create complete DALL-E 3 prompts

Usage:
    verse-images --theme-name modern-minimalist

Requirements:
    pip install openai requests pillow pyyaml
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import requests
from openai import OpenAI
try:
    import yaml
except ImportError:
    yaml = None

# Configuration
# Use current working directory (where the user runs the command)
# This allows the SDK to work with any project structure
PROJECT_DIR = Path.cwd()
DOCS_DIR = PROJECT_DIR / "docs"
IMAGES_DIR = PROJECT_DIR / "images"
THEMES_DIR = DOCS_DIR / "themes"

# DALL-E 3 Configuration
DALLE_MODEL = "dall-e-3"
IMAGE_SIZE = "1024x1792"  # Options: 1024x1024, 1024x1792, 1792x1024 (portrait 1024x1792 recommended, crop to 1024x1536)
IMAGE_QUALITY = "standard"  # Options: standard, hd
IMAGE_STYLE = "natural"  # Options: natural, vivid


class ImageGenerator:
    """Generate images using DALL-E 3 API."""

    def __init__(self, api_key: str, collection: str, theme: str, style_modifier: str = "", theme_config: Optional[Dict] = None):
        """
        Initialize the image generator.

        Args:
            api_key: OpenAI API key
            collection: Collection key (e.g., 'hanuman-chalisa', 'sundar-kaand')
            theme: Theme name (e.g., 'modern-minimalist', 'kids-friendly')
            style_modifier: Additional style description to append to base prompts
            theme_config: Optional theme configuration from YAML file
        """
        self.client = OpenAI(api_key=api_key)
        self.collection = collection
        self.theme = theme
        self.theme_config = theme_config or {}

        # Get style modifier from theme config or parameter
        if not style_modifier and theme_config:
            generation = theme_config.get('theme', {}).get('generation', {})
            style_modifier = generation.get('style_modifier', '').strip()

        self.style_modifier = style_modifier

        # Set collection-specific paths
        self.prompts_file = DOCS_DIR / "image-prompts" / f"{collection}.md"
        self.output_dir = IMAGES_DIR / collection / theme

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Output directory: {self.output_dir}")

    def parse_prompts_file(self) -> Dict[str, str]:
        """
        Parse the image-prompts.md file to extract scene descriptions.

        Returns:
            Dictionary mapping filename to scene description text
        """
        if not self.prompts_file.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_file}")

        with open(self.prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()

        prompts = {}

        # Extract title page scene description
        title_match = re.search(
            r'### Title Page.*?\*\*Scene Description\*\*:\s*(.*?)(?=\n---|\n###|\Z)',
            content,
            re.DOTALL
        )
        if title_match:
            prompts['title-page.png'] = title_match.group(1).strip()

        # Extract opening doha scene descriptions
        doha_sections = re.findall(
            r'### Opening Doha (\d+):.*?\*\*Scene Description\*\*:\s*(.*?)(?=\n---|\n###|\Z)',
            content,
            re.DOTALL
        )
        for doha_num, scene_desc in doha_sections:
            filename = f'opening-doha-{doha_num.zfill(2)}.png'
            prompts[filename] = scene_desc.strip()

        # Extract verse scene descriptions
        # Try Chapter X, Verse Y format first (for Bhagavad Gita)
        chapter_verse_sections = re.findall(
            r'### Chapter (\d+),\s*Verse (\d+).*?\*\*Scene Description\*\*:\s*(.*?)(?=\n---|\n###|\Z)',
            content,
            re.DOTALL
        )
        if chapter_verse_sections:
            for chapter_num, verse_num, scene_desc in chapter_verse_sections:
                filename = f'chapter-{chapter_num.zfill(2)}-verse-{verse_num.zfill(2)}.png'
                prompts[filename] = scene_desc.strip()
        else:
            # Fall back to simple Verse X format (for Hanuman Chalisa)
            verse_sections = re.findall(
                r'### Verse (\d+):.*?\*\*Scene Description\*\*:\s*(.*?)(?=\n---|\n###|\Z)',
                content,
                re.DOTALL
            )
            for verse_num, scene_desc in verse_sections:
                filename = f'verse-{verse_num.zfill(2)}.png'
                prompts[filename] = scene_desc.strip()

        # Extract closing doha scene description
        closing_match = re.search(
            r'### Closing Doha:.*?\*\*Scene Description\*\*:\s*(.*?)(?=\n---|\n###|\Z)',
            content,
            re.DOTALL
        )
        if closing_match:
            prompts['closing-doha.png'] = closing_match.group(1).strip()

        print(f"✓ Parsed {len(prompts)} scene descriptions from {self.prompts_file.name}")
        return prompts

    def build_full_prompt(self, scene_description: str) -> str:
        """
        Build the full prompt by combining scene description with theme style.

        Args:
            scene_description: The scene description from docs/image-prompts.md

        Returns:
            Complete prompt for DALL-E 3
        """
        prompt_parts = []

        # Add scene description
        prompt_parts.append(scene_description)

        # Add visual style modifier
        if self.style_modifier:
            prompt_parts.append(f"Visual Style: {self.style_modifier}")

        return "\n\n".join(prompt_parts)

    def generate_image(self, filename: str, prompt: str, retry_count: int = 3) -> bool:
        """
        Generate a single image using DALL-E 3.

        Args:
            filename: Output filename (e.g., 'verse-01.png')
            prompt: The prompt for image generation
            retry_count: Number of retries on failure

        Returns:
            True if successful, False otherwise
        """
        output_path = self.output_dir / filename

        # Skip if file already exists
        if output_path.exists():
            print(f"⊙ Skipping {filename} (already exists)")
            return True

        full_prompt = self.build_full_prompt(prompt)

        print(f"\n→ Generating {filename}...")
        print(f"  Scene: {prompt[:80]}...")

        for attempt in range(retry_count):
            try:
                # Generate image using DALL-E 3
                response = self.client.images.generate(
                    model=DALLE_MODEL,
                    prompt=full_prompt,
                    size=IMAGE_SIZE,
                    quality=IMAGE_QUALITY,
                    style=IMAGE_STYLE,
                    n=1
                )

                # Download the image
                image_url = response.data[0].url
                image_data = requests.get(image_url).content

                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(image_data)

                file_size = len(image_data) / 1024  # KB
                print(f"✓ Generated {filename} ({file_size:.1f} KB)")

                # Rate limiting - DALL-E 3 has rate limits
                time.sleep(2)

                return True

            except Exception as e:
                print(f"✗ Error generating {filename} (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

        return False

    def generate_all_images(self, start_from: Optional[str] = None) -> None:
        """
        Generate all images for the theme.

        Args:
            start_from: Optional filename to start from (useful for resuming)
        """
        prompts = self.parse_prompts_file()

        # Detect format: check if we have chapter-verse format or simple verse format
        has_chapters = any('chapter-' in f for f in prompts.keys())

        if has_chapters:
            # Bhagavad Gita format: sort by chapter and verse
            # Extract all chapter-verse combinations from prompts and sort them
            ordered_files = sorted(
                [f for f in prompts.keys() if f.startswith('chapter-')],
                key=lambda x: (
                    int(re.search(r'chapter-(\d+)', x).group(1)),
                    int(re.search(r'verse-(\d+)', x).group(1))
                )
            )
        else:
            # Hanuman Chalisa format: original sorting logic
            ordered_files = ['title-page.png']
            ordered_files += [f'opening-doha-{i:02d}.png' for i in range(1, 3)]
            ordered_files += [f'verse-{i:02d}.png' for i in range(1, 41)]
            ordered_files += ['closing-doha.png']

            # Filter to only include files with prompts
            ordered_files = [f for f in ordered_files if f in prompts]

        # Start from specific file if requested
        if start_from:
            try:
                start_idx = ordered_files.index(start_from)
                ordered_files = ordered_files[start_idx:]
                print(f"✓ Resuming from {start_from}")
            except ValueError:
                print(f"⚠ Warning: {start_from} not found, starting from beginning")

        print(f"\n{'='*60}")
        print(f"Generating {len(ordered_files)} images for theme: {self.theme}")
        print(f"Output directory: {self.output_dir}")
        print(f"Style modifier: {self.style_modifier or '(none)'}")
        print(f"{'='*60}\n")

        successful = 0
        failed = []

        for idx, filename in enumerate(ordered_files, 1):
            print(f"\n[{idx}/{len(ordered_files)}] ", end='')

            if self.generate_image(filename, prompts[filename]):
                successful += 1
            else:
                failed.append(filename)

        # Summary
        print(f"\n{'='*60}")
        print(f"Generation complete!")
        print(f"✓ Successful: {successful}/{len(ordered_files)}")
        if failed:
            print(f"✗ Failed: {len(failed)}")
            for f in failed:
                print(f"  - {f}")
        print(f"{'='*60}\n")

        if successful == len(ordered_files):
            print(f"🎉 All images generated successfully!")
            print(f"\nNext steps:")
            print(f"1. Review images in: {self.output_dir}")
            print(f"2. Update _data/themes.yml with your new theme")
            print(f"3. Test the theme on your local Jekyll site")
            print(f"4. Commit and push to GitHub")


def validate_collection(collection: str, project_dir: Path = PROJECT_DIR) -> bool:
    """Validate that collection exists."""
    verses_dir = project_dir / "_verses" / collection
    if not verses_dir.exists():
        print(f"✗ Error: Collection directory not found: {verses_dir}")
        print(f"\nAvailable collections:")
        list_collections()
        return False

    return True


def list_collections(project_dir: Path = PROJECT_DIR):
    """List available collections."""
    verses_base = project_dir / "_verses"
    if not verses_base.exists():
        print("No _verses directory found")
        return

    collections = [d for d in verses_base.iterdir() if d.is_dir()]
    if not collections:
        print("No collections found in _verses/")
        return

    print("\nAvailable collections:")
    for coll_dir in sorted(collections):
        verse_count = len(list(coll_dir.glob("*.md")))
        themes_dir = THEMES_DIR / coll_dir.name
        theme_count = len(list(themes_dir.glob("*.yml"))) if themes_dir.exists() else 0
        print(f"  ✓ {coll_dir.name:35s} ({verse_count} verses, {theme_count} themes)")


def load_theme_config(collection: str, theme: str) -> Optional[Dict]:
    """
    Load theme configuration from YAML file if it exists.

    Args:
        collection: Collection key
        theme: Theme name

    Returns:
        Theme configuration dict or None if not found
    """
    if not yaml:
        return None

    theme_file = THEMES_DIR / collection / f"{theme}.yml"
    if not theme_file.exists():
        print(f"⚠ Warning: Theme file not found: {theme_file}")
        return None

    try:
        with open(theme_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            print(f"✓ Loaded theme configuration from {theme_file}")
            return config
    except Exception as e:
        print(f"⚠ Warning: Failed to load theme config: {e}")
        return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate verse images using DALL-E 3 (supports both chapter-based and simple verse formats)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from theme YAML (automatically reads style from docs/themes/modern-minimalist.yml)
  python scripts/generate_theme_images.py --theme-name modern-minimalist

  # Generate with custom style (overrides theme YAML)
  python scripts/generate_theme_images.py \\
    --theme-name traditional-art \\
    --style "traditional Indian devotional art style with rich colors and gold accents"

  # Generate watercolor style
  python scripts/generate_theme_images.py \\
    --theme-name watercolor \\
    --style "soft watercolor painting style with gentle colors and artistic brush strokes"

  # Resume from a specific image
  python scripts/generate_theme_images.py \\
    --theme-name my-theme \\
    --start-from verse-15.png

Configuration:
  Set your OpenAI API key:
    export OPENAI_API_KEY='your-api-key-here'

  Or use .env file (requires python-dotenv):
    OPENAI_API_KEY=your-api-key-here

Theme YAML Files:
  Place theme specifications in docs/themes/<theme-name>.yml
  The script will automatically read generation settings from the YAML file
  Use --style to override the theme's default style modifier

Cost Estimate:
  - DALL-E 3 Standard: $0.040 per image
  - DALL-E 3 HD: $0.080 per image
  - 47 images × $0.040 = $1.88 (standard quality)
  - 47 images × $0.080 = $3.76 (HD quality)
        """
    )

    parser.add_argument(
        '--collection',
        required=False,  # Not required if --list-collections
        help='Collection key (e.g., hanuman-chalisa, sundar-kaand, sankat-mochan-hanumanashtak)'
    )

    parser.add_argument(
        '--theme',
        required=False,  # Not required if --list-collections
        help='Theme name (e.g., modern-minimalist, kids-friendly, traditional)'
    )

    parser.add_argument(
        '--verse',
        default=None,
        help='Generate image for specific verse only (e.g., verse_01, chaupai_03)'
    )

    parser.add_argument(
        '--style',
        default='',
        help='Style modifier to override theme YAML style'
    )

    parser.add_argument(
        '--list-collections',
        action='store_true',
        help='List available collections and exit'
    )

    parser.add_argument(
        '--api-key',
        default=None,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )

    parser.add_argument(
        '--start-from',
        default=None,
        help='Filename to start from (useful for resuming, e.g., verse-15.png)'
    )

    parser.add_argument(
        '--size',
        choices=['1024x1024', '1024x1792', '1792x1024'],
        default='1024x1792',
        help='Image size (default: 1024x1792 portrait, crop to 1024x1536 for final images)'
    )

    parser.add_argument(
        '--quality',
        choices=['standard', 'hd'],
        default='standard',
        help='Image quality (default: standard, hd costs 2x)'
    )

    parser.add_argument(
        '--style-type',
        choices=['natural', 'vivid'],
        default='natural',
        help='DALL-E style type (default: natural)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regenerate ALL images (deletes entire theme directory with confirmation)'
    )
    parser.add_argument(
        '--regenerate',
        default=None,
        metavar='FILES',
        help='Regenerate specific images (comma-separated, e.g., verse-10.png,verse-25.png)'
    )

    args = parser.parse_args()

    # Handle --list-collections
    if args.list_collections:
        list_collections()
        sys.exit(0)

    # Validate required parameters
    if not args.collection:
        parser.error("--collection is required")
    if not args.theme:
        parser.error("--theme is required")

    # Get API key
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not found!")
        print("\nPlease provide API key via:")
        print("  1. --api-key argument")
        print("  2. OPENAI_API_KEY environment variable")
        print("\nExample:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("  verse-images --collection hanuman-chalisa --theme modern-minimalist")
        sys.exit(1)

    # Validate collection
    if not validate_collection(args.collection):
        sys.exit(1)

    # Check for conflicting options
    if args.force and args.regenerate:
        print("Error: Cannot use --force and --regenerate together")
        print("Use --force to regenerate ALL images, or --regenerate for specific images")
        sys.exit(1)

    # Update global configuration
    global IMAGE_SIZE, IMAGE_QUALITY, IMAGE_STYLE
    IMAGE_SIZE = args.size
    IMAGE_QUALITY = args.quality
    IMAGE_STYLE = args.style_type

    # Validate theme name
    if not re.match(r'^[a-z0-9-]+$', args.theme):
        print("Error: Theme name must contain only lowercase letters, numbers, and hyphens")
        sys.exit(1)

    # Handle --force option
    if args.force:
        images_dir = IMAGES_DIR / args.collection / args.theme
        if images_dir.exists():
            image_files = list(images_dir.glob("*.png"))
            if image_files:
                print(f"\n⚠️  WARNING: Force regeneration will delete {len(image_files)} existing images!")
                print(f"Theme directory: {images_dir}")
                print()
                response = input("Are you sure you want to delete and regenerate ALL images? (y/n): ")

                if response.lower() in ['y', 'yes']:
                    print()
                    print("Deleting existing theme directory...")
                    import shutil
                    shutil.rmtree(images_dir)
                    print(f"✓ Deleted: {images_dir}")
                    print("Will now regenerate all images...")
                    print()
                else:
                    print("Aborted. No images were deleted.")
                    sys.exit(0)
            else:
                print("No existing images found. Will generate all images.")
                print()
        else:
            print("Theme directory not found. Will create and generate all images.")
            print()

    # Handle --regenerate option
    if args.regenerate:
        images_dir = IMAGES_DIR / args.collection / args.theme
        if not images_dir.exists():
            print(f"Error: Theme directory not found: {images_dir}")
            sys.exit(1)

        print("Preparing to regenerate specific images...")
        files_to_regenerate = [f.strip() for f in args.regenerate.split(',')]
        deleted_count = 0

        for filename in files_to_regenerate:
            file_path = images_dir / filename
            if file_path.exists():
                file_path.unlink()
                print(f"  ✓ Deleted: {filename}")
                deleted_count += 1
            else:
                print(f"  ⚠ Not found (will generate): {filename}")

        print()
        if deleted_count > 0:
            print(f"Deleted {deleted_count} existing image(s).")
        print("Will now regenerate missing images...")
        print()

    # Try to load theme configuration
    theme_config = load_theme_config(args.collection, args.theme)

    # Apply theme config defaults if available and not overridden
    if theme_config and not args.style:
        generation = theme_config.get('theme', {}).get('generation', {})
        dalle_params = generation.get('dalle_params', {})

        # Override command line args with theme defaults if not explicitly set
        if args.size == '1024x1792' and 'size' in dalle_params:
            IMAGE_SIZE = dalle_params['size']
            print(f"✓ Using theme size: {IMAGE_SIZE}")

        if args.quality == 'standard' and 'quality' in dalle_params:
            IMAGE_QUALITY = dalle_params['quality']
            print(f"✓ Using theme quality: {IMAGE_QUALITY}")

        if args.style_type == 'natural' and 'style' in dalle_params:
            IMAGE_STYLE = dalle_params['style']
            print(f"✓ Using theme style: {IMAGE_STYLE}")

    # Create generator and run
    try:
        generator = ImageGenerator(api_key, args.collection, args.theme, args.style, theme_config)
        generator.generate_all_images(start_from=args.start_from)
    except KeyboardInterrupt:
        print("\n\n⚠ Generation interrupted by user")
        print("You can resume by running the script with --start-from flag")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
