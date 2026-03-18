"""Tests for multiline-safe devanagari extraction from verse frontmatter (#127)."""

from verse_sdk.audio.generate_audio import extract_devanagari_from_frontmatter


def test_safe_load_folded_multiline_scalar():
    """YAML folded continuation after devanagari: (same issue as #127)."""
    fm = """layout: verse
collection_key: shiv-puran
devanagari: शौनक उवाच । आख्याहि मे
  कथासारं पुराणानां विशेषतः ॥ १॥
title_en: X
"""
    out = extract_devanagari_from_frontmatter(fm)
    assert out is not None
    assert "शौनक" in out
    assert "कथासारं" in out
    assert "विशेषतः" in out


def test_literal_block():
    fm = """devanagari: |
  पंक्ति एक
  पंक्ति दो
layout: verse
"""
    out = extract_devanagari_from_frontmatter(fm)
    assert "पंक्ति एक" in out
    assert "पंक्ति दो" in out


def test_single_line_plain():
    fm = "devanagari: नमो नमः\n"
    assert extract_devanagari_from_frontmatter(fm) == "नमो नमः"
