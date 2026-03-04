"""Tests for --all sequence resolution helpers in verse_sdk/cli/generate.py."""

from verse_sdk.cli.generate import get_all_verse_positions


def test_get_all_verse_positions_from_explicit_sequence(tmp_path):
    verses_dir = tmp_path / "data" / "verses"
    verses_dir.mkdir(parents=True, exist_ok=True)
    (verses_dir / "shiv-puran.yaml").write_text(
        """
_meta:
  sequence:
    - verse-01
    - verse-02
    - verse-03
verse-01:
  devanagari: "A"
verse-02:
  devanagari: "B"
verse-03:
  devanagari: "C"
""".strip()
    )

    assert get_all_verse_positions("shiv-puran", tmp_path) == [1, 2, 3]


def test_get_all_verse_positions_from_yaml_keys_fallback(tmp_path):
    verses_dir = tmp_path / "data" / "verses"
    verses_dir.mkdir(parents=True, exist_ok=True)
    (verses_dir / "hanuman-chalisa.yaml").write_text(
        """
verse-02:
  devanagari: "B"
verse-01:
  devanagari: "A"
verse-03:
  devanagari: "C"
""".strip()
    )

    assert get_all_verse_positions("hanuman-chalisa", tmp_path) == [1, 2, 3]


def test_get_all_verse_positions_requires_canonical_file(tmp_path):
    assert get_all_verse_positions("missing-collection", tmp_path) is None
