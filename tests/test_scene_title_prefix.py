"""Scene title + verse-type parsing fixes for chapter-based IDs (#139)."""

from __future__ import annotations

from pathlib import Path

import yaml

from verse_sdk.cli.generate import (
    create_verse_file_with_content,
    ensure_scene_description_exists,
    extract_verse_type_from_id,
    strip_verse_prefix_from_title,
)


def test_extract_verse_type_from_id_chapter_shloka():
    assert extract_verse_type_from_id("chapter-01-shloka-01") == "shloka"
    assert extract_verse_type_from_id("chapter-02-chaupai-05") == "chaupai"
    assert extract_verse_type_from_id("chapter-18-doha-78") == "doha"


def test_extract_verse_type_from_id_simple():
    assert extract_verse_type_from_id("shloka-01") == "shloka"
    assert extract_verse_type_from_id("chaupai-05") == "chaupai"
    assert extract_verse_type_from_id("verse-02") == "verse"


def test_strip_verse_prefix_from_title():
    assert strip_verse_prefix_from_title("Shloka 1: Ocean of Knowledge") == "Ocean of Knowledge"
    assert strip_verse_prefix_from_title("Shloka 1 Ocean of Knowledge") == "Ocean of Knowledge"
    assert (
        strip_verse_prefix_from_title("Chapter 1: Seeking the Essence of Puranas")
        == "Seeking the Essence of Puranas"
    )
    assert strip_verse_prefix_from_title("Already descriptive") == "Already descriptive"
    assert strip_verse_prefix_from_title("श्लोक 1: शीर्षक") == "शीर्षक"


def test_create_verse_file_sanitizes_title_prefixes(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("verse_sdk.cli.generate.get_navigation_from_sequence", lambda *_args, **_kwargs: (None, None))

    verse_file = tmp_path / "_verses" / "shiv-puran" / "chapter-01-shloka-01.md"
    content = {
        "title_en": "Shloka 1: Seeking the Essence of Puranas",
        "title_hi": "श्लोक 1: पुराणों का सार खोजते हुए",
        "devanagari": "देवनागरी टेक्स्ट",
        "transliteration": "devanagari",
        "phonetic_notes": [],
        "word_meanings": [],
        "literal_translation": {"en": "", "hi": ""},
        "interpretive_meaning": {"en": "", "hi": ""},
        "story": {"en": "", "hi": ""},
        "practical_application": {
            "teaching": {"en": "", "hi": ""},
            "when_to_use": {"en": "", "hi": ""},
        },
        "meaning": "",
        "translation": {"en": ""},
    }

    ok = create_verse_file_with_content(
        verse_file=verse_file,
        content=content,
        collection="shiv-puran",
        verse_num=1,
        verse_id="chapter-01-shloka-01",
        project_dir=tmp_path,
    )
    assert ok is True

    raw = verse_file.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    frontmatter = yaml.safe_load(parts[1]) or {}
    assert "Shloka" not in frontmatter.get("title_en", "")
    assert frontmatter.get("title_en", "").startswith("Seeking the Essence of Puranas")
    assert "श्लोक" not in frontmatter.get("title_hi", "")


def test_ensure_scene_description_strips_prefix_when_title_en_is_prefixed(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)

    def _fake_generate_scene_description(devanagari_text: str, verse_id: str, collection: str):
        return "A generated scene description."

    def _fake_scene_exists(collection: str, verse_id: str, project_dir: Path = Path.cwd()):
        return False

    monkeypatch.setattr(
        "verse_sdk.cli.generate.generate_scene_description", _fake_generate_scene_description
    )
    monkeypatch.setattr(
        "verse_sdk.cli.generate.validate_scene_description_exists", _fake_scene_exists
    )

    ok, _ = ensure_scene_description_exists(
        collection="shiv-puran",
        verse_position=1,
        verse_id="chapter-01-shloka-01",
        devanagari_text="देवनागरी",
        title_en="Chapter 1: Seeking the Essence of Puranas",
        scene_mode="auto-generate",
    )

    assert ok is True
    scenes_file = tmp_path / "data" / "scenes" / "shiv-puran.yml"
    scenes_data = yaml.safe_load(scenes_file.read_text(encoding="utf-8"))
    title = scenes_data["scenes"]["chapter-01-shloka-01"]["title"]
    assert "Chapter 1:" not in title
    assert title.startswith("Seeking the Essence of Puranas")

