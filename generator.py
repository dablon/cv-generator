"""
CV Generator Core
Takes a JSON profile and renders it through Jinja2 templates.
"""

import csv
import json
from pathlib import Path
from typing import Optional


def load_profile(profile_path: str | Path) -> dict:
    """Load and parse a JSON profile file."""
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_keywords(keywords: list[str]) -> list[dict]:
    """Convert flat keyword list to structured format for templates."""
    # Group keywords into rows of 3-4 for display
    return [{"items": keywords[i:i+4]} for i in range(0, len(keywords), 4)]


def render_html(
    profile: dict,
    template_name: str,
    templates_dir: Path,
) -> str:
    """Render profile to HTML using specified template."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml']),
    )
    env.filters['parse_keywords'] = parse_keywords

    template = env.get_template(f"{template_name}/template.html")
    return template.render(
        profile=profile,
        keywords_parsed=parse_keywords(profile.get('keywords', [])),
    )


def render_csv(
    profile: dict,
    output_path: Path,
) -> None:
    """Render profile to CSV (ATS-friendly format)."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow(['Section', 'Content'])

        # Profile
        writer.writerow(['PROFILE', profile.get('profile', '')])

        # Keywords in rows
        keywords = profile.get('keywords', [])
        writer.writerow(['KEYWORDS', ' | '.join(keywords)])

        # Title
        writer.writerow(['TITLE', profile.get('title', '')])


def render_markdown(profile: dict) -> str:
    """Render profile to Markdown (for text-only contexts)."""
    lines = [
        f"# {profile.get('title', 'CV')}",
        "",
        "## Profile",
        profile.get('profile', ''),
        "",
        "## Skills",
    ]

    keywords = profile.get('keywords', [])
    for kw in keywords:
        lines.append(f"- {kw}")

    return '\n'.join(lines)


def generate(
    profile_path: str | Path,
    template_name: str = 'modern',
    templates_dir: Path | None = None,
    output_dir: Path | None = None,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """
    Generate CV in multiple formats from a JSON profile.

    Returns dict of {format: output_path}
    """
    profile = load_profile(profile_path)
    profile_path = Path(profile_path)
    profile_name = profile_path.stem

    if templates_dir is None:
        templates_dir = Path(__file__).parent / 'templates'
    if output_dir is None:
        output_dir = Path(__file__).parent / 'output'
    if formats is None:
        formats = ['html', 'csv', 'md']

    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for fmt in formats:
        output_file = output_dir / f"{profile_name}_{template_name}.{fmt}"

        if fmt == 'html':
            html_content = render_html(profile, template_name, templates_dir)
            output_file.write_text(html_content, encoding='utf-8')
            results['html'] = output_file

        elif fmt == 'csv':
            render_csv(profile, output_file)
            results['csv'] = output_file

        elif fmt == 'md':
            md_content = render_markdown(profile)
            output_file.write_text(md_content, encoding='utf-8')
            results['md'] = output_file

    return results


def list_templates(templates_dir: Path | None = None) -> list[str]:
    """List available template names."""
    if templates_dir is None:
        templates_dir = Path(__file__).parent / 'templates'

    return sorted([
        d.name for d in templates_dir.iterdir()
        if d.is_dir() and (d / 'template.html').exists()
    ])
