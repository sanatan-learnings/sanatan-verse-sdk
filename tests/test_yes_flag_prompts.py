"""Tests for --yes/-y confirmation prompt bypass (#140)."""

from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from verse_sdk.cli.generate import find_next_verse
from verse_sdk.cli.init import init_project


def test_verse_init_yes_skips_nonempty_dir_prompt(tmp_path, monkeypatch):
    # Trigger "Current directory is not empty" confirmation.
    (tmp_path / "dummy.txt").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def _boom(*_args, **_kwargs):
        raise AssertionError("input() should not be called when --yes is set")

    monkeypatch.setattr(builtins, "input", _boom)

    # Minimal to keep scaffolding small.
    init_project(project_name=None, minimal=True, collections=None, num_verses=1, assume_yes=True)

    assert (tmp_path / "_data" / "collections.yml").exists()


def test_verse_generate_yes_skips_auto_sequence_prompt(tmp_path, monkeypatch):
    # Force path: source != explicit → would normally prompt.
    def _fake_get_verse_sequence(_collection: str, _project_dir: Path):
        return ["shloka-01"], "yaml-keys"

    monkeypatch.setattr("verse_sdk.cli.generate.get_verse_sequence", _fake_get_verse_sequence)

    def _boom(*_args, **_kwargs):
        raise AssertionError("input() should not be called when --yes is set")

    monkeypatch.setattr(builtins, "input", _boom)

    next_verse = find_next_verse(
        "shiv-puran",
        project_dir=tmp_path,
        assume_yes=True,
    )

    # When _verses/<collection>/ doesn't exist, find_next_verse returns 1.
    assert next_verse == 1

