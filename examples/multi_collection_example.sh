#!/bin/bash
#
# Example: Generate embeddings for multiple collections
#
# This script demonstrates how to use the multi-collection support
# in the verse-embeddings command.

set -e

echo "Multi-Collection Embeddings Example"
echo "===================================="
echo ""

# Check if collections file exists
COLLECTIONS_FILE="_data/collections.yml"
if [ ! -f "$COLLECTIONS_FILE" ]; then
    echo "Error: Collections file not found: $COLLECTIONS_FILE"
    echo "Please run this script from your project root directory"
    exit 1
fi

echo "Step 1: Verify collections configuration"
echo "-----------------------------------------"
echo "Collections file: $COLLECTIONS_FILE"
echo ""

# Show enabled collections
python3 -c "
import yaml
with open('$COLLECTIONS_FILE', 'r') as f:
    collections = yaml.safe_load(f)
    enabled = {k: v for k, v in collections.items() if v.get('enabled', False)}
    print(f'Enabled collections: {len(enabled)}')
    for key, info in enabled.items():
        print(f'  - {key}: {info.get(\"name_en\", key)}')
        verse_dir = f'_verses/{info.get(\"subdirectory\", key)}'
        import os
        if os.path.exists(verse_dir):
            count = len([f for f in os.listdir(verse_dir) if f.endswith('.md')])
            print(f'    Verses: {count} files')
        else:
            print(f'    Warning: Directory not found - {verse_dir}')
"
echo ""

echo "Step 2: Generate embeddings (dry run - using --help to avoid API costs)"
echo "------------------------------------------------------------------------"
echo "Command that would be used:"
echo "  verse-embeddings --multi-collection --collections-file $COLLECTIONS_FILE --provider openai"
echo ""
echo "For actual generation, you would run:"
echo "  verse-embeddings --multi-collection \\"
echo "    --collections-file $COLLECTIONS_FILE \\"
echo "    --provider openai \\"
echo "    --output ./data/embeddings.json"
echo ""

# Show the help to demonstrate the command exists
verse-embeddings --help | grep -A 5 "multi-collection"

echo ""
echo "Step 3: What the output would contain"
echo "--------------------------------------"
echo "The generated embeddings.json would include:"
echo "  - Verses from all enabled collections"
echo "  - Collection metadata (collection_key, collection_name)"
echo "  - Permalinks from frontmatter (e.g., /chalisa/verse_01/)"
echo "  - Unified format for semantic search across all collections"
echo ""

echo "Example verse entry with collection metadata:"
echo '{'
echo '  "verse_number": 1,'
echo '  "title": "Verse 1: Ocean of Knowledge and Virtues",'
echo '  "url": "/chalisa/verse_01/",'
echo '  "embedding": [...],'
echo '  "metadata": {'
echo '    "devanagari": "...",'
echo '    "transliteration": "...",'
echo '    "literal_translation": "...",'
echo '    "collection_key": "hanuman-chalisa",'
echo '    "collection_name": "Hanuman Chalisa"'
echo '  }'
echo '}'
echo ""

echo "Done! To generate embeddings, run the command shown above."
echo ""
echo "Note: Requires OPENAI_API_KEY in .env file or environment"
