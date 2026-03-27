# ADR-001: CV Generator — Architecture Decision

## Context

Nicolas needs a system that takes a JSON profile and generates visually distinct CVs in multiple formats (HTML, PDF, CSV) for different job applications. ATS systems parse CSV cleanly, recruiters want PDF/HTML for readability, and different industries respond to different visual styles.

## Decision

**Build a modular Python CLI + Web preview system:**

```
JSON Profile → Template Engine → Multiple Formats + Multiple Designs
```

### Stack
- **Python 3.11+** with typer CLI (simpler than argparse, prettier output)
- **Jinja2** for templating (industry standard, battle-tested)
- **WeasyPrint** for PDF generation (pure Python, no LibreOffice needed)
- **CSV** built-in Python csv module

### Template System

Each template is:
- A Jinja2 HTML file in `templates/`
- Self-contained CSS (no external dependencies)
- Rendered identically across HTML → PDF

### Directory Structure

```
cv-generator/
├── cli.py                 # Entry point (typer)
├── generator.py           # Core rendering logic
├── templates/
│   ├── classic/
│   │   ├── template.html
│   │   └── style.css
│   ├── modern/
│   │   ├── template.html
│   │   └── style.css
│   ├── minimal/
│   │   ├── template.html
│   │   └── style.css
│   └── ats-friendly/
│       ├── template.html
│       └── style.css
├── examples/
│   ├── devops-manager.json
│   ├── cloud-architect.json
│   └── ... (Nicolas's profiles)
└── output/                # Generated CVs
```

### Output Formats

| Format | Use Case | Engine |
|--------|----------|--------|
| **HTML** | Email attachments, web upload | Jinja2 |
| **PDF** | Recruiter submission, printing | WeasyPrint (HTML → PDF) |
| **CSV** | ATS parsing, spreadsheet upload | Python csv module (direct) |
| **Markdown** | LinkedIn, text-only contexts | Jinja2 |

### Supported Templates

1. **classic** — Traditional two-column, serif fonts, conservative
2. **modern** — Clean single-column, sans-serif, tech-forward
3. **minimal** — Maximum whitespace, single page, content-first
4. **ats-friendly** — Plain CSV-style layout, maximum keyword density

### CLI Interface

```bash
# Generate all formats from one profile
python cli.py generate --profile v2-platform-architect.json --template modern --output ./output/

# Generate specific format
python cli.py generate --profile v2-platform-architect.json --format pdf --template classic

# Preview web server
python cli.py serve --profile v2-platform-architect.json --port 3000

# List templates
python cli.py list-templates
```

## Consequences

### Pros
- Single source of truth: JSON in, any format out
- Templates are plain HTML/CSS — no proprietary format lock-in
- WeasyPrint renders exactly what you see in HTML
- CSV export ensures ATS compatibility (no formatting = no parsing errors)
- Easy to add new templates — just drop in a new folder

### Cons
- WeasyPrint can be heavy to install (needs specific system deps)
- PDF rendering may vary slightly from browser PDF

## Implementation Priority

1. ✅ Core generator with Jinja2 + CSV
2. ✅ 4 templates (classic, modern, minimal, ats-friendly)
3. ✅ HTML output (always works)
4. ✅ CSV output (direct, ATS-safe)
5. ⏸ PDF output (WeasyPrint — can be added later if needed)
6. ⏸ Web preview server (optional, nice-to-have)

## Status

**Proposed**
