#!/usr/bin/env python3
"""
CV Generator CLI
Usage:
    python cli.py generate --profile examples/v2-platform-architect.json --template modern
    python cli.py list-templates
    python cli.py preview --profile examples/v2-platform-architect.json --port 3000
"""

import typer
from pathlib import Path
from typing import Optional
from generator import generate, list_templates

app = typer.Typer(
    name="cv-generator",
    help="Generate ATS-friendly CVs in HTML, PDF, CSV from JSON profiles.",
)

OUTPUT_DIR = Path(__file__).parent / 'output'
TEMPLATES_DIR = Path(__file__).parent / 'templates'
EXAMPLES_DIR = Path(__file__).parent / 'examples'


@app.command()
def generate(
    profile: Path = typer.Option(..., "--profile", "-p", help="Path to JSON profile"),
    template: str = typer.Option("modern", "--template", "-t", help="Template name"),
    output_dir: Path = typer.Option(OUTPUT_DIR, "--output", "-o", help="Output directory"),
    formats: str = typer.Option("html,csv,md", "--formats", "-f", help="Comma-separated formats: html,csv,md"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Generate CV from JSON profile."""

    format_list = [f.strip() for f in formats.split(',')]
    valid_formats = {'html', 'csv', 'md'}
    invalid = set(format_list) - valid_formats
    if invalid:
        typer.echo(f"Invalid formats: {invalid}. Valid: {valid_formats}", err=True)
        raise typer.Exit(1)

    templates = list_templates(TEMPLATES_DIR)
    if template not in templates:
        typer.echo(f"Template '{template}' not found. Available: {templates}", err=True)
        raise typer.Exit(1)

    if not profile.exists():
        typer.echo(f"Profile not found: {profile}", err=True)
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Generating CV for: {profile.name}")
    typer.echo(f"Template: {template}")
    typer.echo(f"Formats: {format_list}")
    typer.echo("")

    results = generate(
        profile_path=profile,
        template_name=template,
        templates_dir=TEMPLATES_DIR,
        output_dir=output_dir,
        formats=format_list,
    )

    typer.echo("✅ Generated files:")
    for fmt, path in results.items():
        typer.echo(f"  [{fmt.upper()}] {path}")


@app.command()
def list_templates_cmd(
    templates_dir: Path = typer.Option(TEMPLATES_DIR, "--dir", help="Templates directory"),
):
    """List available CV templates."""
    templates = list_templates(templates_dir)
    typer.echo("Available templates:")
    for t in templates:
        typer.echo(f"  • {t}")


@app.command()
def preview(
    profile: Path = typer.Option(..., "--profile", "-p", help="Path to JSON profile"),
    template: str = typer.Option("modern", "--template", "-t", help="Template name"),
    port: int = typer.Option(3000, "--port", help="Preview server port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Preview server host"),
    open_browser: bool = typer.Option(True, "--no-open", help="Don't open browser"),
):
    """Start a local web server to preview CV."""
    import tempfile
    import webbrowser
    import http.server
    import socketserver
    import threading
    from generator import render_html, load_profile

    if not profile.exists():
        typer.echo(f"Profile not found: {profile}", err=True)
        raise typer.Exit(1)

    profile_data = load_profile(profile)
    html_content = render_html(profile_data, template, TEMPLATES_DIR)

    # Write to temp file for serving
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress request logs

    # Change to temp directory
    old_cwd = Path.cwd()
    temp_dir = Path(tempfile.gettempdir())
    temp_file = Path(temp_path)

    try:
        # Copy HTML to temp with proper name
        preview_file = temp_dir / f"cv_preview_{template}.html"
        preview_file.write_text(html_content, encoding='utf-8')

        handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(temp_dir), **kwargs)
        with socketserver.TCPServer((host, port), handler) as httpd:
            url = f"http://{host}:{port}/{preview_file.name}"
            typer.echo(f"📄 Preview server running at: {url}")
            typer.echo("Press Ctrl+C to stop.")

            if open_browser:
                webbrowser.open(url)

            httpd.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\n👋 Preview server stopped.")
    finally:
        old_cwd.chdir()


if __name__ == "__main__":
    app()
