#!/usr/bin/env python3
"""
CV Generator CLI

Command-line interface for the CV Generator. Provides commands to:
- Generate CVs in multiple formats (HTML, PDF, CSV, Markdown)
- List available templates
- Preview CVs in a local web server

Usage:
    python cli.py generate --profile examples/v2-platform-architect.json --template modern
    python cli.py list-templates
    python cli.py preview --profile examples/v2-platform-architect.json --port 3000
"""

import logging
import tempfile
import threading
import webbrowser
import http.server
import socketserver
from pathlib import Path
from typing import Optional

import typer

from generator import generate as generate_cv, list_templates, render_html, load_profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    template: str = typer.Option("modern", "--template", "-t", help="Template name (or 'all' for all templates)"),
    output_dir: Path = typer.Option(OUTPUT_DIR, "--output", "-o", help="Output directory"),
    formats: str = typer.Option("html,csv,md", "--formats", "-f", help="Comma-separated formats: html,csv,md,pdf"),
    all_templates: bool = typer.Option(False, "--all-templates", "--all", help="Generate CV using all available templates"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Generate CV from JSON profile in multiple formats.

    Reads a JSON profile file and generates CV output in the specified formats
    using the selected template. Supports HTML, PDF, CSV, and Markdown formats.

    Args:
        profile: Path to the JSON profile file containing CV data.
        template: Name of the template to use (use 'all' for all templates).
        output_dir: Directory where output files will be saved.
        formats: Comma-separated list of output formats.
                 Valid options: html, csv, md, pdf.
        all_templates: Generate CV using all available templates at once.
        verbose: Enable verbose logging output.

    Raises:
        typer.Exit: If profile doesn't exist, template is invalid, or format is unsupported.

    Example:
        python cli.py generate -p profile.json -t modern -f html,pdf
        python cli.py generate -p profile.json --all-templates -f html
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Parse and validate formats
    format_list = [f.strip() for f in formats.split(',')]
    valid_formats = {'html', 'csv', 'md', 'pdf'}
    invalid = set(format_list) - valid_formats

    if invalid:
        typer.echo(f"Invalid formats: {invalid}. Valid: {valid_formats}", err=True)
        raise typer.Exit(1)

    # Get available templates
    available_templates = list_templates(TEMPLATES_DIR)

    # Determine which templates to use
    if all_templates or template.lower() == 'all':
        templates_to_generate = available_templates
    else:
        if template not in available_templates:
            typer.echo(f"Template '{template}' not found. Available: {available_templates}", err=True)
            raise typer.Exit(1)
        templates_to_generate = [template]

    # Validate profile exists
    if not profile.exists():
        typer.echo(f"Profile not found: {profile}", err=True)
        raise typer.Exit(1)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Display generation info
    typer.echo(f"Generating CV for: {profile.name}")
    typer.echo(f"Templates: {templates_to_generate}")
    typer.echo(f"Formats: {format_list}")
    typer.echo("")

    # Generate CV for each template
    total_files = 0
    try:
        for tmpl in templates_to_generate:
            logger.info(f"Generating CV with template: {tmpl}")
            typer.echo(f"--- Template: {tmpl} ---")

            results = generate_cv(
                profile_path=profile,
                template_name=tmpl,
                templates_dir=TEMPLATES_DIR,
                output_dir=output_dir,
                formats=format_list,
            )

            # Display results for this template
            for fmt, path in results.items():
                typer.echo(f"  [{fmt.upper()}] {path}")

            total_files += len(results)

        logger.info(f"Successfully generated {total_files} files")
        typer.echo(f"\n Total: {total_files} files generated")

    except Exception as e:
        logger.error(f"Failed to generate CV: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def list_templates_cmd(
    templates_dir: Path = typer.Option(TEMPLATES_DIR, "--dir", help="Templates directory"),
):
    """List available CV templates.

    Scans the templates directory and displays all available CV templates
    that can be used with the generate command.

    Args:
        templates_dir: Path to the templates directory (default: ./templates).

    Example:
        python cli.py list-templates
    """
    templates = list_templates(templates_dir)

    if templates:
        typer.echo("Available templates:")
        for t in templates:
            typer.echo(f"  - {t}")
    else:
        typer.echo("No templates found.")


@app.command()
def preview(
    profile: Path = typer.Option(..., "--profile", "-p", help="Path to JSON profile"),
    template: str = typer.Option("modern", "--template", "-t", help="Template name"),
    port: int = typer.Option(3000, "--port", help="Preview server port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Preview server host"),
    open_browser: bool = typer.Option(True, "--no-open", help="Don't open browser"),
):
    """Start a local web server to preview CV.

    Generates an HTML preview of the CV and serves it via a local HTTP server.
    Optionally opens the default browser to display the preview.

    Args:
        profile: Path to the JSON profile file.
        template: Name of the template to use.
        port: Port number for the preview server (default: 3000).
        host: Host address for the server (default: 127.0.0.1).
        open_browser: If True, automatically open the default browser.

    Raises:
        typer.Exit: If profile doesn't exist or template is invalid.

    Example:
        python cli.py preview -p profile.json -t modern --port 8080

    Notes:
        Press Ctrl+C to stop the preview server.
    """
    # Validate profile exists
    if not profile.exists():
        typer.echo(f"Profile not found: {profile}", err=True)
        raise typer.Exit(1)

    # Validate template exists
    available_templates = list_templates(TEMPLATES_DIR)
    if template not in available_templates:
        typer.echo(f"Template '{template}' not found. Available: {available_templates}", err=True)
        raise typer.Exit(1)

    # Load profile and render HTML
    profile_data = load_profile(profile)
    html_content = render_html(profile_data, template, TEMPLATES_DIR)

    # Create temp file for serving
    temp_dir = Path(tempfile.gettempdir())
    preview_file = temp_dir / f"cv_preview_{template}.html"
    preview_file.write_text(html_content, encoding='utf-8')

    # Custom handler that suppresses request logs
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress HTTP request logs

    # Start server
    try:
        handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(temp_dir), **kwargs)
        with socketserver.TCPServer((host, port), handler) as httpd:
            url = f"http://{host}:{port}/{preview_file.name}"
            typer.echo(f"Preview server running at: {url}")
            typer.echo("Press Ctrl+C to stop.")

            if open_browser:
                webbrowser.open(url)

            httpd.serve_forever()

    except KeyboardInterrupt:
        typer.echo("\nPreview server stopped.")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            typer.echo(f"Error: Port {port} is already in use. Try a different port.", err=True)
        else:
            typer.echo(f"Error starting server: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()