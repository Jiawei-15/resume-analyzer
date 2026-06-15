def detect_job_category(job_description: str) -> str:
    text = job_description.lower()

    categories = {
        "software_ai": [
            "python", "java", "javascript", "typescript", "fastapi", "api",
            "sql", "database", "machine learning", "deep learning", "llm",
            "rag", "backend", "frontend", "react", "docker", "cloud"
        ],
        "business": [
            "sales", "marketing", "customer", "business development",
            "crm", "account manager", "lead generation", "market research"
        ],
        "finance": [
            "financial", "finance", "accounting", "excel", "budget",
            "audit", "tax", "bookkeeping", "payroll"
        ],
        "healthcare": [
            "patient", "clinical", "nursing", "medical", "healthcare",
            "caregiver", "pharmacy", "hospital"
        ],
        "education": [
            "teaching", "teacher", "student", "curriculum", "classroom",
            "tutor", "education", "lesson"
        ],
        "hospitality": [
            "restaurant", "server", "barista", "hotel", "kitchen",
            "food", "cashier", "guest service"
        ]
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "general"