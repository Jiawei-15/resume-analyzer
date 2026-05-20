# Live Demo

https://resume-analyzer-6pdw.onrender.com

![CI](https://github.com/Jiawei-15/resume-analyzer/actions/workflows/ci.yml/badge.svg)

---

# AI Resume Analyzer

A full-stack resume analysis web application built with FastAPI, Python, HTML, CSS, and JavaScript.

The application allows users to upload a resume, paste a target job description, and receive a structured analysis of how well the resume matches the role. It extracts technical skills, normalizes common skill aliases, calculates a weighted skill match score, calculates a semantic similarity score, generates feedback for missing skills, and stores match history in a local SQLite database.

This project was built as a portfolio backend/full-stack application focused on resume text processing, API design, semantic matching, automated testing, and deployment workflow.

---

# Features

- Upload resume files in PDF, DOCX, TXT, PNG, JPG, and JPEG formats
- Extract text from PDF, DOCX, and TXT files
- Optional OCR support for image-based resumes when Tesseract OCR is available
- Detect technical skills using a predefined skill database
- Normalize common skill aliases, such as:
  - JS → JavaScript
  - ML → machine learning
  - RESTful APIs → REST API
  - React.js → React
  - Node.js → Nodejs
- Compare resume skills against a target job description
- Calculate a weighted match score based on matched and missing skills
- Calculate a semantic similarity score using either:
  - OpenAI embeddings
  - Local TF-IDF cosine similarity fallback
- Generate structured feedback for missing or weakly represented skills
- Save match history to SQLite
- Provide a `/history` endpoint for recent analyses
- Frontend and backend integration
- Modular FastAPI backend structure
- Pydantic response models
- Logging and validation support
- Automated testing with pytest
- GitHub Actions CI workflow
- Render deployment configuration
- Docker support

---

# Tech Stack

## Backend

- Python 3.11
- FastAPI
- Uvicorn
- SQLite
- scikit-learn
- OpenAI API optional
- pypdf
- python-docx
- Pillow
- pytesseract
- python-dotenv
- Pydantic

## Frontend

- HTML
- CSS
- JavaScript
- Jinja2 templates

## Testing and Deployment

- pytest
- GitHub Actions
- Docker
- Render

## Other Tools

- Git
- GitHub

---

# Project Structure

```text
resume-analyzer/
│
├── app/
│   ├── routers/
│   │   └── resume.py         # API endpoints
│   │
│   ├── services/
│   │   └── resume_service.py # Business logic for analysis and matching
│   │
│   ├── schemas/
│   │   └── responses.py      # Pydantic response models
│   │
│   ├── config.py             # Environment variable loading
│   ├── database.py           # SQLite initialization, save, and query logic
│   ├── normalization.py      # Skill alias normalization rules
│   ├── semantic.py           # OpenAI embedding and TF-IDF semantic matching
│   ├── skills.py             # Master technical skill list
│   ├── utils.py              # Text extraction, skill extraction, scoring, feedback
│   ├── weights.py            # Skill importance weights
│   └── main.py               # FastAPI app entry point
│
├── tests/
│   ├── test_basic.py         # Basic API endpoint tests
│   └── test_utils.py         # Unit tests for core matching logic
│
├── static/
│   ├── script.js             # Frontend request and result rendering logic
│   └── style.css             # Frontend styling
│
├── templates/
│   └── index.html            # Main frontend page
│
├── assets/
│
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI workflow
│
├── Dockerfile
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```

---

# API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Loads the frontend web interface |
| POST | `/upload` | Validates and uploads a resume file |
| POST | `/analyze` | Extracts resume text and detects technical skills |
| POST | `/match` | Compares a resume against a job description |
| GET | `/history` | Returns the 20 most recent resume match results |
| GET | `/docs` | Opens the FastAPI Swagger documentation |

---

# How It Works

1. The user uploads a resume file and pastes a target job description.
2. The FastAPI backend receives the file and job description through a multipart form request.
3. The backend validates the uploaded file extension.
4. Resume text is extracted based on file type:
   - PDF files are parsed with `pypdf`
   - DOCX files are parsed with `python-docx`
   - TXT files are decoded directly
   - Image files can be processed with OCR through `pytesseract`
5. Extracted text is normalized to handle common skill name variations.
6. Technical skills are detected using a predefined skill database.
7. The job description is scanned for required skills.
8. Resume skills and job description skills are compared.
9. A weighted match score is calculated based on matched and missing skills.
10. A semantic similarity score is calculated using either OpenAI embeddings or local TF-IDF.
11. Missing skills are converted into structured feedback.
12. Match results are saved to SQLite history.
13. The frontend displays the score, matched skills, missing skills, strengths, weaknesses, suggestions, and feedback.

---

# Semantic Matching

This project supports two semantic scoring modes.

## 1. OpenAI Embeddings

When `OPENAI_API_KEY` is available and `USE_OPENAI_EMBEDDINGS=True`, the application can use OpenAI `text-embedding-3-small`.

The resume text and job description are converted into vector embeddings, and cosine similarity is used to estimate how semantically similar they are.

## 2. TF-IDF Local Fallback

When OpenAI credentials are missing, disabled, or unavailable, the application falls back to local TF-IDF cosine similarity using scikit-learn.

This allows the application to keep working without external API access.

Example response fields:

```json
{
  "semantic_score": 0.72,
  "semantic_source": "local"
}
```

or:

```json
{
  "semantic_score": 0.84,
  "semantic_source": "openai"
}
```

---

# Skill Matching Logic

The project uses two main matching layers.

## 1. Skill Extraction

Resume text is normalized before skill extraction.

Examples:

```text
JS              → javascript
ML              → machine learning
RESTful APIs    → rest api
React.js        → react
Node.js         → nodejs
```

The normalized text is then compared against a predefined technical skill database.

## 2. Weighted Job Matching

The job description is scanned for required technical skills.

Each detected job skill is classified as either:

- Matched: the skill appears in the resume
- Missing: the skill appears in the job description but not in the resume

The match score is calculated using skill weights. More important skills can contribute more heavily to the final score than smaller peripheral skills.

Example result:

```json
{
  "match_score": 0.67,
  "matched_skills": ["python", "fastapi", "sql"],
  "missing_skills": ["docker", "react"]
}
```

---

# Analysis History

Every `/match` request is saved to a local SQLite database.

The `/history` endpoint returns the 20 most recent analyses with:

- Filename
- Match score
- Semantic score
- Semantic source
- Score explanation
- Resume skills
- Matched skills
- Missing skills
- Feedback

Example request:

```bash
GET /history
```

Example response shape:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "created_at": "2026-05-20T12:30:00",
      "filename": "resume.pdf",
      "match_score": 0.75,
      "semantic_score": 0.68,
      "semantic_source": "local",
      "score_explanation": "Moderate match with some missing skills.",
      "resume_skills": ["python", "fastapi", "sql"],
      "matched_skills": ["python", "sql"],
      "missing_skills": ["docker"],
      "feedback": [
        "Docker is commonly expected for backend and deployment roles."
      ]
    }
  ]
}
```

---

# Testing and CI

The project includes unit tests and basic API tests using `pytest`.

Current test coverage includes:

- Root page loading
- FastAPI documentation page loading
- Required upload field validation
- Required match field validation
- Skill extraction
- Skill alias normalization
- Empty skill extraction cases
- No-match skill extraction cases
- Perfect job match logic
- Partial job match logic
- No-match job logic
- Semantic score field validation
- Semantic source field validation
- Feedback generation for missing skills
- Score explanation categories

GitHub Actions automatically runs the test suite on:

- Pushes to the `main` branch
- Pull requests targeting the `main` branch

The CI workflow installs dependencies, configures a Python 3.11 environment, and runs:

```bash
pytest tests/ -v
```

The CI environment disables OpenAI embeddings so the test suite can run using the local TF-IDF fallback without requiring an API key.

---

# Environment Variables

Create a local `.env` file based on `.env.example`.

```env
OPENAI_API_KEY=your_api_key_here
USE_OPENAI_EMBEDDINGS=True
```

The application can run without an OpenAI API key.

When no API key is provided, or when OpenAI embeddings are disabled, semantic scoring uses local TF-IDF cosine similarity.

For local-only mode:

```env
OPENAI_API_KEY=
USE_OPENAI_EMBEDDINGS=False
```

Do not commit your real `.env` file to GitHub.

---

# Run Locally

## 1. Clone the repository

```bash
git clone https://github.com/Jiawei-15/resume-analyzer.git
cd resume-analyzer
```

## 2. Create and activate a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Create environment file

```bash
cp .env.example .env
```

Then edit `.env` if you want to enable OpenAI embeddings.

## 5. Start the development server

```bash
uvicorn app.main:app --reload
```

## 6. Open the application

```text
http://127.0.0.1:8000
```

## 7. Open API documentation

```text
http://127.0.0.1:8000/docs
```

---

# Run Tests

```bash
pytest tests/ -v
```

For local testing without OpenAI:

```env
OPENAI_API_KEY=
USE_OPENAI_EMBEDDINGS=False
```

---

# Run with Docker

Build the image:

```bash
docker build -t resume-analyzer .
```

Run the container:

```bash
docker run -p 10000:10000 resume-analyzer
```

Open:

```text
http://127.0.0.1:10000
```

Note: OCR for image-based resumes requires Tesseract OCR to be installed in the container or deployment environment. If Tesseract is not available, PDF, DOCX, and TXT parsing can still work, but image OCR may fail.

---

# Deployment

This project includes a `render.yaml` file for Render deployment.

The application is configured to start with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

For deployment, environment variables should be configured in the hosting platform instead of committing them to the repository.

Recommended demo environment variables:

```env
OPENAI_API_KEY=
USE_OPENAI_EMBEDDINGS=False
```

OpenAI embeddings can be enabled by adding a valid API key and setting:

```env
USE_OPENAI_EMBEDDINGS=True
```

---

# Example Use Case

A student or job seeker can upload a resume and paste a backend or full-stack job description.

The application can return:

- Overall match score
- Semantic similarity score
- Matched technical skills
- Missing technical skills
- Strengths
- Weaknesses
- Suggestions
- Skill-specific feedback

Example output:

```text
Match Score: 72%
Semantic Score: 65%
Matched Skills: Python, FastAPI, SQL
Missing Skills: Docker, React
Feedback: Docker is commonly expected for backend and deployment roles.
```

---

# Limitations

- Skill extraction is based on a predefined skill database, so uncommon or highly specialized skills may not be detected.
- Match scores are intended as guidance and should not replace human resume review.
- OCR for image-based resumes requires Tesseract OCR to be installed in the runtime environment.
- SQLite is used for local/demo history storage and is not intended as a production-scale database.
- Semantic scoring depends on either OpenAI embeddings or local TF-IDF similarity, so results may vary depending on configuration.
- The project does not perform advanced resume formatting analysis.
- The project does not guarantee ATS compatibility.
- The current matching logic focuses mainly on technical skills and does not deeply evaluate work experience quality, seniority, achievements, or soft skills.

---

# What I Learned

This project helped me practice:

- Building a FastAPI backend
- Handling file uploads
- Parsing different resume file formats
- Separating API routes, service logic, utilities, and schemas
- Designing structured JSON API responses
- Using SQLite for simple persistence
- Applying text normalization for skill extraction
- Combining keyword-based matching with semantic similarity
- Using OpenAI embeddings as an optional enhancement
- Implementing a local TF-IDF fallback
- Writing unit tests with pytest
- Setting up GitHub Actions CI
- Deploying a web application to Render
- Documenting a full-stack project for portfolio use

---

# Future Improvements

Planned improvements include:

- Add more API integration tests for `/analyze`, `/match`, and `/history`
- Add tests that explicitly verify OpenAI-to-TF-IDF fallback behavior
- Add better error messages for unsupported or unreadable files
- Expand the technical skill database
- Add role-specific skill categories such as backend, frontend, data, machine learning, and DevOps
- Add a history page in the frontend instead of exposing history only through the API
- Improve UI layout for mobile screens
- Add optional user authentication for saving private analysis history
- Add cloud database support for production deployment
- Add more advanced resume analysis beyond keyword and skill matching

---

# Author

Built as a portfolio project to practice full-stack development, FastAPI backend architecture, resume text processing, semantic matching, automated testing, and deployment workflows.