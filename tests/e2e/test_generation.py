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


# =============================================================================
# E2E: All templates and formats generation
# =============================================================================

class TestE2EAllTemplatesAndFormats:
    """E2E tests for all 8 templates and all 4 formats."""

    ALL_TEMPLATES = [
        "modern", "classic", "minimal", "ats-friendly",
        "ats-pro", "executive", "creative", "minimal-pro"
    ]
    ALL_FORMATS = ["html", "pdf", "csv", "md"]

    def test_e2e_all_templates_with_html_format(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate all 8 templates in HTML format."""
        profile = e2e_fixtures_dir / "full_profile.json"

        for template in self.ALL_TEMPLATES:
            output_dir = tmp_path / f"output_{template}"
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
            assert result.exit_code == 0, f"Failed for template {template}: {result.stdout}"

            html_files = list(output_dir.glob("*.html"))
            assert len(html_files) == 1, f"Expected 1 HTML file for template {template}"

            content = html_files[0].read_text(encoding="utf-8")
            assert len(content) > 100, f"HTML content too small for {template}"
            assert "Senior Platform Engineer" in content, f"Missing title for {template}"

    def test_e2e_all_templates_with_csv_format(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate all 8 templates in CSV format."""
        profile = e2e_fixtures_dir / "full_profile.json"

        for template in self.ALL_TEMPLATES:
            output_dir = tmp_path / f"output_{template}"
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", template,
                    "-o", str(output_dir),
                    "-f", "csv",
                ],
            )
            assert result.exit_code == 0, f"Failed for template {template}: {result.stdout}"

            csv_files = list(output_dir.glob("*.csv"))
            assert len(csv_files) == 1, f"Expected 1 CSV file for template {template}"

    def test_e2e_all_templates_with_md_format(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate all 8 templates in Markdown format."""
        profile = e2e_fixtures_dir / "full_profile.json"

        for template in self.ALL_TEMPLATES:
            output_dir = tmp_path / f"output_{template}"
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", template,
                    "-o", str(output_dir),
                    "-f", "md",
                ],
            )
            assert result.exit_code == 0, f"Failed for template {template}: {result.stdout}"

            md_files = list(output_dir.glob("*.md"))
            assert len(md_files) == 1, f"Expected 1 MD file for template {template}"

            content = md_files[0].read_text(encoding="utf-8")
            assert "Senior Platform Engineer" in content, f"Missing title in MD for {template}"

    def test_e2e_all_templates_with_pdf_format(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate all 8 templates in PDF format."""
        profile = e2e_fixtures_dir / "full_profile.json"

        for template in self.ALL_TEMPLATES:
            output_dir = tmp_path / f"output_{template}"
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", template,
                    "-o", str(output_dir),
                    "-f", "pdf",
                ],
            )
            assert result.exit_code == 0, f"Failed for template {template}: {result.stdout}"

            pdf_files = list(output_dir.glob("*.pdf"))
            assert len(pdf_files) == 1, f"Expected 1 PDF file for template {template}"

            # Verify PDF is valid (size > 0)
            pdf_size = pdf_files[0].stat().st_size
            assert pdf_size > 0, f"PDF file is empty for {template}"

    def test_e2e_single_template_all_formats(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: generate modern template in all 4 formats."""
        profile = e2e_fixtures_dir / "full_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html,pdf,csv,md",
            ],
        )
        assert result.exit_code == 0

        # Check all 4 formats are generated
        html_files = list(output_dir.glob("*.html"))
        pdf_files = list(output_dir.glob("*.pdf"))
        csv_files = list(output_dir.glob("*.csv"))
        md_files = list(output_dir.glob("*.md"))

        assert len(html_files) == 1
        assert len(pdf_files) == 1
        assert len(csv_files) == 1
        assert len(md_files) == 1

        # Verify content in each format
        html_content = html_files[0].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in html_content

        pdf_size = pdf_files[0].stat().st_size
        assert pdf_size > 0

        csv_content = csv_files[0].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in csv_content

        md_content = md_files[0].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in md_content


# =============================================================================
# E2E: Complete workflow with loading, rendering, verification
# =============================================================================

class TestE2ECompleteWorkflow:
    """E2E tests for complete end-to-end workflow."""

    def test_e2e_complete_workflow_full_profile_html_pdf_csv_md(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: load profile, render all formats, verify content."""
        # Step 1: Load profile JSON
        profile = load_profile(e2e_fixtures_dir / "full_profile.json")

        assert profile["title"] == "Senior Platform Engineer"
        assert "DevOps" in profile["profile"]
        assert len(profile["experience"]) == 2

        # Step 2: Render to each format
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "pdf", "csv", "md"],
        )

        # Step 3: Verify all files created
        assert len(results) == 4
        assert all(path.exists() for path in results.values())

        # Step 4: Verify HTML content
        html_content = results["html"].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in html_content
        assert "TrafPay" in html_content
        assert "Tafi" in html_content
        assert "Universidad de Medellín" in html_content
        assert "Azure Solutions Architect Expert" in html_content

        # Step 5: Verify PDF is valid (size > 0)
        pdf_size = results["pdf"].stat().st_size
        assert pdf_size > 5000, "PDF file seems too small"

        # Step 6: Verify CSV content
        csv_content = results["csv"].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in csv_content
        assert "Cloud Architect" in csv_content

        # Step 7: Verify Markdown content
        md_content = results["md"].read_text(encoding="utf-8")
        assert "Senior Platform Engineer" in md_content
        assert "DevOps Manager" in md_content
        assert "Tafi" in md_content

    def test_e2e_complete_workflow_minimal_profile(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: complete workflow with minimal profile."""
        # Load minimal profile
        profile = load_profile(e2e_fixtures_dir / "minimal_profile.json")

        assert "title" in profile
        assert "profile" in profile

        # Generate all formats
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=e2e_fixtures_dir / "minimal_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        # Verify files exist and are not empty
        for fmt, path in results.items():
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0


# =============================================================================
# E2E: CLI Integration Tests
# =============================================================================

class TestE2ECLI:
    """E2E tests for CLI integration."""

    def test_e2e_cli_generate_command_execution(
        self, e2e_fixtures_dir, e2e_runner, tmp_path
    ):
        """E2E test: execute python cli.py generate from terminal."""
        profile = e2e_fixtures_dir / "minimal_profile.json"
        output_dir = tmp_path / "output"

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
        assert "Generating CV" in result.stdout
        assert "Generated files" in result.stdout

    def test_e2e_cli_generate_with_multiple_formats(
        self, e2e_fixtures_dir, e2e_runner, tmp_path
    ):
        """E2E test: CLI generates multiple formats correctly."""
        profile = e2e_fixtures_dir / "full_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "classic",
                "-o", str(output_dir),
                "-f", "html,pdf,csv,md",
            ],
        )

        assert result.exit_code == 0
        assert "[HTML]" in result.stdout
        assert "[PDF]" in result.stdout
        assert "[CSV]" in result.stdout
        assert "[MD]" in result.stdout

    def test_e2e_cli_list_templates(self, e2e_runner):
        """E2E test: CLI list-templates command."""
        result = e2e_runner.invoke(app, ["list-templates"])

        assert result.exit_code == 0
        assert "Available templates" in result.stdout

    def test_e2e_cli_invalid_template_error(
        self, e2e_fixtures_dir, e2e_runner, tmp_path
    ):
        """E2E test: CLI handles invalid template gracefully."""
        profile = e2e_fixtures_dir / "minimal_profile.json"
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", str(profile),
                "-t", "nonexistent_template",
                "-o", str(output_dir),
                "-f", "html",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_e2e_cli_missing_profile_error(
        self, e2e_runner, tmp_path
    ):
        """E2E test: CLI handles missing profile gracefully."""
        output_dir = tmp_path / "output"

        result = e2e_runner.invoke(
            app,
            [
                "generate",
                "-p", "nonexistent_profile.json",
                "-t", "modern",
                "-o", str(output_dir),
                "-f", "html",
            ],
        )

        assert result.exit_code != 0


# =============================================================================
# E2E: Edge Cases
# =============================================================================

class TestE2EEdgeCases:
    """E2E tests for edge cases."""

    def test_e2e_profile_with_all_fields(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: profile with all fields generates correctly."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "pdf", "csv", "md"],
        )

        html_content = results["html"].read_text(encoding="utf-8")

        # Verify all data appears in output
        assert "Senior Platform Engineer" in html_content
        assert "nicolasalca@hotmail.com" in html_content
        assert "Medellín, Colombia" in html_content
        assert "Tafi" in html_content
        assert "TrafPay" in html_content
        assert "Universidad de Medellín" in html_content
        assert "Azure Solutions Architect Expert" in html_content
        assert "Spanish" in html_content
        assert "English" in html_content

    def test_e2e_profile_with_minimal_fields(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: profile with minimal fields generates correctly."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "minimal_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=tmp_path / "output",
            formats=["html", "csv", "md"],
        )

        html_content = results["html"].read_text(encoding="utf-8")

        # Minimal profile should still produce valid output
        assert "Test Developer" in html_content
        assert "<!DOCTYPE html>" in html_content

    def test_e2e_profile_with_special_characters(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: profile with special characters/unicode generates correctly."""
        # Create profile with special characters
        special_profile = {
            "title": "Test Developer / Ingeniero de Pruebas",
            "profile": "Testing special chars: ñ, á, é, í, ó, ú, ü, ¡, ¿",
            "email": "test@example.com",
            "location": "Medellín, Colombia",
            "keywords": ["Python", "C#", "JavaScript", "Köln", "São Paulo"],
            "experience": [
                {
                    "title": "Senior Developer / Desarrollador Senior",
                    "company": "Test & Co.",
                    "start_date": "2020",
                    "end_date": "Present",
                    "description": "Working with special chars: Ñ, Á, É"
                }
            ],
            "education": [
                {
                    "degree": "Ingeniería / Engineering",
                    "institution": "Universidad de Medellín",
                    "year": "2015"
                }
            ]
        }

        import json
        special_profile_path = tmp_path / "special_profile.json"
        special_profile_path.write_text(json.dumps(special_profile, ensure_ascii=False), encoding="utf-8")

        # Generate
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=special_profile_path,
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )

        # Verify special characters preserved
        html_content = results["html"].read_text(encoding="utf-8")
        assert "Ingeniero de Pruebas" in html_content
        assert "ñ" in html_content or "ñ" in html_content
        assert "Medellín" in html_content

        csv_content = results["csv"].read_text(encoding="utf-8")
        assert "Ingeniero" in csv_content

        md_content = results["md"].read_text(encoding="utf-8")
        assert "Ingeniero" in md_content

    def test_e2e_unicode_in_keywords(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: unicode characters in keywords handled correctly."""
        unicode_profile = {
            "title": "Multilingual Developer",
            "profile": "Developer with international experience",
            "email": "dev@test.com",
            "location": "Worldwide",
            "keywords": ["Python", "Django", "Flask", "Köln", "São Paulo", "Москва", "北京"],
            "experience": [],
            "education": []
        }

        unicode_profile_path = tmp_path / "unicode_profile.json"
        unicode_profile_path.write_text(json.dumps(unicode_profile, ensure_ascii=False), encoding="utf-8")

        output_dir = tmp_path / "output"
        results = generate(
            profile_path=unicode_profile_path,
            template_name="minimal",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html"],
        )

        html_content = results["html"].read_text(encoding="utf-8")
        # Should not crash and should contain unicode
        assert "Multilingual Developer" in html_content

    def test_e2e_empty_experience_and_education(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: profile with empty experience and education."""
        empty_profile = {
            "title": "New Graduate",
            "profile": "Fresh graduate looking for opportunities",
            "email": "newgrad@test.com",
            "location": "Medellín",
            "keywords": ["Java", "SQL"],
            "experience": [],
            "education": []
        }

        empty_profile_path = tmp_path / "empty_profile.json"
        empty_profile_path.write_text(json.dumps(empty_profile), encoding="utf-8")

        output_dir = tmp_path / "output"
        results = generate(
            profile_path=empty_profile_path,
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["html"],
        )

        html_content = results["html"].read_text(encoding="utf-8")
        assert "New Graduate" in html_content
        assert "Fresh graduate" in html_content


# =============================================================================
# E2E: PDF Validation
# =============================================================================

class TestE2EPDFValidation:
    """E2E tests for PDF output validation."""

    def test_e2e_pdf_generated_for_all_templates(
        self, e2e_fixtures_dir, e2e_templates_dir, e2e_runner, tmp_path
    ):
        """E2E test: PDF generated for all 8 templates."""
        profile = e2e_fixtures_dir / "full_profile.json"
        templates = ["modern", "classic", "minimal", "ats-friendly",
                     "ats-pro", "executive", "creative", "minimal-pro"]

        for template in templates:
            output_dir = tmp_path / f"pdf_{template}"
            result = e2e_runner.invoke(
                app,
                [
                    "generate",
                    "-p", str(profile),
                    "-t", template,
                    "-o", str(output_dir),
                    "-f", "pdf",
                ],
            )
            assert result.exit_code == 0

            pdf_files = list(output_dir.glob("*.pdf"))
            assert len(pdf_files) == 1, f"No PDF generated for {template}"

            pdf_size = pdf_files[0].stat().st_size
            assert pdf_size > 0, f"PDF is empty for {template}"

    def test_e2e_pdf_valid_file_size(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: PDF file has valid size (>5KB for full profile)."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["pdf"],
        )

        pdf_path = results["pdf"]
        pdf_size = pdf_path.stat().st_size

        assert pdf_size > 5000, f"PDF size {pdf_size} bytes seems too small"

    def test_e2e_pdf_contains_profile_data(
        self, e2e_fixtures_dir, e2e_templates_dir, tmp_path
    ):
        """E2E test: PDF contains profile data (basic check)."""
        output_dir = tmp_path / "output"

        results = generate(
            profile_path=e2e_fixtures_dir / "full_profile.json",
            template_name="modern",
            templates_dir=e2e_templates_dir,
            output_dir=output_dir,
            formats=["pdf"],
        )

        pdf_path = results["pdf"]
        pdf_content = pdf_path.read_bytes()

        # PDF files start with %PDF
        assert pdf_content[:4] == b'%PDF', "Not a valid PDF file"

        # Check for some expected content (as bytes)
        assert b'Senior' in pdf_content or b'Platform' in pdf_content
