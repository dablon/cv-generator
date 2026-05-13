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
    """Render CV profile to PDF using Playwright headless browser.

    Renders the HTML template via Chromium and prints to PDF with proper
    A4 pagination, margins, and background graphics.
    """
    from playwright.sync_api import sync_playwright

    html_content = render_html(profile, template_name, templates_dir)

    # Inline the template stylesheet so Chromium has all styles regardless of file paths
    css_path = templates_dir / template_name / "style.css"
    inline_styles = []
    if css_path.exists():
        inline_styles.append(css_path.read_text(encoding="utf-8"))

    # Add print-specific rules for proper A4 sizing and backgrounds
    inline_styles.append("""
    @page { size: A4; margin: 15mm; }
    body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    .experience-item { page-break-inside: avoid; break-inside: avoid; }
    .education-item { page-break-inside: avoid; break-inside: avoid; }
    .content-section { page-break-inside: auto; }
    """)

    style_block = f"<style>\n{' '.join(inline_styles)}\n</style>"

    # Remove external stylesheet link(s) and Google Fonts (network unavailable in Docker/no-internet)
    import re
    html_content = re.sub(
        r'<link[^\u003e]*rel=["\']?stylesheet["\']?[^\u003e]*style\.css[^\u003e]*>',
        '',
        html_content,
        flags=re.IGNORECASE,
    )
    html_content = re.sub(
        r'<link[^\u003e]*fonts\.googleapis\.com[^\u003e]*>',
        '',
        html_content,
        flags=re.IGNORECASE,
    )

    # Inject inlined styles before closing </head>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", style_block + "</head>")
    else:
        html_content = style_block + html_content

    # Inline photo as base64 if present so Chromium embeds it without filesystem access.
    # After render_html() the Jinja2 variable {{ profile.photo }} is already expanded to the actual path.
    photo_path = profile.get("photo")
    if photo_path:
        photo_file = Path(photo_path)
        if photo_file.exists():
            import base64
            ext = photo_file.suffix.lower()
            mime = (
                "image/png" if ext == ".png"
                else "image/jpeg" if ext in (".jpg", ".jpeg")
                else "image/gif" if ext == ".gif"
                else "image/png"
            )
            b64 = base64.b64encode(photo_file.read_bytes()).decode("ascii")
            data_uri = f"data:{mime};base64,{b64}"
            # Replace the already-resolved path in the rendered HTML
            html_content = html_content.replace(f'src="{photo_path}"', f'src="{data_uri}"')
            html_content = html_content.replace(f"src='{photo_path}'", f'src="{data_uri}"')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Use domcontentloaded to avoid stalling on external resources
        page.set_content(html_content, wait_until="domcontentloaded")
        page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
            print_background=True,
        )
        browser.close()
    return None


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


def generate_all(
    profile_path: str | Path,
    templates_dir: Path | None = None,
    output_dir: Path | None = None,
    formats: list[str] | None = None,
) -> dict[str, dict[str, Path]]:
    """Generate CVs for **all** templates at once.

    Returns a nested dict: {template_name: {format: output_path}}.
    """
    if templates_dir is None:
        templates_dir = Path(__file__).parent / 'templates'
    if output_dir is None:
        output_dir = Path(__file__).parent / 'output'
    if formats is None:
        formats = ['html', 'csv', 'md']

    templates = list_templates(templates_dir)
    all_results = {}

    for tmpl in templates:
        all_results[tmpl] = generate(
            profile_path=profile_path,
            template_name=tmpl,
            templates_dir=templates_dir,
            output_dir=output_dir,
            formats=formats,
        )

    return all_results


def list_templates(templates_dir: Path | None = None) -> list[str]:
    if templates_dir is None:
        templates_dir = Path(__file__).parent / 'templates'
    return sorted([
        d.name for d in templates_dir.iterdir()
        if d.is_dir() and (d / 'template.html').exists()
    ])


def validate_template_name(template_name: str, templates_dir: Path) -> None:
    """Validate template name to prevent path traversal attacks.

    Args:
        template_name: Name of the template to validate.
        templates_dir: Path to the templates directory.

    Raises:
        ValueError: If template_name is empty, contains invalid patterns,
                    or resolves outside the templates directory.
    """
    if not template_name:
        raise ValueError("template_name cannot be empty")

    if '..' in template_name or template_name.startswith('/') or template_name.startswith('\\'):
        raise ValueError(f"Invalid template name '{template_name}': path traversal not allowed")

    if len(template_name) > 1 and template_name[1] == ':':
        raise ValueError(f"Invalid template name '{template_name}': absolute paths not allowed")

    available_templates = list_templates(templates_dir)
    if template_name not in available_templates:
        raise ValueError(
            f"Template '{template_name}' not found. Available templates: {available_templates}"
        )

    template_path = (templates_dir / template_name / 'template.html').resolve()
    resolved_templates_dir = templates_dir.resolve()
    try:
        template_path.relative_to(resolved_templates_dir)
    except ValueError:
        raise ValueError(f"Template path '{template_name}' resolves outside templates directory")
