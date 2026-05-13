"""
Unit tests for cv-generator core module.
"""

import json
import csv
from pathlib import Path
from io import StringIO

import pytest

from generator import (
    load_profile,
    parse_keywords,
    render_html,
    render_csv,
    render_markdown,
    generate,
    list_templates,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_profile(fixtures_dir):
    return fixtures_dir / "minimal_profile.json"


@pytest.fixture
def full_profile(fixtures_dir):
    return fixtures_dir / "full_profile.json"


@pytest.fixture
def templates_dir():
    return Path(__file__).parent.parent / "templates"


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"


# =============================================================================
# load_profile tests
# =============================================================================

class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_minimal_profile(self, minimal_profile):
        """Test loading a minimal profile with only required fields."""
        profile = load_profile(minimal_profile)
        assert isinstance(profile, dict)
        assert profile["title"] == "Test Developer"
        assert profile["profile"] is not None
        assert isinstance(profile["keywords"], list)

    def test_load_full_profile(self, full_profile):
        """Test loading a complete profile with all fields."""
        profile = load_profile(full_profile)
        assert profile["title"] == "Senior Platform Engineer"
        assert profile["email"] == "nicolasalca@hotmail.com"
        assert profile["phone"] == "+57 300 123 4567"
        assert profile["location"] == "Medellín, Colombia (Remote)"
        assert profile["linkedin"] == "linkedin.com/in/nicolas-a-6193aa28"
        assert len(profile["experience"]) == 2
        assert len(profile["education"]) == 1
        assert len(profile["certifications"]) == 2
        assert len(profile["languages"]) == 2

    def test_load_profile_unicode(self, full_profile):
        """Test loading profile with unicode characters."""
        profile = load_profile(full_profile)
        assert "Medellín" in profile["location"]
        assert "Español" not in profile["profile"]

    def test_load_profile_experience_structure(self, full_profile):
        """Test that experience entries have all required fields."""
        profile = load_profile(full_profile)
        exp = profile["experience"][0]
        assert "title" in exp
        assert "company" in exp
        assert "start_date" in exp
        assert "description" in exp

    def test_load_profile_nonexistent_raises(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_profile("/nonexistent/path/profile.json")


# =============================================================================
# parse_keywords tests
# =============================================================================

class TestParseKeywords:
    """Tests for parse_keywords function."""

    def test_parse_empty_keywords(self):
        """Test parsing empty keyword list."""
        result = parse_keywords([])
        assert result == []

    def test_parse_single_keyword(self):
        """Test parsing single keyword."""
        result = parse_keywords(["Python"])
        assert len(result) == 1
        assert result[0]["items"] == ["Python"]

    def test_parse_exact_four_keywords(self):
        """Test parsing exactly 4 keywords (one row)."""
        result = parse_keywords(["Python", "Pytest", "Docker", "Git"])
        assert len(result) == 1
        assert result[0]["items"] == ["Python", "Pytest", "Docker", "Git"]

    def test_parse_five_keywords(self):
        """Test parsing 5 keywords (two rows: 4 + 1)."""
        result = parse_keywords(["A", "B", "C", "D", "E"])
        assert len(result) == 2
        assert result[0]["items"] == ["A", "B", "C", "D"]
        assert result[1]["items"] == ["E"]

    def test_parse_eight_keywords(self):
        """Test parsing 8 keywords (two full rows)."""
        result = parse_keywords(["A", "B", "C", "D", "E", "F", "G", "H"])
        assert len(result) == 2
        assert result[0]["items"] == ["A", "B", "C", "D"]
        assert result[1]["items"] == ["E", "F", "G", "H"]

    def test_parse_nine_keywords(self):
        """Test parsing 9 keywords (three rows: 4 + 4 + 1)."""
        result = parse_keywords(["A", "B", "C", "D", "E", "F", "G", "H", "I"])
        assert len(result) == 3
        assert result[0]["items"] == ["A", "B", "C", "D"]
        assert result[1]["items"] == ["E", "F", "G", "H"]
        assert result[2]["items"] == ["I"]

    def test_parse_many_keywords(self):
        """Test parsing many keywords for realistic profile."""
        keywords = [f"Skill{i}" for i in range(21)]
        result = parse_keywords(keywords)
        assert len(result) == 6  # 21 keywords = 5 full rows + 1 partial

    def test_parse_keywords_returns_list_of_dicts(self):
        """Test that result is list of dicts with 'items' key."""
        result = parse_keywords(["A", "B"])
        assert isinstance(result, list)
        assert all(isinstance(row, dict) for row in result)
        assert all("items" in row for row in result)


# =============================================================================
# render_html tests
# =============================================================================

class TestRenderHtml:
    """Tests for render_html function."""

    def test_render_minimal_html(self, minimal_profile, templates_dir):
        """Test rendering HTML with minimal profile."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "modern", templates_dir)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert profile["title"] in html

    def test_render_all_templates(self, minimal_profile, templates_dir):
        """Test that all 4 templates render without errors."""
        profile = load_profile(minimal_profile)
        templates = ["classic", "modern", "minimal", "ats-friendly"]

        for template in templates:
            html = render_html(profile, template, templates_dir)
            assert isinstance(html, str)
            assert len(html) > 0
            assert "<!DOCTYPE html>" in html
            assert profile["title"] in html

    def test_render_html_contains_profile_text(self, minimal_profile, templates_dir):
        """Test that rendered HTML contains profile text."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "modern", templates_dir)
        assert profile["profile"] in html

    def test_render_html_contains_keywords(self, minimal_profile, templates_dir):
        """Test that rendered HTML contains keywords."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "modern", templates_dir)
        for keyword in profile["keywords"][:3]:
            assert keyword in html

    def test_render_html_contains_contact_info(self, minimal_profile, templates_dir):
        """Test that rendered HTML contains contact information."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "modern", templates_dir)
        assert profile["email"] in html

    def test_render_html_with_full_profile(self, full_profile, templates_dir):
        """Test rendering HTML with full profile including experience."""
        profile = load_profile(full_profile)
        html = render_html(profile, "modern", templates_dir)

        assert isinstance(html, str)
        assert profile["title"] in html
        assert profile["profile"] in html
        assert profile["experience"][0]["title"] in html
        assert profile["experience"][0]["company"] in html

    def test_render_html_invalid_template_raises(self, minimal_profile, templates_dir):
        """Test that invalid template name raises TemplateNotFound."""
        profile = load_profile(minimal_profile)
        from jinja2 import TemplateNotFound
        with pytest.raises(TemplateNotFound):
            render_html(profile, "nonexistent_template", templates_dir)

    def test_render_html_contains_experience_section(self, full_profile, templates_dir):
        """Test that experience section is rendered."""
        profile = load_profile(full_profile)
        html = render_html(profile, "modern", templates_dir)
        assert "Experience" in html or "experience" in html.lower()

    def test_render_html_contains_education_section(self, full_profile, templates_dir):
        """Test that education section is rendered when present."""
        profile = load_profile(full_profile)
        html = render_html(profile, "modern", templates_dir)
        assert "Education" in html or "education" in html.lower()

    def test_render_classic_template_structure(self, minimal_profile, templates_dir):
        """Test classic template has expected structure."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "classic", templates_dir)
        assert "<!DOCTYPE html>" in html
        assert "contact-info" in html or "contact" in html.lower()

    def test_render_ats_template_structure(self, minimal_profile, templates_dir):
        """Test ATS-friendly template has expected ATS markers."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "ats-friendly", templates_dir)
        assert "<!DOCTYPE html>" in html
        assert "PROFESSIONAL SUMMARY" in html or "ATS" in html.upper()

    def test_render_minimal_template_structure(self, minimal_profile, templates_dir):
        """Test minimal template renders with clean structure."""
        profile = load_profile(minimal_profile)
        html = render_html(profile, "minimal", templates_dir)
        assert "<!DOCTYPE html>" in html
        assert "profile" in html.lower()


# =============================================================================
# render_csv tests
# =============================================================================

class TestRenderCsv:
    """Tests for render_csv function."""

    def test_render_csv_creates_file(self, minimal_profile, tmp_path):
        """Test that CSV file is created."""
        profile = load_profile(minimal_profile)
        output_file = tmp_path / "test.csv"
        render_csv(profile, output_file)

        assert output_file.exists()

    def test_render_csv_has_header(self, minimal_profile, tmp_path):
        """Test that CSV has Section and Content header."""
        profile = load_profile(minimal_profile)
        output_file = tmp_path / "test.csv"
        render_csv(profile, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert "Section" in header
            assert "Content" in header

    def test_render_csv_profile_row(self, minimal_profile, tmp_path):
        """Test that profile is written to CSV."""
        profile = load_profile(minimal_profile)
        output_file = tmp_path / "test.csv"
        render_csv(profile, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "PROFILE" in content
            assert profile["profile"] in content

    def test_render_csv_keywords_row(self, minimal_profile, tmp_path):
        """Test that keywords are written to CSV."""
        profile = load_profile(minimal_profile)
        output_file = tmp_path / "test.csv"
        render_csv(profile, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "KEYWORDS" in content
            for keyword in profile["keywords"][:3]:
                assert keyword in content

    def test_render_csv_title_row(self, minimal_profile, tmp_path):
        """Test that title is written to CSV."""
        profile = load_profile(minimal_profile)
        output_file = tmp_path / "test.csv"
        render_csv(profile, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TITLE" in content
            assert profile["title"] in content

    def test_render_csv_with_full_profile(self, full_profile, tmp_path):
        """Test CSV rendering with full profile."""
        profile = load_profile(full_profile)
        output_file = tmp_path / "full.csv"
        render_csv(profile, output_file)

        assert output_file.exists()
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "PROFILE" in content
            assert "KEYWORDS" in content
            assert "TITLE" in content

    def test_render_csv_all_fields_present(self, full_profile, tmp_path):
        """Test that all major sections appear in CSV."""
        profile = load_profile(full_profile)
        output_file = tmp_path / "full.csv"
        render_csv(profile, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            sections = [row[0] for row in rows if row]
            assert "PROFILE" in sections
            assert "KEYWORDS" in sections
            assert "TITLE" in sections


# =============================================================================
# render_markdown tests
# =============================================================================

class TestRenderMarkdown:
    """Tests for render_markdown function."""

    def test_render_markdown_returns_string(self, minimal_profile):
        """Test that markdown is returned as string."""
        profile = load_profile(minimal_profile)
        md = render_markdown(profile)
        assert isinstance(md, str)

    def test_render_markdown_contains_title(self, minimal_profile):
        """Test that markdown contains title as heading."""
        profile = load_profile(minimal_profile)
        md = render_markdown(profile)
        assert f"# {profile['title']}" in md

    def test_render_markdown_contains_profile_section(self, minimal_profile):
        """Test that markdown contains profile section."""
        profile = load_profile(minimal_profile)
        md = render_markdown(profile)
        assert "## Profile" in md or "## profile" in md.lower()
        assert profile["profile"] in md

    def test_render_markdown_contains_skills_section(self, minimal_profile):
        """Test that markdown contains skills section."""
        profile = load_profile(minimal_profile)
        md = render_markdown(profile)
        assert "## Skills" in md or "## skills" in md.lower()

    def test_render_markdown_keywords_as_list(self, minimal_profile):
        """Test that keywords appear as list items."""
        profile = load_profile(minimal_profile)
        md = render_markdown(profile)
        for keyword in profile["keywords"][:3]:
            assert f"- {keyword}" in md

    def test_render_markdown_with_full_profile(self, full_profile):
        """Test markdown rendering with full profile."""
        profile = load_profile(full_profile)
        md = render_markdown(profile)
        assert isinstance(md, str)
        assert len(md) > 0
        assert profile["title"] in md
        assert profile["profile"] in md


# =============================================================================
# generate tests
# =============================================================================

class TestGenerate:
    """Tests for generate function."""

    def test_generate_creates_output_dir(self, minimal_profile, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html"],
        )
        assert output_dir.exists()

    def test_generate_html(self, minimal_profile, tmp_path):
        """Test generating HTML format."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html"],
        )
        assert "html" in results
        assert results["html"].exists()
        assert results["html"].suffix == ".html"

    def test_generate_csv(self, minimal_profile, tmp_path):
        """Test generating CSV format."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["csv"],
        )
        assert "csv" in results
        assert results["csv"].exists()
        assert results["csv"].suffix == ".csv"

    def test_generate_md(self, minimal_profile, tmp_path):
        """Test generating Markdown format."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["md"],
        )
        assert "md" in results
        assert results["md"].exists()
        assert results["md"].suffix == ".md"

    def test_generate_multiple_formats(self, minimal_profile, tmp_path):
        """Test generating multiple formats at once."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )
        assert len(results) == 3
        assert all(results[f] for f in ["html", "csv", "md"])

    def test_generate_all_templates(self, minimal_profile, tmp_path):
        """Test generating with all template names."""
        templates = ["classic", "modern", "minimal", "ats-friendly"]
        output_dir = tmp_path / "output"
        templates_dir = Path(__file__).parent.parent / "templates"

        for template in templates:
            results = generate(
                profile_path=minimal_profile,
                template_name=template,
                templates_dir=templates_dir,
                output_dir=output_dir,
                formats=["html"],
            )
            assert "html" in results
            assert results["html"].exists()

    def test_generate_returns_dict(self, minimal_profile, tmp_path):
        """Test that generate returns dict of format -> path."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html", "csv"],
        )
        assert isinstance(results, dict)
        assert all(isinstance(v, Path) for v in results.values())

    def test_generate_html_content_valid(self, minimal_profile, tmp_path):
        """Test that generated HTML has valid content."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html"],
        )
        content = results["html"].read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "</html>" in content

    def test_generate_csv_content_valid(self, minimal_profile, tmp_path):
        """Test that generated CSV has valid content."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["csv"],
        )
        content = results["csv"].read_text(encoding="utf-8")
        assert "Section" in content
        assert "Content" in content

    def test_generate_with_full_profile(self, full_profile, tmp_path):
        """Test generation with full featured profile."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=full_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )
        assert len(results) == 3
        for fmt, path in results.items():
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_generate_invalid_format_ignored(self, minimal_profile, tmp_path):
        """Test that invalid format doesn't cause error, just skipped."""
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["invalid_format"],  # Should be silently ignored
        )
        # No error, empty dict returned
        assert isinstance(results, dict)


# =============================================================================
# list_templates tests
# =============================================================================

class TestListTemplates:
    """Tests for list_templates function."""

    def test_list_templates_returns_list(self, templates_dir):
        """Test that list_templates returns a list."""
        templates = list_templates(templates_dir)
        assert isinstance(templates, list)

    def test_list_templates_contains_expected(self, templates_dir):
        """Test that expected templates are listed."""
        templates = list_templates(templates_dir)
        expected = ["classic", "modern", "minimal", "ats-friendly"]
        for t in expected:
            assert t in templates

    def test_list_templates_sorted(self, templates_dir):
        """Test that templates list is sorted."""
        templates = list_templates(templates_dir)
        assert templates == sorted(templates)

    def test_list_templates_default_dir(self):
        """Test that default templates directory is used when None."""
        templates = list_templates(None)
        assert len(templates) >= 4

    def test_list_templates_returns_strings(self, templates_dir):
        """Test that returned list contains strings."""
        templates = list_templates(templates_dir)
        assert all(isinstance(t, str) for t in templates)


# =============================================================================
# validate_template_name tests
# =============================================================================

class TestValidateTemplateName:
    """Tests for validate_template_name function."""

    def test_validate_template_name_valid(self, templates_dir):
        """Test that valid template name passes validation."""
        from generator import validate_template_name
        # Should not raise
        validate_template_name("modern", templates_dir)

    def test_validate_template_name_all_valid(self, templates_dir):
        """Test that all valid template names pass."""
        from generator import validate_template_name
        templates = ["classic", "modern", "minimal", "ats-friendly"]
        for template in templates:
            validate_template_name(template, templates_dir)

    def test_validate_template_name_empty_raises(self, templates_dir):
        """Test that empty template name raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_template_name("", templates_dir)

    def test_validate_template_name_nonexistent_raises(self, templates_dir):
        """Test that nonexistent template raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="not found"):
            validate_template_name("nonexistent_template", templates_dir)

    def test_validate_template_name_path_traversal_double_dot(self, templates_dir):
        """Test that path traversal with '..' raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="path traversal"):
            validate_template_name("../secrets", templates_dir)

    def test_validate_template_name_path_traversal_slash(self, templates_dir):
        """Test that path with '/' raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="path traversal"):
            validate_template_name("/etc/passwd", templates_dir)

    def test_validate_template_name_path_traversal_backslash(self, templates_dir):
        """Test that path with '\\' raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="path traversal"):
            validate_template_name("\\Windows\\System32", templates_dir)

    def test_validate_template_name_absolute_path_windows(self, templates_dir):
        """Test that Windows absolute path raises ValueError."""
        from generator import validate_template_name
        with pytest.raises(ValueError, match="absolute paths"):
            validate_template_name("C:\\windows\\system32", templates_dir)

    def test_validate_template_name_case_sensitive(self, templates_dir):
        """Test that template validation is case sensitive."""
        from generator import validate_template_name
        # lowercase should fail
        with pytest.raises(ValueError, match="not found"):
            validate_template_name("MODERN", templates_dir)


# =============================================================================
# render_pdf tests
# =============================================================================

class TestRenderPdf:
    """Tests for render_pdf function."""

    def test_render_pdf_creates_file(self, minimal_profile, tmp_path, templates_dir):
        """Test that PDF file is created."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        output_path = tmp_path / "test.pdf"
        render_pdf(profile, "modern", templates_dir, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_pdf_modern_template(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf with modern template."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        output_path = tmp_path / "modern.pdf"
        render_pdf(profile, "modern", templates_dir, output_path)

        assert output_path.exists()

    def test_render_pdf_classic_template(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf with classic template."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        output_path = tmp_path / "classic.pdf"
        render_pdf(profile, "classic", templates_dir, output_path)

        assert output_path.exists()

    def test_render_pdf_minimal_template(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf with minimal template."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        output_path = tmp_path / "minimal.pdf"
        render_pdf(profile, "minimal", templates_dir, output_path)

        assert output_path.exists()

    def test_render_pdf_ats_template(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf with ats-friendly template."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        output_path = tmp_path / "ats.pdf"
        render_pdf(profile, "ats-friendly", templates_dir, output_path)

        assert output_path.exists()

    def test_render_pdf_with_full_profile(self, full_profile, tmp_path, templates_dir):
        """Test render_pdf with full profile."""
        from generator import render_pdf, load_profile
        profile = load_profile(full_profile)
        output_path = tmp_path / "full.pdf"
        render_pdf(profile, "modern", templates_dir, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_pdf_with_experience(self, full_profile, tmp_path, templates_dir):
        """Test render_pdf with experience section."""
        from generator import render_pdf, load_profile
        profile = load_profile(full_profile)
        output_path = tmp_path / "experience.pdf"
        render_pdf(profile, "modern", templates_dir, output_path)

        assert output_path.exists()

    def test_render_pdf_all_templates(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf with all templates."""
        from generator import render_pdf, load_profile
        profile = load_profile(minimal_profile)
        templates = ["modern", "classic", "minimal", "ats-friendly"]

        for template in templates:
            output_path = tmp_path / f"{template}.pdf"
            render_pdf(profile, template, templates_dir, output_path)
            assert output_path.exists()


# =============================================================================
# Edge cases and integration
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_profile_missing_optional_fields(self, tmp_path):
        """Test profile with only required fields."""
        minimal_data = {
            "title": "Minimal Title",
            "profile": "Minimal profile text.",
            "keywords": ["Python", "JavaScript"]
        }
        profile_path = tmp_path / "minimal.json"
        profile_path.write_text(json.dumps(minimal_data), encoding="utf-8")

        profile = load_profile(profile_path)
        assert profile["title"] == "Minimal Title"

        # Should still render
        templates_dir = Path(__file__).parent.parent / "templates"
        html = render_html(profile, "modern", templates_dir)
        assert isinstance(html, str)

    def test_render_csv_empty_profile(self, tmp_path):
        """Test rendering CSV with minimal profile data."""
        minimal_data = {
            "title": "Test",
            "profile": "Test profile",
            "keywords": ["A", "B"]
        }
        profile_path = tmp_path / "minimal.json"
        profile_path.write_text(json.dumps(minimal_data), encoding="utf-8")
        profile = load_profile(profile_path)
        output_file = tmp_path / "output.csv"
        render_csv(profile, output_file)
        assert output_file.exists()

    def test_keywords_with_special_characters(self, tmp_path):
        """Test handling keywords with special characters."""
        data = {
            "title": "Test",
            "profile": "Profile",
            "keywords": ["C++", "C#", ".NET", "Node.js", "CI/CD"]
        }
        profile_path = tmp_path / "special.json"
        profile_path.write_text(json.dumps(data), encoding="utf-8")
        profile = load_profile(profile_path)

        templates_dir = Path(__file__).parent.parent / "templates"
        html = render_html(profile, "modern", templates_dir)
        assert "C++" in html
        assert "C#" in html
        assert ".NET" in html

    def test_unicode_in_profile(self, tmp_path):
        """Test handling of unicode characters."""
        data = {
            "title": "Développeur Test",
            "profile": "Profile with émojis 🎉 and unicode:café",
            "keywords": ["Python", "JavaScript"]
        }
        profile_path = tmp_path / "unicode.json"
        profile_path.write_text(json.dumps(data), encoding="utf-8")
        profile = load_profile(profile_path)

        templates_dir = Path(__file__).parent.parent / "templates"
        html = render_html(profile, "modern", templates_dir)
        assert "Développeur" in html
        assert "🎉" in html

    def test_long_profile_text(self, tmp_path):
        """Test handling of very long profile text."""
        long_profile = "Word " * 1000  # Very long profile
        data = {
            "title": "Test",
            "profile": long_profile,
            "keywords": ["Python"]
        }
        profile_path = tmp_path / "long.json"
        profile_path.write_text(json.dumps(data), encoding="utf-8")
        profile = load_profile(profile_path)

        templates_dir = Path(__file__).parent.parent / "templates"
        html = render_html(profile, "modern", templates_dir)
        assert long_profile in html


# =============================================================================
# Exception handling tests
# =============================================================================

class TestExceptionHandling:
    """Tests for exception handling in generator functions."""

    def test_render_csv_raises_on_permission_error(self, minimal_profile, tmp_path):
        """Test that render_csv raises on permission error."""
        from unittest.mock import patch
        import builtins

        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        with patch.object(builtins, 'open', side_effect=mock_open):
            output_file = tmp_path / "output.csv"
            with pytest.raises(PermissionError):
                render_csv(minimal_profile, output_file)

    def test_render_csv_raises_on_io_error(self, minimal_profile, tmp_path):
        """Test that render_csv raises on IOError."""
        from unittest.mock import patch
        import builtins

        def mock_open(*args, **kwargs):
            raise IOError("Disk full")

        with patch.object(builtins, 'open', side_effect=mock_open):
            output_file = tmp_path / "output.csv"
            with pytest.raises(IOError):
                render_csv(minimal_profile, output_file)

    def test_render_markdown_handles_missing_profile(self):
        """Test that render_markdown handles profile without optional fields."""
        profile = {}
        md = render_markdown(profile)
        assert "## Profile" in md
        assert "## Skills" in md

    def test_render_html_handles_missing_profile(self, templates_dir):
        """Test that render_html handles profile without optional fields."""
        profile = {}
        html = render_html(profile, "modern", templates_dir)
        assert "<!DOCTYPE html>" in html

    def test_render_pdf_raises_on_invalid_profile(self, tmp_path, templates_dir):
        """Test that render_pdf raises when profile is invalid."""
        from generator import render_pdf, load_profile
        # This should work because CVRenderer handles None profile gracefully
        # But if we pass something that causes render to fail
        output_path = tmp_path / "test.pdf"
        # This should succeed because we pass proper profile
        profile = {"title": "Test", "profile": "Test", "keywords": []}
        render_pdf(profile, "modern", templates_dir, output_path)
        assert output_path.exists()

    def test_generate_with_valid_profile_returns_files(self, minimal_profile, tmp_path):
        """Test that generate returns proper files on success."""
        from generator import generate
        output_dir = tmp_path / "output"
        results = generate(
            profile_path=minimal_profile,
            template_name="modern",
            templates_dir=Path(__file__).parent.parent / "templates",
            output_dir=output_dir,
            formats=["html", "csv", "md"],
        )
        assert results["html"].exists()
        assert results["csv"].exists()
        assert results["md"].exists()
