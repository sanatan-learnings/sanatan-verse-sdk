#!/usr/bin/env python3
"""
Comprehensive help command - provides guidance on using sanatan-verse-sdk.

This command shows workflows, common commands, troubleshooting tips, and links to documentation.

Usage:
    verse-help
    verse-help --topic setup
    verse-help --topic workflows
    verse-help --topic commands
"""

import argparse
import sys
from pathlib import Path


def show_main_help():
    """Show main help screen with all topics."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      SANATAN VERSE SDK HELP                                ║
║                  Generate Multimedia Content for Spiritual Texts            ║
╚════════════════════════════════════════════════════════════════════════════╝

📖 QUICK START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

New Project (Complete Setup in 2 Minutes)
──────────────────────────────────────────────────────────────────────────────

  1. Install sanatan-verse-sdk:
     pip install sanatan-verse-sdk

  2. Initialize project with collection:
     verse-init --project-name my-project --collection hanuman-chalisa
     cd my-project

  3. Configure API keys:
     cp .env.example .env
     # Edit .env and add your API keys from:
     # - OpenAI: https://platform.openai.com/api-keys
     # - ElevenLabs: https://elevenlabs.io/app/settings/api-keys

  4. Add canonical text:
     # Edit data/verses/hanuman-chalisa.yaml with Devanagari text

  5. Validate setup:
     verse-validate

  6. Generate first verse:
     verse-generate --collection hanuman-chalisa --verse 1


Existing Project
──────────────────────────────────────────────────────────────────────────────

  Check and fix project structure:
    verse-validate --fix

  Add a new collection:
    verse-init --collection sundar-kaand --num-verses 60


🛠️  COMMON COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project Setup
──────────────────────────────────────────────────────────────────────────────
  verse-init                   Initialize new project with structure
  verse-validate               Check project structure and configuration
  verse-validate --fix         Auto-fix common issues

Content Generation
──────────────────────────────────────────────────────────────────────────────
  verse-generate               Generate images and audio for verses
  verse-images                 Generate images only
  verse-audio                  Generate audio pronunciation only
  verse-embeddings             Update vector embeddings for search

Puranic Context (RAG)
──────────────────────────────────────────────────────────────────────────────
  verse-index-sources          Index source texts (PDF/TXT/MD) for RAG
  verse-puranic-context        Generate Puranic context boxes for verses

Information
──────────────────────────────────────────────────────────────────────────────
  verse-generate --list-collections   List available collections
  verse-generate --show-structure     Show directory structure conventions
  verse-help                          This help screen (comprehensive guide)


📋 COMMON WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Complete Verse Content
──────────────────────────────────────────────────────────────────────────────
  # Generate everything (image + audio + embeddings)
  verse-generate --collection hanuman-chalisa --verse 15

  # With custom theme
  verse-generate --collection hanuman-chalisa --verse 15 --theme kids-friendly

  # Skip embeddings for faster generation
  verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings


Generate Specific Content Types
──────────────────────────────────────────────────────────────────────────────
  # Image only
  verse-generate --collection hanuman-chalisa --verse 1 --image

  # Audio only
  verse-generate --collection hanuman-chalisa --verse 1 --audio


Batch Processing
──────────────────────────────────────────────────────────────────────────────
  # Generate range of verses
  verse-generate --collection hanuman-chalisa --verse 1-10

  # Auto-generate next verse in sequence
  verse-generate --collection hanuman-chalisa --next

  # Bash loop for all verses
  for i in {1..43}; do
    verse-generate --collection hanuman-chalisa --verse $i
    sleep 5  # Rate limiting
  done


Add New Collection to Existing Project
──────────────────────────────────────────────────────────────────────────────
  # Add collection with templates
  verse-init --collection sundar-kaand --num-verses 60

  # Add canonical text
  # Edit data/verses/sundar-kaand.yaml

  # Validate
  verse-validate

  # Generate first verse
  verse-generate --collection sundar-kaand --verse 1


🔧 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Collection not found"
──────────────────────────────────────────────────────────────────────────────
  → Check _data/collections.yml exists and has collection defined
  → Ensure collection has "enabled: true"
  → Run: verse-validate --fix

"Verse not found in data file"
──────────────────────────────────────────────────────────────────────────────
  → Add verse to data/verses/<collection>.yaml with devanagari field
  → Example format:
    verse-01:
      devanagari: "श्रीगुरु चरन सरोज रज..."

"OPENAI_API_KEY not set"
──────────────────────────────────────────────────────────────────────────────
  → Create .env file: cp .env.example .env
  → Add your key: OPENAI_API_KEY=sk-your_actual_key
  → Get key from: https://platform.openai.com/api-keys

"Theme not found"
──────────────────────────────────────────────────────────────────────────────
  → Check data/themes/<collection>/<theme>.yml exists
  → Use default theme: --theme modern-minimalist
  → Create theme file with proper YAML structure

"Audio generation failed"
──────────────────────────────────────────────────────────────────────────────
  → Check ELEVENLABS_API_KEY is set in .env
  → Verify verse file exists: _verses/<collection>/verse-NN.md
  → Ensure Devanagari text is present in verse file

Project structure issues
──────────────────────────────────────────────────────────────────────────────
  → Run: verse-validate --detailed
  → Auto-fix: verse-validate --fix
  → Preview: verse-validate --fix --dry-run


📁 DIRECTORY STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

your-project/
├── .env                                  # API keys
├── _data/
│   ├── collections.yml                   # Collection registry
│   └── verse-config.yml                  # Project-level defaults (subject, subject_type)
├── _verses/
│   └── <collection-key>/                 # Verse markdown files
│       ├── verse-01.md
│       ├── verse-02.md
│       └── ...
├── data/
│   ├── themes/                           # Theme configurations
│   │   └── <collection-key>/
│   │       ├── modern-minimalist.yml
│   │       └── kids-friendly.yml
│   ├── verses/                           # Canonical verse text
│   │   └── <collection>.yaml
│   ├── scenes/                           # Scene descriptions for image generation
│   │   └── <collection>.yml
│   ├── sources/                          # Source texts for RAG indexing
│   │   └── shiv-puran.pdf
│   ├── puranic-index/                    # Indexed Puranic episodes
│   │   └── <key>.yml
│   └── embeddings/                       # Vector embeddings
│       └── puranic/                      # Puranic source embeddings
│       └── <key>.json
├── images/                               # Generated images (gitignored)
│   └── <collection>/
│       └── <theme>/
│           └── verse-01.png
└── audio/                                # Generated audio (gitignored)
    └── <collection>/
        ├── verse-01-full.mp3
        └── verse-01-slow.mp3

Convention: Use kebab-case for collection keys (e.g., hanuman-chalisa)


💰 API COSTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Per Verse (Complete Workflow)
──────────────────────────────────────────────────────────────────────────────
  Image (DALL-E 3):         $0.04 (standard) / $0.08 (HD)
  Audio (ElevenLabs):       ~$0.001 (2 files: full + slow)
  Embeddings (OpenAI):      ~$0.0001 (negligible)
  ────────────────────────────────────────────────────────────────────────────
  Total per verse:          ~$0.04-$0.08

Examples
──────────────────────────────────────────────────────────────────────────────
  Hanuman Chalisa (43 verses):     ~$1.72 - $3.44
  Bhagavad Gita (700 verses):      ~$28 - $56

Cost Optimization Tips:
  • Use standard quality images (not HD)
  • Skip embeddings during batch: --no-update-embeddings
  • Generate only what you need: --image or --audio
  • Update embeddings once at the end: verse-embeddings --multi-collection


📚 MORE HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Topic-Specific Help
──────────────────────────────────────────────────────────────────────────────
  verse-help --topic setup        Project setup and initialization
  verse-help --topic workflows    Common workflows and patterns
  verse-help --topic commands     Detailed command reference
  verse-help --topic themes       Theme customization guide
  verse-help --topic batch        Batch processing techniques

Command-Specific Help
──────────────────────────────────────────────────────────────────────────────
  verse-init --help
  verse-validate --help
  verse-generate --help
  verse-images --help
  verse-audio --help
  verse-embeddings --help

Documentation
──────────────────────────────────────────────────────────────────────────────
  Online Docs:     https://github.com/sanatan-learnings/sanatan-verse-sdk
  Usage Guide:     https://github.com/sanatan-learnings/sanatan-verse-sdk/blob/main/docs/usage.md
  Troubleshooting: https://github.com/sanatan-learnings/sanatan-verse-sdk/blob/main/docs/troubleshooting.md
  Example Project: https://github.com/sanatan-learnings/hanuman-gpt

Support
──────────────────────────────────────────────────────────────────────────────
  Report Issues:   https://github.com/sanatan-learnings/sanatan-verse-sdk/issues
  Discussions:     https://github.com/sanatan-learnings/sanatan-verse-sdk/discussions

╔════════════════════════════════════════════════════════════════════════════╗
║  Pro Tip: Run 'verse-validate' regularly to catch configuration issues     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


def show_setup_help():
    """Show detailed project setup help."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         PROJECT SETUP HELP                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

🚀 NEW PROJECT SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Install SDK
──────────────────────────────────────────────────────────────────────────────
  pip install sanatan-verse-sdk

Step 2: Initialize Project
──────────────────────────────────────────────────────────────────────────────
  # Create project with collection templates
  verse-init --project-name my-verse-project --collection hanuman-chalisa
  cd my-verse-project

  What gets created:
    ✓ Complete directory structure
    ✓ Sample verse files (3 by default, customizable with --num-verses)
    ✓ Canonical verse YAML template
    ✓ Theme configuration
    ✓ Scene descriptions template
    ✓ Collection entry in _data/collections.yml
    ✓ .gitignore configured for verse projects
    ✓ README.md with project documentation

Step 3: Configure API Keys
──────────────────────────────────────────────────────────────────────────────
  cp .env.example .env
  nano .env  # Or your preferred editor

  Add your actual API keys:
    OPENAI_API_KEY=sk-your_openai_key_from_platform
    ELEVENLABS_API_KEY=your_elevenlabs_key

  Get API keys:
    • OpenAI:     https://platform.openai.com/api-keys
    • ElevenLabs: https://elevenlabs.io/app/settings/api-keys

Step 4: Add Canonical Text
──────────────────────────────────────────────────────────────────────────────
  Edit data/verses/hanuman-chalisa.yaml:

  verse-01:
    devanagari: "श्रीगुरु चरन सरोज रज, निजमन मुकुर सुधारि।"

  verse-02:
    devanagari: "बरनउँ रघुबर बिमल जसु, जो दायक फल चारि।।"

  See docs/local-verses.md for YAML format details.

Step 5: Validate Setup
──────────────────────────────────────────────────────────────────────────────
  verse-validate

  If issues found:
    verse-validate --fix         # Auto-fix common issues
    verse-validate --dry-run     # Preview fixes without applying

Step 6: Generate First Verse
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1

  What gets generated:
    🎨 Image: images/hanuman-chalisa/modern-minimalist/verse-01.png
    🎵 Audio (full): audio/hanuman-chalisa/verse-01-full.mp3
    🎵 Audio (slow): audio/hanuman-chalisa/verse-01-slow.mp3
    🔍 Embeddings: data/embeddings/puranic/<key>.json (updated)


📦 ADD COLLECTION TO EXISTING PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # Navigate to existing project
  cd my-existing-project

  # Add new collection
  verse-init --collection sundar-kaand --num-verses 60

  What happens:
    ✓ Creates new collection files (doesn't overwrite existing)
    ✓ Appends to _data/collections.yml (preserves existing collections)
    ✓ Creates templates for the new collection only

  Safety: Existing files are NEVER overwritten.

  Complete workflow:
    verse-init --collection sundar-kaand --num-verses 60
    # Edit data/verses/sundar-kaand.yaml with canonical text
    verse-validate
    verse-generate --collection sundar-kaand --verse 1


🔍 VALIDATE EXISTING PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After cloning or modifying a project:

  verse-validate                 # Check structure
  verse-validate --detailed      # Show detailed information
  verse-validate --fix           # Auto-fix missing directories/files
  verse-validate --dry-run       # Preview changes without applying


📖 BACK TO MAIN HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  verse-help                     # Main help screen
  verse-help --topic workflows   # Common workflows
  verse-help --topic commands    # Command reference
""")


def show_workflows_help():
    """Show common workflows help."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         COMMON WORKFLOWS                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

🎨 GENERATE COMPLETE VERSE CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Default (Everything)
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 15

  Generates:
    • Image (DALL-E 3, modern-minimalist theme)
    • Audio (full speed + slow speed)
    • Updates embeddings for search

With Custom Theme
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 15 --theme kids-friendly

Skip Embeddings (Faster)
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings


🎯 GENERATE SPECIFIC CONTENT TYPES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Image Only
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1 --image
  verse-generate --collection hanuman-chalisa --verse 1 --image --theme kids-friendly

Audio Only
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1 --audio


📦 BATCH PROCESSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Range of Verses
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1-10
  verse-generate --collection hanuman-chalisa --verse 15-20 --no-update-embeddings

Auto-Generate Next Verse
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --next

Bash Loop for All Verses
──────────────────────────────────────────────────────────────────────────────
  # Generate all 43 verses
  for i in {1..43}; do
    verse-generate --collection hanuman-chalisa --verse $i
    sleep 5  # Rate limiting to avoid API throttling
  done

Bash Loop with Error Handling
──────────────────────────────────────────────────────────────────────────────
  for i in {1..43}; do
    verse-generate --collection hanuman-chalisa --verse $i || {
      echo "Failed on verse $i"
      exit 1
    }
    sleep 5
  done

Skip Existing Content
──────────────────────────────────────────────────────────────────────────────
  # Only generate if image doesn't exist
  for i in {1..43}; do
    if [ ! -f "images/hanuman-chalisa/modern-minimalist/verse-$(printf "%02d" $i).png" ]; then
      verse-generate --collection hanuman-chalisa --verse $i --image
      sleep 5
    fi
  done


🎨 THEME WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate with Different Themes
──────────────────────────────────────────────────────────────────────────────
  # Modern theme
  verse-generate --collection hanuman-chalisa --verse 1 --theme modern-minimalist

  # Kids theme
  verse-generate --collection hanuman-chalisa --verse 1 --theme kids-friendly

  # Traditional theme
  verse-generate --collection hanuman-chalisa --verse 1 --theme traditional-art

Generate All Verses with Multiple Themes
──────────────────────────────────────────────────────────────────────────────
  for theme in modern-minimalist kids-friendly traditional-art; do
    for i in {1..43}; do
      verse-generate --collection hanuman-chalisa --verse $i --image --theme $theme
      sleep 5
    done
  done


🔄 UPDATE WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Regenerate Images Only
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1-43 --image --no-update-embeddings

Regenerate Audio Only
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1-43 --audio --no-update-embeddings

Update Embeddings After Batch
──────────────────────────────────────────────────────────────────────────────
  # Generate all verses without updating embeddings
  verse-generate --collection hanuman-chalisa --verse 1-43 --no-update-embeddings

  # Update embeddings once at the end
  verse-embeddings --multi-collection


📖 BACK TO MAIN HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  verse-help                     # Main help screen
  verse-help --topic setup       # Project setup
  verse-help --topic commands    # Command reference
""")


def show_commands_help():
    """Show detailed command reference."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         COMMAND REFERENCE                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 PROJECT SETUP COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

verse-init
──────────────────────────────────────────────────────────────────────────────
  Initialize project with directory structure and templates.

  Options:
    --project-name NAME          Create project in new subdirectory
    --collection NAME            Create collection with templates (repeatable)
    --num-verses N               Number of sample verses (default: 3)
    --minimal                    Create minimal structure without examples

  Examples:
    verse-init --project-name my-project --collection hanuman-chalisa
    verse-init --collection sundar-kaand --num-verses 60
    verse-init --minimal

  See: verse-init --help
  Docs: docs/commands/verse-init.md


verse-validate
──────────────────────────────────────────────────────────────────────────────
  Validate project structure and configuration.

  Options:
    --detailed                   Show detailed validation info
    --fix                        Auto-fix common issues
    --dry-run                    Preview changes (use with --fix)
    --collection NAME            Validate specific collection
    --format FORMAT              Output format: text (default) or json

  Examples:
    verse-validate
    verse-validate --fix
    verse-validate --fix --dry-run
    verse-validate --collection hanuman-chalisa
    verse-validate --format json

  See: verse-validate --help
  Docs: docs/commands/verse-validate.md


🎨 CONTENT GENERATION COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

verse-generate
──────────────────────────────────────────────────────────────────────────────
  Generate images and audio for verses (orchestrates everything).

  Required:
    --collection KEY             Collection key (e.g., hanuman-chalisa)
    --verse N or M-N             Verse position or range (e.g., 15, 1-10)
       OR
    --next                       Auto-generate next verse in sequence

  Optional:
    --all                        Generate image + audio (default)
    --image                      Generate image only
    --audio                      Generate audio only
    --theme NAME                 Theme name (default: modern-minimalist)
    --no-update-embeddings       Skip embeddings update (faster)
    --regenerate-content         Regenerate AI content from canonical text
    --dry-run                    Preview without making API calls

  Information:
    --list-collections           List available collections
    --show-structure             Show directory structure conventions

  Examples:
    verse-generate --collection hanuman-chalisa --verse 15
    verse-generate --collection hanuman-chalisa --verse 1-10
    verse-generate --collection hanuman-chalisa --next
    verse-generate --collection hanuman-chalisa --verse 15 --theme kids-friendly
    verse-generate --collection hanuman-chalisa --verse 15 --image
    verse-generate --collection hanuman-chalisa --verse 15 --no-update-embeddings

  See: verse-generate --help
  Docs: docs/commands/verse-generate.md


verse-images
──────────────────────────────────────────────────────────────────────────────
  Generate images with DALL-E 3 (lower-level command).

  Options:
    --collection KEY             Collection key
    --theme NAME                 Theme name (default: modern-minimalist)
    --verse VERSE_ID             Verse ID (e.g., verse-01)
    --all                        Generate images for all verses

  Examples:
    verse-images --collection hanuman-chalisa --theme modern-minimalist --verse verse-01
    verse-images --collection hanuman-chalisa --theme kids-friendly --all

  See: verse-images --help
  Docs: docs/commands/verse-images.md


verse-audio
──────────────────────────────────────────────────────────────────────────────
  Generate audio pronunciation with ElevenLabs (lower-level command).

  Options:
    --collection KEY             Collection key
    --verse VERSE_ID             Verse ID (e.g., verse-01)
    --all                        Generate audio for all verses

  Examples:
    verse-audio --collection hanuman-chalisa --verse verse-01
    verse-audio --collection hanuman-chalisa --all

  See: verse-audio --help


verse-embeddings
──────────────────────────────────────────────────────────────────────────────
  Update vector embeddings for semantic search.

  Options:
    --multi-collection           Process all enabled collections
    --collections-file PATH      Path to collections.yml

  Examples:
    verse-embeddings --multi-collection
    verse-embeddings --multi-collection --collections-file _data/collections.yml

  See: verse-embeddings --help


🔎 PURANIC CONTEXT COMMANDS (RAG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

verse-index-sources
──────────────────────────────────────────────────────────────────────────────
  Index Puranic source texts (PDF/TXT/MD) into structured episodes and
  embeddings for RAG retrieval.

  Required:
    --file PATH                  Path to source file

  Optional:
    --force                      Re-index from scratch
    --update-meta                Patch _meta without re-indexing (fast)
    --chunk-size CHARS           Characters per chunk (default: 4000)
    --provider PROVIDER          Embedding provider: openai (default) or bedrock-cohere
    --project-dir PATH           Project directory (default: current)

  Examples:
    verse-index-sources --file data/sources/shiv-puran.pdf
    verse-index-sources --file data/sources/shiv-puran.pdf --provider bedrock-cohere
    verse-index-sources --file data/sources/shiv-puran.pdf --chunk-size 6000
    verse-index-sources --file data/sources/shiv-puran.pdf --update-meta

  See: verse-index-sources --help
  Docs: docs/commands/verse-index-sources.md


verse-puranic-context
──────────────────────────────────────────────────────────────────────────────
  Generate Puranic context boxes for verse files using RAG retrieval or
  GPT-4o free recall.

  Required:
    --collection KEY             Collection key
    --verse ID or --all          Process specific verse or all verses

  Optional:
    --regenerate                 Overwrite existing puranic_context entries
    --project-dir PATH           Project directory (default: current)

  subject and subject_type are read from _data/collections.yml (not CLI flags):
    subject: Hanuman
    subject_type: deity

  Examples:
    verse-puranic-context --collection hanuman-chalisa --verse chaupai-15
    verse-puranic-context --collection hanuman-chalisa --all
    verse-puranic-context --collection hanuman-chalisa --all --regenerate

  See: verse-puranic-context --help
  Docs: docs/commands/verse-puranic-context.md


📖 BACK TO MAIN HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  verse-help                     # Main help screen
  verse-help --topic setup       # Project setup
  verse-help --topic workflows   # Common workflows
  verse-help --topic themes      # Theme customization
""")


def show_themes_help():
    """Show theme customization help."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         THEME CUSTOMIZATION                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

🎨 THEME SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Themes control the visual style of generated images.
Location: data/themes/<collection>/<theme-name>.yml


📝 THEME FILE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Basic Structure:
──────────────────────────────────────────────────────────────────────────────
  name: Theme Display Name
  style: |
    Description of the visual style.
    Artistic direction and mood.

  colors:
    primary: "#HEX_COLOR"
    secondary: "#HEX_COLOR"
    background: "#HEX_COLOR"

  art_direction: |
    - Bullet point 1
    - Bullet point 2
    - Bullet point 3


🎨 EXAMPLE THEMES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Modern Minimalist (Default)
──────────────────────────────────────────────────────────────────────────────
  name: Modern Minimalist
  style: |
    Clean, minimalist design with focus on spiritual symbolism.
    Simple geometric shapes and calming colors.
    Contemporary interpretation of traditional themes.

  colors:
    primary: "#FF6B35"
    secondary: "#004E89"
    background: "#F7F9F9"

  art_direction: |
    - Minimalist composition
    - Soft gradients
    - Geometric patterns
    - Modern typography
    - Spiritual symbolism


Kids Friendly
──────────────────────────────────────────────────────────────────────────────
  name: Kids Friendly
  style: |
    Bright, colorful, and cheerful design appealing to children.
    Cartoon-like characters with friendly expressions.
    Bold colors and simple compositions.

  colors:
    primary: "#FF6B9D"
    secondary: "#4ECDC4"
    background: "#FFE66D"

  art_direction: |
    - Cartoon style illustration
    - Bright and cheerful colors
    - Simple, child-friendly imagery
    - Fun and engaging composition
    - Friendly character designs


Traditional Art
──────────────────────────────────────────────────────────────────────────────
  name: Traditional Art
  style: |
    Traditional Indian art style inspired by ancient manuscripts.
    Rich colors, intricate patterns, and classical composition.
    Spiritual and authentic aesthetic.

  colors:
    primary: "#B8860B"
    secondary: "#8B0000"
    background: "#FFF8DC"

  art_direction: |
    - Traditional Indian art style
    - Intricate details and patterns
    - Rich, royal colors
    - Classical composition
    - Authentic spiritual imagery


🛠️  CREATING A NEW THEME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Create Theme File
──────────────────────────────────────────────────────────────────────────────
  mkdir -p data/themes/hanuman-chalisa
  nano data/themes/hanuman-chalisa/watercolor-art.yml

Step 2: Define Theme
──────────────────────────────────────────────────────────────────────────────
  name: Watercolor Art
  style: |
    Soft watercolor painting style with flowing colors.
    Dreamy and artistic interpretation.
    Warm, vibrant colors with gentle blending.

  colors:
    primary: "#E63946"
    secondary: "#457B9D"
    background: "#F1FAEE"

  art_direction: |
    - Watercolor painting technique
    - Soft edges and flowing colors
    - Artistic interpretation
    - Warm and inviting atmosphere
    - Hand-painted aesthetic

Step 3: Use the Theme
──────────────────────────────────────────────────────────────────────────────
  verse-generate --collection hanuman-chalisa --verse 1 --theme watercolor-art


💡 THEME TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • Test themes on a few verses before batch processing
  • Use consistent themes for entire collections
  • Create theme variants for different audiences (kids, adults, scholars)
  • Keep art_direction concise and specific
  • Use colors that complement the spiritual theme
  • Reference existing themes as templates


📖 BACK TO MAIN HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  verse-help                     # Main help screen
  verse-help --topic setup       # Project setup
  verse-help --topic workflows   # Common workflows
  verse-help --topic commands    # Command reference
""")


def show_batch_help():
    """Show batch processing help."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         BATCH PROCESSING GUIDE                              ║
╚════════════════════════════════════════════════════════════════════════════╝

📦 BATCH PROCESSING TECHNIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Built-in Range Support
──────────────────────────────────────────────────────────────────────────────
  # Generate verses 1-10
  verse-generate --collection hanuman-chalisa --verse 1-10

  # Generate verses 15-20 without embeddings (faster)
  verse-generate --collection hanuman-chalisa --verse 15-20 --no-update-embeddings


Basic Bash Loop
──────────────────────────────────────────────────────────────────────────────
  # Generate all verses in collection
  for i in {1..43}; do
    verse-generate --collection hanuman-chalisa --verse $i
    sleep 5  # Rate limiting to avoid API throttling
  done


Loop with Error Handling
──────────────────────────────────────────────────────────────────────────────
  #!/bin/bash
  COLLECTION="hanuman-chalisa"
  START=1
  END=43

  for i in $(seq $START $END); do
    echo "Processing verse $i..."

    verse-generate --collection $COLLECTION --verse $i || {
      echo "✗ Failed on verse $i"
      exit 1
    }

    echo "✓ Verse $i completed"
    sleep 5
  done

  echo "✓ Batch processing complete!"


Skip Existing Content
──────────────────────────────────────────────────────────────────────────────
  # Only generate if image doesn't exist
  for i in {1..43}; do
    IMAGE="images/hanuman-chalisa/modern-minimalist/verse-$(printf "%02d" $i).png"
    if [ ! -f "$IMAGE" ]; then
      echo "Generating verse $i..."
      verse-generate --collection hanuman-chalisa --verse $i --image
      sleep 5
    else
      echo "Skipping verse $i (already exists)"
    fi
  done


Progress Tracking
──────────────────────────────────────────────────────────────────────────────
  #!/bin/bash
  COLLECTION="hanuman-chalisa"
  START=1
  END=43
  TOTAL=$((END - START + 1))

  for i in $(seq $START $END); do
    CURRENT=$((i - START + 1))
    PERCENT=$((CURRENT * 100 / TOTAL))

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Progress: $CURRENT/$TOTAL ($PERCENT%) - Verse $i"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    verse-generate --collection $COLLECTION --verse $i || {
      echo "✗ Failed on verse $i"
      exit 1
    }

    sleep 5
  done


Multiple Themes
──────────────────────────────────────────────────────────────────────────────
  #!/bin/bash
  COLLECTION="hanuman-chalisa"
  THEMES="modern-minimalist kids-friendly traditional-art"

  for theme in $THEMES; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing theme: $theme"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for i in {1..43}; do
      echo "Generating verse $i with theme $theme..."
      verse-generate --collection $COLLECTION --verse $i --image --theme $theme --no-update-embeddings
      sleep 5
    done
  done

  # Update embeddings once at the end
  verse-embeddings --multi-collection


Parallel Processing (Advanced)
──────────────────────────────────────────────────────────────────────────────
  # Use GNU parallel for faster processing (install with: brew install parallel)
  # WARNING: Be mindful of API rate limits!

  parallel -j 2 --delay 3 \\
    "verse-generate --collection hanuman-chalisa --verse {} --no-update-embeddings" \\
    ::: {1..43}

  # Update embeddings after parallel processing
  verse-embeddings --multi-collection


💰 COST OPTIMIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Skip Embeddings During Batch
──────────────────────────────────────────────────────────────────────────────
  # Generate all verses without embeddings
  for i in {1..43}; do
    verse-generate --collection hanuman-chalisa --verse $i --no-update-embeddings
    sleep 5
  done

  # Update embeddings once at the end (much faster)
  verse-embeddings --multi-collection


Generate Only What You Need
──────────────────────────────────────────────────────────────────────────────
  # Images only
  verse-generate --collection hanuman-chalisa --verse 1-43 --image --no-update-embeddings

  # Audio only
  verse-generate --collection hanuman-chalisa --verse 1-43 --audio --no-update-embeddings


⚠️  BEST PRACTICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rate Limiting
──────────────────────────────────────────────────────────────────────────────
  • Always add sleep delays between API calls (minimum 5 seconds)
  • Monitor API usage and adjust delays as needed
  • Be aware of API rate limits:
    - OpenAI: Varies by tier
    - ElevenLabs: Depends on subscription plan

Error Recovery
──────────────────────────────────────────────────────────────────────────────
  • Use error handling in loops (|| exit 1)
  • Log output for debugging: 2>&1 | tee batch.log
  • Check for errors before continuing
  • Save progress regularly

Testing
──────────────────────────────────────────────────────────────────────────────
  • Test on a small range first (e.g., 1-3 verses)
  • Verify output quality before batch processing
  • Use --dry-run to preview without API calls

Monitoring
──────────────────────────────────────────────────────────────────────────────
  • Monitor API costs in provider dashboards
  • Track progress with counters and percentages
  • Keep logs of batch operations


📖 BACK TO MAIN HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  verse-help                     # Main help screen
  verse-help --topic setup       # Project setup
  verse-help --topic workflows   # Common workflows
  verse-help --topic commands    # Command reference
""")


def main():
    """Main entry point for verse-help command."""
    parser = argparse.ArgumentParser(
        description="Comprehensive help for sanatan-verse-sdk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Topics:
  setup       - Project setup and initialization
  workflows   - Common workflows and patterns
  commands    - Detailed command reference
  themes      - Theme customization guide
  batch       - Batch processing techniques

Examples:
  verse-help                     # Main help screen
  verse-help --topic setup       # Project setup help
  verse-help --topic workflows   # Common workflows
  verse-help --topic commands    # Command reference
  verse-help --topic themes      # Theme customization
  verse-help --topic batch       # Batch processing
        """
    )

    parser.add_argument(
        "--topic",
        choices=["setup", "workflows", "commands", "themes", "batch"],
        help="Show help for specific topic"
    )

    args = parser.parse_args()

    if args.topic == "setup":
        show_setup_help()
    elif args.topic == "workflows":
        show_workflows_help()
    elif args.topic == "commands":
        show_commands_help()
    elif args.topic == "themes":
        show_themes_help()
    elif args.topic == "batch":
        show_batch_help()
    else:
        show_main_help()


if __name__ == "__main__":
    main()
