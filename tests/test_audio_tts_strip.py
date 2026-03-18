"""TTS normalization: strip ॥ N ॥ from end; optional frontmatter overrides (#129)."""

import pytest

from verse_sdk.audio.generate_audio import (
    strip_trailing_verse_markers_for_tts,
    tts_input_from_verse_frontmatter,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("श्लोक पाठ ॥ १॥", "श्लोक पाठ"),
        ("श्लोक पाठ॥१॥", "श्लोक पाठ"),
        ("श्लोक पाठ ॥ 1 ॥", "श्लोक पाठ"),
        ("नमो नमः", "नमो नमः"),
        ("अंत ॥ १२॥", "अंत"),
    ],
)
def test_strip_trailing_verse_markers(raw, expected):
    assert strip_trailing_verse_markers_for_tts(raw) == expected


def test_tts_override_tts_text():
    fm = """devanagari: श्लोक ॥ १॥
tts_text: कस्टम टीटीएस
"""
    assert tts_input_from_verse_frontmatter(fm, "ignored") == "कस्टम टीटीएस"


def test_tts_override_devanagari_audio():
    fm = """devanagari: आ
devanagari_audio: ब
"""
    assert tts_input_from_verse_frontmatter(fm, "आ") == "ब"


def test_tts_prefers_tts_text_over_devanagari_audio():
    fm = """devanagari: x
tts_text: first
devanagari_audio: second
"""
    assert tts_input_from_verse_frontmatter(fm, "x") == "first"


def test_tts_strips_when_no_override():
    fm = "layout: verse\n"
    assert tts_input_from_verse_frontmatter(fm, "पाठ ॥ २॥") == "पाठ"
    assert tts_input_from_verse_frontmatter(fm, "विशेषतः ॥ १॥") == "विशेषतः"
