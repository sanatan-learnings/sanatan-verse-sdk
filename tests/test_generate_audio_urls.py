"""Tests for wiring audio URLs into verse frontmatter (#122)."""

from pathlib import Path

import yaml

from verse_sdk.cli.generate import update_verse_frontmatter_audio_urls


def test_update_verse_frontmatter_audio_urls(tmp_path):
    vf = tmp_path / "chaupai-01.md"
    vf.write_text(
        "---\n"
        "layout: verse\n"
        "collection_key: hanuman-chalisa\n"
        "title_en: Test\n"
        "---\n",
        encoding="utf-8",
    )
    assert update_verse_frontmatter_audio_urls(vf, "hanuman-chalisa", "chaupai-01")
    parts = vf.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["audio_full"] == "/audio/hanuman-chalisa/chaupai-01-full.mp3"
    assert fm["audio_slow"] == "/audio/hanuman-chalisa/chaupai-01-slow.mp3"
    assert fm["audio"] == fm["audio_full"]
