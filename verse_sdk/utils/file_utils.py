"""File handling utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List


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


def puranic_embeddings_dir(project_dir: Path) -> Path:
    """Canonical directory for puranic source embeddings."""
    return project_dir / "data" / "embeddings" / "puranic"


def puranic_embeddings_path(project_dir: Path, key: str) -> Path:
    """Canonical path for puranic source embeddings."""
    return puranic_embeddings_dir(project_dir) / f"{key}.json"


def find_puranic_embeddings_path(project_dir: Path, key: str) -> Path:
    """Return canonical puranic embeddings path, falling back to legacy if present."""
    canonical = puranic_embeddings_path(project_dir, key)
    if canonical.exists():
        return canonical
    legacy = project_dir / "data" / "embeddings" / f"{key}.json"
    if legacy.exists():
        return legacy
    return canonical
