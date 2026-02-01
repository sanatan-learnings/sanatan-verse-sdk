#!/usr/bin/env python3
"""
Unified verse content generator - generates text, images, and audio for a specific verse.

This command orchestrates the generation of all content types for a verse:
1. Text content (verse frontmatter and fields) using GPT-4
2. Image using DALL-E 3
3. Audio pronunciation using ElevenLabs

Usage:
    # Generate everything for Chapter 2, Verse 47
    verse-generate --chapter 2 --verse 47 --all

    # Generate only image and audio
    verse-generate --chapter 2 --verse 47 --image --audio

    # Generate only text
    verse-generate --chapter 2 --verse 47 --text

    # For texts without chapters (like Hanuman Chalisa)
    verse-generate --verse 15 --all

Requirements:
    - OPENAI_API_KEY environment variable
    - ELEVENLABS_API_KEY environment variable (for audio)
"""

import os
import sys
import argparse
import subprocess
import yaml
from pathlib import Path
from typing import Optional, Dict

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

# Initialize OpenAI client
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_chapter_names(chapter: int) -> tuple[Optional[str], Optional[str]]:
    """Fetch chapter names (English and Hindi) from GPT-4."""
    print(f"\n{'='*60}")
    print("FETCHING CHAPTER NAMES FROM GPT-4")
    print(f"{'='*60}\n")

    if not openai_client:
        print("Error: OPENAI_API_KEY not set")
        return None, None

    print(f"Fetching chapter names for Chapter {chapter}...")

    prompt = f"""What is the name of Chapter {chapter} of the Bhagavad Gita?

Provide ONLY:
1. English name (e.g., "Karma Yoga")
2. Hindi name in Devanagari (e.g., "कर्म योग")

Format your response as:
English: [name]
Hindi: [name in Devanagari]"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Bhagavad Gita scholar. Provide accurate chapter names."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )

        content = response.choices[0].message.content.strip()

        # Parse response
        english_name = None
        hindi_name = None

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('English:'):
                english_name = line.replace('English:', '').strip()
            elif line.startswith('Hindi:'):
                hindi_name = line.replace('Hindi:', '').strip()

        if english_name and hindi_name:
            print(f"\n✓ Fetched chapter names:")
            print(f"  English: {english_name}")
            print(f"  Hindi: {hindi_name}")
            print()
            return english_name, hindi_name
        else:
            print("✗ Could not parse chapter names from response")
            return None, None

    except Exception as e:
        print(f"✗ Error fetching chapter names: {e}")
        return None, None


def fetch_sanskrit_text(chapter: Optional[int], verse: int) -> Optional[str]:
    """Fetch Sanskrit text from GPT-4 for the specified verse."""
    print(f"\n{'='*60}")
    print("FETCHING SANSKRIT TEXT FROM GPT-4")
    print(f"{'='*60}\n")

    if not openai_client:
        print("Error: OPENAI_API_KEY not set")
        return None

    if chapter:
        verse_ref = f"Chapter {chapter}, Verse {verse}"
    else:
        verse_ref = f"Verse {verse}"

    print(f"Fetching Sanskrit text for {verse_ref}...")

    prompt = f"""Please provide the exact Sanskrit text in Devanagari script for Bhagavad Gita {verse_ref}.

Provide ONLY the Sanskrit verse text in Devanagari, nothing else. No transliteration, no translation, no explanations - just the pure Devanagari text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Bhagavad Gita scholar. Provide exact Sanskrit verses in Devanagari script."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for accuracy
            max_tokens=200
        )

        sanskrit_text = response.choices[0].message.content.strip()

        # Remove any extra formatting or explanations
        lines = sanskrit_text.split('\n')
        sanskrit_lines = [line.strip() for line in lines if line.strip() and any('\u0900' <= c <= '\u097F' for c in line)]
        sanskrit_text = '\n'.join(sanskrit_lines)

        if sanskrit_text:
            print(f"\n✓ Fetched Sanskrit text:")
            print(f"  {sanskrit_text[:80]}...")
            print()
            return sanskrit_text
        else:
            print("✗ Could not extract Sanskrit text from response")
            return None

    except Exception as e:
        print(f"✗ Error fetching Sanskrit text: {e}")
        return None


def generate_image(chapter: Optional[int], verse: int, theme: str) -> bool:
    """Generate image for the specified verse."""
    print(f"\n{'='*60}")
    print("STEP 1: GENERATING IMAGE")
    print(f"{'='*60}\n")

    # First, ensure the scene description exists in docs/image-prompts.md
    prompts_file = Path.cwd() / "docs" / "image-prompts.md"

    if not prompts_file.exists():
        print(f"Error: {prompts_file} not found")
        print("Please create scene descriptions in docs/image-prompts.md first")
        return False

    # Read prompts file to check if verse exists
    with open(prompts_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if chapter:
        search_pattern = f"### Chapter {chapter}, Verse {verse}"
    else:
        search_pattern = f"### Verse {verse}"

    if search_pattern not in content:
        print(f"Error: Scene description for {search_pattern} not found in {prompts_file}")
        print(f"\nPlease add a scene description like:")
        print(f"\n{search_pattern}")
        print("**Scene Description**:")
        print("[Describe the visual scene here...]")
        return False

    print(f"✓ Found scene description for {search_pattern}")

    # Construct the filename to regenerate
    if chapter:
        filename = f"chapter-{chapter:02d}-verse-{verse:02d}.png"
    else:
        filename = f"verse-{verse:02d}.png"

    print(f"✓ Will generate: {filename}")
    print(f"✓ Theme: {theme}")

    # Run verse-images command with --regenerate flag
    cmd = [
        "verse-images",
        "--theme-name", theme,
        "--regenerate", filename
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Image generated successfully: images/{theme}/{filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating image: {e}")
        return False


def generate_audio(chapter: Optional[int], verse: int) -> bool:
    """Generate audio for the specified verse."""
    print(f"\n{'='*60}")
    print("STEP 2: GENERATING AUDIO")
    print(f"{'='*60}\n")

    # Check if verse file exists
    verses_dir = Path.cwd() / "_verses"

    if chapter:
        verse_file = verses_dir / f"chapter_{chapter:02d}_verse_{verse:02d}.md"
    else:
        verse_file = verses_dir / f"verse_{verse:02d}.md"

    if not verse_file.exists():
        print(f"Error: Verse file not found: {verse_file}")
        print("Please create the verse markdown file first")
        return False

    print(f"✓ Found verse file: {verse_file}")

    # Construct the audio filenames to regenerate
    if chapter:
        base_name = f"chapter_{chapter:02d}_verse_{verse:02d}"
    else:
        base_name = f"verse_{verse:02d}"

    filenames = f"{base_name}_full.mp3,{base_name}_slow.mp3"

    print(f"✓ Will generate: {base_name}_full.mp3 and {base_name}_slow.mp3")

    # Run verse-audio command with --regenerate flag
    cmd = [
        "verse-audio",
        "--regenerate", filenames
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Audio generated successfully:")
        print(f"  - audio/{base_name}_full.mp3")
        print(f"  - audio/{base_name}_slow.mp3")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating audio: {e}")
        return False


def generate_image_prompt(chapter: Optional[int], verse: int, sanskrit: str, chapter_name_en: Optional[str] = None) -> bool:
    """Generate scene description for image generation using GPT-4."""
    print(f"\n{'='*60}")
    print("GENERATING IMAGE PROMPT (Scene Description)")
    print(f"{'='*60}\n")

    if not openai_client:
        print("Error: OPENAI_API_KEY not set")
        return False

    # Check if prompts file exists
    prompts_file = Path.cwd() / "docs" / "image-prompts.md"
    if not prompts_file.exists():
        print(f"Error: {prompts_file} not found")
        print("Creating docs/image-prompts.md...")
        prompts_file.parent.mkdir(parents=True, exist_ok=True)
        prompts_file.write_text("# Bhagavad Gita Image Prompts\n\n")

    # Read existing content
    with open(prompts_file, 'r', encoding='utf-8') as f:
        existing_content = f.read()

    # Check if prompt already exists
    if chapter:
        search_pattern = f"### Chapter {chapter}, Verse {verse}"
    else:
        search_pattern = f"### Verse {verse}"

    if search_pattern in existing_content:
        print(f"✓ Scene description already exists for {search_pattern}")
        return True

    print(f"Generating scene description using GPT-4...")
    print(f"Sanskrit verse: {sanskrit[:50]}...")

    # Create GPT-4 prompt
    system_prompt = """You are an expert in Bhagavad Gita imagery and Indian spiritual art. Your task is to create vivid, detailed scene descriptions for generating images using DALL-E 3.

The scene descriptions should:
- Be 3-5 sentences long
- Include specific visual details: setting, characters, poses, expressions, clothing, colors
- Specify lighting and mood (golden hour, ethereal glow, dramatic, peaceful, etc.)
- Balance realistic and symbolic/spiritual elements
- Include traditional Indian visual elements
- Convey the spiritual essence of the verse
- Be concrete and visual (avoid abstract concepts)

Example good description:
"Lord Krishna stands in a teaching pose on the battlefield, his divine form radiating wisdom and serenity, with one hand raised in a gesture of instruction (abhaya mudra). He is speaking to Arjuna, who sits attentively on his chariot, bow resting beside him, listening intently to Krishna's profound teaching. The scene captures the essence of Karma Yoga - around them, symbolic visual elements represent the teaching: on one side, hands performing various actions (working, serving, creating) glowing with golden light representing 'right to action'; on the other side, fruits and outcomes fade into mist representing 'detachment from results.'"
"""

    user_prompt = f"""Create a scene description for an image representing this Bhagavad Gita verse:

Chapter: {chapter if chapter else 'N/A'}
Verse: {verse}
{f'Chapter Theme: {chapter_name_en}' if chapter_name_en else ''}

Sanskrit Text:
{sanskrit}

Generate a vivid 3-5 sentence scene description suitable for DALL-E 3 image generation. Focus on visual, concrete details that capture the spiritual essence of this verse."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        scene_description = response.choices[0].message.content.strip()
        print(f"\n✓ Generated scene description:")
        print(f"  {scene_description[:100]}...\n")

        # Append to prompts file
        new_entry = f"\n---\n\n{search_pattern}\n\n**Scene Description**:\n{scene_description}\n"

        with open(prompts_file, 'a', encoding='utf-8') as f:
            f.write(new_entry)

        print(f"✓ Added scene description to {prompts_file}")
        return True

    except Exception as e:
        print(f"✗ Error generating scene description: {e}")
        return False


def generate_text(chapter: Optional[int], verse: int, sanskrit: str, chapter_name_en: Optional[str] = None, chapter_name_hi: Optional[str] = None) -> bool:
    """Generate text content for the specified verse using GPT-4."""
    print(f"\n{'='*60}")
    print("GENERATING TEXT CONTENT (Verse File)")
    print(f"{'='*60}\n")

    if not openai_client:
        print("Error: OPENAI_API_KEY not set")
        return False

    # Check if verse file already exists
    verses_dir = Path.cwd() / "_verses"
    verses_dir.mkdir(exist_ok=True)

    if chapter:
        verse_file = verses_dir / f"chapter_{chapter:02d}_verse_{verse:02d}.md"
        filename_base = f"chapter_{chapter:02d}_verse_{verse:02d}"
        image_filename = f"chapter-{chapter:02d}-verse-{verse:02d}.png"
    else:
        verse_file = verses_dir / f"verse_{verse:02d}.md"
        filename_base = f"verse_{verse:02d}"
        image_filename = f"verse-{verse:02d}.png"

    if verse_file.exists():
        print(f"✓ Verse file already exists: {verse_file}")
        response = input("Overwrite? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("Skipped.")
            return True

    print(f"Generating verse content using GPT-4...")
    print(f"Sanskrit verse: {sanskrit[:50]}...")

    # Create GPT-4 prompt for comprehensive verse analysis
    system_prompt = """You are an expert scholar of the Bhagavad Gita with deep knowledge of Sanskrit, Hindu philosophy, and spiritual teachings. Your task is to create comprehensive, accurate, and accessible content for a Bhagavad Gita verse.

Generate content in a structured YAML-like format that will be easy to parse. Include:
1. Transliteration (IAST format)
2. Word-by-word meanings (Sanskrit word, roman transliteration, English and Hindi meanings)
3. Literal translation (English and Hindi)
4. Interpretive meaning (2-3 paragraphs explaining the deeper spiritual significance - English and Hindi)
5. Story/context (2-3 paragraphs explaining the narrative context - English and Hindi)
6. Practical application (specific examples in daily life - English and Hindi)

Be accurate, insightful, and accessible to modern readers."""

    user_prompt = f"""Generate comprehensive content for this Bhagavad Gita verse:

Chapter: {chapter if chapter else 'N/A'}
Verse: {verse}
{f'Chapter Name: {chapter_name_en} / {chapter_name_hi}' if chapter_name_en else ''}

Sanskrit (Devanagari):
{sanskrit}

Please provide:
1. Transliteration (IAST format with diacritics)
2. Word meanings (list each significant word with roman, English, and Hindi meanings)
3. Literal translation (English and Hindi)
4. Interpretive meaning (English and Hindi) - 2-3 paragraphs explaining the spiritual significance
5. Story/context (English and Hindi) - 2-3 paragraphs explaining the narrative context
6. Practical application (English and Hindi) - specific examples for daily life

Format your response as clear sections I can parse."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        generated_content = response.choices[0].message.content.strip()
        print(f"\n✓ Generated content ({len(generated_content)} characters)")

        # Parse the generated content and create the markdown file
        # For now, create a template that includes the generated content
        # In production, you'd parse this more carefully

        # Get previous/next verse paths
        if chapter:
            prev_verse_path = f"/verses/chapter-{chapter:02d}-verse-{verse-1:02d}/" if verse > 1 else ""
            next_verse_path = f"/verses/chapter-{chapter:02d}-verse-{verse+1:02d}/"
            title_en = f"Chapter {chapter}, Verse {verse}"
            title_hi = f"अध्याय {chapter}, श्लोक {verse}"
        else:
            prev_verse_path = f"/verses/verse-{verse-1:02d}/" if verse > 1 else ""
            next_verse_path = f"/verses/verse-{verse+1:02d}/"
            title_en = f"Verse {verse}"
            title_hi = f"श्लोक {verse}"

        # Create frontmatter
        frontmatter = f"""---
layout: verse
title_en: "{title_en}"
title_hi: "{title_hi}"
chapter: {chapter if chapter else ''}
verse_number: {verse}
previous_verse: {prev_verse_path}
next_verse: {next_verse_path}
"""

        if chapter and chapter_name_en:
            frontmatter += f"""chapter_info:
  number: {chapter}
  name_en: "{chapter_name_en}"
  name_hi: "{chapter_name_hi or ''}"
"""

        frontmatter += f"""image: /images/modern-minimalist/{image_filename}
audio_full: /audio/{filename_base}_full.mp3
audio_slow: /audio/{filename_base}_slow.mp3

devanagari: |
  {sanskrit}

# TODO: Parse and format the AI-generated content below
# Generated content:
"""

        full_content = frontmatter + "\n" + generated_content + "\n---\n"

        # Write to file
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"\n✓ Created verse file: {verse_file}")
        print(f"\n⚠️  NOTE: The AI-generated content is included as comments.")
        print(f"   Please review and format it properly into the verse structure.")
        print(f"   See existing verse files for the expected format.")

        return True

    except Exception as e:
        print(f"✗ Error generating text content: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate text, images, and audio for a specific verse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simplest usage - everything auto-fetched from GPT-4
  verse-generate --chapter 1 --verse 3 --all

  # Generate everything for Chapter 2, Verse 47
  verse-generate --chapter 2 --verse 47 --all

  # Generate with custom Sanskrit text (chapter names still auto-fetched)
  verse-generate --chapter 2 --verse 47 --all \\
    --sanskrit "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।..."

  # Generate only image prompt
  verse-generate --chapter 3 --verse 10 --prompt

  # Generate only text content
  verse-generate --chapter 3 --verse 10 --text

  # Generate only image and audio (requires existing scene description and verse file)
  verse-generate --chapter 2 --verse 47 --image --audio

  # Override auto-fetched chapter names (optional)
  verse-generate --chapter 3 --verse 10 --all \\
    --chapter-name-en "Karma Yoga" \\
    --chapter-name-hi "कर्म योग"

  # For texts without chapters (Hanuman Chalisa) - provide Sanskrit
  verse-generate --verse 15 --all --sanskrit "..." --theme modern-minimalist

Environment Variables:
  OPENAI_API_KEY      - Required for auto-fetching and AI generation
  ELEVENLABS_API_KEY  - Required for audio generation

Note:
  Sanskrit text and chapter names are automatically fetched from GPT-4 if not provided.
  All you need is --chapter and --verse numbers!
        """
    )

    # Verse identification
    parser.add_argument(
        "--chapter",
        type=int,
        help="Chapter number (optional for texts like Hanuman Chalisa)",
        metavar="N"
    )
    parser.add_argument(
        "--verse",
        type=int,
        required=True,
        help="Verse number (required)",
        metavar="N"
    )

    # Content types
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate text, image prompt, image, and audio"
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Generate text content (verse file)"
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Generate image prompt (scene description)"
    )
    parser.add_argument(
        "--image",
        action="store_true",
        help="Generate image"
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Generate audio pronunciation"
    )

    # Input data
    parser.add_argument(
        "--sanskrit",
        type=str,
        help="Sanskrit verse text in Devanagari (optional - will be fetched from GPT-4 if not provided)",
        metavar="TEXT"
    )
    parser.add_argument(
        "--chapter-name-en",
        type=str,
        help="Chapter name in English (optional - will be fetched from GPT-4 if not provided)",
        metavar="NAME"
    )
    parser.add_argument(
        "--chapter-name-hi",
        type=str,
        help="Chapter name in Hindi (optional - will be fetched from GPT-4 if not provided)",
        metavar="NAME"
    )

    # Options
    parser.add_argument(
        "--theme",
        default="modern-minimalist",
        help="Theme name for image generation (default: modern-minimalist)",
        metavar="NAME"
    )

    args = parser.parse_args()

    # Validate options
    if not any([args.all, args.text, args.prompt, args.image, args.audio]):
        parser.error("Please specify at least one of: --all, --text, --prompt, --image, --audio")

    # Determine what to generate
    generate_text_flag = args.all or args.text
    generate_prompt_flag = args.all or args.prompt
    generate_image_flag = args.all or args.image
    generate_audio_flag = args.all or args.audio

    # Display header
    print("\n" + "="*60)
    print("VERSE CONTENT GENERATOR")
    print("="*60)

    if args.chapter:
        print(f"\nVerse: Chapter {args.chapter}, Verse {args.verse}")
    else:
        print(f"\nVerse: Verse {args.verse}")

    print(f"Theme: {args.theme}")
    if args.sanskrit:
        print(f"Sanskrit: {args.sanskrit[:50]}...")
    print("\nGenerating:")
    if generate_text_flag:
        print("  ✓ Text content (verse file)")
    if generate_prompt_flag:
        print("  ✓ Image prompt (scene description)")
    if generate_image_flag:
        print("  ✓ Image")
    if generate_audio_flag:
        print("  ✓ Audio")
    print()

    # Check API keys
    if generate_text_flag or generate_prompt_flag or generate_image_flag:
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set (required for text/prompt/image generation)")
            print("Set it in .env file or environment")
            sys.exit(1)

    if generate_audio_flag:
        if not os.getenv("ELEVENLABS_API_KEY"):
            print("Error: ELEVENLABS_API_KEY not set (required for audio generation)")
            print("Set it in .env file or environment")
            sys.exit(1)

    # Fetch Sanskrit text if needed but not provided
    sanskrit_text = args.sanskrit
    if (generate_text_flag or generate_prompt_flag) and not sanskrit_text:
        print("Sanskrit text not provided. Fetching from GPT-4...")
        sanskrit_text = fetch_sanskrit_text(args.chapter, args.verse)
        if not sanskrit_text:
            print("\n✗ Error: Could not fetch Sanskrit text from GPT-4")
            print("Please provide the Sanskrit text manually with --sanskrit flag")
            sys.exit(1)
        # Update args for display
        args.sanskrit = sanskrit_text

    # Fetch chapter names if needed but not provided
    chapter_name_en = args.chapter_name_en
    chapter_name_hi = args.chapter_name_hi
    if args.chapter and (generate_text_flag or generate_prompt_flag):
        if not chapter_name_en or not chapter_name_hi:
            print("Chapter names not provided. Fetching from GPT-4...")
            fetched_en, fetched_hi = fetch_chapter_names(args.chapter)
            if fetched_en and fetched_hi:
                chapter_name_en = chapter_name_en or fetched_en
                chapter_name_hi = chapter_name_hi or fetched_hi
                # Update args
                args.chapter_name_en = chapter_name_en
                args.chapter_name_hi = chapter_name_hi
            else:
                print("\n⚠ Warning: Could not fetch chapter names from GPT-4")
                print("Continuing without chapter names...")

    # Track success
    results = {
        'text': None,
        'prompt': None,
        'image': None,
        'audio': None
    }

    # Generate content (in order: text -> prompt -> image -> audio)
    try:
        if generate_text_flag:
            results['text'] = generate_text(
                args.chapter,
                args.verse,
                sanskrit_text,
                args.chapter_name_en,
                args.chapter_name_hi
            )

        if generate_prompt_flag:
            results['prompt'] = generate_image_prompt(
                args.chapter,
                args.verse,
                sanskrit_text,
                args.chapter_name_en
            )

        if generate_image_flag:
            results['image'] = generate_image(args.chapter, args.verse, args.theme)

        if generate_audio_flag:
            results['audio'] = generate_audio(args.chapter, args.verse)

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

    if generate_text_flag:
        status = "✓" if results['text'] else "✗"
        print(f"{status} Text (verse file): {'Success' if results['text'] else 'Failed'}")

    if generate_prompt_flag:
        status = "✓" if results['prompt'] else "✗"
        print(f"{status} Image prompt (scene description): {'Success' if results['prompt'] else 'Failed'}")

    if generate_image_flag:
        status = "✓" if results['image'] else "✗"
        print(f"{status} Image: {'Success' if results['image'] else 'Failed'}")

    if generate_audio_flag:
        status = "✓" if results['audio'] else "✗"
        print(f"{status} Audio: {'Success' if results['audio'] else 'Failed'}")

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
