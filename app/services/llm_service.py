import json
import os
from typing import Any, Dict, List

from openai import OpenAI
from app.config import get_openai_timeout_seconds
from app.services.openai_retry import call_openai_with_retries


class LLMService:
    """
    Generates evidence-grounded resume rewrite suggestions.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(
            api_key=api_key,
            timeout=get_openai_timeout_seconds(),
            max_retries=0
        )

    def generate_resume_rewrite_suggestions(
        self,
        resume_text: str,
        job_description: str,
        evidence_map: List[Dict[str, Any]],
        weak_matches: List[str],
        missing_matches: List[str]
    ) -> List[Dict[str, str]]:
        prompt = self._build_prompt(
            resume_text=resume_text,
            job_description=job_description,
            evidence_map=evidence_map,
            weak_matches=weak_matches,
            missing_matches=missing_matches
        )

        response = call_openai_with_retries(
            lambda: self.client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
                temperature=0.2
            ),
            operation_name="resume rewrite"
        )

        output_text = response.output_text

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            return [{
                "target": "LLM output parsing failed",
                "issue": "The LLM did not return valid JSON.",
                "suggested_bullet": "",
                "reason": output_text[:500],
                "confidence": "low"
            }]

        return parsed.get("rewrite_suggestions", [])

    def _build_prompt(
        self,
        resume_text: str,
        job_description: str,
        evidence_map: List[Dict[str, Any]],
        weak_matches: List[str],
        missing_matches: List[str]
    ) -> str:
        return f"""
You are an expert technical resume editor.

Your task:
Generate resume rewrite suggestions based ONLY on the candidate's existing resume evidence and the job requirements.

Critical rules:
1. Do NOT invent experience, projects, companies, metrics, technologies, certifications, or achievements.
2. If evidence is missing, suggest what kind of experience should be added, but mark it as a recommendation, not as a completed achievement.
3. Suggested bullets must be realistic and based on the resume_text or evidence_map.
4. Keep bullets concise, technical, and suitable for a software / AI resume.
5. Return valid JSON only. Do not include markdown.

Return this exact JSON structure:
{{
  "rewrite_suggestions": [
    {{
      "target": "The job requirement being improved",
      "issue": "What is weak or missing",
      "suggested_bullet": "A resume bullet the user can use or adapt",
      "reason": "Why this improves job alignment",
      "confidence": "high | medium | low"
    }}
  ]
}}

Candidate resume:
{resume_text}

Job description:
{job_description}

Evidence map:
{json.dumps(evidence_map, ensure_ascii=False, indent=2)}

Weak matches:
{json.dumps(weak_matches, ensure_ascii=False)}

Missing matches:
{json.dumps(missing_matches, ensure_ascii=False)}
"""