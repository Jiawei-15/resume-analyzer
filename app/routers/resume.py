from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.database import get_history

from app.schemas.responses import (
    UploadResponse,
    AnalyzeResumeResponse
)

from app.services.resume_service import (
    validate_resume_file,
    analyze_resume_logic,
    match_resume_logic
)


router = APIRouter()


@router.post("/upload", tags=["Resume"], response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    validate_resume_file(file)

    content = await file.read()

    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "size": len(content)
        }
    }


@router.post("/analyze", tags=["Resume"], response_model=AnalyzeResumeResponse)
async def analyze_resume(file: UploadFile = File(...)):
    validate_resume_file(file)

    content = await file.read()

    result = analyze_resume_logic(
        file,
        content
    )

    return {
        "success": True,
        "data": result
    }


@router.post("/match", tags=["Resume"])
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    validate_resume_file(file)

    cleaned_job_description = job_description.strip()

    if not cleaned_job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    if len(cleaned_job_description) < 30:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short. Please provide a more complete job description."
        )

    content = await file.read()

    result = match_resume_logic(
        file,
        content,
        cleaned_job_description
    )

    return {
        "success": True,
        "data": result
    }


@router.get("/history", tags=["Resume"])
def get_analysis_history():
    return {
        "success": True,
        "data": get_history()
    }