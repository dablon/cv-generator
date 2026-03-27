# CV Generator

Generate ATS-friendly CVs in multiple formats from a single JSON profile.

```
JSON Profile → [CV Generator] → HTML | PDF | CSV | Markdown
```

## Quick Start

```bash
# Install dependencies
pip install -e .

# Generate all formats (HTML, CSV, MD)
python cli.py generate --profile examples/v2-platform-architect.json --template modern

# Preview in browser
python cli.py preview --profile examples/v2-platform-architect.json --template modern

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
  "title": "Your Title",
  "subtitle": "Keywords · Keywords",
  "email": "you@email.com",
  "phone": "+1 555 000 0000",
  "location": "City, Country",
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
    {"name": "English", "level": "Professional"}
  ]
}
```

## Output Formats

| Format | Use Case |
|--------|----------|
| **HTML** | Email attachments, web upload, browser preview |
| **CSV** | ATS systems (Indeed, LinkedIn), spreadsheet imports |
| **MD** | Text-only contexts, Markdown-friendly platforms |
| **PDF** | Recruiter submission, printing (coming soon) |

## Project Structure

```
cv-generator/
├── cli.py              # CLI entry point
├── generator.py        # Core rendering logic
├── templates/
│   ├── classic/         # Traditional two-column
│   ├── modern/          # Clean, tech-forward
│   ├── minimal/         # Maximum whitespace
│   └── ats-friendly/    # ATS-optimized
├── examples/            # Sample profiles
└── output/               # Generated CVs
```

## License

Private - Nicolas Alcaraz
