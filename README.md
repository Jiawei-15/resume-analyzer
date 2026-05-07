# AI Resume Analyzer

A FastAPI-based backend project that analyzes PDF resumes against job descriptions and returns structured feedback.

---

## Features

- PDF resume parsing
- Skill extraction
- Job description matching
- Match score generation
- Missing skill analysis
- Resume improvement feedback

---

## Demo

### Match Endpoint Input

![Match Input](./assets/match-input.png)

### Sample Match Result

![Match Output](./assets/match-output.png)

---

## Tech Stack

- Python
- FastAPI
- pypdf
- Regex-based text processing

---

## Run Locally

```bash
uvicorn app.main:app --reload