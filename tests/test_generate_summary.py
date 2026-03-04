"""Tests for generation summary status helpers."""

from verse_sdk.cli.generate import operation_status


def test_operation_status_success():
    symbol, label = operation_status(True)
    assert symbol == "✓"
    assert label == "Success"


def test_operation_status_failure():
    symbol, label = operation_status(False)
    assert symbol == "✗"
    assert label == "Failed"


def test_operation_status_skipped_with_custom_label():
    symbol, label = operation_status(None, skipped_label="Skipped (new file)")
    assert symbol == "•"
    assert label == "Skipped (new file)"
