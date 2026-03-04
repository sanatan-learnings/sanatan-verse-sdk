"""Tests for YAML scene loading behavior in verse_sdk/cli/generate.py."""

from pathlib import Path

from verse_sdk.cli.generate import _SCENE_SEQUENCE_WARNED_FILES, load_scenes_from_yaml


def _write_scenes_file(project_dir: Path, collection: str, include_sequence: bool) -> None:
    scenes_dir = project_dir / "data" / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    sequence_block = "  sequence:\n    - verse-01\n" if include_sequence else ""
    content = (
        "_meta:\n"
        f"  collection: {collection}\n"
        f"{sequence_block}"
        "scenes:\n"
        "  verse-01:\n"
        "    title: \"Verse 1\"\n"
        "    description: |\n"
        "      Scene description.\n"
    )
    (scenes_dir / f"{collection}.yml").write_text(content, encoding="utf-8")


def test_load_scenes_ignores_meta_sequence_and_warns_once(tmp_path, capsys):
    _SCENE_SEQUENCE_WARNED_FILES.clear()
    _write_scenes_file(tmp_path, "shiv-puran", include_sequence=True)

    data = load_scenes_from_yaml("shiv-puran", tmp_path)
    err = capsys.readouterr().err

    assert isinstance(data, dict)
    assert "_meta" in data
    assert "sequence" not in data["_meta"]
    assert "Ignoring _meta.sequence" in err
    assert "data/verses/shiv-puran.yml" in err


def test_load_scenes_warns_only_once_per_file(tmp_path, capsys):
    _SCENE_SEQUENCE_WARNED_FILES.clear()
    _write_scenes_file(tmp_path, "shiv-puran", include_sequence=True)

    _ = load_scenes_from_yaml("shiv-puran", tmp_path)
    first_err = capsys.readouterr().err
    _ = load_scenes_from_yaml("shiv-puran", tmp_path)
    second_err = capsys.readouterr().err

    assert "Ignoring _meta.sequence" in first_err
    assert second_err == ""
