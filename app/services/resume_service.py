import logging

from fastapi import HTTPException

from app.utils import (
    extract_text_from_pdf,
    extract_skills,
    match_job,
    generate_feedback,
    explain_score
)

logger = logging.getLogger(__name__)


def validate_pdf(file):
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Rejected non-PDF file: {file.filename}")

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )


def parse_resume(content, filename):
    try:
        extracted_text = extract_text_from_pdf(content)

    except Exception as e:
        logger.error(f"PDF parsing failed: {str(e)}")

        raise HTTPException(
            status_code=400,
            detail="Failed to read PDF file."
        )

    if not extracted_text.strip():
        logger.warning(f"No readable text found in: {filename}")

        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    return extracted_text


def analyze_resume_logic(file, content):
    logger.info(f"Analyzing resume: {file.filename}")

    extracted_text = parse_resume(content, file.filename)

    skills = extract_skills(extracted_text)

    logger.info(
        f"Extracted {len(skills)} skills from {file.filename}"
    )

    return {
        "filename": file.filename,
        "text_preview": extracted_text[:1500],
        "text_length": len(extracted_text),
        "skills_found": skills,
        "skills_count": len(skills)
    }


def match_resume_logic(file, content, job_description):
    logger.info(f"Matching resume: {file.filename}")

    extracted_text = parse_resume(content, file.filename)

    skills = extract_skills(extracted_text)

    result = match_job(skills, job_description)

    feedback = generate_feedback(result["missing_skills"])

    logger.info(
        f"Match completed for {file.filename} | Score: {result['match_score']}"
    )

    return {
        "filename": file.filename,
        "resume_skills": skills,
        "match_score": result["match_score"],
        "semantic_score": result["semantic_score"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "score_explanation": explain_score(result["match_score"]),
        "feedback": feedback
    }