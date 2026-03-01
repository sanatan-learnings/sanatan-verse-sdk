#!/usr/bin/env python3
"""
Parse canonical source text into data/verses/<collection>.yaml.

Supports basic plain-text parsing with optional chapter detection.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


CHAPTER_PATTERNS = [
    re.compile(r"^\s*Chapter\s+(\d+)\b", re.IGNORECASE),
    re.compile(r"^\s*अध्याय\s+(\d+)\b"),
    re.compile(r"^\s*अध्यायः\s+(\d+)\b"),
]


def _normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _collect_files(source: Optional[List[str]], source_dir: Optional[str], source_glob: str) -> List[Path]:
    if source and source_dir:
        raise ValueError("Use either --source or --source-dir (not both).")

    files: List[Path] = []

    if source:
        files = [Path(p) for p in source]
    elif source_dir:
        root = Path(source_dir)
        files = sorted(root.glob(source_glob))
    else:
        raise ValueError("Provide --source or --source-dir.")

    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Source files not found: {', '.join(missing)}")

    return files


def _detect_chapter(line: str) -> Optional[int]:
    for pattern in CHAPTER_PATTERNS:
        match = pattern.match(line)
        if match:
            return int(match.group(1))
    return None


def _split_verses(lines: List[str]) -> List[str]:
    verses: List[str] = []
    buffer: List[str] = []

    for line in lines:
        if not line.strip():
            if buffer:
                verses.append(_normalize_text(" ".join(buffer)))
                buffer = []
            continue

        buffer.append(line.strip())

    if buffer:
        verses.append(_normalize_text(" ".join(buffer)))

    return verses


def _parse_plain(files: List[Path], chaptered: bool) -> List[Tuple[Optional[int], str]]:
    entries: List[Tuple[Optional[int], str]] = []
    current_chapter: Optional[int] = None

    for path in files:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        if chaptered:
            buffer: List[str] = []
            for line in lines:
                chapter = _detect_chapter(line)
                if chapter is not None:
                    if buffer:
                        verses = _split_verses(buffer)
                        entries.extend([(current_chapter, v) for v in verses])
                        buffer = []
                    current_chapter = chapter
                    continue
                buffer.append(line)
            if buffer:
                verses = _split_verses(buffer)
                entries.extend([(current_chapter, v) for v in verses])
        else:
            verses = _split_verses(lines)
            entries.extend([(None, v) for v in verses])

    return entries


def _build_yaml(entries: List[Tuple[Optional[int], str]], collection_key: str, chaptered: bool) -> Dict[str, Dict[str, str]]:
    output: Dict[str, Dict[str, str]] = {}

    if chaptered:
        chapter_counts: Dict[int, int] = {}
        for chapter, text in entries:
            chapter_num = chapter if chapter is not None else 1
            chapter_counts.setdefault(chapter_num, 0)
            chapter_counts[chapter_num] += 1
            verse_num = chapter_counts[chapter_num]
            key = f"chapter-{chapter_num:02d}-shloka-{verse_num:02d}"
            output[key] = {"devanagari": text}
    else:
        for idx, (_, text) in enumerate(entries, start=1):
            key = f"verse-{idx:02d}"
            output[key] = {"devanagari": text}

    if not output:
        raise ValueError("No verses detected. Check input files or format.")

    return output


def _render_yaml(data: Dict[str, Dict[str, str]]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Parse canonical source text into data/verses/<collection>.yaml",
    )
    parser.add_argument("--collection", required=True, help="Collection key (e.g., hanuman-chalisa)")
    parser.add_argument("--source", action="append", help="Source file path (repeatable)")
    parser.add_argument("--source-dir", help="Directory containing source files")
    parser.add_argument("--source-glob", default="**/*.txt", help="Glob for source files under --source-dir")
    parser.add_argument("--format", default="devanagari-plain", choices=["devanagari-plain", "chaptered-plain"])
    parser.add_argument("--output", help="Output YAML path (default: data/verses/<collection>.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing output")
    parser.add_argument("--diff", action="store_true", help="Show unified diff if output changes")

    args = parser.parse_args()

    try:
        files = _collect_files(args.source, args.source_dir, args.source_glob)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    chaptered = args.format == "chaptered-plain"
    entries = _parse_plain(files, chaptered=chaptered)
    data = _build_yaml(entries, args.collection, chaptered=chaptered)
    rendered = _render_yaml(data)

    output_path = Path(args.output) if args.output else Path("data") / "verses" / f"{args.collection}.yaml"
    existing = output_path.read_text(encoding="utf-8") if output_path.exists() else None

    if args.diff and existing is not None and existing != rendered:
        diff = difflib.unified_diff(
            existing.splitlines(),
            rendered.splitlines(),
            fromfile=str(output_path),
            tofile=str(output_path),
            lineterm="",
        )
        print("\n".join(diff))

    total = len(data)
    print(f"Parsed {total} verses from {len(files)} file(s).")
    print(f"Output: {output_path}")

    if args.dry_run:
        print("Dry run: no files written.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if existing == rendered:
        print("No changes detected; output is up to date.")
        return

    output_path.write_text(rendered, encoding="utf-8")
    print("Wrote canonical YAML.")


if __name__ == "__main__":
    main()
