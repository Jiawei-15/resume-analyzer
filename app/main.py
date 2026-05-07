from fastapi import FastAPI, UploadFile, File, Form

from app.utils import (
    extract_text_from_pdf,
    extract_skills,
    match_job,
    generate_feedback,
    explain_score
)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "API is running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "filename": file.filename,
        "size": len(content)
    }


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    skills = extract_skills(extracted_text)

    return {
        "filename": file.filename,
        "text_preview": extracted_text[:1500],
        "text_length": len(extracted_text),
        "skills_found": skills,
        "skills_count": len(skills)
    }


@app.post("/match")
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    skills = extract_skills(extracted_text)

    result = match_job(skills, job_description)
    feedback = generate_feedback(result["missing_skills"])

    return {
        "filename": file.filename,
        "resume_skills": skills,
        **result,
        "score_explanation": explain_score(result["match_score"]),
        "feedback": feedback
    }