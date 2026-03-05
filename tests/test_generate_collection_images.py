"""Tests for auto-generation of collection overview images in verse-generate."""

import yaml

from verse_sdk.cli.generate import ensure_collection_overview_images, ensure_collection_scene_entries


def test_ensure_collection_scene_entries_upserts_cover(tmp_path):
    scenes_dir = tmp_path / "data" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    scenes_file = scenes_dir / "shiv-puran.yml"
    scenes_file.write_text(
        """
_meta:
  collection: shiv-puran
scenes:
  verse-01:
    title: Verse 1
    description: Existing description
""".strip(),
        encoding="utf-8",
    )

    ensure_collection_scene_entries("shiv-puran", project_dir=tmp_path)

    data = yaml.safe_load(scenes_file.read_text(encoding="utf-8"))
    assert "cover" in data["scenes"]
    assert "verse-01" in data["scenes"]


def test_ensure_collection_overview_images_only_generates_missing(tmp_path, monkeypatch):
    image_dir = tmp_path / "images" / "shiv-puran" / "modern-minimalist"
    image_dir.mkdir(parents=True, exist_ok=True)
    (image_dir / "cover.png").write_bytes(b"ok")

    calls = []

    def _fake_generate_image(collection, verse, theme, verse_id=None, verbose=False, quiet=False):
        calls.append((collection, verse, theme, verse_id, verbose, quiet))
        return True

    monkeypatch.setattr("verse_sdk.cli.generate.generate_image", _fake_generate_image)

    ok = ensure_collection_overview_images(
        "shiv-puran",
        "modern-minimalist",
        project_dir=tmp_path,
        dry_run=False,
    )

    assert ok is True
    assert calls == []
    assert (tmp_path / "images" / "cover.png").exists()


def test_ensure_collection_overview_images_dry_run_does_not_call_generator(tmp_path, monkeypatch):
    calls = []

    def _fake_generate_image(collection, verse, theme, verse_id=None, verbose=False, quiet=False):
        calls.append((collection, verse, theme, verse_id, verbose, quiet))
        return True

    monkeypatch.setattr("verse_sdk.cli.generate.generate_image", _fake_generate_image)

    ok = ensure_collection_overview_images(
        "hanuman-chalisa",
        "modern-minimalist",
        project_dir=tmp_path,
        dry_run=True,
    )

    assert ok is True
    assert calls == []


def test_ensure_collection_overview_images_generates_collection_cover_when_missing(tmp_path, monkeypatch):
    calls = []

    def _fake_generate_image(collection, verse, theme, verse_id=None, verbose=False, quiet=False):
        calls.append((collection, verse, theme, verse_id, verbose, quiet))
        out = tmp_path / "images" / collection / theme / f"{verse_id}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"ok")
        return True

    monkeypatch.setattr("verse_sdk.cli.generate.generate_image", _fake_generate_image)

    ok = ensure_collection_overview_images(
        "shiv-puran",
        "modern-minimalist",
        project_dir=tmp_path,
        dry_run=False,
    )

    assert ok is True
    assert calls == [("shiv-puran", 0, "modern-minimalist", "cover", False, False)]
    assert (tmp_path / "images" / "shiv-puran" / "modern-minimalist" / "cover.png").exists()
    assert (tmp_path / "images" / "cover.png").exists()
