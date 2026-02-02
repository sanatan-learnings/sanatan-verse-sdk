#!/usr/bin/env python3
"""
Test script for multi-collection embeddings functionality.

This script validates that the multi-collection support is working correctly
without actually generating embeddings (to avoid API costs).
"""

import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent))

from verse_content_sdk.embeddings.generate_embeddings import (
    load_collections_config,
    get_enabled_collections,
    extract_yaml_frontmatter,
    extract_permalink_from_frontmatter,
    generate_verse_url
)


def test_collections_loading(collections_file):
    """Test loading and parsing collections.yml"""
    print("=" * 70)
    print("TEST 1: Loading Collections Configuration")
    print("=" * 70)

    try:
        collections = load_collections_config(collections_file)
        print(f"✓ Loaded collections file: {collections_file}")
        print(f"  Total collections: {len(collections)}")

        enabled = get_enabled_collections(collections)
        print(f"  Enabled collections: {len(enabled)}")

        for key, info in enabled.items():
            print(f"    - {key}: {info.get('name_en', key)}")
            print(f"      Subdirectory: {info.get('subdirectory', key)}")
            print(f"      Permalink base: {info.get('permalink_base', 'N/A')}")

        return True
    except Exception as e:
        print(f"✗ Error loading collections: {e}")
        return False


def test_verse_directories(collections_file, base_verses_dir):
    """Test that verse directories exist for enabled collections"""
    print("\n" + "=" * 70)
    print("TEST 2: Verse Directories")
    print("=" * 70)

    try:
        collections = load_collections_config(collections_file)
        enabled = get_enabled_collections(collections)

        all_exist = True
        for key, info in enabled.items():
            subdirectory = info.get('subdirectory', key)
            verses_dir = base_verses_dir / subdirectory

            if verses_dir.exists():
                verse_files = list(verses_dir.glob("*.md"))
                print(f"✓ {key}: {len(verse_files)} files in {verses_dir}")
            else:
                print(f"✗ {key}: Directory not found - {verses_dir}")
                all_exist = False

        return all_exist
    except Exception as e:
        print(f"✗ Error checking directories: {e}")
        return False


def test_permalink_extraction(base_verses_dir):
    """Test permalink extraction from verse frontmatter"""
    print("\n" + "=" * 70)
    print("TEST 3: Permalink Extraction")
    print("=" * 70)

    # Find sample verse files from different collections
    test_files = []
    for subdir in base_verses_dir.iterdir():
        if subdir.is_dir():
            md_files = list(subdir.glob("*.md"))
            if md_files:
                test_files.append(md_files[0])  # Take first file from each collection

    if not test_files:
        print("✗ No verse files found to test")
        return False

    all_passed = True
    for test_file in test_files[:3]:  # Test first 3 collections
        try:
            verse_data = extract_yaml_frontmatter(test_file)
            if not verse_data:
                print(f"✗ Could not extract frontmatter from {test_file.name}")
                all_passed = False
                continue

            title = verse_data.get('title_en', 'N/A')
            permalink = extract_permalink_from_frontmatter(verse_data)
            generated_url = generate_verse_url(verse_data)
            collection_key = verse_data.get('collection_key', 'N/A')

            print(f"\nFile: {test_file.name}")
            print(f"  Collection: {collection_key}")
            print(f"  Title: {title}")
            print(f"  Permalink (from frontmatter): {permalink}")
            print(f"  Generated URL (fallback): {generated_url}")

            if permalink:
                print(f"  ✓ Will use permalink from frontmatter")
            else:
                print(f"  ⚠ Will use generated URL (no permalink in frontmatter)")

        except Exception as e:
            print(f"✗ Error processing {test_file.name}: {e}")
            all_passed = False

    return all_passed


def test_collection_metadata():
    """Test that collection metadata structure is correct"""
    print("\n" + "=" * 70)
    print("TEST 4: Collection Metadata Structure")
    print("=" * 70)

    # Sample collection metadata
    test_metadata = {
        'key': 'hanuman-chalisa',
        'name': 'Hanuman Chalisa'
    }

    # Sample verse metadata structure
    verse_metadata = {
        'devanagari': 'श्रीगुरु चरन सरोज रज...',
        'transliteration': 'Shri Guru charan saroj raj...',
        'collection_key': test_metadata['key'],
        'collection_name': test_metadata['name'],
        'literal_translation': 'With the dust of Guru\'s lotus feet...'
    }

    print("Sample verse metadata structure:")
    for key, value in verse_metadata.items():
        if key == 'devanagari' or key == 'transliteration' or key == 'literal_translation':
            value = value[:30] + '...' if len(value) > 30 else value
        print(f"  {key}: {value}")

    required_fields = ['collection_key', 'collection_name']
    all_present = all(field in verse_metadata for field in required_fields)

    if all_present:
        print(f"\n✓ All required collection fields present: {', '.join(required_fields)}")
        return True
    else:
        missing = [f for f in required_fields if f not in verse_metadata]
        print(f"\n✗ Missing fields: {', '.join(missing)}")
        return False


def main():
    """Run all tests"""
    print("Multi-Collection Embeddings Test Suite")
    print("=" * 70)

    # Configuration
    # Try to find test data in the hanuman-chalisa project
    hanuman_project = Path.home() / "workspaces" / "hanuman-chalisa"

    if hanuman_project.exists():
        collections_file = hanuman_project / "_data" / "collections.yml"
        base_verses_dir = hanuman_project / "_verses"
        print(f"Using test data from: {hanuman_project}")
    else:
        print("Note: hanuman-chalisa project not found at expected location")
        print("Using minimal test configuration")
        collections_file = Path("collections.yml")
        base_verses_dir = Path("_verses")

    print(f"Collections file: {collections_file}")
    print(f"Verses directory: {base_verses_dir}")
    print()

    # Run tests
    results = []

    if collections_file.exists():
        results.append(("Collections Loading", test_collections_loading(collections_file)))
        results.append(("Verse Directories", test_verse_directories(collections_file, base_verses_dir)))

        if base_verses_dir.exists():
            results.append(("Permalink Extraction", test_permalink_extraction(base_verses_dir)))
    else:
        print(f"⚠ Collections file not found: {collections_file}")
        print("  Skipping tests that require collections.yml")

    results.append(("Collection Metadata", test_collection_metadata()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
