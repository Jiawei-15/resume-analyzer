from typing import List
from pydantic import BaseModel


class UploadData(BaseModel):
    filename: str
    size: int


class UploadResponse(BaseModel):
    success: bool
    data: UploadData


class AnalyzeSummary(BaseModel):
    text_length: int
    skills_count: int
    overall_level: str


class AnalyzeSkills(BaseModel):
    found: List[str]


class AnalyzeReport(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class AnalyzeResumeData(BaseModel):
    filename: str
    summary: AnalyzeSummary
    skills: AnalyzeSkills
    analysis: AnalyzeReport
    text_preview: str


class AnalyzeResumeResponse(BaseModel):
    success: bool
    data: AnalyzeResumeData


class MatchSummary(BaseModel):
    match_score: float
    semantic_score: float
    semantic_source: str
    score_explanation: str


class MatchSkills(BaseModel):
    resume_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]


class MatchReport(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    feedback: List[str]


class MatchResumeData(BaseModel):
    filename: str
    summary: MatchSummary
    skills: MatchSkills
    analysis: MatchReport


class MatchResumeResponse(BaseModel):
    success: bool
    data: MatchResumeData