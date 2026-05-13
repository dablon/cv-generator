# CV Generator

Generate professional, ATS-friendly CVs in multiple formats from a single JSON profile. Uses headless Chromium via Playwright for pixel-perfect PDF rendering.

```
JSON Profile → [CV Generator] → HTML | PDF | CSV | Markdown
```

## Quick Start

### Using Docker (Recommended)

Docker avoids Python dependency hell. The container bundles Chromium and all system libraries.

```bash
# Build the image
docker build -t cv-generator .

# Generate all formats (HTML, CSV, MD, PDF)
docker run --rm -v "${PWD}/output:/app/output" cv-generator `
  python cli.py generate --profile data/v5-devops-engineer.json --template modern

# Generate specific formats
docker run --rm -v "${PWD}/output:/app/output" cv-generator `
  python cli.py generate --profile data/v5-devops-engineer.json --template modern --formats pdf

# All templates, all formats
docker run --rm -v "${PWD}/output:/app/output" cv-generator `
  python cli.py generate --profile data/v5-devops-engineer.json --all-templates -f html,csv,md,pdf

# Preview in browser (local only, not in Docker)
python cli.py preview --profile data/v5-devops-engineer.json --template modern
```

**Note:** On first run, ensure the `output/` directory exists locally.

### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
python -m playwright install chromium

# Generate CV
python cli.py generate --profile data/v5-devops-engineer.json --template modern --formats pdf

# Preview in browser
python cli.py preview --profile data/v5-devops-engineer.json --template modern

# List available templates
python cli.py list-templates
```

## Templates

| Template | Best For |
|----------|----------|
| `modern` | Tech companies, startups, product companies |
| `classic` | Traditional industries, corporate, finance |
| `minimal` | One-page limit, recruiter emails |
| `ats-friendly` | Maximum ATS parseability, keyword density |
| `ats-pro` | Enhanced ATS layout with skills grid |
| `executive` | C-level roles, leadership positions |
| `creative` | Design, marketing, creative industries |
| `minimal-pro` | Ultra-clean single-column |
| `two-column` | Clean sidebar with numbered sections |
| `timeline` | Visual vertical timeline for experience |
| `card-stack` | Card-based layout with shadows |

## JSON Profile Format

```json
{
  "name": "Your Name",
  "title": "Job Title",
  "subtitle": "Keywords · Keywords",
  "photo": "path/to/photo.png",
  "email": "you@email.com",
  "phone": "+1 555 000 0000",
  "location": "City, Country (Remote)",
  "linkedin": "linkedin.com/in/yourprofile",
  "profile": "Your professional summary...",
  "keywords": ["Skill", "Skill", "Skill"],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company",
      "location": "City, Country",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "description": "What you did..."
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University",
      "year": "2015 - 2018"
    }
  ],
  "certifications": ["Cert 1", "Cert 2"],
  "languages": [
    {"name": "English", "level": "B2 - Upper Intermediate"}
  ]
}
```

### Photo Support

Add a `photo` field with a path to a PNG/JPG/GIF. The image is automatically inlined as base64 in PDF output so it works in Docker without filesystem access.

```json
{
  "photo": "data/profile-photo.png"
}
```

## Output Formats

| Format | Use Case |
|--------|----------|
| **HTML** | Email attachments, web upload, browser preview |
| **CSV** | ATS systems (Indeed, LinkedIn), spreadsheet imports |
| **MD** | Text-only contexts, Markdown-friendly platforms |
| **PDF** | Recruiter submission, printing |

## PDF Rendering

PDFs are generated via **Playwright + headless Chromium** for pixel-perfect rendering:

- Template CSS is automatically inlined — no external file dependencies.
- Google Fonts links are stripped to avoid network stalls in Docker.
- Background colors and graphics are preserved with `print-color-adjust: exact`.
- Photos are embedded as base64 data URIs.

## Project Structure

```
cv-generator/
├── cli.py              # CLI entry point
├── generator.py        # Core rendering logic (HTML, PDF, CSV, MD)
├── Dockerfile          # Docker container with Chromium
├── requirements.txt    # Python dependencies
├── templates/
│   ├── modern/         # Tech-forward with sidebar
│   ├── classic/        # Traditional two-column
│   ├── minimal/        # Maximum whitespace
│   ├── ats-friendly/   # ATS-optimized
│   ├── ats-pro/        # Enhanced ATS layout
│   ├── executive/      # C-level table layout
│   ├── creative/       # Visual creative style
│   ├── minimal-pro/    # Ultra-clean single-column
│   ├── two-column/     # Clean sidebar + numbered sections
│   ├── timeline/       # Vertical timeline experience
│   └── card-stack/     # Card-based modern layout
├── data/               # JSON profile files
└── output/             # Generated CVs
```

## Testing

```bash
# Run all tests
pytest tests/test_generator.py -v

# Run with coverage
pytest --cov=generator --cov-report=html
```

## License

Private - Nicolas Alcaraz
