import pytest
from app.utils import extract_skills, match_job, generate_feedback, explain_score


# ── extract_skills ──────────────────────────────────────────────

def test_extract_skills_basic():
    text = "I have experience with Python, Docker, and React."
    skills = extract_skills(text)
    assert "python" in skills
    assert "docker" in skills
    assert "react" in skills


def test_extract_skills_normalization():
    # "JS" should normalize to "javascript"
    text = "I use JS and RESTful APIs daily."
    skills = extract_skills(text)
    assert "javascript" in skills
    assert "rest api" in skills


def test_extract_skills_empty():
    skills = extract_skills("")
    assert skills == []


def test_extract_skills_no_match():
    skills = extract_skills("I enjoy hiking and cooking.")
    assert skills == []


# ── match_job ───────────────────────────────────────────────────

def test_match_job_perfect_match():
    resume_text = "Experienced Python developer with SQL and Docker skills."
    resume_skills = ["python", "sql", "docker"]
    job_text = "We need Python, SQL, and Docker experience."
    result = match_job(resume_text, resume_skills, job_text)
    assert result["match_score"] == 1.0
    assert result["missing_skills"] == []
    assert set(result["matched_skills"]) == {"python", "sql", "docker"}


def test_match_job_no_match():
    resume_text = "I know HTML and CSS."
    resume_skills = ["html", "css"]
    job_text = "We need Python, Docker, and machine learning experience."
    result = match_job(resume_text, resume_skills, job_text)
    assert result["match_score"] == 0.0
    assert "python" in result["missing_skills"]
    assert "docker" in result["missing_skills"]


def test_match_job_partial_match():
    resume_text = "Python developer with some Docker knowledge."
    resume_skills = ["python", "docker"]
    job_text = "We need Python, Docker, and React skills."
    result = match_job(resume_text, resume_skills, job_text)
    assert 0.0 < result["match_score"] < 1.0
    assert "react" in result["missing_skills"]
    assert "python" in result["matched_skills"]


def test_match_job_returns_semantic_score():
    resume_text = "Python and machine learning engineer."
    resume_skills = ["python", "machine learning"]
    job_text = "Looking for a Python ML engineer."
    result = match_job(resume_text, resume_skills, job_text)
    assert "semantic_score" in result
    assert 0.0 <= result["semantic_score"] <= 1.0


def test_match_job_returns_semantic_source():
    resume_text = "Backend developer."
    resume_skills = ["backend"]
    job_text = "Backend engineering role."
    result = match_job(resume_text, resume_skills, job_text)
    assert result["semantic_source"] in ("openai", "local")


# ── generate_feedback ───────────────────────────────────────────

def test_generate_feedback_empty():
    feedback = generate_feedback([])
    assert len(feedback) == 1
    assert "aligns well" in feedback[0]


def test_generate_feedback_known_skill():
    feedback = generate_feedback(["fastapi"])
    assert any("FastAPI" in f for f in feedback)


def test_generate_feedback_unknown_skill():
    feedback = generate_feedback(["verilog"])
    assert len(feedback) == 1
    assert "verilog" in feedback[0].lower()


def test_generate_feedback_multiple_skills():
    feedback = generate_feedback(["docker", "sql", "react"])
    assert len(feedback) == 3


# ── explain_score ───────────────────────────────────────────────

def test_explain_score_strong():
    assert "Strong" in explain_score(0.85)


def test_explain_score_moderate():
    assert "Moderate" in explain_score(0.65)


def test_explain_score_partial():
    assert "Partial" in explain_score(0.45)


def test_explain_score_weak():
    assert "Weak" in explain_score(0.2)