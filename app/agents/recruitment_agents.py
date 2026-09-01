import uuid

from app.agents.base_agent import BaseAgent

from app.services.ai_skill_service import (
    extract_job_requirements,
    extract_resume_capabilities,
    compare_dynamic_skills
)

from app.services.chunk_service import chunk_text
from app.services.embedding_service import get_embedding
from app.services.vector_store import add_embedding, clear_embeddings, search_embedding


class JobAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__("Job Analysis Agent")

    def run(self, state):

        try:
            result = extract_job_requirements(
                state["job_description"]
            )

            return self.success(result)

        except Exception as e:
            return self.failure(e)


class ResumeAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__("Resume Analysis Agent")

    def run(self, state):

        try:
            result = extract_resume_capabilities(
                state["resume_text"]
            )

            return self.success(result)

        except Exception as e:
            return self.failure(e)


class EvidenceRetrievalAgent(BaseAgent):

    def __init__(self):
        super().__init__("Evidence Retrieval Agent")

    def run(self, state):

        vector_namespace = uuid.uuid4().hex

        try:
            resume_text = state["resume_text"]
            job_description = state["job_description"]

            chunks = chunk_text(resume_text)

            clear_embeddings(
                namespace=vector_namespace
            )

            for chunk in chunks:
                embedding = get_embedding(chunk)

                add_embedding(
                    embedding,
                    chunk,
                    namespace=vector_namespace
                )

            query_embedding = get_embedding(job_description)

            relevant_chunks = search_embedding(
                query_embedding,
                namespace=vector_namespace
            )

            if not relevant_chunks:
                retrieved_evidence = resume_text[:3000]
            else:
                retrieved_evidence = "\n\n".join(relevant_chunks)

            result = {
                "retrieved_evidence": retrieved_evidence,
                "chunks_count": len(chunks),
                "retrieved_chunks_count": len(relevant_chunks)
            }

            return self.success(result)

        except Exception as e:
            return self.failure(e)

        finally:
            clear_embeddings(
                namespace=vector_namespace
            )


class MatchDiagnosisAgent(BaseAgent):

    def __init__(self):
        super().__init__("Match Diagnosis Agent")

    def run(self, state):

        try:
            result = compare_dynamic_skills(
                state["job_profile"],
                state["resume_profile"]
            )

            return self.success(result)

        except Exception as e:
            return self.failure(e)


class ResumeRewriteAgent(BaseAgent):
    """
    Rule-based fallback rewrite agent.

    This agent is used when:
    - LLM service is not configured
    - LLM call fails
    - LLM returns empty or invalid suggestions
    """

    def __init__(self):
        super().__init__("Resume Rewrite Agent")

    def run(self, state):

        try:
            match_profile = state.get("match_profile", {})
            job_profile = state.get("job_profile", {})

            missing_items = self._extract_missing_items(match_profile)
            weak_items = self._extract_weak_items(match_profile)

            suggestions = []

            for item in weak_items:
                suggestions.append(
                    self._build_suggestion(
                        target=item,
                        strength="weak"
                    )
                )

            for item in missing_items:
                suggestions.append(
                    self._build_suggestion(
                        target=item,
                        strength="missing"
                    )
                )

            if not suggestions:
                suggestions.append({
                    "target": "General resume optimization",
                    "issue": "The resume has reasonable alignment with the job profile, but the technical impact can be clearer.",
                    "suggested_bullet": "Refine project descriptions by naming the technologies used, the problem solved, and the measurable or practical outcome.",
                    "reason": "This makes the resume easier for recruiters and AI screening systems to evaluate.",
                    "confidence": "medium"
                })

            result = {
                "rewrite_suggestions": suggestions,
                "used_fallback": True
            }

            return self.success(result)

        except Exception as e:
            return self.failure(e)

    def _extract_missing_items(self, match_profile):

        possible_keys = [
            "missing_skills",
            "missing_matches",
            "gaps",
            "weaknesses",
            "missing_requirements"
        ]

        return self._extract_list_from_keys(
            match_profile,
            possible_keys
        )

    def _extract_weak_items(self, match_profile):

        possible_keys = [
            "weak_matches",
            "partial_matches",
            "improvement_areas",
            "needs_improvement"
        ]

        return self._extract_list_from_keys(
            match_profile,
            possible_keys
        )

    def _extract_list_from_keys(self, data, keys):

        for key in keys:
            value = data.get(key)

            if isinstance(value, list):
                return [
                    str(item)
                    for item in value
                ]

            if isinstance(value, str) and value.strip():
                return [value]

        return []

    def _build_suggestion(self, target, strength):

        if strength == "missing":
            issue = f"No clear resume evidence was found for {target}."
            confidence = "low"
        else:
            issue = f"Resume evidence for {target} is present but not specific enough."
            confidence = "medium"

        return {
            "target": target,
            "issue": issue,
            "suggested_bullet": self._generate_bullet(target, strength),
            "reason": (
                f"This improves alignment with job descriptions that mention {target} "
                "by making the relevant experience easier to identify."
            ),
            "confidence": confidence
        }

    def _generate_bullet(self, target, strength):

        target_lower = target.lower()

        if "fastapi" in target_lower:
            return "Built RESTful backend APIs with FastAPI for resume upload, job description matching, and structured AI analysis."

        if "python" in target_lower:
            return "Developed Python-based backend services for text processing, skill extraction, and job-resume matching."

        if "docker" in target_lower:
            if strength == "missing":
                return "Recommendation: add Docker experience by containerizing the application for consistent local and cloud deployment."
            return "Containerized the application with Docker to improve deployment consistency across local and cloud environments."

        if "rag" in target_lower or "retrieval" in target_lower:
            return "Implemented a retrieval pipeline that maps job requirements to relevant resume evidence using embedding-based similarity search."

        if "openai" in target_lower or "llm" in target_lower:
            return "Integrated LLM-based analysis to generate structured resume feedback, match diagnosis, and improvement suggestions."

        if "sql" in target_lower or "database" in target_lower or "sqlite" in target_lower:
            return "Designed database models to store resume analysis history, match scores, extracted skills, and feedback results."

        if "react" in target_lower or "frontend" in target_lower:
            return "Built an interactive frontend interface to display match scores, retrieved evidence, and resume improvement suggestions."

        return f"Recommendation: add concrete project evidence demonstrating practical use of {target}."


class LLMResumeRewriteAgent(BaseAgent):
    """
    LLM-powered rewrite agent with rule-based fallback.

    Important:
    The LLM should not invent experience.
    It should generate suggestions based on resume text, job description,
    retrieved evidence, and match diagnosis.
    """

    def __init__(self):
        super().__init__("LLM Resume Rewrite Agent")
        self.fallback_agent = ResumeRewriteAgent()

        try:
            from app.services.llm_service import LLMService
            self.llm_service = LLMService()
        except Exception as e:
            self.llm_service = None
            self.initialization_error = str(e)

    def run(self, state):

        if self.llm_service is None:
            fallback_result = self.fallback_agent.run(state)

            if fallback_result.get("success", False):
                fallback_result["result"]["used_fallback"] = True
                fallback_result["result"]["llm_error"] = getattr(
                    self,
                    "initialization_error",
                    "LLM service is not available."
                )

            return fallback_result

        try:
            match_profile = state.get("match_profile", {})
            evidence_profile = state.get("evidence_profile", {})

            retrieved_evidence = evidence_profile.get(
                "retrieved_evidence",
                ""
            )

            weak_matches = self._extract_weak_items(match_profile)
            missing_matches = self._extract_missing_items(match_profile)

            evidence_map = self._build_evidence_map_for_llm(
                retrieved_evidence
            )

            rewrite_suggestions = self.llm_service.generate_resume_rewrite_suggestions(
                resume_text=state.get("resume_text", ""),
                job_description=state.get("job_description", ""),
                evidence_map=evidence_map,
                weak_matches=weak_matches,
                missing_matches=missing_matches
            )

            if not rewrite_suggestions:
                fallback_result = self.fallback_agent.run(state)

                if fallback_result.get("success", False):
                    fallback_result["result"]["used_fallback"] = True
                    fallback_result["result"]["llm_error"] = "LLM returned empty suggestions."

                return fallback_result

            result = {
                "rewrite_suggestions": rewrite_suggestions,
                "used_fallback": False,
                "llm_error": None
            }

            return self.success(result)

        except Exception as e:
            fallback_result = self.fallback_agent.run(state)

            if fallback_result.get("success", False):
                fallback_result["result"]["used_fallback"] = True
                fallback_result["result"]["llm_error"] = str(e)

            return fallback_result

    def _build_evidence_map_for_llm(self, retrieved_evidence):

        if not retrieved_evidence:
            return []

        return [
            {
                "requirement": "General job description alignment",
                "evidence_strength": "retrieved",
                "evidence": [
                    {
                        "chunk": retrieved_evidence,
                        "score": "N/A"
                    }
                ]
            }
        ]

    def _extract_missing_items(self, match_profile):

        possible_keys = [
            "missing_skills",
            "missing_matches",
            "gaps",
            "weaknesses",
            "missing_requirements"
        ]

        return self._extract_list_from_keys(
            match_profile,
            possible_keys
        )

    def _extract_weak_items(self, match_profile):

        possible_keys = [
            "weak_matches",
            "partial_matches",
            "improvement_areas",
            "needs_improvement"
        ]

        return self._extract_list_from_keys(
            match_profile,
            possible_keys
        )

    def _extract_list_from_keys(self, data, keys):

        for key in keys:
            value = data.get(key)

            if isinstance(value, list):
                return [
                    str(item)
                    for item in value
                ]

            if isinstance(value, str) and value.strip():
                return [value]

        return []
