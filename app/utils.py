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


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


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

    total = len(matched) + len(missing)
    score = len(matched) / total if total > 0 else 0

    return {
        "match_score": round(score, 2),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing)
    }


def generate_feedback(missing_skills: list) -> list:
    feedback = []

    for skill in missing_skills:
        if skill == "fastapi":
            feedback.append("Add FastAPI to your skills or project descriptions if you have used it.")
        elif skill == "docker":
            feedback.append("Mention Docker experience in a project section if you have used it.")
        elif skill == "linux":
            feedback.append("Show Linux usage through development, scripting, or deployment work.")
        elif skill == "rest api":
            feedback.append("Describe any API-related coursework or projects more explicitly.")
        elif skill == "sql":
            feedback.append("Highlight database work or SQL usage in projects.")
        elif skill == "machine learning":
            feedback.append("Include machine learning models, tools, or related coursework in more detail.")
        elif skill == "pandas":
            feedback.append("Add evidence of pandas use if it is relevant to your background.")
        elif skill == "data analysis":
            feedback.append("Make data analysis work more explicit through project descriptions or coursework.")
        else:
            feedback.append(f"Consider adding evidence of {skill} if it is relevant to your background.")

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