import os
import tempfile
from typing import Any, Dict

from fastapi import UploadFile, HTTPException

from app.agents.orchestrator import RecruitmentOrchestrator

try:
    from app.database import save_analysis
except ImportError:
    save_analysis = None


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


def validate_resume_file(file: UploadFile) -> None:
    """
    Validate uploaded resume file.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded."
        )

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file."
        )


def analyze_resume_logic(
    file: UploadFile,
    content: bytes
) -> Dict[str, Any]:
    """
    Basic resume analysis endpoint logic.
    Keep this compatible with your existing /analyze endpoint.
    """

    resume_text = extract_text_from_upload(
        file=file,
        content=content
    )

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded resume."
        )

    skills = extract_simple_skills(resume_text)

    result = {
        "filename": file.filename,
        "summary": {
            "text_length": len(resume_text),
            "skills_count": len(skills),
            "overall_level": estimate_resume_level(skills)
        },
        "skills": {
            "found": skills
        },
        "analysis": {
            "strengths": build_basic_strengths(skills),
            "weaknesses": build_basic_weaknesses(skills),
            "suggestions": build_basic_suggestions(skills)
        },
        "text_preview": resume_text[:800]
    }

    return result


def match_resume_logic(
    file: UploadFile,
    content: bytes,
    job_description: str
) -> Dict[str, Any]:
    """
    Match resume against job description using the multi-agent pipeline.

    This function normalizes the orchestrator output into a frontend-friendly
    response shape, so the UI can reliably access job, resume, match,
    evidence, rewrite, and trace data.
    """

    resume_text = extract_text_from_upload(
        file=file,
        content=content
    )

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded resume."
        )

    orchestrator = RecruitmentOrchestrator()

    orchestrator_result = orchestrator.run(
        resume_text=resume_text,
        job_description=job_description
    )

    match_result = orchestrator_result.get(
        "match_result",
        {}
    )

    job_profile = orchestrator_result.get(
        "job_profile",
        {}
    )

    resume_profile = orchestrator_result.get(
        "resume_profile",
        {}
    )

    evidence_profile = orchestrator_result.get(
        "evidence_profile",
        {}
    )

    rewrite_profile = orchestrator_result.get(
        "rewrite_profile",
        {}
    )

    agent_trace = orchestrator_result.get(
        "trace",
        []
    )

    retrieved_evidence = evidence_profile.get(
        "retrieved_evidence",
        ""
    )

    rewrite_suggestions = rewrite_profile.get(
        "rewrite_suggestions",
        []
    )

    resume_skills = (
        resume_profile.get("technical_skills", [])
        + resume_profile.get("domain_skills", [])
        + resume_profile.get("soft_skills", [])
    )

    result = {
        **match_result,

        "filename": file.filename,

        "job_profile": job_profile,
        "resume_profile": resume_profile,
        "evidence_profile": evidence_profile,
        "rewrite_profile": rewrite_profile,

        "job_title": job_profile.get(
            "job_title",
            "General Role"
        ),
        "industry": job_profile.get(
            "industry",
            "General"
        ),
        "candidate_title": resume_profile.get(
            "candidate_title",
            "General Candidate"
        ),

        "required_skills": job_profile.get(
            "required_skills",
            []
        ),
        "preferred_skills": job_profile.get(
            "preferred_skills",
            []
        ),
        "soft_skills": job_profile.get(
            "soft_skills",
            []
        ),
        "responsibilities": job_profile.get(
            "responsibilities",
            []
        ),

        "resume_skills": resume_skills,
        "work_evidence": resume_profile.get(
            "work_evidence",
            []
        ),

        "retrieved_evidence": retrieved_evidence,
        "rewrite_suggestions": rewrite_suggestions,
        "agent_trace": agent_trace,

        "used_fallback": rewrite_profile.get(
            "used_fallback",
            False
        ),
        "llm_error": rewrite_profile.get(
            "llm_error"
        )
    }

    save_match_result_if_possible(
        filename=file.filename,
        result=result
    )

    return result


def extract_text_from_upload(
    file: UploadFile,
    content: bytes
) -> str:
    """
    Extract text from uploaded TXT, PDF, or DOCX resume.
    """

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == ".txt":
        return extract_text_from_txt(content)

    if file_extension == ".pdf":
        return extract_text_from_pdf(content)

    if file_extension == ".docx":
        return extract_text_from_docx(content)

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type."
    )


def extract_text_from_txt(content: bytes) -> str:
    """
    Extract text from TXT file.
    """

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode(
            "latin-1",
            errors="ignore"
        )


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text from PDF file.

    Requires:
    pip install pypdf
    """

    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF support requires pypdf. Please install it with: pip install pypdf"
        )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        reader = PdfReader(temp_path)

        pages = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

        return "\n".join(pages)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def extract_text_from_docx(content: bytes) -> str:
    """
    Extract text from DOCX file.

    Requires:
    pip install python-docx
    """

    try:
        from docx import Document
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="DOCX support requires python-docx. Please install it with: pip install python-docx"
        )

    with tempfile.NamedTemporaryFile(
        suffix=".docx",
        delete=False
    ) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        document = Document(temp_path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def extract_simple_skills(resume_text: str) -> list[str]:
    """
    Lightweight skill extraction for /analyze fallback.
    Your advanced matching still happens inside the agent pipeline.
    """

    known_skills = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "React",
        "FastAPI",
        "Flask",
        "Django",
        "Node.js",
        "SQL",
        "SQLite",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Docker",
        "Git",
        "GitHub",
        "REST API",
        "API",
        "HTML",
        "CSS",
        "Machine Learning",
        "AI",
        "LLM",
        "OpenAI",
        "RAG",
        "Embedding",
        "Vector Search"
    ]

    lower_text = resume_text.lower()

    found = []

    for skill in known_skills:
        if skill.lower() in lower_text:
            found.append(skill)

    return found


def estimate_resume_level(skills: list[str]) -> str:
    """
    Estimate rough resume level from extracted skills.
    """

    if len(skills) >= 10:
        return "strong"

    if len(skills) >= 5:
        return "medium"

    return "entry"


def build_basic_strengths(skills: list[str]) -> list[str]:
    """
    Build simple strengths for /analyze endpoint.
    """

    strengths = []

    if skills:
        strengths.append(
            "The resume includes identifiable technical skills."
        )

    if "Python" in skills:
        strengths.append(
            "The resume shows Python programming experience."
        )

    if "FastAPI" in skills or "API" in skills or "REST API" in skills:
        strengths.append(
            "The resume includes backend or API-related experience."
        )

    if "React" in skills or "JavaScript" in skills:
        strengths.append(
            "The resume includes frontend development experience."
        )

    if not strengths:
        strengths.append(
            "The resume text was extracted successfully, but technical strengths are not explicit."
        )

    return strengths


def build_basic_weaknesses(skills: list[str]) -> list[str]:
    """
    Build simple weaknesses for /analyze endpoint.
    """

    weaknesses = []

    if len(skills) < 5:
        weaknesses.append(
            "The resume may not list enough explicit technical skills."
        )

    if "Docker" not in skills:
        weaknesses.append(
            "Docker or deployment experience is not clearly visible."
        )

    if (
        "SQL" not in skills
        and "SQLite" not in skills
        and "PostgreSQL" not in skills
        and "MySQL" not in skills
    ):
        weaknesses.append(
            "Database experience is not clearly visible."
        )

    if not weaknesses:
        weaknesses.append(
            "No major basic weaknesses were detected from keyword-level analysis."
        )

    return weaknesses


def build_basic_suggestions(skills: list[str]) -> list[str]:
    """
    Build simple suggestions for /analyze endpoint.
    """

    suggestions = [
        "Use concrete project bullets that explain the problem, technology stack, implementation, and result.",
        "Add job-relevant keywords naturally instead of listing disconnected tools."
    ]

    if "Docker" not in skills:
        suggestions.append(
            "Consider adding Docker or deployment experience if you have used it."
        )

    if "FastAPI" not in skills:
        suggestions.append(
            "If applicable, mention FastAPI or backend API experience more explicitly."
        )

    if "RAG" not in skills and "Embedding" not in skills:
        suggestions.append(
            "If applicable, describe AI retrieval, embedding, or LLM-related project experience."
        )

    return suggestions


def save_match_result_if_possible(
    filename: str,
    result: Dict[str, Any]
) -> None:
    """
    Persist the frontend-friendly match result in the history schema.
    """

    if save_analysis is None:
        raise RuntimeError("History persistence is unavailable.")

    feedback = normalize_history_list(
        result.get("feedback")
    )

    history_result = {
        "match_score": result.get("match_score"),
        "semantic_score": result.get("semantic_score"),
        "semantic_source": (
            result.get("semantic_source")
            or "multi_agent_pipeline"
        ),
        "score_explanation": (
            result.get("score_explanation")
            or ""
        ),
        "resume_skills": normalize_history_list(
            result.get("resume_skills")
        ),
        "matched_skills": normalize_history_list(
            result.get("matched_skills")
        ),
        "missing_skills": normalize_history_list(
            result.get("missing_skills")
        )
    }

    save_analysis(
        filename=filename,
        result=history_result,
        feedback=feedback
    )


def normalize_history_list(value: Any) -> list:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    return [value]
