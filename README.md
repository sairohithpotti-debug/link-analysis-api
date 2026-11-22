# AI-Powered Website Link Analysis API

A FastAPI service that validates public URLs with SSRF protection, extracts and cleans webpage content, and generates a structured 5-section marketing, SEO, competitive intelligence, and audience analysis using Gemini structured JSON outputs.

## Project Structure

```text
link-analysis-api/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── schemas.py
    └── services/
        ├── __init__.py
        ├── url_validator.py
        ├── scraper.py
        └── analyzer.py
