from app.agents.recruitment_agents import (
    JobAnalysisAgent,
    ResumeAnalysisAgent,
    EvidenceRetrievalAgent,
    MatchDiagnosisAgent,
    LLMResumeRewriteAgent
)


class RecruitmentOrchestrator:

    def __init__(self):

        self.job_agent = JobAnalysisAgent()

        self.resume_agent = ResumeAnalysisAgent()

        self.evidence_agent = EvidenceRetrievalAgent()

        self.match_agent = MatchDiagnosisAgent()

        self.rewrite_agent = LLMResumeRewriteAgent()

    def run(
        self,
        resume_text,
        job_description
    ):

        state = {
            "resume_text": resume_text,
            "job_description": job_description
        }

        trace = []

        job_result = self.job_agent.run(state)

        trace.append(job_result)

        if not self._is_success(job_result):
            return self._build_failed_result(
                trace=trace,
                error_stage="job_analysis",
                error_message="Job analysis failed."
            )

        state["job_profile"] = self._get_result(job_result)

        resume_result = self.resume_agent.run(state)

        trace.append(resume_result)

        if not self._is_success(resume_result):
            return self._build_failed_result(
                trace=trace,
                error_stage="resume_analysis",
                error_message="Resume analysis failed.",
                state=state
            )

        state["resume_profile"] = self._get_result(resume_result)

        evidence_result = self.evidence_agent.run(state)

        trace.append(evidence_result)

        if self._is_success(evidence_result):
            state["evidence_profile"] = self._get_result(evidence_result)
        else:
            state["evidence_profile"] = {
                "retrieved_evidence": "",
                "chunks_count": 0,
                "retrieved_chunks_count": 0,
                "error": "Evidence retrieval failed."
            }

        match_result = self.match_agent.run(state)

        trace.append(match_result)

        if self._is_success(match_result):
            state["match_profile"] = self._get_result(match_result)
        else:
            state["match_profile"] = {
                "error": "Match diagnosis failed."
            }

        rewrite_result = self.rewrite_agent.run(state)

        trace.append(rewrite_result)

        if self._is_success(rewrite_result):
            state["rewrite_profile"] = self._get_result(rewrite_result)
        else:
            state["rewrite_profile"] = {
                "rewrite_suggestions": [],
                "used_fallback": True,
                "llm_error": "Rewrite agent failed."
            }

        return {
            "trace": trace,
            "job_profile": state.get("job_profile", {}),
            "resume_profile": state.get("resume_profile", {}),
            "evidence_profile": state.get("evidence_profile", {}),
            "match_result": state.get("match_profile", {}),
            "rewrite_profile": state.get("rewrite_profile", {})
        }

    def _is_success(self, agent_result):

        if agent_result.get("success") is True:
            return True

        if agent_result.get("status") == "success":
            return True

        return False

    def _get_result(self, agent_result):

        return agent_result.get(
            "result",
            {}
        )

    def _build_failed_result(
        self,
        trace,
        error_stage,
        error_message,
        state=None
    ):

        if state is None:
            state = {}

        return {
            "trace": trace,
            "job_profile": state.get("job_profile", {}),
            "resume_profile": state.get("resume_profile", {}),
            "evidence_profile": state.get("evidence_profile", {}),
            "match_result": {
                "error_stage": error_stage,
                "error": error_message,
                "match_score": 0.0,
                "matched_skills": [],
                "missing_skills": [],
                "feedback": [
                    error_message
                ],
                "recommendations": [],
                "risk_flags": []
            },
            "rewrite_profile": {
                "rewrite_suggestions": [],
                "used_fallback": True,
                "llm_error": error_message
            }
        }