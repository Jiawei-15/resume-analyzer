from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool

from app.config import (
    UPLOAD_READ_CHUNK_BYTES,
    get_max_job_description_chars,
    get_max_upload_bytes
)
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


async def read_upload_content_with_limit(file: UploadFile) -> bytes:
    max_bytes = get_max_upload_bytes()
    total_bytes = 0
    chunks = []

    while True:
        read_size = min(
            UPLOAD_READ_CHUNK_BYTES,
            max_bytes - total_bytes + 1
        )
        chunk = await file.read(read_size)

        if not chunk:
            break

        total_bytes += len(chunk)

        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    "Uploaded file is too large. "
                    f"Maximum size is {max_bytes} bytes."
                )
            )

        chunks.append(chunk)

    return b"".join(chunks)


def clean_job_description_with_limit(job_description: str) -> str:
    cleaned_job_description = job_description.strip()
    max_chars = get_max_job_description_chars()

    if not cleaned_job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    if len(cleaned_job_description) > max_chars:
        raise HTTPException(
            status_code=413,
            detail=(
                "Job description is too long. "
                f"Maximum length is {max_chars} characters."
            )
        )

    if len(cleaned_job_description) < 30:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short. Please provide a more complete job description."
        )

    return cleaned_job_description


@router.post("/upload", tags=["Resume"], response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    validate_resume_file(file)

    content = await read_upload_content_with_limit(file)

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

    content = await read_upload_content_with_limit(file)

    result = await run_in_threadpool(
        analyze_resume_logic,
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

    cleaned_job_description = clean_job_description_with_limit(
        job_description
    )

    content = await read_upload_content_with_limit(file)

    result = await run_in_threadpool(
        match_resume_logic,
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