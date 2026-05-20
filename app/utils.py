from app.semantic import semantic_match
from app.weights import SKILL_WEIGHTS
from app.normalization import NORMALIZATION_MAP
from app.skills import SKILLS_DB

from io import BytesIO
import re

from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf = PdfReader(BytesIO(file_bytes))
    extracted_text = ""

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text + "\n"

    return extracted_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def extract_text_from_image(file_bytes: bytes) -> str:
    image = Image.open(BytesIO(file_bytes))

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available in PATH."
        )

    return text


def normalize_text(text: str) -> str:
    text = text.lower()

    for old, new in NORMALIZATION_MAP.items():
        text = text.replace(old, new)

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


def match_job(resume_text: str, resume_skills: list, job_text: str) -> dict:
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

    semantic_score, semantic_source = semantic_match(
        resume_text,
        job_text
    )

    return {
        "match_score": round(score, 2),
        "semantic_score": semantic_score,
        "semantic_source":semantic_source,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing)
    }


SKILL_FEEDBACK = {
    "python": "Add Python projects that show real usage, not just listed as a skill.",
    "fastapi": "Consider adding FastAPI project experience or backend API development examples.",
    "docker": "Docker is commonly expected for backend and deployment roles.",
    "machine learning": "Add ML coursework, projects, or model development experience.",
    "sql": "Database and SQL skills are frequently required for backend positions.",
    "react": "React experience improves full-stack role alignment.",
    "javascript": "JavaScript is core for frontend and full-stack roles.",
    "typescript": "TypeScript is increasingly expected in production frontend codebases.",
    "nodejs": "Node.js experience strengthens backend and full-stack profiles.",
    "rest api": "Add REST API design or consumption experience to your projects.",
    "git": "Make sure version control usage is visible in your project descriptions.",
    "github": "Link your GitHub profile and ensure repositories are active and documented.",
    "html": "Include frontend projects that demonstrate real HTML/CSS usage.",
    "css": "Include frontend projects that demonstrate real HTML/CSS usage.",
    "pandas": "Add data analysis projects using pandas to demonstrate practical data skills.",
    "numpy": "NumPy experience is expected for data and ML roles.",
    "scikit-learn": "Add a project that uses scikit-learn for a real prediction or classification task.",
    "tensorflow": "TensorFlow experience is valued for deep learning roles.",
    "pytorch": "PyTorch is widely used in research and production ML roles.",
    "deep learning": "Add deep learning project experience with real datasets.",
    "data analysis": "Include a project with end-to-end data analysis and visualization.",
    "backend": "Demonstrate backend engineering through APIs, databases, or deployment work.",
    "frontend": "Include frontend framework or UI project experience.",
    "linux": "Familiarity with Linux is expected for most backend and DevOps roles.",
    "jupyter": "Jupyter notebook experience supports data science and ML roles.",
    "opencv": "Add a computer vision project using OpenCV.",
    "robotics": "Include robotics project experience with real hardware or simulation.",
    "simulation": "Add simulation project work to demonstrate systems thinking.",
    "java": "Include Java projects, especially if applying to enterprise or Android roles.",
    "c++": "C++ experience is valued for systems programming, robotics, and performance-critical roles.",
    "typescript": "TypeScript is increasingly expected in production frontend codebases.",
    "flask": "Add a Flask web application or API project to your portfolio.",
    "django": "Django experience is valued for full-featured backend web development roles.",
    "numpy": "NumPy experience is expected for data and ML roles.",
    "pytorch": "PyTorch is widely used in research and production ML roles.",
    "regression": "Include a project that applies regression modeling to a real dataset.",
    "cross-validation": "Show model evaluation skills by documenting cross-validation in your ML projects.",
    "threejs": "Add a 3D visualization or WebGL project using Three.js.",
    "chartjs": "Include a data visualization project using Chart.js.",
    "yaml": "YAML is commonly used in DevOps and configuration management; show it in project setup files.",
    "verilog": "Include digital design or FPGA projects using Verilog.",
    "assembly": "Add low-level programming or embedded systems experience using Assembly.",
    "arm": "ARM architecture experience is valued for embedded and systems roles.",
    "oop": "Demonstrate object-oriented design through well-structured project code.",
    "graph search": "Include algorithm projects that implement graph search techniques.",
    "recursion": "Show algorithmic thinking through projects or problems that use recursion.",
}

DEFAULT_FEEDBACK = "Consider adding real project experience with {skill} to strengthen your profile."


def generate_feedback(missing_skills: list) -> list:
    if not missing_skills:
        return ["Your resume aligns well with the target role requirements."]

    feedback = []
    for skill in missing_skills:
        msg = SKILL_FEEDBACK.get(skill, DEFAULT_FEEDBACK.format(skill=skill))
        feedback.append(msg)

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