from fastapi import FastAPI, UploadFile, File
from pypdf import PdfReader
from io import BytesIO
import re

app = FastAPI()

# A simple skills list for the first version
SKILLS_DB = [
    "python", "java", "c", "c++", "javascript", "typescript",
    "html", "css", "sql", "mysql", "postgresql",
    "fastapi", "flask", "django", "react", "node.js",
    "pandas", "numpy", "scikit-learn", "matplotlib",
    "machine learning", "deep learning", "data analysis",
    "git", "github", "docker", "linux",
    "aws", "api", "rest api", "tensorflow", "pytorch"
]


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
        # escape special regex symbols in skill names like c++ or node.js
        pattern = re.escape(skill.lower())

        if re.search(rf"\b{pattern}\b", normalized_text):
            found_skills.append(skill)

    return sorted(list(set(found_skills)))


@app.get("/")
def read_root():
    return {"message": "API is running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "filename": file.filename,
        "size": len(content)
    }


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    skills = extract_skills(extracted_text)

    return {
        "filename": file.filename,
        "text_preview": extracted_text[:1500],
        "text_length": len(extracted_text),
        "skills_found": skills,
        "skills_count": len(skills)
    }
def match_job(resume_skills: list, job_text: str):
    job_text = job_text.lower()

    matched = []
    missing = []

    for skill in SKILLS_DB:
        if skill in job_text:
            if skill in resume_skills:
                matched.append(skill)
            else:
                missing.append(skill)

    total = len(matched) + len(missing)
    score = len(matched) / total if total > 0 else 0

    return {
        "match_score": round(score, 2),
        "matched_skills": matched,
        "missing_skills": missing
    }
from fastapi import Form

@app.post("/match")
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    skills = extract_skills(extracted_text)
    result = match_job(skills, job_description)
    feedback = generate_feedback(result["missing_skills"])

    return {
        "filename": file.filename,
        "resume_skills": skills,
        **result,
        "feedback": feedback
    }
def generate_feedback(missing_skills: list) -> list:
    feedback = []

    for skill in missing_skills:
        if skill == "fastapi":
            feedback.append("Add FastAPI to your skills or project descriptions if you have used it.")
        elif skill == "docker":
            feedback.append("Mention Docker experience in a project section.")
        elif skill == "linux":
            feedback.append("Show Linux usage through development, scripting, or deployment work.")
        elif skill == "rest api":
            feedback.append("Describe any API-related coursework or projects more explicitly.")
        elif skill == "sql":
            feedback.append("Highlight database work or SQL usage in projects.")
        elif skill == "machine learning":
            feedback.append("Include machine learning models, tools, or related coursework in more detail.")
        else:
            feedback.append(f"Consider adding evidence of {skill} if it is relevant to your background.")

    return feedback