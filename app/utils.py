from app.weights import SKILL_WEIGHTS
from app.normalization import NORMALIZATION_MAP
from io import BytesIO
import re
from pypdf import PdfReader

from app.skills import SKILLS_DB


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf = PdfReader(BytesIO(file_bytes))
    extracted_text = ""

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text + "\n"

    return extracted_text


def extract_skills(text: str) -> list:
    normalized_text = normalize_text(text)
    found_skills = []

    for skill in SKILLS_DB:
        pattern = re.escape(skill.lower())

        if skill == "api":
            if " api " in normalized_text or " apis " in normalized_text:
                found_skills.append(skill)
        else:
            if re.search(r"\b" + pattern + r"\b", normalized_text):
                found_skills.append(skill)

    return sorted(list(set(found_skills)))


def match_job(resume_skills: list, job_text: str) -> dict:
    normalized_job_text = normalize_text(job_text)

    matched = []
    missing = []

    for skill in SKILLS_DB:
        pattern = re.escape(skill.lower())

        if skill == "api":
            job_has_skill = " api " in normalized_job_text or " apis " in normalized_job_text
        else:
            job_has_skill = re.search(r"\b" + pattern + r"\b", normalized_job_text)

        if job_has_skill:
            if skill in resume_skills:
                matched.append(skill)
            else:
                missing.append(skill)

    matched_weight = 0
    missing_weight = 0

    for skill in matched:
        matched_weight += SKILL_WEIGHTS.get(skill, 1)

    for skill in missing:
        missing_weight += SKILL_WEIGHTS.get(skill, 1)

    total_weight = matched_weight + missing_weight

    score = (
        matched_weight / total_weight
        if total_weight > 0 else 0
    )

    return {
        "match_score": round(score, 2),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing)
    }


def generate_feedback(missing_skills: list) -> list:
    feedback = []

    if "fastapi" in missing_skills:
        feedback.append(
            "Consider adding FastAPI project experience or backend API development examples."
        )

    if "docker" in missing_skills:
        feedback.append(
            "Docker knowledge is commonly expected for deployment-focused backend roles."
        )

    if "machine learning" in missing_skills:
        feedback.append(
            "Add machine learning coursework, projects, or model development experience."
        )

    if "backend" in missing_skills:
        feedback.append(
            "Demonstrate backend engineering experience through APIs, databases, or deployment work."
        )

    if "frontend" in missing_skills:
        feedback.append(
            "Consider including frontend frameworks or UI project experience."
        )

    if "sql" in missing_skills:
        feedback.append(
            "Database and SQL skills are frequently required for backend positions."
        )

    if "react" in missing_skills:
        feedback.append(
            "Adding React or frontend framework experience may improve full-stack role alignment."
        )

    if not feedback:
        feedback.append(
            "Your resume aligns well with the target role requirements."
        )

    return feedback


def explain_score(score: float) -> str:
    if score >= 0.8:
        return "Strong match for the target role."
    elif score >= 0.6:
        return "Moderate match with some missing skills."
    elif score >= 0.4:
        return "Partial match. Several important skills are missing."
    else:
        return "Weak match for this role."
    
    
def normalize_text(text: str) -> str:
    text = text.lower()

    for old, new in NORMALIZATION_MAP.items():
        text = text.replace(old, new)

    return text