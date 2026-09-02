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
        resultBox.innerHTML = `
            <div class="error">
                <strong>Error:</strong> Please upload a resume file.
            </div>
        `;
        return;
    }

    if (!jobDescription.trim()) {
        resultBox.innerHTML = `
            <div class="error">
                <strong>Error:</strong> Please enter a job description.
            </div>
        `;
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

        const jobProfile = data.job_profile || {};
        const resumeProfile = data.resume_profile || {};

        const dynamicScore = getNumber(
            data.dynamic_match_score ?? data.match_score,
            0
        );

        const scorePercent = clampNumber(
            Math.round(dynamicScore * 100),
            0,
            100
        );

        const semanticScorePercent = normalizeScorePercent(
            data.semantic_score
        );
        const semanticSource = data.semantic_source || "unknown";
        const matchedSkills =
            data.dynamic_matched_skills
            || data.matched_skills
            || data.matched_requirements
            || [];

        const missingSkills =
            data.dynamic_missing_skills
            || data.missing_skills
            || data.missing_requirements
            || [];

        const jobTitle =
            jobProfile.job_title
            || data.job_title
            || "Unknown role";

        const industry =
            jobProfile.industry
            || data.industry
            || "Unknown industry";

        const candidateTitle =
            resumeProfile.candidate_title
            || data.candidate_title
            || "Unknown candidate profile";

        const requiredSkills =
            jobProfile.required_skills
            || data.required_skills
            || [];

        const preferredSkills =
            jobProfile.preferred_skills
            || data.preferred_skills
            || [];

        const jobSoftSkills =
            jobProfile.soft_skills
            || data.soft_skills
            || [];

        const responsibilities =
            jobProfile.responsibilities
            || data.responsibilities
            || [];

        const candidateIndustries =
            resumeProfile.industries
            || [];

        const technicalSkills =
            resumeProfile.technical_skills
            || [];

        const domainSkills =
            resumeProfile.domain_skills
            || [];

        const candidateSoftSkills =
            resumeProfile.soft_skills
            || [];

        const workEvidence =
            resumeProfile.work_evidence
            || data.work_evidence
            || [];

        const retrievedEvidence = data.retrieved_evidence || "";
        const rewriteSuggestions = data.rewrite_suggestions || [];
        const agentTrace = data.agent_trace || [];

        const usedFallback = data.used_fallback;
        const llmError = data.llm_error;

        resultBox.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div>
                        <h2>AI Recruitment & Career Match Report</h2>
                        <p class="file-name">${escapeHTML(data.filename || "Unknown file")}</p>
                    </div>
                    <div class="score-badge">${scorePercent}%</div>
                </div>

                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>

                <p class="score-text">
                    ${buildScoreExplanation(scorePercent, matchedSkills, missingSkills)}
                </p>

                <div class="result-grid">
                    <div class="result-section">
                        <h3>Overall Scores</h3>
                        <p><strong>Dynamic Match:</strong> ${scorePercent}%</p>
                        <p><strong>Semantic Score:</strong> ${semanticScorePercent}%</p>
                        <p><strong>Semantic Source:</strong> ${escapeHTML(semanticSource)}</p>
                        <p><strong>Matched Requirements:</strong> ${matchedSkills.length}</p>
                        <p><strong>Missing Requirements:</strong> ${missingSkills.length}</p>
                        <p><strong>LLM Fallback Used:</strong> ${escapeHTML(String(usedFallback ?? "unknown"))}</p>
                    </div>

                    <div class="result-section">
                        <h3>System Classification</h3>
                        <p><strong>Industry:</strong> ${escapeHTML(industry)}</p>
                        <p><strong>Job Title:</strong> ${escapeHTML(jobTitle)}</p>
                        <p><strong>Candidate Profile:</strong> ${escapeHTML(candidateTitle)}</p>
                    </div>
                </div>

                <div class="result-section feedback-section">
                    <h3>1. Role Understanding</h3>

                    <p><strong>Target Role:</strong> ${escapeHTML(jobTitle)}</p>
                    <p><strong>Industry:</strong> ${escapeHTML(industry)}</p>

                    <h4>Required Skills</h4>
                    <ul>
                        ${renderList(requiredSkills, "No required skills extracted.")}
                    </ul>

                    <h4>Preferred Skills</h4>
                    <ul>
                        ${renderList(preferredSkills, "No preferred skills extracted.")}
                    </ul>

                    <h4>Soft Skills</h4>
                    <ul>
                        ${renderList(jobSoftSkills, "No soft skills extracted.")}
                    </ul>

                    <h4>Responsibilities</h4>
                    <ul>
                        ${renderList(responsibilities, "No responsibilities extracted.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>2. Candidate Understanding</h3>

                    <p><strong>Candidate Profile:</strong> ${escapeHTML(candidateTitle)}</p>

                    <h4>Candidate Industries</h4>
                    <ul>
                        ${renderList(candidateIndustries, "No candidate industries extracted.")}
                    </ul>

                    <h4>Technical Skills</h4>
                    <ul>
                        ${renderList(technicalSkills, "No technical skills extracted.")}
                    </ul>

                    <h4>Domain Skills</h4>
                    <ul>
                        ${renderList(domainSkills, "No domain skills extracted.")}
                    </ul>

                    <h4>Soft Skills</h4>
                    <ul>
                        ${renderList(candidateSoftSkills, "No soft skills extracted.")}
                    </ul>

                    <h4>Work Evidence</h4>
                    <ul>
                        ${renderList(workEvidence, "No work evidence extracted.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>3. Match Diagnosis</h3>

                    <h4>Matched Skills / Requirements</h4>
                    <ul>
                        ${renderList(matchedSkills, "No matched skills detected.")}
                    </ul>

                    <h4>Missing Skills / Requirements</h4>
                    <ul>
                        ${renderList(missingSkills, "No missing skills detected.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>4. Evidence From Resume</h3>
                    <p class="score-text">
                        ${escapeHTML(retrievedEvidence || "No retrieved resume evidence available.")}
                    </p>
                </div>

                <div class="result-section feedback-section">
                    <h3>5. Resume Rewrite Suggestions</h3>

                    ${renderRewriteSuggestions(rewriteSuggestions)}

                    ${llmError
                ? `<p class="score-text"><strong>LLM Note:</strong> ${escapeHTML(llmError)}</p>`
                : ""
            }
                </div>

                <div class="result-section feedback-section">
                    <h3>6. Agent Trace</h3>
                    ${renderAgentTrace(agentTrace)}
                </div>
            </div>
        `;

    } catch (error) {
        resultBox.innerHTML = `
            <div class="error">
                <strong>Error:</strong> Failed to connect to the server.
            </div>
        `;
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
            const matchScore = getNumber(record.match_score, 0);
            const semanticScorePercent = normalizeScorePercent(
                record.semantic_score
            );
            return `
                        <div class="history-item">
                            <p><strong>File:</strong> ${escapeHTML(record.filename || "Unknown file")}</p>
                            <p><strong>Match Score:</strong> ${Math.round(matchScore * 100)}%</p>
                            <p><strong>Semantic Score:</strong> ${semanticScorePercent}%</p>
                            <p><strong>Source:</strong> ${escapeHTML(record.semantic_source || "unknown")}</p>
                            <p><strong>Matched:</strong> ${escapeHTML(formatList(record.matched_skills))}</p>
                            <p><strong>Missing:</strong> ${escapeHTML(formatList(record.missing_skills))}</p>
                        </div>
                    `;
        }).join("")}
            </div>
        `;

    } catch (error) {
        historyBox.innerHTML = `
            <div class="error">
                <strong>Error:</strong> Failed to connect to the server.
            </div>
        `;
    }
});

function getNumber(value, fallback = 0) {
    return typeof value === "number" && !Number.isNaN(value)
        ? value
        : fallback;
}

function clampNumber(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function normalizeScorePercent(value) {
    const score = getNumber(value, 0);

    if (score >= 0 && score <= 1) {
        return clampNumber(
            Math.round(score * 100),
            0,
            100
        );
    }

    return clampNumber(
        Math.round(score),
        0,
        100
    );
}
function buildScoreExplanation(scorePercent, matchedSkills, missingSkills) {
    if (scorePercent >= 75) {
        return "Strong alignment. The resume shows clear overlap with the target role.";
    }

    if (scorePercent >= 50) {
        return "Partial alignment. The resume has relevant evidence, but several requirements are still missing or weak.";
    }

    if (scorePercent > 0) {
        return "Weak to partial alignment. The resume needs stronger role-specific evidence before applying.";
    }

    if (matchedSkills.length === 0 && missingSkills.length === 0) {
        return "No match diagnosis was returned. Check whether the extraction and matching pipeline produced structured output.";
    }

    return "Low alignment. The resume does not show enough visible overlap with the job requirements.";
}

function renderList(items, emptyMessage) {
    if (!items || items.length === 0) {
        return `<li>${escapeHTML(emptyMessage)}</li>`;
    }

    return items
        .map(item => `<li>${escapeHTML(formatItem(item))}</li>`)
        .join("");
}

function renderRewriteSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        return `
            <p class="score-text">
                No rewrite suggestions available.
            </p>
        `;
    }

    return suggestions.map((item, index) => {
        if (typeof item === "string") {
            return `
                <div class="suggestion-card">
                    <h4>Suggestion ${index + 1}</h4>
                    <p>${escapeHTML(item)}</p>
                </div>
            `;
        }

        return `
            <div class="suggestion-card">
                <h4>${escapeHTML(item.target || `Suggestion ${index + 1}`)}</h4>
                <p><strong>Issue:</strong> ${escapeHTML(item.issue || "No issue provided.")}</p>
                <p><strong>Suggested Bullet:</strong> ${escapeHTML(item.suggested_bullet || "No bullet suggestion provided.")}</p>
                <p><strong>Reason:</strong> ${escapeHTML(item.reason || "No reason provided.")}</p>
                <p><strong>Confidence:</strong> ${escapeHTML(item.confidence || "unknown")}</p>
            </div>
        `;
    }).join("");
}

function renderAgentTrace(trace) {
    if (!trace || trace.length === 0) {
        return `
            <p class="score-text">
                No agent trace available.
            </p>
        `;
    }

    return `
        <ul>
            ${trace.map(step => {
        const agentName =
            step.agent_name
            || step.agent
            || step.name
            || "Unknown Agent";

        const status =
            step.status
            || step.success
            || "unknown";

        return `
                    <li>
                        <strong>${escapeHTML(agentName)}:</strong>
                        ${escapeHTML(String(status))}
                    </li>
                `;
    }).join("")}
        </ul>
    `;
}

function formatItem(item) {
    if (typeof item === "string") {
        return item;
    }

    if (typeof item === "number") {
        return String(item);
    }

    if (item === null || item === undefined) {
        return "";
    }

    return JSON.stringify(item);
}

function formatList(items) {
    if (!items || items.length === 0) {
        return "None";
    }

    return items.map(formatItem).join(", ");
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
