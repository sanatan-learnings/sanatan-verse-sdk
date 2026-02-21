"""Tests for verse_sdk/utils/ — yaml_parser and file_utils."""

import json
from pathlib import Path

import pytest

from verse_sdk.cli.generate import extract_verse_number_from_id
from verse_sdk.utils.file_utils import (
    ensure_directory,
    find_markdown_files,
    get_file_size_kb,
    read_json,
    write_json,
)
from verse_sdk.utils.yaml_parser import extract_yaml_frontmatter, get_nested_value

# ---------------------------------------------------------------------------
# extract_yaml_frontmatter
# ---------------------------------------------------------------------------

def test_extract_frontmatter_basic(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("---\nverse_number: 1\ntitle_en: Test\n---\nBody text")
    result = extract_yaml_frontmatter(f)
    assert result == {"verse_number": 1, "title_en": "Test"}


def test_extract_frontmatter_no_delimiter(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("No frontmatter here")
    assert extract_yaml_frontmatter(f) is None


def test_extract_frontmatter_unclosed(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("---\nverse_number: 1\n")
    assert extract_yaml_frontmatter(f) is None


def test_extract_frontmatter_unicode(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("---\ndevanagari: श्रीगुरु चरन सरोज रज\n---\nBody")
    result = extract_yaml_frontmatter(f)
    assert result["devanagari"] == "श्रीगुरु चरन सरोज रज"


def test_extract_frontmatter_nested(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("---\ntitle:\n  en: Hello\n  hi: नमस्ते\n---\nBody")
    result = extract_yaml_frontmatter(f)
    assert result["title"] == {"en": "Hello", "hi": "नमस्ते"}


# ---------------------------------------------------------------------------
# get_nested_value
# ---------------------------------------------------------------------------

def test_get_nested_flat_key():
    assert get_nested_value({"foo": "bar"}, "foo") == "bar"


def test_get_nested_missing_key_returns_default():
    assert get_nested_value({"foo": "bar"}, "baz", default="DEFAULT") == "DEFAULT"


def test_get_nested_missing_key_default_none():
    assert get_nested_value({}, "missing") is None


def test_get_nested_with_lang():
    data = {"title": {"en": "Hello", "hi": "नमस्ते"}}
    assert get_nested_value(data, "title", lang="en") == "Hello"
    assert get_nested_value(data, "title", lang="hi") == "नमस्ते"


def test_get_nested_lang_missing_falls_back_to_dict():
    data = {"title": {"en": "Hello"}}
    result = get_nested_value(data, "title", lang="fr")
    assert result == {"en": "Hello"}


def test_get_nested_non_dict_value_ignores_lang():
    data = {"count": 42}
    assert get_nested_value(data, "count", lang="en") == 42


# ---------------------------------------------------------------------------
# file_utils
# ---------------------------------------------------------------------------

def test_ensure_directory_creates(tmp_path):
    new_dir = tmp_path / "a" / "b" / "c"
    assert not new_dir.exists()
    ensure_directory(new_dir)
    assert new_dir.is_dir()


def test_ensure_directory_idempotent(tmp_path):
    ensure_directory(tmp_path)  # already exists — should not raise


def test_write_and_read_json_roundtrip(tmp_path):
    data = {"verse": 1, "text": "श्रीराम", "tags": ["a", "b"]}
    out = tmp_path / "data.json"
    write_json(data, out)
    assert out.exists()
    loaded = read_json(out)
    assert loaded == data


def test_write_json_creates_parent_dirs(tmp_path):
    out = tmp_path / "nested" / "deep" / "data.json"
    write_json({"key": "value"}, out)
    assert out.exists()


def test_write_json_unicode(tmp_path):
    data = {"devanagari": "हनुमान"}
    out = tmp_path / "unicode.json"
    write_json(data, out)
    raw = out.read_text(encoding="utf-8")
    assert "हनुमान" in raw  # ensure_ascii=False


def test_write_json_pretty(tmp_path):
    out = tmp_path / "pretty.json"
    write_json({"a": 1}, out, pretty=True)
    raw = out.read_text()
    assert "\n" in raw  # pretty-printed has newlines


def test_write_json_compact(tmp_path):
    out = tmp_path / "compact.json"
    write_json({"a": 1}, out, pretty=False)
    raw = out.read_text().strip()
    assert raw == '{"a": 1}'


def test_find_markdown_files(tmp_path):
    (tmp_path / "verse-01.md").write_text("a")
    (tmp_path / "verse-02.md").write_text("b")
    (tmp_path / "notes.txt").write_text("c")
    files = find_markdown_files(tmp_path)
    names = [f.name for f in files]
    assert "verse-01.md" in names
    assert "verse-02.md" in names
    assert "notes.txt" not in names


def test_get_file_size_kb(tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"x" * 1024)
    assert get_file_size_kb(f) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# extract_verse_number_from_id
# ---------------------------------------------------------------------------

def test_extract_verse_number_numbered():
    assert extract_verse_number_from_id("chaupai-16") == 16


def test_extract_verse_number_zero_padded():
    assert extract_verse_number_from_id("doha-03") == 3


def test_extract_verse_number_named_returns_none():
    assert extract_verse_number_from_id("doha-opening") is None


def test_extract_verse_number_named_closing_returns_none():
    assert extract_verse_number_from_id("doha-closing") is None


def test_extract_verse_number_no_suffix_returns_none():
    assert extract_verse_number_from_id("mangalacharan") is None


def test_extract_verse_number_underscore_separator():
    assert extract_verse_number_from_id("shloka_01") == 1
