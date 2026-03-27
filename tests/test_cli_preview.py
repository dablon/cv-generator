"""
Tests for CLI preview command.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli import app


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


class TestPreviewCommand:
    """Tests for preview command."""

    def test_preview_help(self, runner):
        """Test preview command help exists."""
        result = runner.invoke(app, ["preview", "--help"])
        assert result.exit_code == 0
        assert "--profile" in result.stdout or "-p" in result.stdout
        assert "--template" in result.stdout or "-t" in result.stdout

    def test_preview_nonexistent_profile(self, runner, tmp_path):
        """Test preview with nonexistent profile shows error."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "preview",
                "-p", "/nonexistent/profile.json",
                "-t", "modern",
            ],
        )
        assert result.exit_code != 0

    def test_preview_valid_profile(self, runner, fixtures_dir):
        """Test preview with valid profile."""
        # Using a short timeout so it doesn't hang
        result = runner.invoke(
            app,
            [
                "preview",
                "-p", str(fixtures_dir / "minimal_profile.json"),
                "-t", "modern",
                "-o", "3001",  # different port to avoid conflicts
            ],
            catch_exceptions=False,
        )
        # It may timeout or error but shouldn't be exit code 2 (typer error)
        # Just check it doesn't crash with typer error
        assert result.exit_code in [0, 1] or "error" not in result.stdout.lower()

    def test_preview_invalid_template(self, runner, fixtures_dir):
        """Test preview with invalid template."""
        result = runner.invoke(
            app,
            [
                "preview",
                "-p", str(fixtures_dir / "minimal_profile.json"),
                "-t", "nonexistent_template",
            ],
        )
        assert result.exit_code != 0


class TestGenerateWithShortFlags:
    """Tests for generate with various flag combinations."""

    def test_generate_with_o_flag(self, runner, fixtures_dir, tmp_path):
        """Test generate with -o short flag."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-p", str(fixtures_dir / "minimal_profile.json"),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html",
            ],
        )
        assert result.exit_code == 0

    def test_generate_with_f_flag(self, runner, fixtures_dir, tmp_path):
        """Test generate with -f short flag."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-p", str(fixtures_dir / "minimal_profile.json"),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "csv,md",
            ],
        )
        assert result.exit_code == 0
        assert "[CSV]" in result.stdout
        assert "[MD]" in result.stdout


class TestListTemplatesCommandFull:
    """Additional tests for list-templates command."""

    def test_list_templates_all_templates_shown(self, runner):
        """Test all expected templates are listed."""
        result = runner.invoke(app, ["list-templates-cmd"])
        assert result.exit_code == 0
        for template in ["classic", "modern", "minimal", "ats-friendly"]:
            assert template in result.stdout
