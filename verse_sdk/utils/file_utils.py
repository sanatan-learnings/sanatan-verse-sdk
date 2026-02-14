"""File handling utilities."""

import json
from pathlib import Path
from typing import List, Any
from datetime import datetime


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory
    """
    path.mkdir(parents=True, exist_ok=True)


def write_json(data: Any, output_path: Path, pretty: bool = True) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to write
        output_path: Path to output file
        pretty: Whether to format with indentation
    """
    ensure_directory(output_path.parent)

    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False)


def read_json(file_path: Path) -> Any:
    """
    Read data from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_markdown_files(directory: Path, pattern: str = "*.md") -> List[Path]:
    """
    Find all markdown files in a directory.

    Args:
        directory: Directory to search
        pattern: Glob pattern for matching files

    Returns:
        Sorted list of Path objects
    """
    return sorted(directory.glob(pattern))


def get_file_size_kb(file_path: Path) -> float:
    """
    Get file size in kilobytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in KB
    """
    return file_path.stat().st_size / 1024
