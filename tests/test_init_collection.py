"""Tests for verse_sdk/cli/init_collection.py."""

from pathlib import Path

import yaml

from verse_sdk.cli.init_collection import (
    detect_sections,
    generate_index_html,
    scaffold_collection,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_verses(verses_dir: Path, *stems: str):
    verses_dir.mkdir(parents=True, exist_ok=True)
    for stem in stems:
        (verses_dir / f"{stem}.md").write_text(f"---\nverse_id: {stem}\n---\n")


def _make_collections_yml(project_dir: Path, key: str, **extra):
    data_dir = project_dir / "_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "name_en": "Test Collection",
        "name_hi": "टेस्ट",
        "icon": "📿",
        "permalink_base": f"/{key}/",
        "subdirectory": key,
        "enabled": True,
        **extra,
    }
    (data_dir / "collections.yml").write_text(yaml.dump({key: config}))
    return config


# ---------------------------------------------------------------------------
# detect_sections
# ---------------------------------------------------------------------------

def test_detect_sections_empty_dir(tmp_path):
    result = detect_sections(tmp_path / "nonexistent")
    assert result == []


def test_detect_sections_single_type(tmp_path):
    verses_dir = tmp_path / "_verses" / "test"
    _make_verses(verses_dir, "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04", "chaupai-05")
    sections = detect_sections(verses_dir)
    assert len(sections) == 1
    assert sections[0]["prefix"] == "chaupai"
    assert len(sections[0]["verse_ids"]) == 5
    assert sections[0]["is_loop"] is True


def test_detect_sections_loop_threshold(tmp_path):
    verses_dir = tmp_path / "_verses" / "test"
    # Exactly 3 → not a loop; 4 → loop
    _make_verses(verses_dir, "doha-01", "doha-02", "doha-03")
    sections = detect_sections(verses_dir)
    assert sections[0]["is_loop"] is False

    verses_dir2 = tmp_path / "_verses" / "test2"
    _make_verses(verses_dir2, "doha-01", "doha-02", "doha-03", "doha-04")
    sections2 = detect_sections(verses_dir2)
    assert sections2[0]["is_loop"] is True


def test_detect_sections_multiple_types_with_sequence(tmp_path):
    verses_dir = tmp_path / "_verses" / "test"
    _make_verses(verses_dir,
                 "doha-opening",
                 "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04",
                 "doha-closing")
    sequence = ["doha-opening", "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04", "doha-closing"]
    sections = detect_sections(verses_dir, sequence=sequence)
    assert len(sections) == 3
    assert sections[0]["prefix"] == "doha"
    assert sections[0]["verse_ids"] == ["doha-opening"]
    assert sections[1]["prefix"] == "chaupai"
    assert sections[1]["is_loop"] is True
    assert sections[2]["prefix"] == "doha"
    assert sections[2]["verse_ids"] == ["doha-closing"]


def test_detect_sections_multiple_types_alpha_fallback(tmp_path):
    """Without a sequence, alphabetical sort merges both doha groups."""
    verses_dir = tmp_path / "_verses" / "test"
    _make_verses(verses_dir,
                 "doha-opening",
                 "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04",
                 "doha-closing")
    sections = detect_sections(verses_dir)  # no sequence
    # Alphabetical: chaupai-* < doha-closing < doha-opening → 2 sections
    assert len(sections) == 2
    assert sections[0]["prefix"] == "chaupai"
    assert sections[1]["prefix"] == "doha"
    assert len(sections[1]["verse_ids"]) == 2  # both dohas merged


def test_detect_sections_qualifier(tmp_path):
    verses_dir = tmp_path / "_verses" / "test"
    _make_verses(verses_dir, "doha-opening")
    sections = detect_sections(verses_dir)
    assert sections[0]["qualifier"] == "opening"


def test_detect_sections_numbered_has_no_qualifier(tmp_path):
    verses_dir = tmp_path / "_verses" / "test"
    _make_verses(verses_dir, "doha-01")
    sections = detect_sections(verses_dir)
    assert sections[0]["qualifier"] is None


# ---------------------------------------------------------------------------
# generate_index_html
# ---------------------------------------------------------------------------

def test_generate_includes_collection_name():
    config = {"name_en": "Bajrang Baan", "name_hi": "बजरंग बाण", "icon": "🛡️", "permalink_base": "/bajrang-baan/"}
    html = generate_index_html("bajrang-baan", config, [])
    assert "Bajrang Baan" in html
    assert "बजरंग बाण" in html


def test_generate_includes_puranic_legend():
    config = {"name_en": "Test", "permalink_base": "/test/"}
    html = generate_index_html("test-col", config, [])
    assert "puranic-legend-compact" in html
    assert "Puranic stories" in html


def test_generate_includes_hero_image():
    config = {"name_en": "Test", "permalink_base": "/test/"}
    html = generate_index_html("my-collection", config, [])
    assert "my-collection/modern-minimalist/title-page.png" in html


def test_generate_loop_section_contains_for_loop():
    config = {"name_en": "Test", "permalink_base": "/test/"}
    sections = [{"prefix": "chaupai", "verse_ids": ["chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04"], "is_loop": True, "qualifier": None}]
    html = generate_index_html("test", config, sections)
    assert "for verse in chaupai_verses" in html
    assert "has-puranic-context" in html
    assert "puranic-badge" in html


def test_generate_individual_section_contains_verse_ids():
    config = {"name_en": "Test", "permalink_base": "/test/"}
    sections = [{"prefix": "doha", "verse_ids": ["doha-opening"], "is_loop": False, "qualifier": "opening"}]
    html = generate_index_html("test", config, sections)
    assert "doha-opening" in html
    assert "Opening Doha" in html
    assert "has-puranic-context" in html


def test_generate_layout_frontmatter():
    config = {"name_en": "Test", "permalink_base": "/test/"}
    html = generate_index_html("test", config, [])
    assert html.startswith("---\n")
    assert "layout: default" in html
    assert "collection_key: test" in html


# ---------------------------------------------------------------------------
# scaffold_collection
# ---------------------------------------------------------------------------

def test_scaffold_creates_index_html(tmp_path):
    key = "bajrang-baan"
    _make_collections_yml(tmp_path, key)
    verses_dir = tmp_path / "_verses" / key
    _make_verses(verses_dir, "doha-opening",
                 "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04",
                 "doha-closing")
    result = scaffold_collection(key, tmp_path)
    assert result is True
    output = tmp_path / key / "index.html"
    assert output.exists()
    content = output.read_text()
    assert "bajrang-baan" in content
    assert "puranic-legend-compact" in content


def test_scaffold_skips_existing_without_overwrite(tmp_path):
    key = "test-col"
    _make_collections_yml(tmp_path, key)
    output = tmp_path / key / "index.html"
    output.parent.mkdir(parents=True)
    output.write_text("original")
    scaffold_collection(key, tmp_path, overwrite=False)
    assert output.read_text() == "original"


def test_scaffold_overwrites_with_flag(tmp_path):
    key = "test-col"
    _make_collections_yml(tmp_path, key)
    output = tmp_path / key / "index.html"
    output.parent.mkdir(parents=True)
    output.write_text("original")
    scaffold_collection(key, tmp_path, overwrite=True)
    assert output.read_text() != "original"


def test_scaffold_unknown_collection_returns_false(tmp_path):
    _make_collections_yml(tmp_path, "real-collection")
    result = scaffold_collection("nonexistent", tmp_path)
    assert result is False


def test_scaffold_respects_canonical_sequence(tmp_path):
    key = "bajrang-baan"
    _make_collections_yml(tmp_path, key)
    verses_dir = tmp_path / "_verses" / key
    _make_verses(verses_dir, "doha-opening",
                 "chaupai-01", "chaupai-02", "chaupai-03", "chaupai-04",
                 "doha-closing")
    # Write canonical YAML with sequence
    verses_data_dir = tmp_path / "data" / "verses"
    verses_data_dir.mkdir(parents=True)
    (verses_data_dir / f"{key}.yaml").write_text(
        "_meta:\n  sequence:\n    - doha-opening\n"
        "    - chaupai-01\n    - chaupai-02\n    - chaupai-03\n    - chaupai-04\n"
        "    - doha-closing\n"
    )
    scaffold_collection(key, tmp_path, overwrite=True)
    content = (tmp_path / key / "index.html").read_text()
    # doha-opening should appear before chaupai block, which appears before doha-closing
    assert content.index("doha-opening") < content.index("chaupai-")
    assert content.index("chaupai-") < content.index("doha-closing")


def test_scaffold_creates_parent_dir(tmp_path):
    key = "new-collection"
    _make_collections_yml(tmp_path, key)
    output = tmp_path / key / "index.html"
    assert not output.parent.exists()
    scaffold_collection(key, tmp_path)
    assert output.exists()
