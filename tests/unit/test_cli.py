"""Tests for the albumgrab CLI entry point.

Slice 1 pins only the entry-point surface (help/usage). The behavioral CLI
tests (listing, selection loop, notices) arrive with Slice 3.
"""

from typer.testing import CliRunner

from albumgrab.cli import app

runner = CliRunner()


def test_help_shows_usage_and_artist_argument() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "artist" in result.output
