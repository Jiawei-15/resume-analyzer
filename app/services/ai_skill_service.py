import json
import logging
import re
from typing import Dict, List

from openai import OpenAI, OpenAIError
from app.config import OPENAI_API_KEY, get_openai_timeout_seconds
from app.services.openai_retry import call_openai_with_retries


LOGGER = logging.getLogger(__name__)


TECH_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "html",
    "css",
    "react",
    "vue",
    "angular",
    "node.js",
    "fastapi",
    "flask",
    "django",
    "spring boot",
    "sql",
    "sqlite",
    "mysql",
    "postgresql",
    "mongodb",
    "rest api",
    "api",
    "docker",
    "kubernetes",
    "git",
    "github",
    "linux",
    "aws",
    "azure",
    "gcp",
    "vercel",
    "render",
    "ci/cd",
    "testing",
    "pytest",
    "unit testing",
    "logging",
    "pydantic",
    "jinja2",
    "machine learning",
    "deep learning",
    "nlp",
    "llm",
    "openai",
    "rag",
    "embedding",
    "vector database",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "excel",
    "power bi",
    "tableau"
]


BUSINESS_SKILLS = [
    "sales",
    "customer service",
    "crm",
    "lead generation",
    "cold calling",
    "negotiation",
    "account management",
    "market research",
    "marketing",
    "social media",
    "content creation",
    "seo",
    "email marketing",
    "data entry",
    "administration",
    "scheduling",
    "inventory management",
    "bookkeeping",
    "accounting",
    "invoicing",
    "payroll",
    "budgeting",
    "financial reporting",
    "project management",
    "operations",
    "vendor management"
]


HOSPITALITY_SKILLS = [
    "food preparation",
    "food safety",
    "kitchen operations",
    "knife skills",
    "cooking",
    "baking",
    "grilling",
    "line cook",
    "prep cook",
    "menu preparation",
    "dishwashing",
    "cleaning",
    "sanitation",
    "cash handling",
    "pos system",
    "serving",
    "bartending",
    "front desk",
    "guest service",
    "housekeeping"
]


HEALTHCARE_SKILLS = [
    "patient care",
    "clinical support",
    "medical terminology",
    "first aid",
    "cpr",
    "vital signs",
    "care planning",
    "medication assistance",
    "health records",
    "infection control",
    "personal support",
    "elder care"
]


TRADE_LOGISTICS_SKILLS = [
    "warehouse",
    "shipping",
    "receiving",
    "picking",
    "packing",
    "forklift",
    "logistics",
    "supply chain",
    "quality control",
    "maintenance",
    "repair",
    "installation",
    "construction",
    "carpentry",
    "plumbing",
    "electrical",
    "safety procedures",
    "equipment operation"
]


SOFT_SKILLS = [
    "communication",
    "teamwork",
    "collaboration",
    "problem solving",
    "analytical thinking",
    "leadership",
    "ownership",
    "adaptability",
    "attention to detail",
    "time management",
    "organization",
    "reliability",
    "multitasking",
    "customer-oriented",
    "work under pressure",
    "conflict resolution"
]


ALL_SKILLS = (
    TECH_SKILLS
    + BUSINESS_SKILLS
    + HOSPITALITY_SKILLS
    + HEALTHCARE_SKILLS
    + TRADE_LOGISTICS_SKILLS
    + SOFT_SKILLS
)


JOB_TITLE_PATTERNS = {
    "Software Engineer": [
        "software engineer",
        "software developer",
        "backend developer",
        "backend engineer",
        "frontend developer",
        "full stack developer",
        "web developer"
    ],
    "AI Engineer": [
        "ai engineer",
        "machine learning engineer",
        "llm engineer",
        "ml engineer",
        "applied ai engineer"
    ],
    "Data Analyst": [
        "data analyst",
        "business analyst",
        "reporting analyst",
        "data scientist"
    ],
    "Cook / Kitchen Staff": [
        "cook",
        "line cook",
        "prep cook",
        "chef",
        "kitchen helper",
        "kitchen staff"
    ],
    "Server / Customer Service": [
        "server",
        "waiter",
        "waitress",
        "cashier",
        "customer service representative",
        "guest service"
    ],
    "Sales Representative": [
        "sales representative",
        "sales associate",
        "account executive",
        "business development"
    ],
    "Administrative Assistant": [
        "administrative assistant",
        "office assistant",
        "receptionist",
        "coordinator"
    ],
    "Accounting / Finance Assistant": [
        "accounting assistant",
        "bookkeeper",
        "finance assistant",
        "payroll assistant"
    ],
    "Warehouse / Logistics Worker": [
        "warehouse associate",
        "warehouse worker",
        "shipper",
        "receiver",
        "logistics coordinator",
        "forklift operator"
    ],
    "Healthcare Support Worker": [
        "personal support worker",
        "care aide",
        "healthcare assistant",
        "nursing assistant"
    ]
}


INDUSTRY_KEYWORDS = {
    "Technology": [
        "software",
        "developer",
        "engineer",
        "api",
        "cloud",
        "data",
        "ai",
        "machine learning",
        "web application"
    ],
    "Hospitality / Food Service": [
        "restaurant",
        "kitchen",
        "cook",
        "chef",
        "food",
        "server",
        "guest",
        "hospitality"
    ],
    "Business / Sales": [
        "sales",
        "client",
        "customer",
        "crm",
        "lead",
        "account",
        "business development"
    ],
    "Administration": [
        "administrative",
        "office",
        "reception",
        "scheduling",
        "data entry",
        "coordinator"
    ],
    "Accounting / Finance": [
        "accounting",
        "bookkeeping",
        "invoice",
        "payroll",
        "budget",
        "financial"
    ],
    "Healthcare": [
        "patient",
        "care",
        "clinical",
        "medical",
        "healthcare",
        "elder"
    ],
    "Logistics / Trades": [
        "warehouse",
        "shipping",
        "receiving",
        "forklift",
        "construction",
        "maintenance",
        "repair"
    ]
}


RESPONSIBILITY_PATTERNS = {
    "software": "Build and maintain software systems",
    "develop": "Develop and improve business or technical solutions",
    "customer": "Support customers and resolve service issues",
    "client": "Communicate with clients and manage service expectations",
    "food": "Prepare food according to quality and safety standards",
    "kitchen": "Support kitchen operations and maintain cleanliness",
    "inventory": "Track inventory and support operational accuracy",
    "schedule": "Coordinate schedules and administrative tasks",
    "report": "Prepare reports and communicate findings",
    "sales": "Support sales activities and customer acquisition",
    "warehouse": "Handle warehouse, shipping, and receiving tasks",
    "patient": "Support patient care and safety procedures",
    "clean": "Maintain cleanliness, sanitation, and workplace safety"
}


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

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=get_openai_timeout_seconds(),
        max_retries=0
    )

    try:
        response = call_openai_with_retries(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Return only valid JSON. No markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            ),
            operation_name="profile JSON extraction"
        )
    except OpenAIError as exc:
        LOGGER.warning(
            "OpenAI profile extraction unavailable: %s.",
            type(exc).__name__
        )
        return {}

    content = response.choices[0].message.content
    return _safe_json_parse(content)


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    text = _normalize_text(text)
    phrase = _normalize_text(phrase)

    if not text or not phrase:
        return False

    return phrase in text


def _extract_known_skills(text: str, skills: List[str]) -> List[str]:
    found = []

    for skill in skills:
        if _contains_phrase(text, skill):
            found.append(skill)

    return sorted(list(set(found)))


def _guess_job_title(text: str) -> str:
    normalized = _normalize_text(text)

    for title, patterns in JOB_TITLE_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized:
                return title

    if "engineer" in normalized:
        return "Engineer"

    if "developer" in normalized:
        return "Developer"

    if "assistant" in normalized:
        return "Assistant"

    if "manager" in normalized:
        return "Manager"

    if "coordinator" in normalized:
        return "Coordinator"

    return "General Role"


def _guess_industry(text: str) -> str:
    normalized = _normalize_text(text)

    industry_scores = {}

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in normalized:
                score += 1

        industry_scores[industry] = score

    best_industry = max(
        industry_scores,
        key=industry_scores.get
    )

    if industry_scores[best_industry] == 0:
        return "General"

    return best_industry


def _extract_responsibilities(text: str) -> List[str]:
    normalized = _normalize_text(text)
    responsibilities = []

    for keyword, responsibility in RESPONSIBILITY_PATTERNS.items():
        if keyword in normalized:
            responsibilities.append(responsibility)

    return sorted(list(set(responsibilities)))


def _validate_job_profile(profile: Dict) -> bool:
    if not isinstance(profile, dict):
        return False

    required_skills = profile.get("required_skills", [])

    if not isinstance(required_skills, list):
        return False

    return len(required_skills) > 0


def _validate_resume_profile(profile: Dict) -> bool:
    if not isinstance(profile, dict):
        return False

    technical_skills = profile.get("technical_skills", [])
    domain_skills = profile.get("domain_skills", [])
    soft_skills = profile.get("soft_skills", [])

    if not isinstance(technical_skills, list):
        return False

    if not isinstance(domain_skills, list):
        return False

    if not isinstance(soft_skills, list):
        return False

    return len(technical_skills + domain_skills + soft_skills) > 0


def _split_skills_by_domain(skills: List[str]) -> Dict[str, List[str]]:
    technical_skills = []
    domain_skills = []
    soft_skills = []

    tech_set = set(TECH_SKILLS)
    soft_set = set(SOFT_SKILLS)

    for skill in skills:
        skill_lower = skill.lower()

        if skill_lower in tech_set:
            technical_skills.append(skill)
        elif skill_lower in soft_set:
            soft_skills.append(skill)
        else:
            domain_skills.append(skill)

    return {
        "technical_skills": sorted(list(set(technical_skills))),
        "domain_skills": sorted(list(set(domain_skills))),
        "soft_skills": sorted(list(set(soft_skills)))
    }


def extract_job_requirements(job_description: str) -> dict:
    prompt = f"""
You are an expert recruitment analyst.

Extract structured job requirements from the job description.

The job may be from ANY industry, including technology, hospitality,
sales, administration, accounting, healthcare, logistics, trades, or customer service.

Return ONLY valid JSON in this exact format:

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

    llm_result = _call_openai_json(prompt)

    if _validate_job_profile(llm_result):
        return llm_result

    extracted_skills = _extract_known_skills(
        job_description,
        ALL_SKILLS
    )

    split_skills = _split_skills_by_domain(extracted_skills)

    required_skills = (
        split_skills["technical_skills"]
        + split_skills["domain_skills"]
    )

    return {
        "job_title": _guess_job_title(job_description),
        "industry": _guess_industry(job_description),
        "required_skills": required_skills,
        "preferred_skills": [],
        "soft_skills": split_skills["soft_skills"],
        "responsibilities": _extract_responsibilities(job_description)
    }


def extract_resume_capabilities(resume_text: str) -> dict:
    prompt = f"""
You are an expert resume analyst.

Extract structured candidate capabilities from the resume.

The resume may come from ANY background, including technology,
hospitality, sales, administration, accounting, healthcare, logistics,
trades, or customer service.

Return ONLY valid JSON in this exact format:

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

    llm_result = _call_openai_json(prompt)

    if _validate_resume_profile(llm_result):
        return llm_result

    extracted_skills = _extract_known_skills(
        resume_text,
        ALL_SKILLS
    )

    split_skills = _split_skills_by_domain(extracted_skills)

    industry = _guess_industry(resume_text)

    candidate_title = "General Candidate"

    if split_skills["technical_skills"]:
        candidate_title = "Technology Candidate"
    elif industry == "Hospitality / Food Service":
        candidate_title = "Hospitality Candidate"
    elif industry == "Business / Sales":
        candidate_title = "Business / Sales Candidate"
    elif industry == "Administration":
        candidate_title = "Administrative Candidate"
    elif industry == "Accounting / Finance":
        candidate_title = "Accounting / Finance Candidate"
    elif industry == "Healthcare":
        candidate_title = "Healthcare Support Candidate"
    elif industry == "Logistics / Trades":
        candidate_title = "Logistics / Trades Candidate"

    work_evidence = _extract_work_evidence(resume_text)

    return {
        "candidate_title": candidate_title,
        "industries": [industry],
        "technical_skills": split_skills["technical_skills"],
        "domain_skills": split_skills["domain_skills"],
        "soft_skills": split_skills["soft_skills"],
        "work_evidence": work_evidence
    }


def _extract_work_evidence(text: str) -> List[str]:
    evidence_keywords = [
        "built",
        "developed",
        "implemented",
        "designed",
        "created",
        "deployed",
        "managed",
        "supported",
        "prepared",
        "served",
        "handled",
        "maintained",
        "organized",
        "coordinated",
        "assisted",
        "processed",
        "cleaned",
        "cooked",
        "trained",
        "reported",
        "analyzed",
        "improved"
    ]

    sentences = re.split(r"[\n。.!?]", text)
    evidence = []

    for sentence in sentences:
        clean_sentence = sentence.strip()

        if not clean_sentence:
            continue

        normalized = _normalize_text(clean_sentence)

        if any(keyword in normalized for keyword in evidence_keywords):
            evidence.append(clean_sentence)

        if len(evidence) >= 10:
            break

    return evidence


def _normalize_skill_text(skill: str) -> str:
    skill = skill.lower().strip()

    remove_words = [
        "skills",
        "skill",
        "experience",
        "proficiency",
        "knowledge",
        "ability to",
        "able to",
        "familiar with",
        "working with"
    ]

    for word in remove_words:
        skill = skill.replace(word, "")

    skill = re.sub(r"[^a-z0-9+#.\s/-]", " ", skill)
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

    if not job_words or not resume_words:
        return False

    overlap = job_words.intersection(resume_words)

    overlap_ratio = len(overlap) / max(
        len(job_words),
        len(resume_words)
    )

    return overlap_ratio >= 0.5


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

    score = round(score, 2)

    return {
        "dynamic_match_score": score,
        "dynamic_matched_skills": matched,
        "dynamic_missing_skills": missing,

        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,

        "matched_requirements": matched,
        "missing_requirements": missing,

        "feedback": _build_match_feedback(
            score,
            matched,
            missing,
            job_profile,
            resume_profile
        ),
        "recommendations": _build_recommendations(missing),

        "job_profile": job_profile,
        "resume_profile": resume_profile
    }


def _build_match_feedback(
    score: float,
    matched: List[str],
    missing: List[str],
    job_profile: Dict,
    resume_profile: Dict
) -> List[str]:
    feedback = []

    if score >= 0.75:
        feedback.append("Strong alignment with the target role.")
    elif score >= 0.45:
        feedback.append("Moderate alignment with the target role, with several improvement areas.")
    elif score > 0:
        feedback.append("Limited alignment. The resume needs stronger evidence for this role.")
    else:
        feedback.append("No clear skill alignment was detected from the available text.")

    if matched:
        feedback.append(
            "Matched requirements include: " + ", ".join(matched[:8])
        )

    if missing:
        feedback.append(
            "Missing or weakly represented requirements include: "
            + ", ".join(missing[:8])
        )

    job_title = job_profile.get("job_title", "the target role")
    candidate_title = resume_profile.get("candidate_title", "the candidate")

    feedback.append(
        f"The system compared {candidate_title} against {job_title} using extracted skills and responsibilities."
    )

    return feedback


def _build_recommendations(missing: List[str]) -> List[str]:
    if not missing:
        return [
            "Strengthen resume bullet points with specific outcomes and measurable impact.",
            "Add clearer evidence of responsibilities that match the target job description."
        ]

    recommendations = []

    for skill in missing[:6]:
        recommendations.append(
            f"Add concrete resume evidence related to {skill}."
        )

    return recommendations