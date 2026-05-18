# Live Demo

https://resume-analyzer-6pdw.onrender.com

![CI](https://github.com/Jiawei-15/resume-analyzer/actions/workflows/ci.yml/badge.svg)

---

# AI Resume Analyzer

A full-stack resume analysis web application built with FastAPI, Python, HTML, CSS, and JavaScript.

The system analyzes a resume (PDF, DOCX, TXT, or image), extracts technical skills, compares them with a target job description, generates structured feedback on skill alignment and missing keywords, and persists analysis history to a local SQLite database.

---

# Features

- Upload PDF, DOCX, TXT, PNG, JPG, and JPEG resumes
- Automatic text extraction including OCR for image-based resumes
- Technical skill detection with alias normalization (JS → JavaScript, ML → machine learning, etc.)
- Weighted skill matching — core skills contribute more to the match score than peripheral ones
- Two-mode semantic scoring: OpenAI embeddings when available, TF-IDF cosine similarity as local fallback
- Skill-level feedback — every missing skill generates a specific, actionable suggestion
- Analysis history persisted to SQLite with a `/history` REST endpoint
- Frontend + backend integration
- REST API architecture with FastAPI
- Modular backend structure
- Logging and validation support

---

# Tech Stack

## Backend
- Python 3.11
- FastAPI
- Uvicorn
- SQLite
- scikit-learn (TF-IDF semantic matching)
- OpenAI API (optional)
- pypdf, python-docx, Pillow, pytesseract
- python-dotenv

## Frontend
- HTML
- CSS
- JavaScript

## Other Tools
- Git / GitHub
- Jinja2
- Docker
- GitHub Actions (CI)
- Render (deployment)

---

# Project Structure

```text
resume-analyzer/
│
├── app/
│   ├── routers/
│   │   └── resume.py         # API endpoints
│   ├── services/
│   │   └── resume_service.py # Business logic
│   ├── schemas/
│   │   └── responses.py      # Pydantic response models
│   ├── config.py             # Environment variable loading
│   ├── database.py           # SQLite init, save, query
│   ├── normalization.py      # Skill alias mapping
│   ├── semantic.py           # TF-IDF and OpenAI semantic matching
│   ├── skills.py             # Master skill list
│   ├── utils.py              # Text extraction, matching, feedback
│   ├── weights.py            # Skill importance weights
│   └── main.py               # FastAPI app entry point
│
├── tests/
│   ├── test_basic.py         # API endpoint tests
│   └── test_utils.py         # Unit tests for core logic
│
├── static/
├── templates/
├── assets/
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Semantic Matching

This project supports two semantic scoring modes:

1. **OpenAI Embeddings**
   - Uses OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` is available and `USE_OPENAI_EMBEDDINGS=True`

2. **TF-IDF Local Fallback**
   - Uses scikit-learn TF-IDF cosine similarity when OpenAI credentials are missing or disabled
   - No external API required — works fully offline

Both modes return a `semantic_score` and `semantic_source` field in the API response.

---

## Analysis History

Every `/match` request is saved to a local SQLite database. The `/history` endpoint returns the 20 most recent analyses with full skill breakdowns and feedback.

```bash
GET /history
```

---

## Environment Variables

Create a local `.env` file based on `.env.example`:

```env
OPENAI_API_KEY=your_api_key_here
USE_OPENAI_EMBEDDINGS=True
```

The application runs without an OpenAI key — TF-IDF scoring activates automatically.

---

# How It Works

1. User uploads a resume file (PDF, DOCX, TXT, or image)
2. Backend extracts text — OCR is used for image files
3. Skill aliases are normalized (e.g. "RESTful APIs" → "rest api")
4. Technical skills are matched against a master skill list
5. Matched and missing skills are compared against the job description
6. Weighted match score and semantic score are calculated
7. Per-skill feedback is generated for every missing skill
8. Analysis is saved to SQLite history
9. Results are returned to the frontend

---

# Run Locally

## Clone repository

```bash
git clone https://github.com/Jiawei-15/resume-analyzer.git
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Start server

```bash
uvicorn app.main:app --reload
```

## Open browser

```text
http://127.0.0.1:8000
```

## Run tests

```bash
pytest tests/ -v
```

## Run with Docker

```bash
docker build -t resume-analyzer .
docker run -p 10000:10000 resume-analyzer
```

---

# Author

Built as a portfolio backend/full-stack project focused on resume analysis and API architecture.
