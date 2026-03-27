"""
CV Generator Core
"""

import csv
import json
from pathlib import Path


def load_profile(profile_path: str | Path) -> dict:
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_keywords(keywords: list[str]) -> list[dict]:
    return [{"items": keywords[i:i+4]} for i in range(0, len(keywords), 4)]


def render_html(profile: dict, template_name: str, templates_dir: Path) -> str:
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


def render_pdf(profile: dict, template_name: str, templates_dir: Path, output_path: Path) -> None:
    from weasyprint import HTML
    html_content = render_html(profile, template_name, templates_dir)
    HTML(string=html_content, base_url=str(templates_dir)).write_pdf(str(output_path))


def render_csv(profile: dict, output_path: Path) -> None:
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(['Section', 'Content'])
        writer.writerow(['PROFILE', profile.get('profile', '')])
        keywords = profile.get('keywords', [])
        writer.writerow(['KEYWORDS', ' | '.join(keywords)])
        writer.writerow(['TITLE', profile.get('title', '')])


def render_markdown(profile: dict) -> str:
    lines = [
        f"# {profile.get('title', 'CV')}",
        "",
        "## Profile",
        profile.get('profile', ''),
        "",
        "## Skills",
    ]
    for kw in profile.get('keywords', []):
        lines.append(f"- {kw}")
    return '\n'.join(lines)


def generate(
    profile_path: str | Path,
    template_name: str = 'modern',
    templates_dir: Path | None = None,
    output_dir: Path | None = None,
    formats: list[str] | None = None,
) -> dict[str, Path]:
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
        elif fmt == 'pdf':
            render_pdf(profile, template_name, templates_dir, output_file)
            results['pdf'] = output_file

    return results


def list_templates(templates_dir: Path | None = None) -> list[str]:
    if templates_dir is None:
        templates_dir = Path(__file__).parent / 'templates'
    return sorted([
        d.name for d in templates_dir.iterdir()
        if d.is_dir() and (d / 'template.html').exists()
    ])
