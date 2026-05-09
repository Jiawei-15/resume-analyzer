from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from app.utils import (
    extract_text_from_pdf,
    extract_skills,
    match_job,
    generate_feedback,
    explain_score
)

app = FastAPI(title="AI Resume Analyzer API")


@app.get("/", tags=["System"])
def read_root():
    return {
        "success": True,
        "data": {
            "message": "API is running"
        }
    }


@app.post("/upload", tags=["Resume"])
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "size": len(content)
        }
    }


@app.post("/analyze", tags=["Resume"])
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    content = await file.read()

    try:
        extracted_text = extract_text_from_pdf(content)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to read PDF file."
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    skills = extract_skills(extracted_text)

    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "text_preview": extracted_text[:1500],
            "text_length": len(extracted_text),
            "skills_found": skills,
            "skills_count": len(skills)
        }
    }


@app.post("/match", tags=["Matching"])
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    content = await file.read()

    try:
        extracted_text = extract_text_from_pdf(content)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to read PDF file."
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    skills = extract_skills(extracted_text)
    result = match_job(skills, job_description)
    feedback = generate_feedback(result["missing_skills"])

    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "resume_skills": skills,
            "match_score": result["match_score"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "score_explanation": explain_score(result["match_score"]),
            "feedback": feedback
        }
    }