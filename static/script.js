const form = document.getElementById("match-form");
const resultBox = document.getElementById("result");
const historyButton = document.getElementById("history-button");
const historyBox = document.getElementById("history");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    resultBox.innerHTML = `<div class="loading">Analyzing resume...</div>`;

    const fileInput = document.getElementById("resume");
    const jobDescription = document.getElementById("job-description").value;

    if (!fileInput.files || fileInput.files.length === 0) {
        resultBox.innerHTML = `<div class="error"><strong>Error:</strong> Please upload a resume file.</div>`;
        return;
    }

    if (!jobDescription.trim()) {
        resultBox.innerHTML = `<div class="error"><strong>Error:</strong> Please enter a job description.</div>`;
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("job_description", jobDescription);

    try {
        const response = await fetch("/match", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            resultBox.innerHTML = `
                <div class="error">
                    <strong>Error:</strong> ${escapeHTML(result.detail || "Something went wrong.")}
                </div>
            `;
            return;
        }

        const data = result.data || {};
        const summary = data.summary || {};
        const analysis = data.analysis || {};
        const recommendations = data.recommendations || {};
        const riskFlags = data.risk_flags || [];
        const dynamicAnalysis = data.dynamic_analysis || {};
        const jobProfileWrapper = data.job_profile || {};
        const rag = data.rag || {};

        const aiJobProfile = dynamicAnalysis.job_profile || {};
        const aiResumeProfile = dynamicAnalysis.resume_profile || {};

        const matchScore = typeof summary.match_score === "number" ? summary.match_score : 0;
        const semanticScore = typeof summary.semantic_score === "number" ? summary.semantic_score : 0;
        const dynamicScore = typeof dynamicAnalysis.dynamic_match_score === "number"
            ? dynamicAnalysis.dynamic_match_score
            : 0;

        const scorePercent = Math.round(matchScore * 100);
        const semanticPercent = Math.round(semanticScore * 100);
        const dynamicPercent = Math.round(dynamicScore * 100);

        resultBox.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div>
                        <h2>AI Recruitment & Career Match Report</h2>
                        <p class="file-name">${escapeHTML(data.filename || "Unknown file")}</p>
                    </div>
                    <div class="score-badge">${dynamicPercent}%</div>
                </div>

                <div class="score-bar">
                    <div class="score-fill" style="width: ${dynamicPercent}%"></div>
                </div>

                <p class="score-text">
                    ${escapeHTML(summary.score_explanation || "No score explanation available.")}
                </p>

                <div class="result-grid">
                    <div class="result-section">
                        <h3>Overall Scores</h3>
                        <p><strong>Dynamic AI Match:</strong> ${dynamicPercent}%</p>
                        <p><strong>Keyword Match:</strong> ${scorePercent}%</p>
                        <p><strong>Semantic Score:</strong> ${semanticPercent}%</p>
                        <p><strong>Semantic Source:</strong> ${escapeHTML(summary.semantic_source || "unknown")}</p>
                        <p><strong>Match Level:</strong> ${escapeHTML(summary.level || "unknown")}</p>
                    </div>

                    <div class="result-section">
                        <h3>System Classification</h3>
                        <p><strong>Rule Category:</strong> ${escapeHTML(jobProfileWrapper.category || "unknown")}</p>
                        <p><strong>AI Industry:</strong> ${escapeHTML(aiJobProfile.industry || "unknown")}</p>
                        <p><strong>AI Job Title:</strong> ${escapeHTML(aiJobProfile.job_title || "unknown")}</p>
                    </div>
                </div>

                <div class="result-section feedback-section">
                    <h3>1. Role Understanding</h3>
                    <p><strong>Target Role:</strong> ${escapeHTML(aiJobProfile.job_title || "Unknown role")}</p>
                    <p><strong>Industry:</strong> ${escapeHTML(aiJobProfile.industry || "Unknown industry")}</p>

                    <h4>Required Skills</h4>
                    <ul>
                        ${renderList(aiJobProfile.required_skills, "No required skills extracted.")}
                    </ul>

                    <h4>Preferred Skills</h4>
                    <ul>
                        ${renderList(aiJobProfile.preferred_skills, "No preferred skills extracted.")}
                    </ul>

                    <h4>Responsibilities</h4>
                    <ul>
                        ${renderList(aiJobProfile.responsibilities, "No responsibilities extracted.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>2. Candidate Understanding</h3>
                    <p><strong>Candidate Profile:</strong> ${escapeHTML(aiResumeProfile.candidate_title || "Unknown candidate profile")}</p>

                    <h4>Candidate Industries</h4>
                    <ul>
                        ${renderList(aiResumeProfile.industries, "No candidate industries extracted.")}
                    </ul>

                    <h4>Technical Skills</h4>
                    <ul>
                        ${renderList(aiResumeProfile.technical_skills, "No technical skills extracted.")}
                    </ul>

                    <h4>Domain Skills</h4>
                    <ul>
                        ${renderList(aiResumeProfile.domain_skills, "No domain skills extracted.")}
                    </ul>

                    <h4>Soft Skills</h4>
                    <ul>
                        ${renderList(aiResumeProfile.soft_skills, "No soft skills extracted.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>3. Match Diagnosis</h3>

                    <h4>AI Matched Skills</h4>
                    <ul>
                        ${renderList(dynamicAnalysis.dynamic_matched_skills, "No AI matched skills.")}
                    </ul>

                    <h4>AI Missing Skills</h4>
                    <ul>
                        ${renderList(dynamicAnalysis.dynamic_missing_skills, "No AI missing skills.")}
                    </ul>

                    <h4>Strengths</h4>
                    <ul>
                        ${renderList(analysis.strengths, "No strengths detected.")}
                    </ul>

                    <h4>Weaknesses</h4>
                    <ul>
                        ${renderList(analysis.weaknesses, "No major weaknesses detected.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>4. Evidence From Resume</h3>
                    <p class="score-text">
                        ${escapeHTML(rag.retrieved_context_preview || "No retrieved resume evidence available.")}
                    </p>
                </div>

                <div class="result-section feedback-section">
                    <h3>5. Action Plan</h3>

                    <h4>Suggestions</h4>
                    <ul>
                        ${renderList(analysis.suggestions, "No suggestions available.")}
                    </ul>

                    <h4>Suggested Resume Bullets</h4>
                    <ul>
                        ${renderList(recommendations.resume_bullets, "No resume bullet suggestions available.")}
                    </ul>

                    <h4>Interview Talking Points</h4>
                    <ul>
                        ${renderList(recommendations.interview_talking_points, "No interview talking points available.")}
                    </ul>

                    <h4>Risk Flags</h4>
                    <ul>
                        ${renderList(riskFlags, "No major risk flags detected.")}
                    </ul>

                    <h4>Feedback</h4>
                    <ul>
                        ${renderList(analysis.feedback, "No major feedback needed.")}
                    </ul>
                </div>
            </div>
        `;

    } catch (error) {
        resultBox.innerHTML = `<div class="error"><strong>Error:</strong> Failed to connect to the server.</div>`;
    }
});

historyButton.addEventListener("click", async () => {
    historyBox.innerHTML = `<div class="loading">Loading history...</div>`;

    try {
        const response = await fetch("/history");
        const result = await response.json();

        if (!response.ok) {
            historyBox.innerHTML = `
                <div class="error">
                    <strong>Error:</strong> ${escapeHTML(result.detail || "Failed to load history.")}
                </div>
            `;
            return;
        }

        const records = result.data || [];

        if (records.length === 0) {
            historyBox.innerHTML = `
                <div class="history-card">
                    <h3>Recent History</h3>
                    <p>No analysis history yet.</p>
                </div>
            `;
            return;
        }

        historyBox.innerHTML = `
            <div class="history-card">
                <h3>Recent History</h3>
                ${records.map(record => {
            const matchScore = typeof record.match_score === "number"
                ? Math.round(record.match_score * 100)
                : 0;

            const semanticScore = typeof record.semantic_score === "number"
                ? Math.round(record.semantic_score * 100)
                : 0;

            return `
                        <div class="history-item">
                            <p><strong>File:</strong> ${escapeHTML(record.filename || "Unknown file")}</p>
                            <p><strong>Match Score:</strong> ${matchScore}%</p>
                            <p><strong>Semantic Score:</strong> ${semanticScore}%</p>
                            <p><strong>Source:</strong> ${escapeHTML(record.semantic_source || "unknown")}</p>
                            <p><strong>Matched:</strong> ${escapeHTML(formatList(record.matched_skills))}</p>
                            <p><strong>Missing:</strong> ${escapeHTML(formatList(record.missing_skills))}</p>
                        </div>
                    `;
        }).join("")}
            </div>
        `;

    } catch (error) {
        historyBox.innerHTML = `<div class="error"><strong>Error:</strong> Failed to connect to the server.</div>`;
    }
});

function renderList(items, emptyMessage) {
    if (!items || items.length === 0) {
        return `<li>${escapeHTML(emptyMessage)}</li>`;
    }

    return items.map(item => `<li>${escapeHTML(item)}</li>`).join("");
}

function formatList(items) {
    if (!items || items.length === 0) {
        return "None";
    }

    return items.join(", ");
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}