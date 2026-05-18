const form = document.getElementById("match-form");
const resultBox = document.getElementById("result");

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
                    <strong>Error:</strong> ${result.detail || "Something went wrong."}
                </div>
            `;
            return;
        }

        const data = result.data;

        const summary = data.summary || {};
        const skills = data.skills || {};
        const analysis = data.analysis || {};

        const matchScore = typeof summary.match_score === "number" ? summary.match_score : 0;
        const semanticScore = typeof summary.semantic_score === "number" ? summary.semantic_score : 0;

        const scorePercent = Math.round(matchScore * 100);
        const semanticPercent = Math.round(semanticScore * 100);

        resultBox.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div>
                        <h2>Analysis Result</h2>
                        <p class="file-name">${data.filename}</p>
                    </div>
                    <div class="score-badge">${scorePercent}%</div>
                </div>

                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>

                <p class="score-text">${summary.score_explanation || "No score explanation available."}</p>

                <p><strong>Semantic Score:</strong> ${semanticPercent}%</p>

                <p><strong>Semantic Source:</strong> ${summary.semantic_source || "unknown"}</p>

                <div class="result-grid">
                    <div class="result-section">
                        <h3>Resume Skills</h3>
                        <ul>
                            ${renderList(skills.resume_skills, "No resume skills found.")}
                        </ul>
                    </div>

                    <div class="result-section">
                        <h3>Matched Skills</h3>
                        <ul>
                            ${renderList(skills.matched_skills, "No matched skills found.")}
                        </ul>
                    </div>

                    <div class="result-section">
                        <h3>Missing Skills</h3>
                        <ul>
                            ${renderList(skills.missing_skills, "No missing skills found.")}
                        </ul>
                    </div>
                </div>

                <div class="result-section feedback-section">
                    <h3>Strengths</h3>
                    <ul>
                        ${renderList(analysis.strengths, "No strengths detected.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>Weaknesses</h3>
                    <ul>
                        ${renderList(analysis.weaknesses, "No major weaknesses detected.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>Suggestions</h3>
                    <ul>
                        ${renderList(analysis.suggestions, "No suggestions available.")}
                    </ul>
                </div>

                <div class="result-section feedback-section">
                    <h3>Feedback</h3>
                    <ul>
                        ${renderList(analysis.feedback, "No major feedback needed.")}
                    </ul>
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


function renderList(items, emptyMessage) {
    if (!items || items.length === 0) {
        return `<li>${emptyMessage}</li>`;
    }

    return items.map(item => `<li>${item}</li>`).join("");
}