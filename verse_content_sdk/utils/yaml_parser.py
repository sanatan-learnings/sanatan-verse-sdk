"""YAML front matter parsing utilities."""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any


def extract_yaml_frontmatter(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract YAML front matter from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Dictionary containing the YAML data, or None if no front matter found
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        return None

    end_idx = content.find('---', 3)
    if end_idx == -1:
        return None

    yaml_content = content[3:end_idx].strip()
    return yaml.safe_load(yaml_content)


def get_nested_value(data: Dict[str, Any], key: str, lang: Optional[str] = None, default: Any = None) -> Any:
    """
    Get a value from nested dictionary, optionally for a specific language.

    Args:
        data: The dictionary to search
        key: The key to look for
        lang: Optional language code (e.g., 'en', 'hi')
        default: Default value if key not found

    Returns:
        The value found, or default
    """
    if key not in data:
        return default

    value = data[key]

    if lang and isinstance(value, dict) and lang in value:
        return value[lang]

    return value
