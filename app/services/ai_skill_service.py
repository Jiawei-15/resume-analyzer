import json
import re

from openai import OpenAI
from app.config import OPENAI_API_KEY


def _has_valid_openai_key() -> bool:
    if not OPENAI_API_KEY:
        return False

    if "你的key" in OPENAI_API_KEY:
        return False

    try:
        OPENAI_API_KEY.encode("ascii")
    except UnicodeEncodeError:
        return False

    return OPENAI_API_KEY.startswith("sk-")


def _safe_json_parse(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}
        return {}


def _call_openai_json(prompt: str) -> dict:
    if not _has_valid_openai_key():
        return {}

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid JSON. No markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content
    return _safe_json_parse(content)


def extract_job_requirements(job_description: str) -> dict:
    prompt = f"""
You are an expert career analyst.

Extract structured job requirements from this job description.

Return ONLY valid JSON in this format:

{{
  "job_title": "",
  "industry": "",
  "required_skills": [],
  "preferred_skills": [],
  "soft_skills": [],
  "responsibilities": []
}}

Job Description:
{job_description}
"""

    return _call_openai_json(prompt)


def extract_resume_capabilities(resume_text: str) -> dict:
    prompt = f"""
You are an expert resume analyst.

Extract structured candidate capabilities from this resume.

Return ONLY valid JSON in this format:

{{
  "candidate_title": "",
  "industries": [],
  "technical_skills": [],
  "domain_skills": [],
  "soft_skills": [],
  "work_evidence": []
}}

Resume:
{resume_text}
"""

    return _call_openai_json(prompt)


def _normalize_skill_set(skills: list) -> dict:
    normalized = {}

    for skill in skills:
        if not isinstance(skill, str):
            continue

        clean_skill = skill.strip()

        if clean_skill:
            normalized[clean_skill.lower()] = clean_skill

    return normalized


def _normalize_skill_text(skill: str) -> str:
    skill = skill.lower().strip()

    remove_words = [
        "skills",
        "skill",
        "experience",
        "proficiency",
        "knowledge",
        "ability to",
        "able to"
    ]

    for word in remove_words:
        skill = skill.replace(word, "")

    skill = re.sub(r"[^a-z0-9\s]", " ", skill)
    skill = re.sub(r"\s+", " ", skill).strip()

    return skill


def _skills_are_similar(job_skill: str, resume_skill: str) -> bool:
    job_clean = _normalize_skill_text(job_skill)
    resume_clean = _normalize_skill_text(resume_skill)

    if not job_clean or not resume_clean:
        return False

    if job_clean == resume_clean:
        return True

    if job_clean in resume_clean or resume_clean in job_clean:
        return True

    job_words = set(job_clean.split())
    resume_words = set(resume_clean.split())

    overlap = job_words.intersection(resume_words)

    return len(overlap) > 0


def compare_dynamic_skills(job_profile: dict, resume_profile: dict) -> dict:
    job_skills = (
        job_profile.get("required_skills", [])
        + job_profile.get("preferred_skills", [])
        + job_profile.get("soft_skills", [])
    )

    resume_skills = (
        resume_profile.get("technical_skills", [])
        + resume_profile.get("domain_skills", [])
        + resume_profile.get("soft_skills", [])
    )

    matched = []
    missing = []

    for job_skill in job_skills:
        found_match = False

        for resume_skill in resume_skills:
            if _skills_are_similar(job_skill, resume_skill):
                matched.append(job_skill)
                found_match = True
                break

        if not found_match:
            missing.append(job_skill)

    matched = sorted(list(set(matched)))
    missing = sorted(list(set(missing)))

    total = len(matched) + len(missing)
    score = len(matched) / total if total > 0 else 0

    return {
        "dynamic_match_score": round(score, 2),
        "dynamic_matched_skills": matched,
        "dynamic_missing_skills": missing,
        "job_profile": job_profile,
        "resume_profile": resume_profile
    }