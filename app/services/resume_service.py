import logging

from fastapi import HTTPException

from app.database import save_analysis

from app.utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    extract_text_from_image,
    extract_skills,
    match_job,
    generate_feedback,
    explain_score
)

logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg"
}


def get_file_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""

    return "." + filename.lower().split(".")[-1]


def validate_resume_file(file):
    extension = get_file_extension(file.filename)

    if extension not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Rejected unsupported file: {file.filename}")

        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, TXT, PNG, JPG, and JPEG files are supported."
        )


def parse_resume(content, filename):
    extension = get_file_extension(filename)

    try:
        if extension == ".pdf":
            extracted_text = extract_text_from_pdf(content)

        elif extension == ".docx":
            extracted_text = extract_text_from_docx(content)

        elif extension == ".txt":
            extracted_text = extract_text_from_txt(content)

        elif extension in [".png", ".jpg", ".jpeg"]:
            extracted_text = extract_text_from_image(content)

        else:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX, TXT, PNG, JPG, and JPEG files are supported."
            )

    except HTTPException:
        raise

    except RuntimeError as e:
        logger.error(f"OCR failed for {filename}: {str(e)}")

        raise HTTPException(
            status_code=400,
            detail="Image OCR failed. Tesseract OCR may not be installed or configured."
        )

    except Exception as e:
        logger.error(f"Resume parsing failed for {filename}: {str(e)}")

        raise HTTPException(
            status_code=400,
            detail="Failed to read resume file."
        )

    if not extracted_text.strip():
        logger.warning(f"No readable text found in: {filename}")

        raise HTTPException(
            status_code=400,
            detail="No readable text found in the resume file."
        )

    return extracted_text


def get_resume_level(skills_count):
    if skills_count >= 12:
        return "Strong"
    elif skills_count >= 6:
        return "Moderate"
    else:
        return "Needs Improvement"


def generate_strengths(skills):
    strengths = []

    if not skills:
        return ["No clear technical skills were detected from the resume."]

    if len(skills) >= 6:
        strengths.append("The resume includes a reasonable number of technical skills.")

    programming_indicators = [
        "python",
        "java",
        "javascript",
        "typescript",
        "fastapi",
        "flask",
        "django",
        "scikit-learn",
        "pandas",
        "numpy"
    ]

    if any(skill.lower() in programming_indicators for skill in skills):
        strengths.append("The resume shows programming or framework experience.")

    if any(skill.lower() in ["fastapi", "flask", "django", "react", "node.js"] for skill in skills):
        strengths.append("The resume shows exposure to practical web development tools.")

    if any(skill.lower() in ["machine learning", "scikit-learn", "pandas", "numpy"] for skill in skills):
        strengths.append("The resume includes data or machine learning related skills.")

    if not strengths:
        strengths.append("The resume contains some relevant skills, but they need stronger context.")

    return strengths


def generate_weaknesses(skills):
    weaknesses = []

    if len(skills) < 5:
        weaknesses.append("The resume may not show enough technical depth based on detected skills.")

    programming_indicators = [
        "python",
        "java",
        "javascript",
        "typescript",
        "fastapi",
        "flask",
        "django",
        "scikit-learn",
        "pandas",
        "numpy"
    ]

    if not any(skill.lower() in programming_indicators for skill in skills):
        weaknesses.append("No major programming language or programming framework was clearly detected.")

    if not any(skill.lower() in ["git", "github"] for skill in skills):
        weaknesses.append("Git or GitHub experience is not clearly visible.")

    if not any(skill.lower() in ["api", "fastapi", "flask", "django", "react"] for skill in skills):
        weaknesses.append("The resume does not clearly show full-stack or API development experience.")

    if not weaknesses:
        weaknesses.append(
            "The main weakness is not the skill list itself, but whether the resume explains projects with enough detail."
        )

    return weaknesses


def generate_resume_suggestions(skills):
    suggestions = []

    suggestions.append(
        "Add project bullet points that explain what was built, what tools were used, and what the result was."
    )

    if not any(skill.lower() in ["git", "github"] for skill in skills):
        suggestions.append("Include GitHub or version control experience if available.")

    if not any(skill.lower() in ["api", "fastapi", "flask", "django"] for skill in skills):
        suggestions.append("Add API/backend project experience if relevant.")

    if len(skills) < 8:
        suggestions.append(
            "Add more concrete technical keywords, but only if they are supported by real project experience."
        )

    suggestions.append(
        "Use measurable details where possible, such as number of files processed, response time, accuracy, or project scope."
    )

    return suggestions


def generate_match_strengths(matched_skills):
    if not matched_skills:
        return ["The resume does not clearly match the main skills in the job description."]

    strengths = [
        f"The resume matches {len(matched_skills)} skill(s) from the job description."
    ]

    if len(matched_skills) >= 5:
        strengths.append("The candidate shows strong overlap with the role requirements.")
    elif len(matched_skills) >= 2:
        strengths.append("The candidate shows some relevant overlap with the role requirements.")

    return strengths


def generate_match_weaknesses(missing_skills):
    if not missing_skills:
        return ["No major missing skills were detected from the job description."]

    weaknesses = [
        f"The resume is missing {len(missing_skills)} skill(s) from the job description."
    ]

    weaknesses.append(
        "Some required keywords may not be visible enough for recruiter screening or ATS matching."
    )

    return weaknesses


def generate_match_suggestions(missing_skills):
    suggestions = []

    if missing_skills:
        suggestions.append(
            "If the candidate has real experience with the missing skills, add them naturally into project or experience bullet points."
        )

        suggestions.append(
            "Do not keyword-stuff missing skills without real supporting experience."
        )

        suggestions.append(
            "Add one project bullet that directly connects the resume to the target job description."
        )
    else:
        suggestions.append(
            "The resume already covers the main detected job skills. Improve it by adding measurable project outcomes."
        )

    return suggestions


def analyze_resume_logic(file, content):
    logger.info(f"Analyzing resume: {file.filename}")

    extracted_text = parse_resume(content, file.filename)

    skills = extract_skills(extracted_text)

    logger.info(
        f"Extracted {len(skills)} skills from {file.filename}"
    )

    return {
        "filename": file.filename,
        "summary": {
            "text_length": len(extracted_text),
            "skills_count": len(skills),
            "overall_level": get_resume_level(len(skills))
        },
        "skills": {
            "found": skills
        },
        "analysis": {
            "strengths": generate_strengths(skills),
            "weaknesses": generate_weaknesses(skills),
            "suggestions": generate_resume_suggestions(skills)
        },
        "text_preview": extracted_text[:1500]
    }


def match_resume_logic(file, content, job_description):
    logger.info(f"Matching resume: {file.filename}")

    extracted_text = parse_resume(content, file.filename)

    skills = extract_skills(extracted_text)

    result = match_job(extracted_text, skills, job_description)

    feedback = generate_feedback(result["missing_skills"])

    logger.info(
        f"Match completed for {file.filename} | Score: {result['match_score']}"
    )

    save_analysis(
        filename=file.filename,
        result={
            "match_score": result["match_score"],
            "semantic_score": result["semantic_score"],
            "semantic_source": result["semantic_source"],
            "score_explanation": explain_score(result["match_score"]),
            "resume_skills": skills,
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
        },
        feedback=feedback
    )

    return {
        "filename": file.filename,
        "summary": {
            "match_score": result["match_score"],
            "semantic_score": result["semantic_score"],
            "semantic_source": result["semantic_source"],
            "score_explanation": explain_score(result["match_score"])
        },
        "skills": {
            "resume_skills": skills,
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"]
        },
        "analysis": {
            "strengths": generate_match_strengths(result["matched_skills"]),
            "weaknesses": generate_match_weaknesses(result["missing_skills"]),
            "suggestions": generate_match_suggestions(result["missing_skills"]),
            "feedback": feedback
        }
    }