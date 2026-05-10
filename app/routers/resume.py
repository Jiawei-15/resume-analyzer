from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.resume_service import (
    validate_pdf,
    analyze_resume_logic,
    match_resume_logic
)

router = APIRouter()


@router.post("/upload", tags=["Resume"])
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "size": len(content)
        }
    }


@router.post("/analyze", tags=["Resume"])
async def analyze_resume(file: UploadFile = File(...)):
    validate_pdf(file)

    content = await file.read()

    result = analyze_resume_logic(file, content)

    return {
        "success": True,
        "data": result
    }


@router.post("/match", tags=["Matching"])
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    validate_pdf(file)

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    content = await file.read()

    result = match_resume_logic(
        file,
        content,
        job_description
    )

    return {
        "success": True,
        "data": result
    }