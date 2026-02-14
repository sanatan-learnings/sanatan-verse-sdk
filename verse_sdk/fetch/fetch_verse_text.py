#!/usr/bin/env python3
"""
Fetch traditional Devanagari verse text from local canonical sources.

This script reads verse text from local YAML files in data/verses/{collection}.yaml (or .yml).
Canonical source files must be created manually to ensure text accuracy and quality.
"""

import sys
import re
import json
import argparse
import yaml
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install requests beautifulsoup4")
    sys.exit(1)


# Authoritative sources for different collections
SOURCES = {
    "sundar-kaand": {
        "name": "Ramcharitmanas - Sundar Kand",
        "url_template": "https://www.ramcharitmanas.net/sundar-kand/doha-{verse_num}",
        "url_template_chaupai": "https://www.ramcharitmanas.net/sundar-kand/chaupai-{verse_num}",
        "selectors": [
            ".verse-text",
            ".devanagari",
            "div.hindi-text",
            "p.verse",
        ]
    },
    "hanuman-chalisa": {
        "name": "Hanuman Chalisa",
        "url_template": "https://www.hanumanworld.com/hanuman-chalisa-verse-{verse_num}.html",
        "selectors": [
            ".chalisa-verse",
            ".devanagari-text",
            "div.verse",
        ]
    }
}


def clean_devanagari_text(text: str) -> str:
    """Clean and normalize Devanagari text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove common artifacts
    text = text.replace('।।', '।।')  # Normalize double danda
    text = text.replace('॥', '।।')    # Normalize to standard danda

    # Remove English characters and numbers (except verse markers)
    # Keep Devanagari characters and punctuation
    text = re.sub(r'[A-Za-z]+', '', text)

    return text.strip()


def fetch_from_ramcharitmanas_net(collection: str, verse_num: int, verse_type: str = "chaupai") -> Optional[str]:
    """
    Fetch verse from ramcharitmanas.net

    Args:
        collection: Collection name (e.g., "sundar-kaand")
        verse_num: Verse number
        verse_type: "chaupai" or "doha"

    Returns:
        Devanagari text or None if not found
    """
    try:
        # Try different URL patterns
        urls = [
            f"https://www.ramcharitmanas.net/sundar-kand/{verse_type}-{verse_num}",
            f"https://www.ramcharitmanas.net/sundar/{verse_type}-{verse_num}.htm",
            f"https://www.ramcharitmanas.net/sunderkand-{verse_type}-{verse_num}.html",
        ]

        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Try different selectors
                    selectors = [
                        'div.devanagari',
                        'p.hindi',
                        'div.verse-hindi',
                        'span.devanagari',
                        'div[lang="hi"]',
                    ]

                    for selector in selectors:
                        elements = soup.select(selector)
                        if elements:
                            text = ' '.join([el.get_text() for el in elements])
                            text = clean_devanagari_text(text)
                            if text and len(text) > 10:  # Must have substantial content
                                return text
            except Exception as e:
                continue

        return None

    except Exception as e:
        print(f"Error fetching from ramcharitmanas.net: {e}", file=sys.stderr)
        return None


def fetch_from_generic_source(url: str, selectors: list) -> Optional[str]:
    """Fetch verse from a generic URL with CSS selectors."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([el.get_text() for el in elements])
                text = clean_devanagari_text(text)
                if text and len(text) > 10:
                    return text

        return None

    except Exception as e:
        print(f"Error fetching from {url}: {e}", file=sys.stderr)
        return None


def fetch_from_local_file(collection: str, verse_id: str, project_dir: Path = None) -> Optional[Dict]:
    """
    Fetch verse text from local YAML file in data/verses/{collection}.yaml or .yml

    Args:
        collection: Collection key (e.g., "sundar-kaand")
        verse_id: Verse identifier (e.g., "chaupai_05", "verse_10", "doha_01")
        project_dir: Project directory (defaults to current working directory)

    Returns:
        Dictionary with verse data or None if not found
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Look for local verses file - try .yaml first, then .yml
    verses_file = project_dir / "data" / "verses" / f"{collection}.yaml"
    if not verses_file.exists():
        verses_file = project_dir / "data" / "verses" / f"{collection}.yml"

    if not verses_file.exists():
        return None

    try:
        with open(verses_file, 'r', encoding='utf-8') as f:
            verses_data = yaml.safe_load(f)

        if not verses_data:
            return None

        # Ignore metadata keys (starting with underscore)
        if verse_id.startswith('_'):
            return None

        if verse_id not in verses_data:
            return None

        verse_data = verses_data[verse_id]

        # Handle two formats:
        # 1. chaupai_01: "devanagari text" (string)
        # 2. chaupai_01: {devanagari: "text", ...} (dict)
        if isinstance(verse_data, str):
            # Simple string format - wrap it in a dict
            return {'devanagari': verse_data}
        elif isinstance(verse_data, dict):
            # Dict format - validate required field
            if 'devanagari' not in verse_data:
                print(f"Warning: Verse {verse_id} in {verses_file} missing 'devanagari' field", file=sys.stderr)
                return None
            return verse_data
        else:
            print(f"Warning: Verse {verse_id} in {verses_file} has invalid format (expected string or dict)", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Error reading local verses file {verses_file}: {e}", file=sys.stderr)
        return None


def fetch_verse_text(collection: str, verse_id: str) -> Dict[str, any]:
    """
    Fetch traditional Devanagari text for a verse.

    First checks for local YAML file in data/verses/{collection}.yaml,
    then falls back to fetching from authoritative online sources.

    Args:
        collection: Collection key (e.g., "sundar-kaand")
        verse_id: Verse identifier (e.g., "chaupai_05", "verse_10", "doha_01")

    Returns:
        Dictionary with verse text and metadata
    """
    # Parse verse_id to get type and number
    match = re.match(r'(chaupai|doha|verse)_?(\d+)', verse_id)
    if not match:
        return {
            "success": False,
            "error": f"Invalid verse_id format: {verse_id}"
        }

    verse_type = match.group(1)
    verse_num = int(match.group(2))

    print(f"Fetching {verse_type} {verse_num} from {collection}...", file=sys.stderr)

    # Check local file (only source)
    local_data = fetch_from_local_file(collection, verse_id)
    if local_data:
        print(f"✓ Found in local file: data/verses/{collection}.{{yaml,yml}}", file=sys.stderr)
        return {
            "success": True,
            "collection": collection,
            "verse_id": verse_id,
            "verse_type": verse_type,
            "verse_number": verse_num,
            "devanagari": local_data.get("devanagari"),
            "transliteration": local_data.get("transliteration"),
            "meaning": local_data.get("meaning"),
            "translation": local_data.get("translation"),
            "source": "local_file",
            "verified": True
        }

    # No local file found - fail with clear error
    return {
        "success": False,
        "error": f"Canonical source not found. Please create data/verses/{collection}.yaml with verse text for '{verse_id}'",
        "collection": collection,
        "verse_id": verse_id,
        "help": f"See docs/local-verses.md for format details"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch traditional Devanagari verse text from local canonical sources (data/verses/{collection}.yaml)"
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Collection key (e.g., sundar-kaand, hanuman-chalisa)"
    )
    parser.add_argument(
        "--verse",
        required=True,
        help="Verse identifier (e.g., chaupai_05, verse_10, doha_01)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    result = fetch_verse_text(args.collection, args.verse)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["success"]:
            print(result["devanagari"])
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
