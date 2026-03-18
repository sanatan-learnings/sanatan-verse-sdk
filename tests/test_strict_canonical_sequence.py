"""Strict canonical verse-id mapping (#142)."""

from __future__ import annotations

from pathlib import Path

from verse_sdk.cli.generate import get_verse_sequence, infer_verse_id


def test_get_verse_sequence_filters_legacy_when_chapter_based_present(tmp_path: Path):
    (tmp_path / "data" / "verses").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "verses" / "shiv-puran.yaml").write_text(
        """
_meta:
  sequence:
    - chapter-01-shloka-01
    - verse-01
chapter-01-shloka-01: {}
verse-01: {}
""".lstrip(),
        encoding="utf-8",
    )

    seq, source = get_verse_sequence("shiv-puran", project_dir=tmp_path)
    assert source == "explicit"
    assert seq == ["chapter-01-shloka-01"]


def test_infer_verse_id_uses_filtered_sequence(tmp_path: Path):
    (tmp_path / "data" / "verses").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "verses" / "shiv-puran.yaml").write_text(
        """
_meta:
  sequence:
    - chapter-01-shloka-01
    - verse-01
chapter-01-shloka-01: {}
verse-01: {}
""".lstrip(),
        encoding="utf-8",
    )

    verse_id = infer_verse_id("shiv-puran", 1, project_dir=tmp_path)
    assert verse_id == "chapter-01-shloka-01"

    verse_id_2 = infer_verse_id("shiv-puran", 2, project_dir=tmp_path)
    assert verse_id_2 is None

