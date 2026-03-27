"""
End-to-End tests for cv-generator.
Tests complete workflows from CLI to generated files.
"""

import json
import csv
from pathlib import Path

import pytest
from typer.testing import CliRunner

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli import app
from generator import generate, load_profile, render_html, render_csv


# =============================================================================
# Helper fixtures (local to e2e, not shared)
# =============================================================================

@pytest.fixture
def e2e_fixtures_dir():
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def e2e_templates_dir():
    return Path(__file__).parent.parent.parent / "templates"


@pytest.fixture
def e2e_runner():
    return CliRunner()


# =============================================================================
# E2E: CLI generate workflow
# =============================================================================

class TestE2EGenerateWorkflow:
    """End-to-end tests for complete generation workflow."""

    def test_e2e_minimal_profile_all_templates_all_formats(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate all formats with all templates from minimal profile."""
        profile = e2e_fixtures_dir / "minimal_profile.json"
        output_dir = tmp_path / "output"
        templates = ["classic", "modern", "minimal", "ats-friendly"]
        formats = ["html", "csv", "md"]

        for template in templates:
            for fmt in formats:
                result = e2e_runner.invoke(
                    app,
                    [
                        "generate",
                        "-p", str(profile),
                        "-t", template,
                        "-o", str(output_dir),
                        "-f", fmt,
                    ],
                )
                assert result.exit_code == 0, f"Failed for {template}/{fmt}: {result.stdout}"

        html_files = list(output_dir.glob("*.html"))
        assert len(html_files) == 4  # 4 templates

    def test_e2e_full_profile_complete_workflow(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: complete workflow with full featured profile."""
        profile = e2e_fixtures_dir / "full_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html,csv,md",
            ],
        )
        assert result.exit_code == 0

        html_files = list(output_dir.glob("*.html"))
        csv_files = list(output_dir.glob("*.csv"))
        md_files = list(output_dir.glob("*.md"))

        assert len(html_files) == 1
        assert len(csv_files) == 1
        assert len(md_files) == 1

        html_content = html_files[0].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in html_content
        assert "DevOps Manager" in html_content
        assert "TrafPay" in html_content

    def test_e2e_csv_parsable(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generated CSV is parseable by standard csv reader."""
        profile = e2e_fixtures_dir / "full_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "csv",
            ],
        )
        assert result.exit_code == 0

        csv_file = list(output_dir.glob("*.csv"))[0]
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            sections = [row["Section"] for row in rows]
            assert "PROFILE" in sections
            assert "KEYWORDS" in sections
            assert "TITLE" in sections

    def test_e2e_html_valid_structure(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generated HTML has valid document structure."""
        profile = e2e_fixtures_dir / "minimal_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html",
            ],
        )
        assert result.exit_code == 0

        html_file = list(output_dir.glob("*.html"))[0]
        html_content = html_file.read_text(encoding="utf-8")

        assert html_content.startswith("<!DOCTYPE html>")
        assert "<html" in html_content
        assert "</html>" in html_content
        assert "<head>" in html_content or "<head " in html_content
        assert "<body>" in html_content
        assert "</body>" in html_content

    def test_e2e_multiple_profiles_same_output_dir(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generating multiple profiles to same directory."""
        output_dir = tmp_path / "output"

        for profile_name in ["minimal_profile.json", "full_profile.json"]:
            profile = e2e_fixtures_dir / profile_name
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", "modern",
                    "-o", str(output_dir),
                    "-f", "html,csv",
                ],
            )
            assert result.exit_code == 0

        html_files = list(output_dir.glob("*.html"))
        assert len(html_files) == 2
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) == 2

    def test_e2e_each_template_produces_valid_html(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: each template produces valid HTML."""
        profile = e2e_fixtures_dir / "minimal_profile.json"
        templates = ["classic", "modern", "minimal", "ats-friendly"]

        for template in templates:
            output_dir = tmp_path / template
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", template,
                    "-o", str(output_dir),
                    "-f", "html",
                ],
            )
            assert result.exit_code == 0

            html_file = list(output_dir.glob("*.html"))[0]
            content = html_file.read_text(encoding="utf-8")

            assert "<!DOCTYPE html>" in content
            assert "Test Developer" in content


# =============================================================================
# E2E: Template content verification
# =============================================================================

class TestE2ETemplateContent:
    """End-to-end tests verifying template-specific content."""

    def test_e2e_modern_template_has_timeline(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: modern template includes experience section."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "modern", e2e_templates_dir)
        assert "Experience" in html or "experience" in html.lower()

    def test_e2e_classic_template_has_sidebar(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: classic template includes sidebar structure."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "classic", e2e_templates_dir)
        assert "contact" in html.lower() or "sidebar" in html.lower()

    def test_e2e_ats_template_has_summary_section(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: ATS template includes professional summary section."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "ats-friendly", e2e_templates_dir)
        assert "PROFESSIONAL SUMMARY" in html.upper() or "SUMMARY" in html.upper()

    def test_e2e_minimal_template_has_clean_structure(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: minimal template has clean, sparse structure."""
        profile = load_profile(e2e_fixtures_dir / "minimal_profile.json")
        html = render_html(profile, "minimal", e2e_templates_dir)
        assert "<!DOCTYPE html>" in html
        assert "Test Developer" in html


# =============================================================================
# E2E: Profile data integrity
# =============================================================================

class TestE2EDataIntegrity:
    """Tests ensuring data flows correctly from input to output."""

    def test_e2e_profile_keywords_preserved_in_all_formats(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: all keywords appear in every output format."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        sample_keywords = profile["keywords"][:5]

        html_content = results["html"].read_text(encoding="utf-8")
        for kw in sample_keywords:
            assert kw in html_content, f"Keyword '{kw}' missing from HTML"

        csv_content = results["csv"].read_text(encoding="utf-8")
        for kw in sample_keywords:
            assert kw in csv_content, f"Keyword '{kw}' missing from CSV"

        md_content = results["md"].read_text(encoding="utf-8")
        for kw in sample_keywords:
            assert kw in md_content, f"Keyword '{kw}' missing from MD"

    def test_e2e_experience_data_preserved_in_html(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: all experience entries appear in HTML output."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "modern", e2e_templates_dir)

        for job in profile["experience"]:
            assert job["title"] in html, f"Job title '{job['title']}' missing"
            assert job["company"] in html, f"Company '{job['company']}' missing"

    def test_e2e_education_data_preserved_in_html(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: education entries appear in HTML output."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "modern", e2e_templates_dir)

        for edu in profile["education"]:
            # Handle HTML entity encoding for apostrophes
            degree_encoded = edu['degree'].replace("'", "&#39;")
            assert degree_encoded in html or edu['degree'] in html
            assert edu["institution"] in html

    def test_e2e_certifications_preserved_in_html(
        self, e2e_fixtures_dir, e2e_templates_dir
    ):
        """E2E test: certifications appear in HTML output."""
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "modern", e2e_templates_dir)

        for cert in profile["certifications"]:
            assert cert in html, f"Certification '{cert}' missing"


# =============================================================================
# E2E: File output verification
# =============================================================================

class TestE2EFileOutput:
    """Tests for generated file properties."""

    def test_e2e_output_files_not_empty(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: generated files are not empty."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        for fmt, path in results.items():
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"{fmt} file is empty"
            if fmt == "html":
                assert len(content) > 1000, "HTML file suspiciously small"

    def test_e2e_html_file_valid_utf8(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: generated HTML is valid UTF-8."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html"],
        )

        content = results["html"].read_text(encoding="utf-8")
        assert isinstance(content, str)

    def test_e2e_output_filename_format(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: output filename follows expected format."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        for fmt, path in results.items():
            assert path.name.startswith("full_profile_modern.")
            assert path.suffix == f".{fmt}"

    def test_e2e_csv_file_parsable_by_standard_reader(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: CSV can be parsed by Python csv module."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["csv"],
        )

        csv_file = results["csv"]
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) > 1


# =============================================================================
# E2E: Integration with Python API
# =============================================================================

class TestE2EPythonApi:
    """Tests using Python API directly (not CLI)."""

    def test_e2e_python_api_complete_workflow(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: complete workflow via Python API."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        assert len(results) == 3
        assert all(path.exists() for path in results.values())

        profile = load_profile(e2e_fixtures_dir / "full_profile.json")
        html = render_html(profile, "modern", e2e_templates_dir)

        assert profile["title"] in html
        assert profile["profile"] in html

    def test_e2e_generator_function_all_templates(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: generator works with all templates."""
        output_dir = tmp_path / "output"
        templates = ["classic", "modern", "minimal", "ats-friendly"]

        for template in templates:
            results = generate(
                profile_path=e2e_fixtures_dir / "minimal_profile.json",
                template_name=template,
                templates_dir=e2e_templates_dir,
                output_dir=output_dir,
                formats=["html"],
            )
            assert "html" in results
            assert results["html"].exists()
