"""Tests for pure helper functions in verse_sdk/cli/puranic_context.py."""

from pathlib import Path

import pytest
import yaml

from verse_sdk.cli.puranic_context import (
    _VAGUE_SECTIONS,
    _reject_uncited_entries,
    build_prompt,
    cosine_similarity,
    filter_episodes_by_subject,
    load_collection_subject,
    load_project_defaults,
    parse_verse_file,
    update_verse_file,
)

# ---------------------------------------------------------------------------
# _VAGUE_SECTIONS
# ---------------------------------------------------------------------------

def test_vague_sections_contains_common_placeholders():
    assert "unknown" in _VAGUE_SECTIONS
    assert "various" in _VAGUE_SECTIONS
    assert "not directly mentioned" in _VAGUE_SECTIONS
    assert "n/a" in _VAGUE_SECTIONS


# ---------------------------------------------------------------------------
# _reject_uncited_entries
# ---------------------------------------------------------------------------

def _make_entry(entry_id, section, text="Shiv Puran"):
    return {
        "id": entry_id,
        "source_texts": [{"text": text, "section": section}],
    }


def test_reject_uncited_keeps_valid_entry():
    entries = [_make_entry("hanuman-birth", "Rudrasamhita, Chapter 12")]
    result = _reject_uncited_entries(entries)
    assert len(result) == 1
    assert result[0]["id"] == "hanuman-birth"


def test_reject_uncited_drops_vague_section():
    for vague in ["not directly mentioned", "Unknown", "Various", "N/A", "none"]:
        entries = [_make_entry("e1", vague)]
        result = _reject_uncited_entries(entries)
        assert result == [], f"Expected '{vague}' to be rejected"


def test_reject_uncited_drops_bare_numeric_section():
    entries = [_make_entry("e1", "71")]
    result = _reject_uncited_entries(entries)
    assert result == []


def test_reject_uncited_drops_empty_section():
    entries = [_make_entry("e1", "")]
    result = _reject_uncited_entries(entries)
    assert result == []


def test_reject_uncited_cross_scripture_rejected():
    entries = [_make_entry("e1", "Book 3, Chapter 5", text="Mahabharata")]
    result = _reject_uncited_entries(entries, indexed_source_names=["Shiv Puran"])
    assert result == []


def test_reject_uncited_cross_scripture_kept_when_matching():
    entries = [_make_entry("e1", "Book 3, Chapter 5", text="Shiv Puran")]
    result = _reject_uncited_entries(entries, indexed_source_names=["Shiv Puran"])
    assert len(result) == 1


def test_reject_uncited_no_source_texts():
    entries = [{"id": "e1", "source_texts": []}]
    result = _reject_uncited_entries(entries)
    assert result == []


def test_reject_uncited_keeps_valid_among_mixed():
    entries = [
        _make_entry("good", "Rudrasamhita, Chapter 12"),
        _make_entry("bad", "Not directly mentioned"),
    ]
    result = _reject_uncited_entries(entries)
    assert len(result) == 1
    assert result[0]["id"] == "good"


# ---------------------------------------------------------------------------
# load_project_defaults
# ---------------------------------------------------------------------------

def test_load_project_defaults_returns_empty_when_no_file(tmp_path):
    result = load_project_defaults(tmp_path)
    assert result == {}


def test_load_project_defaults_reads_defaults(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "verse-config.yml").write_text(
        "defaults:\n  subject: Hanuman\n  subject_type: deity\n"
    )
    result = load_project_defaults(tmp_path)
    assert result == {"subject": "Hanuman", "subject_type": "deity"}


def test_load_project_defaults_missing_defaults_key(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "verse-config.yml").write_text("other_key: value\n")
    result = load_project_defaults(tmp_path)
    assert result == {}


def test_load_project_defaults_empty_file(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "verse-config.yml").write_text("")
    result = load_project_defaults(tmp_path)
    assert result == {}


# ---------------------------------------------------------------------------
# load_collection_subject
# ---------------------------------------------------------------------------

def test_load_collection_subject_from_collections_yml(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "collections.yml").write_text(
        "hanuman-chalisa:\n  subject: Hanuman\n  subject_type: deity\n"
    )
    subject, subject_type = load_collection_subject("hanuman-chalisa", tmp_path)
    assert subject == "Hanuman"
    assert subject_type == "deity"


def test_load_collection_subject_falls_back_to_project_defaults(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "collections.yml").write_text("hanuman-chalisa:\n  enabled: true\n")
    (data_dir / "verse-config.yml").write_text(
        "defaults:\n  subject: Shiva\n  subject_type: deity\n"
    )
    subject, subject_type = load_collection_subject("hanuman-chalisa", tmp_path)
    assert subject == "Shiva"


def test_load_collection_subject_returns_none_when_not_configured(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "collections.yml").write_text("hanuman-chalisa:\n  enabled: true\n")
    subject, _ = load_collection_subject("hanuman-chalisa", tmp_path)
    assert subject is None


def test_load_collection_subject_collection_overrides_project(tmp_path):
    data_dir = tmp_path / "_data"
    data_dir.mkdir()
    (data_dir / "collections.yml").write_text(
        "hanuman-chalisa:\n  subject: Hanuman\n  subject_type: deity\n"
    )
    (data_dir / "verse-config.yml").write_text(
        "defaults:\n  subject: Shiva\n  subject_type: deity\n"
    )
    subject, _ = load_collection_subject("hanuman-chalisa", tmp_path)
    assert subject == "Hanuman"  # collection wins


# ---------------------------------------------------------------------------
# filter_episodes_by_subject
# ---------------------------------------------------------------------------

def test_filter_episodes_by_subject_matches_keyword():
    episodes = [
        {"id": "hanuman-birth", "keywords": ["Hanuman", "birth"], "summary_en": ""},
        {"id": "shiva-dance", "keywords": ["Shiva", "Tandava"], "summary_en": ""},
    ]
    result = filter_episodes_by_subject(episodes, "Hanuman")
    assert len(result) == 1
    assert result[0]["id"] == "hanuman-birth"


def test_filter_episodes_by_subject_falls_back_to_all_when_no_match():
    episodes = [
        {"id": "shiva-dance", "keywords": ["Shiva"], "summary_en": ""},
    ]
    result = filter_episodes_by_subject(episodes, "Hanuman")
    assert result == episodes  # no match → return original


def test_filter_episodes_by_subject_case_insensitive():
    episodes = [
        {"id": "ep1", "keywords": ["HANUMAN"], "summary_en": "hanuman appears"},
    ]
    result = filter_episodes_by_subject(episodes, "Hanuman")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

def test_cosine_similarity_identical_vectors():
    v = [0.6, 0.8]
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0, abs=1e-6)


def test_cosine_similarity_opposite_vectors():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# parse_verse_file / update_verse_file
# ---------------------------------------------------------------------------

def test_parse_verse_file_valid(tmp_path):
    f = tmp_path / "verse-01.md"
    f.write_text("---\nverse_number: 1\ndevanagari: जय हनुमान\n---\nBody text here")
    fm, body = parse_verse_file(f)
    assert fm["verse_number"] == 1
    assert fm["devanagari"] == "जय हनुमान"
    assert "Body text here" in body


def test_parse_verse_file_missing_returns_none(tmp_path):
    fm, body = parse_verse_file(tmp_path / "nonexistent.md")
    assert fm is None
    assert body is None


def test_parse_verse_file_no_frontmatter(tmp_path):
    f = tmp_path / "verse.md"
    f.write_text("Just body text, no frontmatter")
    fm, body = parse_verse_file(f)
    assert fm == {}


def test_update_verse_file_roundtrip(tmp_path):
    f = tmp_path / "verse-01.md"
    f.write_text("---\nverse_number: 1\n---\nOriginal body")
    fm, body = parse_verse_file(f)
    fm["new_field"] = "added"
    update_verse_file(f, fm, body)
    fm2, body2 = parse_verse_file(f)
    assert fm2["new_field"] == "added"
    assert "Original body" in body2


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_includes_devanagari():
    fm = {"devanagari": "जय हनुमान ज्ञान गुन सागर", "title_en": "Verse 1"}
    prompt = build_prompt(fm, "verse-01")
    assert "जय हनुमान ज्ञान गुन सागर" in prompt


def test_build_prompt_uses_verse_id_as_fallback_title():
    fm = {"devanagari": "text"}
    prompt = build_prompt(fm, "chaupai-06")
    assert "chaupai-06" in prompt


def test_build_prompt_includes_translation():
    fm = {"translation": {"en": "Victory to Hanuman"}}
    prompt = build_prompt(fm, "v1")
    assert "Victory to Hanuman" in prompt
