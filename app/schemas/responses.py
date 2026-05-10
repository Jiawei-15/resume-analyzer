from pydantic import BaseModel
from typing import List, Any


class ApiResponse(BaseModel):
    success: bool
    data: Any


class MatchResponse(BaseModel):
    filename: str
    resume_skills: List[str]
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    score_explanation: str
    feedback: List[str]