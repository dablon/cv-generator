"""
Unit tests for PDF Generator module (pdf_generator.py).

Tests the CVRenderer class with different templates and profile configurations.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pdf_generator import CVRenderer


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_profile():
    """Minimal profile with only required fields."""
    return {
        "title": "Test Developer",
        "profile": "Experienced test developer.",
        "keywords": ["Python", "Pytest", "CI/CD"],
        "email": "test@example.com",
        "location": "Test City, Country",
        "linkedin": "linkedin.com/in/test"
    }


@pytest.fixture
def full_profile(fixtures_dir):
    """Load full profile from fixture file."""
    with open(fixtures_dir / "full_profile.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def profile_with_experience():
    """Profile with experience entries."""
    return {
        "title": "Senior Engineer",
        "profile": "Experienced engineer.",
        "keywords": ["Python", "Java"],
        "email": "engineer@test.com",
        "location": "Remote",
        "linkedin": "linkedin.com/in/engineer",
        "experience": [
            {
                "title": "Tech Lead",
                "company": "Acme Corp",
                "location": "New York",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "description": "Led a team of 10 engineers."
            },
            {
                "title": "Senior Developer",
                "company": "Tech Inc",
                "start_date": "Jan 2018",
                "end_date": "Dec 2019",
                "description": "Developed microservices."
            }
        ]
    }


@pytest.fixture
def profile_with_education():
    """Profile with education entries."""
    return {
        "title": "Developer",
        "profile": "Developer profile.",
        "keywords": ["Python"],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "MIT",
                "year": "2020"
            }
        ]
    }


@pytest.fixture
def profile_with_languages():
    """Profile with languages."""
    return {
        "title": "Developer",
        "profile": "Profile.",
        "keywords": ["Python"],
        "languages": [
            {"name": "English", "level": "Fluent"},
            {"name": "Spanish", "level": "Native"}
        ]
    }


@pytest.fixture
def profile_with_certifications():
    """Profile with certifications."""
    return {
        "title": "Developer",
        "profile": "Profile.",
        "keywords": ["Python"],
        "certifications": [
            "AWS Solutions Architect",
            "Azure Developer"
        ]
    }


@pytest.fixture
def empty_profile():
    """Profile with only title (minimum required)."""
    return {
        "title": "Minimal Title",
        "profile": "",
        "keywords": []
    }


# =============================================================================
# CVRenderer.__init__ tests
# =============================================================================

class TestCVRendererInit:
    """Tests for CVRenderer initialization."""

    def test_init_stores_profile(self, minimal_profile):
        """Test that profile is stored correctly."""
        renderer = CVRenderer(minimal_profile)
        assert renderer.profile == minimal_profile

    def test_init_sets_a4_dimensions(self, minimal_profile):
        """Test that A4 dimensions are set."""
        renderer = CVRenderer(minimal_profile)
        assert renderer.width > 0
        assert renderer.height > 0

    def test_init_sets_margin(self, minimal_profile):
        """Test that margin is set."""
        renderer = CVRenderer(minimal_profile)
        assert renderer.margin > 0

    def test_init_calculates_content_width(self, minimal_profile):
        """Test that content width is calculated."""
        renderer = CVRenderer(minimal_profile)
        assert renderer.content_width > 0
        assert renderer.content_width < renderer.width

    def test_init_with_empty_profile(self, empty_profile):
        """Test initialization with minimal profile."""
        renderer = CVRenderer(empty_profile)
        assert renderer.profile == empty_profile
        assert renderer.profile["title"] == "Minimal Title"

    def test_init_with_full_profile(self, full_profile):
        """Test initialization with full profile."""
        renderer = CVRenderer(full_profile)
        assert renderer.profile == full_profile
        assert "experience" in renderer.profile


# =============================================================================
# CVRenderer.render tests
# =============================================================================

class TestCVRendererRender:
    """Tests for CVRenderer.render method."""

    def test_render_creates_pdf_file(self, minimal_profile, tmp_path):
        """Test that PDF file is created."""
        output_path = tmp_path / "test.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()
        # Check it's not empty
        assert output_path.stat().st_size > 0

    def test_render_modern_template(self, minimal_profile, tmp_path):
        """Test rendering with modern template."""
        output_path = tmp_path / "modern.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_render_classic_template(self, minimal_profile, tmp_path):
        """Test rendering with classic template."""
        output_path = tmp_path / "classic.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="classic")

        assert output_path.exists()

    def test_render_minimal_template(self, minimal_profile, tmp_path):
        """Test rendering with minimal template."""
        output_path = tmp_path / "minimal.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="minimal")

        assert output_path.exists()

    def test_render_ats_template(self, minimal_profile, tmp_path):
        """Test rendering with ats-friendly template."""
        output_path = tmp_path / "ats.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="ats-friendly")

        assert output_path.exists()

    def test_render_default_template(self, minimal_profile, tmp_path):
        """Test that default template is modern."""
        output_path = tmp_path / "default.pdf"
        renderer = CVRenderer(minimal_profile)
        # No template specified - should default to modern
        renderer.render(str(output_path))

        assert output_path.exists()

    def test_render_invalid_template_uses_modern(self, minimal_profile, tmp_path):
        """Test that invalid template falls back to modern."""
        output_path = tmp_path / "invalid.pdf"
        renderer = CVRenderer(minimal_profile)
        # Should not raise, falls back to modern
        renderer.render(str(output_path), template="nonexistent")

        assert output_path.exists()


# =============================================================================
# CVRenderer.render with different profiles
# =============================================================================

class TestCVRendererRenderProfiles:
    """Tests for rendering different profile types."""

    def test_render_minimal_profile(self, minimal_profile, tmp_path):
        """Test rendering with minimal profile."""
        output_path = tmp_path / "minimal.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_full_profile(self, full_profile, tmp_path):
        """Test rendering with full profile."""
        output_path = tmp_path / "full.pdf"
        renderer = CVRenderer(full_profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_render_profile_with_experience(self, profile_with_experience, tmp_path):
        """Test rendering profile with experience."""
        output_path = tmp_path / "experience.pdf"
        renderer = CVRenderer(profile_with_experience)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_render_profile_with_education(self, profile_with_education, tmp_path):
        """Test rendering profile with education."""
        output_path = tmp_path / "education.pdf"
        renderer = CVRenderer(profile_with_education)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_render_profile_with_languages(self, profile_with_languages, tmp_path):
        """Test rendering profile with languages."""
        output_path = tmp_path / "languages.pdf"
        renderer = CVRenderer(profile_with_languages)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_render_profile_with_certifications(self, profile_with_certifications, tmp_path):
        """Test rendering profile with certifications."""
        output_path = tmp_path / "certifications.pdf"
        renderer = CVRenderer(profile_with_certifications)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()


# =============================================================================
# Test handling of optional fields
# =============================================================================

class TestCVRendererOptionalFields:
    """Tests for handling optional/missing fields."""

    def test_profile_with_none_values(self, tmp_path):
        """Test profile with None values."""
        profile = {
            "title": "Test",
            "profile": "Test profile",
            "keywords": ["Python"],
            "email": None,
            "location": None,
            "linkedin": None
        }
        output_path = tmp_path / "none_values.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_with_empty_strings(self, tmp_path):
        """Test profile with empty strings."""
        profile = {
            "title": "Test",
            "profile": "",
            "keywords": [],
            "email": "",
            "location": "",
            "linkedin": ""
        }
        output_path = tmp_path / "empty_strings.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_without_experience(self, minimal_profile, tmp_path):
        """Test profile without experience section."""
        profile = minimal_profile.copy()
        profile.pop("experience", None)

        output_path = tmp_path / "no_experience.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_without_education(self, minimal_profile, tmp_path):
        """Test profile without education section."""
        profile = minimal_profile.copy()
        profile.pop("education", None)

        output_path = tmp_path / "no_education.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_without_languages(self, minimal_profile, tmp_path):
        """Test profile without languages section."""
        profile = minimal_profile.copy()
        profile.pop("languages", None)

        output_path = tmp_path / "no_languages.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_without_certifications(self, minimal_profile, tmp_path):
        """Test profile without certifications section."""
        profile = minimal_profile.copy()
        profile.pop("certifications", None)

        output_path = tmp_path / "no_certs.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()


# =============================================================================
# Test all templates with full profile
# =============================================================================

class TestCVRendererAllTemplates:
    """Tests for all template types with full profile."""

    @pytest.mark.parametrize("template", ["modern", "classic", "minimal", "ats-friendly"])
    def test_render_all_templates_with_full_profile(self, full_profile, tmp_path, template):
        """Test rendering all templates with full profile."""
        output_path = tmp_path / f"{template}.pdf"
        renderer = CVRenderer(full_profile)
        renderer.render(str(output_path), template=template)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    @pytest.mark.parametrize("template", ["modern", "classic", "minimal", "ats-friendly"])
    def test_render_all_templates_with_minimal_profile(self, minimal_profile, tmp_path, template):
        """Test rendering all templates with minimal profile."""
        output_path = tmp_path / f"{template}_minimal.pdf"
        renderer = CVRenderer(minimal_profile)
        renderer.render(str(output_path), template=template)

        assert output_path.exists()


# =============================================================================
# Test generator.py render_pdf function
# =============================================================================

class TestRenderPdfFunction:
    """Tests for generator.render_pdf function."""

    def test_render_pdf_function(self, minimal_profile, tmp_path, templates_dir):
        """Test render_pdf from generator module."""
        from generator import render_pdf

        output_path = tmp_path / "rendered.pdf"
        render_pdf(minimal_profile, "modern", templates_dir, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


# =============================================================================
# Test edge cases and error handling
# =============================================================================

class TestCVRendererEdgeCases:
    """Edge case tests for CVRenderer."""

    def test_profile_with_many_keywords(self, tmp_path):
        """Test profile with many keywords."""
        profile = {
            "title": "Developer",
            "profile": "Profile",
            "keywords": [f"Skill{i}" for i in range(30)]
        }
        output_path = tmp_path / "many_skills.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_with_unicode(self, tmp_path):
        """Test profile with unicode characters."""
        profile = {
            "title": "Développeur",
            "profile": "Profil avec émoji 🎉",
            "keywords": ["Python", "JavaScript"],
            "email": "test@example.com",
            "location": "São Paulo, Brazil",
            "linkedin": "linkedin.com/in/test"
        }
        output_path = tmp_path / "unicode.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_with_url_linkedin(self, tmp_path):
        """Test profile with full LinkedIn URL."""
        profile = {
            "title": "Developer",
            "profile": "Profile",
            "keywords": ["Python"],
            "linkedin": "https://www.linkedin.com/in/johndoe"
        }
        output_path = tmp_path / "url_linkedin.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_with_long_description(self, tmp_path):
        """Test profile with long job description."""
        profile = {
            "title": "Developer",
            "profile": "Profile",
            "keywords": ["Python"],
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Company",
                    "start_date": "2020",
                    "end_date": "Present",
                    "description": "Word " * 200
                }
            ]
        }
        output_path = tmp_path / "long_desc.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()

    def test_profile_with_empty_experience_list(self, tmp_path):
        """Test profile with empty experience list."""
        profile = {
            "title": "Developer",
            "profile": "Profile",
            "keywords": ["Python"],
            "experience": []
        }
        output_path = tmp_path / "empty_exp.pdf"
        renderer = CVRenderer(profile)
        renderer.render(str(output_path), template="modern")

        assert output_path.exists()
