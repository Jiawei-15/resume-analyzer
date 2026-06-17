# AI Recruitment Copilot

A full-stack AI-powered recruitment and resume matching application built with **FastAPI**, **OpenAI API**, **embeddings**, **multi-agent workflow orchestration**, **SQLite**, and a vanilla **HTML/CSS/JavaScript** frontend.

The application allows users to upload a resume, paste a target job description, and receive a structured AI-generated report that includes:

* Job description analysis
* Candidate capability extraction
* Dynamic resume-job match score
* Matched and missing requirements
* Resume evidence retrieval
* AI-generated resume rewrite suggestions
* Agent execution trace
* Local analysis history

This project was built as a portfolio AI engineering project focused on **LLM application development**, **multi-agent system design**, **retrieval-based evidence matching**, **FastAPI backend architecture**, **frontend-backend integration**, **testing**, and **deployment workflow**.

---

## Live Demo

https://resume-analyzer-6pdw.onrender.com

---

## Project Highlights

* Refactored a traditional resume analyzer into a **multi-agent AI recruitment copilot**
* Integrated **OpenAI Chat Completions** for structured job and resume analysis
* Integrated **OpenAI Embeddings** for resume evidence retrieval
* Built a lightweight **in-memory vector search pipeline**
* Implemented a modular **agent orchestration layer**
* Added AI-generated resume rewrite suggestions based on job gaps
* Updated frontend rendering to support dynamic AI output
* Added API-level pytest coverage for major endpoints
* Cleaned legacy keyword-matching modules and simplified the backend structure

---

## Core Features

### Resume Upload and Parsing

Users can upload resumes in:

* PDF
* DOCX
* TXT

The backend extracts text from the uploaded resume and validates unsupported file types.

### Job Description Analysis

The system uses an LLM to extract structured job requirements from a pasted job description, including:

* Job title
* Industry
* Required skills
* Preferred skills
* Soft skills
* Responsibilities

### Resume Capability Analysis

The system analyzes the candidate resume and extracts:

* Candidate profile
* Relevant industries
* Technical skills
* Domain skills
* Soft skills
* Work evidence

### Multi-Agent Matching Pipeline

The `/match` endpoint runs a multi-agent workflow:

1. **JobAnalysisAgent**
   Extracts structured requirements from the job description.

2. **ResumeAnalysisAgent**
   Extracts structured candidate capabilities from the resume.

3. **EvidenceRetrievalAgent**
   Splits resume text into chunks, generates embeddings, and retrieves relevant resume evidence.

4. **MatchDiagnosisAgent**
   Compares job requirements with resume capabilities and generates a dynamic match score.

5. **LLMResumeRewriteAgent**
   Generates targeted resume rewrite suggestions using the job description, resume evidence, and match diagnosis.

### Evidence Retrieval

The project includes a lightweight retrieval pipeline:

```text
resume text
→ chunking
→ embedding generation
→ in-memory vector storage
→ similarity search
→ retrieved resume evidence
```

This gives the match report supporting evidence instead of only returning a score.

### AI Resume Rewrite Suggestions

The system generates targeted improvement suggestions, such as:

* Missing job requirement evidence
* Weak project descriptions
* Suggested resume bullet rewrites
* Reasoning for each suggestion
* Confidence level

### Analysis History

The application stores match history in a local SQLite database and exposes a `/history` endpoint for recent analyses.

### Testing

The project includes pytest-based API tests for:

* Root page loading
* FastAPI docs loading
* Upload validation
* Match validation
* Resume analysis endpoint
* Match endpoint response structure
* Unsupported file validation
* History endpoint

Current local test result:

```text
9 passed
```

---

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn
* OpenAI API
* OpenAI Chat Completions
* OpenAI Embeddings
* SQLite
* Pydantic
* pypdf
* python-docx
* python-dotenv

### AI / LLM

* Multi-agent workflow orchestration
* Structured JSON extraction
* Resume-job requirement matching
* Embedding-based evidence retrieval
* LLM-generated resume rewrite suggestions
* Rule-based fallback behavior

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 templates

### Testing and Deployment

* pytest
* GitHub Actions-compatible test suite
* Render deployment configuration
* Docker support

---

## Project Structure

```text
AI Recruitment Copilot/
│
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── orchestrator.py
│   │   └── recruitment_agents.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── resume.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── responses.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_skill_service.py
│   │   ├── chunk_service.py
│   │   ├── embedding_service.py
│   │   ├── job_profile_service.py
│   │   ├── llm_service.py
│   │   ├── resume_service.py
│   │   └── vector_store.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── tests/
│   └── test_basic.py
│
├── assets/
│   ├── homepage.png
│   ├── match-input.png
│   ├── match-output.png
│   └── results.png
│
├── Dockerfile
├── requirements.txt
├── render.yaml
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## API Endpoints

| Method | Endpoint   | Description                                       |
| ------ | ---------- | ------------------------------------------------- |
| GET    | `/`        | Loads the frontend web interface                  |
| POST   | `/upload`  | Validates uploaded resume files                   |
| POST   | `/analyze` | Performs basic resume analysis                    |
| POST   | `/match`   | Runs the multi-agent resume-job matching pipeline |
| GET    | `/history` | Returns recent analysis history                   |
| GET    | `/docs`    | Opens the FastAPI Swagger documentation           |

---

## Example `/match` Response Fields

The `/match` endpoint returns a structured report containing:

```json
{
  "success": true,
  "data": {
    "filename": "resume.txt",
    "dynamic_match_score": 0.86,
    "dynamic_matched_skills": [
      "Python",
      "FastAPI",
      "SQL",
      "Git",
      "machine learning"
    ],
    "dynamic_missing_skills": [
      "Java"
    ],
    "job_profile": {
      "job_title": "Backend Developer",
      "industry": "Technology",
      "required_skills": [],
      "preferred_skills": [],
      "soft_skills": [],
      "responsibilities": []
    },
    "resume_profile": {
      "candidate_title": "Machine Learning Engineer",
      "industries": [],
      "technical_skills": [],
      "domain_skills": [],
      "soft_skills": [],
      "work_evidence": []
    },
    "retrieved_evidence": "...",
    "rewrite_suggestions": [],
    "agent_trace": [],
    "used_fallback": false,
    "llm_error": null
  }
}
```

---

## How It Works

1. The user uploads a resume and submits a job description.
2. The FastAPI backend validates the uploaded file.
3. Resume text is extracted from PDF, DOCX, or TXT.
4. The job description is sent to the Job Analysis Agent.
5. The resume text is sent to the Resume Analysis Agent.
6. Resume text is split into chunks.
7. Embeddings are generated for resume chunks and the job description.
8. Relevant resume evidence is retrieved through vector similarity search.
9. The Match Diagnosis Agent compares job requirements and resume capabilities.
10. The LLM Resume Rewrite Agent generates improvement suggestions.
11. The frontend displays the full report, including score, evidence, gaps, suggestions, and agent trace.
12. The result is optionally saved to SQLite history.

---

## Multi-Agent Workflow

```text
User Upload + Job Description
        │
        ▼
Resume Router
        │
        ▼
Resume Service
        │
        ▼
Recruitment Orchestrator
        │
        ├── JobAnalysisAgent
        │       └── Extract job requirements
        │
        ├── ResumeAnalysisAgent
        │       └── Extract candidate capabilities
        │
        ├── EvidenceRetrievalAgent
        │       └── Retrieve relevant resume evidence with embeddings
        │
        ├── MatchDiagnosisAgent
        │       └── Compare job requirements and resume capabilities
        │
        └── LLMResumeRewriteAgent
                └── Generate resume rewrite suggestions
```

---

## Environment Variables

Create a local `.env` file based on `.env.example`.

```env
OPENAI_API_KEY=your_api_key_here
USE_OPENAI_EMBEDDINGS=True
```

Do not commit your real `.env` file to GitHub.

The application includes fallback handling when the OpenAI service is unavailable, but the full AI workflow is designed to run with a valid OpenAI API key.

---

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Jiawei-15/resume-analyzer.git
cd resume-analyzer
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create environment file

```bash
cp .env.example .env
```

Then add your OpenAI API key if you want to run the full AI workflow.

### 5. Start the development server

```bash
uvicorn app.main:app --reload
```

### 6. Open the application

```text
http://127.0.0.1:8000
```

### 7. Open API documentation

```text
http://127.0.0.1:8000/docs
```

---

## Run Tests

```bash
pytest
```

Expected result:

```text
9 passed
```

---

## Run with Docker

Build the image:

```bash
docker build -t ai-recruitment-copilot .
```

Run the container:

```bash
docker run -p 10000:10000 ai-recruitment-copilot
```

Open:

```text
http://127.0.0.1:10000
```

---

## Deployment

This project includes a `render.yaml` file for Render deployment.

The application is configured to start with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

For deployment, environment variables should be configured in the hosting platform instead of committing them to the repository.

---

## Example Use Case

A job seeker can upload a resume and paste a software engineering or AI-related job description.

The system can return:

* AI match score
* Matched job requirements
* Missing job requirements
* Structured job profile
* Structured candidate profile
* Resume evidence retrieved from the uploaded file
* AI-generated resume rewrite suggestions
* Agent execution trace

Example output:

```text
Dynamic AI Match: 86%
Matched Requirements: Python, FastAPI, SQL, Git, machine learning
Missing Requirements: Java
Candidate Profile: Machine Learning Engineer
LLM Fallback Used: false
```

---

## Current Limitations

* The current vector store is in-memory and designed for demo use.
* Match scoring is useful for guidance, but it should not replace human resume review.
* AI extraction results may vary slightly depending on the job description and resume wording.
* Long resumes and complex job descriptions may increase response time because multiple LLM and embedding calls are used.
* The current retrieval pipeline retrieves general resume evidence, but requirement-level evidence mapping is a planned improvement.
* SQLite is used for local/demo history storage and is not intended as a production-scale database.

---

## Future Improvements

Planned improvements include:

* Requirement-level evidence mapping
* Weighted must-have vs nice-to-have job requirement scoring
* Mock OpenAI services for faster and more stable CI tests
* Caching embeddings to reduce repeated API calls
* Async or optional resume rewrite generation for faster user experience
* Better support for enterprise job description parsing
* More detailed ATS-style risk analysis
* Improved frontend loading states and progress feedback
* Persistent vector database support

---

## Resume Summary

This project demonstrates practical experience with:

* FastAPI backend development
* OpenAI API integration
* Multi-agent AI workflow design
* Embedding-based retrieval
* Resume-job matching logic
* API response design
* Frontend-backend integration
* SQLite persistence
* pytest API testing
* Deployment-oriented project structure

---
