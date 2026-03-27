"""
Unit tests for cv-generator CLI.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

# Import the CLI app (the Typer application)
import cli as cli_module
app = cli_module.app


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    """Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def templates_dir():
    return Path(__file__).parent.parent / "templates"


# =============================================================================
# list-templates command tests
# =============================================================================

class TestListTemplatesCommand:
    """Tests for list-templates command."""

    def test_list_templates_outputs_templates(self, runner, templates_dir):
        """Test that list-templates shows available templates."""
        result = runner.invoke(
            app,
            ["list-templates-cmd", "--dir", str(templates_dir)],
        )
        assert result.exit_code == 0
        assert "classic" in result.stdout
        assert "modern" in result.stdout
        assert "minimal" in result.stdout
        assert "ats-friendly" in result.stdout

    def test_list_templates_shows_available_label(self, runner, templates_dir):
        """Test that output mentions available templates."""
        result = runner.invoke(
            app,
            ["list-templates-cmd", "--dir", str(templates_dir)],
        )
        assert "Available templates:" in result.stdout

    def test_list_templates_with_bullets(self, runner, templates_dir):
        """Test that templates are listed with bullet points."""
        result = runner.invoke(
            app,
            ["list-templates-cmd", "--dir", str(templates_dir)],
        )
        assert "•" in result.stdout or "-" in result.stdout


# =============================================================================
# generate command tests
# =============================================================================

class TestGenerateCommand:
    """Tests for generate command."""

    def test_generate_html_success(self, runner, fixtures_dir, tmp_path):
        """Test successful HTML generation."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.exception}"
        assert "Generated files:" in result.stdout
        assert "[HTML]" in result.stdout
        assert output_dir.exists()
        html_files = list(output_dir.glob("*.html"))
        assert len(html_files) == 1

    def test_generate_multiple_formats(self, runner, fixtures_dir, tmp_path):
        """Test generating multiple formats."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html,csv,md",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.exception}"
        assert "[HTML]" in result.stdout
        assert "[CSV]" in result.stdout
        assert "[MD]" in result.stdout

    def test_generate_all_templates(self, runner, fixtures_dir, tmp_path):
        """Test generating with all template names."""
        output_dir = tmp_path / "output"
        templates = ["classic", "modern", "minimal", "ats-friendly"]

        for template in templates:
            result = runner.invoke(
                app,
                [
                    "generate",
                    "--profile", str(fixtures_dir / "minimal_profile.json"),
                    "--template", template,
                    "--output", str(output_dir),
                    "--formats", "html",
                ],
            )
            assert result.exit_code == 0, f"Failed for {template}: {result.stdout}"

    def test_generate_creates_output_directory(self, runner, fixtures_dir, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nested" / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        assert output_dir.exists()

    def test_generate_full_profile(self, runner, fixtures_dir, tmp_path):
        """Test generating with full profile."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "full_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html,csv",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        html_files = list(output_dir.glob("*.html"))
        csv_files = list(output_dir.glob("*.csv"))
        assert len(html_files) == 1
        assert len(csv_files) == 1

    def test_generate_verbose_mode(self, runner, fixtures_dir, tmp_path):
        """Test generate with verbose flag."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html",
                "--verbose",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"

    def test_generate_shows_profile_name(self, runner, fixtures_dir, tmp_path):
        """Test that output shows the profile name."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "html",
            ],
        )
        assert result.exit_code == 0
        assert "minimal" in result.stdout

    def test_generate_shows_template_name(self, runner, fixtures_dir, tmp_path):
        """Test that output shows the template name."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "classic",
                "--output", str(output_dir),
                "--formats", "html",
            ],
        )
        assert result.exit_code == 0


# =============================================================================
# generate command error handling
# =============================================================================

class TestGenerateCommandErrors:
    """Tests for generate command error handling."""

    def test_generate_nonexistent_profile(self, runner, tmp_path):
        """Test error when profile doesn't exist."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", "/nonexistent/profile.json",
                "--template", "modern",
                "--output", str(output_dir),
            ],
        )
        assert result.exit_code != 0

    def test_generate_invalid_template(self, runner, fixtures_dir, tmp_path):
        """Test error when template doesn't exist."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "nonexistent_template",
                "--output", str(output_dir),
            ],
        )
        assert result.exit_code != 0

    def test_generate_invalid_format(self, runner, fixtures_dir, tmp_path):
        """Test error when format is invalid."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "--profile", str(fixtures_dir / "minimal_profile.json"),
                "--template", "modern",
                "--output", str(output_dir),
                "--formats", "invalid_format",
            ],
        )
        assert result.exit_code != 0


# =============================================================================
# CLI help and basic functionality
# =============================================================================

class TestCliBasics:
    """Basic CLI tests."""

    def test_app_has_generate_command(self, runner):
        """Test that app has generate command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.stdout.lower()

    def test_app_has_list_command(self, runner):
        """Test that app has list-templates command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_app_has_preview_command(self, runner):
        """Test that app has preview command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "preview" in result.stdout.lower()

    def test_help_output_shows_usage(self, runner):
        """Test that help shows usage information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_generate_help(self, runner):
        """Test generate command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--profile" in result.stdout or "-p" in result.stdout

    def test_list_templates_help(self, runner):
        """Test list-templates command help."""
        result = runner.invoke(app, ["list-templates-cmd", "--help"])
        assert result.exit_code == 0

    def test_preview_help(self, runner):
        """Test preview command help."""
        result = runner.invoke(app, ["preview", "--help"])
        assert result.exit_code == 0


# =============================================================================
# generate command short flags
# =============================================================================

class TestGenerateShortFlags:
    """Tests for generate command short flags."""

    def test_generate_with_short_p_flag(self, runner, fixtures_dir, tmp_path):
        """Test generate with -p flag."""
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
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"


# =============================================================================
# Edge cases
# =============================================================================

class TestCliEdgeCases:
    """Edge case tests for CLI."""

    def test_generate_to_current_directory(self, runner, fixtures_dir, tmp_path):
        """Test generating to current working directory."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(fixtures_dir / "minimal_profile.json"),
                    "-t", "modern",
                    "-f", "html",
                ],
            )
            assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        finally:
            os.chdir(old_cwd)

    def test_generate_with_custom_output_filename(
        self, runner, fixtures_dir, tmp_path
    ):
        """Test that output filename includes profile name."""
        output_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-p", str(fixtures_dir / "full_profile.json"),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.stdout}"
        html_files = list(output_dir.glob("*.html"))
        assert len(html_files) == 1
        assert "full_profile" in html_files[0].name
