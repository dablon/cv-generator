# CV Generator

Generate ATS-friendly CVs in multiple formats from a single JSON profile.

```
JSON Profile → [CV Generator] → HTML | PDF | CSV | Markdown
```

## Quick Start

### Using Docker (Recommended)

Docker avoids Python dependency hell. The container has everything pre-installed.

```bash
# Build the image
docker build -t cv-generator .

# Generate all formats (HTML, CSV, MD, PDF)
docker run --rm -v "$(pwd)/output:/app/output" cv-generator \
  python cli.py generate --profile data/v5-devops-engineer.json --template classic

# Generate specific formats
docker run --rm -v "$(pwd)/output:/app/output" cv-generator \
  python cli.py generate --profile data/v5-devops-engineer.json --template classic --formats pdf

# All templates, all formats
docker run --rm -v "$(pwd)/output:/app/output" cv-generator \
  python cli.py generate --profile data/v5-devops-engineer.json --all-templates -f html,csv,md,pdf

# Preview in browser
docker run --rm -v "$(pwd)/output:/app/output" cv-generator \
  python cli.py preview --profile data/v5-devops-engineer.json --template classic
```

The `-v "$(pwd)/output:/app/output"` mounts the container's output to your local `output/` folder.

**Note:** On first run, ensure the `output/` directory exists locally: `mkdir -p output`

### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Generate CV
python cli.py generate --profile data/v5-devops-engineer.json --template classic --formats pdf

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

## JSON Profile Format

```json
{
  "name": "Your Name",
  "title": "Job Title",
  "subtitle": "Keywords · Keywords",
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

## Output Formats

| Format | Use Case |
|--------|----------|
| **HTML** | Email attachments, web upload, browser preview |
| **CSV** | ATS systems (Indeed, LinkedIn), spreadsheet imports |
| **MD** | Text-only contexts, Markdown-friendly platforms |
| **PDF** | Recruiter submission, printing |

## Project Structure

```
cv-generator/
├── cli.py              # CLI entry point
├── generator.py        # Core rendering logic
├── pdf_generator.py    # PDF rendering with ReportLab
├── Dockerfile          # Docker container definition
├── templates/
│   ├── classic/         # Traditional two-column
│   ├── modern/          # Clean, tech-forward
│   ├── minimal/         # Maximum whitespace
│   └── ats-friendly/    # ATS-optimized
├── data/                # JSON profile files
├── examples/            # Sample profiles
└── output/              # Generated CVs
```

## License

Private - Nicolas Alcaraz
